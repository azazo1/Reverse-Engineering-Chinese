# Chapter 18: Driver Architecture

## Introduction

Before writing the blink driver's first constant, we lay down the skeleton every
driver in this course shares — and the pattern every future RP2350 driver you
write should copy. The design has one goal: put every piece of *decidable*
logic in a library that a desktop test runner can exercise, and leave the binary
with only the embedded shell.

## The Module Split

A driver project contains five source files, divided by role:

```
src/
├── lib.rs      # library root: exports config and logic modules
├── config.rs   # constants, fully documented, all testable
├── led.rs      # the LED state machine (pure logic, testable)
└── main.rs     # the async entry point (embedded only)

(button drivers add button.rs; UART drivers add uart.rs)
```

The rule of thumb: if a piece of code has inputs, outputs, and behavior that
could be wrong, it belongs in the **library**, where you can call it from a
`#[test]`. If a piece of code touches hardware — pins, timers, interrupts — it
belongs in the **binary**, which is not tested (its `test = false` in
`Cargo.toml`, Chapter 8), but is small.

```
+------------------+          +------------------+
|   lib.rs         |          |   main.rs        |
+------------------+          +------------------+
|  config.rs       |          |  init()          |
|  led.rs          |   test   |  Output::new     |
|  (pure logic)    |  ←────── |  loop { ... }    |
+------------------+          |  Timer.await     |
                              +------------------+
```

## config.rs

The configuration module is a collection of documented constants:

```
pub const BLINK_DELAY_MS: u64 = 500;
pub const MIN_BLINK_DELAY_MS: u64 = 10;
pub const MAX_BLINK_DELAY_MS: u64 = 10000;
```

Every constant answers four questions in its docstring: what is it, why does it
exist, what os the valid range, and what is the concrete value. Chapter 19
shows the standard in its exact, final form.

## lib.rs

Library root is three lines plus the standard header:

```rust
#![cfg_attr(not(test), no_std)]
pub mod config;
pub mod led;
```

- `no_std` unless we are testing — the host-testing switch of Chapter 25.
- The two private source modules become public library modules.

## main.rs

The binary main is the thin shell that turns pure logic into hardware behavior:

```rust
let p = embassy_rp::init(Default::default());
let mut led = Output::new(p.PIN_16, Level::Low);
let mut controller = LedController::new();
loop {
    let state = controller.toggle();
    ...
    Timer::after_millis(controller.delay_ms()).await;
}
```

Notice what `main` does *not* contain: no debounce math, no timing policy, no
state. All of that lives in the library. `main` wires three things together —
the executor, the pin, and the controller — then lets the loop run forever.

## Host Testability

The payoff of the split arrives in one command:

```
cargo test --lib --target <host> --no-default-features
```

Because `config.rs`, `led.rs`, and their siblings are pure Rust — no
`embassy-rp`, no `cortex-m`, no `panic-halt` — they compile on a desktop with
nothing but `core`/`std`, and a full terminal of `#[test]` functions starts and
ends in milliseconds. Hardware behavior (a pin flipping, a wire resetting) is
*not* unit-tested; the *decisions* around it are.

## Summary

- Split the driver into a testable library (`lib.rs`, `config.rs`, `led.rs`)
  and a thin embedded binary (`main.rs`).
- `config.rs` holds documented constants; `lib.rs` exports them under
  `cfg_attr(not(test), no_std)`.
- `main.rs` wires hardware and executor but owns almost no logic.
- The library compiles and tests on the host with `--no-default-features`.

Now we write the real files. Chapter 19 opens with `config.rs` — the standard
headers and the first documented constants.