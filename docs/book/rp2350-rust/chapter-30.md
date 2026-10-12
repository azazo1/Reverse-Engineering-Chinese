# Chapter 30: The Complete Integration

## Introduction

Every driver in this course was built to the same blueprint: a pure, testable
controller; a documented config module; and a tiny async shell that reads
hardware, feeds the controller, and writes hardware back. This final chapter
assembles the three drivers into one integrated firmware — and, more
importantly, shows how to *design* such a system. It ends with the full
architecture and the habits that will serve any future driver.

## The Shared Architecture

Lay the three drivers side by side and the pattern is unmistakable:

```
              BLINK            BUTTON             UART
logic file    led.rs           button.rs          uart.rs
hardware      main.rs          main.rs            main.rs
config        config.rs        config.rs          config.rs
sensor        timer            GPIO15 in          UART0_RX
actuator      GPIO16 out       GPIO16 out         UART0_TX
cadence       Timer 500 ms     Timer 5 ms         interrupt + DMA
```

Every driver is three files with four habits:

1. `config.rs` owns tunables as documented constants.
2. The controller file owns logic as pure methods and hosts the test suite.
3. `main.rs` is the only file that imports Embassy peripherals.
4. The loop is read → controller → write → await.

Because the controller never sees a pin, the whole logic layer is host-testable;
because `main` is thin, the hardware layer is trivially auditable.

## The Integration Project

A practical capstone: one firmware where the button chooses the blink speed,
and UART reports the state. Its skeleton — applying every rule this course
taught — looks like this:

```
src/
  config.rs         delay + baud + debounce constants
  led.rs             LedController (unchanged)
  button.rs          ButtonController (unchanged)
  uart.rs            UartController (unchanged)
  main.rs            executor: button -> led, uart logs state
Cargo.toml / memory.x / build.rs   build system (unchanged)
Makefile            test/build/flash     host testing pipeline
```

The three controllers were designed to compose: each is `Clone + Copy`, each
starts via `new()`, and none of them owns hardware. Integration is then only a
policy decision in `main`:

```rust
#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let p = embassy_rp::init(Default::default());
    let mut led = Output::new(p.PIN_16, Level::Low);
    let mut button = ButtonController::new();
    let mut controller = LedController::new();
    // ... uart setup (Ch 28/29) ...
    loop {
        button.update(true); // sampled from GPIO15 each cycle
        let interval = if button.is_pressed() { 100 } else { 500 };
        let state = controller.toggle();
        led.set_level(Level::from(!led_state_to_level(state)));
        // ... uart.write(state_log).await;
        Timer::after_millis(interval).await;
    }
}
```

That is the course reduced to one loop: sample, decide, act, wait — and every
decision is a named constant or a tested method.

## Split the Work With Async Tasks

The shared-single-loop version is simple, but Embassy rewards a different
shape: independent async **tasks** that run cooperatively. The core insight is
that spawnable tasks divide the system along responsibility lines, letting the
executor interleave them:

```
                    +---------------+
   Spawner -------> | executor      |
                    |               |
                    |  button_task  : samples GPIO15, flips speed via channel
                    |  blink_task   : toggles LED at selected speed
                    |  uart_task    : echoes bytes + logs state changes
                    +---------------+
```

`_spawner` — reserved since Chapter 14 — is exactly what this needs:

```rust
#[embassy_executor::main]
async fn main(spawner: Spawner) {
    spawner.spawn(blink_task()).unwrap();
    spawner.spawn(button_task()).unwrap();
    spawner.spawn(uart_task()).unwrap();
}
```

Each task is a loop like the ones in every driver, and Embassy's time and
signal primitives coordinate them. The debug attribute `#[embassy_executor::task]`
turns each into a runtime entity; the compiler guarantees spawnable tasks are
`Send` and correctly sized. This is the destination the course has been
walking toward: three small loops, one executor, zero polling.

## Rules for the Next Driver

Before you wire a new peripheral, apply the five habits this course made second
nature:

1. **Config first.** Every tunable is a documented constant in `config.rs`
   with a test.
2. **Controller pure.** The logic layer takes primitives and returns echoed
   results — host-testable, no HAL imports.
3. **Docs with the standard.** C-block header, `//!` FILE block, and
   `/// # Details` / `# Arguments` / `# Returns` per item.
4. **Tests per banner.** Construction, behavior, traits — twenty tests are a
   normal morning.
5. **Async shell last.** The `main` file binds peripherals, spawns tasks, and
   loops; it is the only embedded file.

## The Complete Picture

Everything from Chapter 1 to here resolves into one system:

```
+----------------------------------------------------------------------+
|  RP2350 firmware (Rust + Embassy)                                    |
|                                                                      |
|  pure logic  ->  host-tested controllers (std)                       |
|  embedded    ->  thin main.rs shells (no_std)                        |
|  build       ->  config.toml / memory.x / build.rs / Makefile        |
|  async       ->  executor, tasks, Timer, interrupt + DMA UART        |
+----------------------------------------------------------------------+
```

The three drivers are the proof, the tests are the guarantee, and the
architecture is the reusable lesson. You now hold the full developer's path
from a bare chip to an integrated, interrupt-driven, host-tested Rust system.

## Summary

- All three drivers share one blueprint: config constants, pure controllers
  with test suites, and thin async shells.
- Integration composes unchanged controllers; only `main.rs` defines policy.
- Embassy tasks split the system by responsibility under one executor; the
  reserved `_spawner` finally earns its name.
- The five habits — config first, pure controller, standard docs, tests per
  banner, async shell last — apply verbatim to your next driver.
- The course's whole journey collapses to: sample, decide, act, wait —
  cooperatively, safely, and testably.

Congratulations. You built a foundation that will carry every driver you
write next.