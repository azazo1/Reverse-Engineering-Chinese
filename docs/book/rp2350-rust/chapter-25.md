# Chapter 25: Host Testing with cargo test

## Introduction

Every driver in this course ships a test suite, and every suite runs on a
desktop — not the chip. The mechanism is a two-file trick of Cargo configuration
we glimpsed in Chapters 8, 18, and 19. This chapter turns it into a complete
story: why host testing matters, how `lib.rs` makes a crate dual-purpose, and
what `make test` actually commands.

## Why Test on the Host

Hardware is not a good test harness. Each test run requires flashing, wiring,
and human observation, and the answers come back in seconds or minutes — or as
a mysterious LED pattern. State machines, constants, and conversion functions,
on the other hand, need no hardware at all: give them inputs, assert on
outputs, repeat.

Compare the two loops:

```
On the chip:                   On the host:
build -> flash -> wire         cargo test --lib --no-default-features
-> press button -> observe     -> 20 asserts in ~1 second
-> repeat for each change       -> repeat freely, zero wiring
```

Config typos, broken `toggle` transitions, and debounce edge cases are found in
milliseconds on a laptop, long before the board is ever powered. The test suite
becomes part of normal development, not an afterthought.

## lib.rs and cfg_attr

The library root is the hinge. Its single attribution line switches the crate
between `no_std` (when building firmware) and `std` (when testing):

```rust
//! FILE: lib.rs
//!
//! DESCRIPTION:
//! RP2350 Blink Driver Library Module Exports.
//!
//! BRIEF:
//! Exports all public modules for testing and reuse.
//! Conditionally enables std for host testing.
//!
//! AUTHOR: Kevin Thomas
//! CREATION DATE: November 28, 2025
//! UPDATE DATE: December 4, 2025

#![cfg_attr(not(test), no_std)]
pub mod config;
pub mod led;
```

Read the magic line out loud: "apply `no_std` only when we are NOT compiling
for tests."

```
cargo build                    -> cfg(test) false -> #![no_std]   (bare metal)
cargo test                     -> cfg(test) true  -> #![no_std] skipped
                                 (std available for the test runner)
```

The library is always pure logic — `config.rs`, `led.rs`, `button.rs`,
`uart.rs` import nothing embedded — so it builds and runs under `std`
identically. The hardware crates never enter the test build at all.

## make test — no-default-features

The Makefile's test target is the complete ritual:

```make
test:
	cargo test --lib --target $(shell rustc --print host-tuple) --no-default-features
```

Decode each flag against what we learned:

- `--lib` — Test only the library target. The binary's `main.rs` is
  `test = false` and is simply not compiled.
- `--target $(shell rustc --print host-tuple)` — Compile for the *host* CPU,
  overriding `.cargo/config.toml`'s embedded target. The tests run as native
  desktop binaries.
- `--no-default-features` — Drop the `default` feature from `Cargo.toml`
  (Chapter 8), which is what pulls in `embassy-executor`, `embassy-time`,
  `embassy-rp`, `cortex-m`, `cortex-m-rt`, and `panic-halt`. None of those can
  build for a desktop; none of them exist in this build.

The result is a second, parallel crate graph: same pure modules, zero embedded
dependencies, everything testable.

## Reading the Test Output

A passing button-driver run looks like this:

```
$ make test
running 20 tests
test tests::test_new_controller_not_pressed ... ok
test tests::test_default_equals_new          ... ok
test tests::test_pressed_after_threshold     ... ok
test tests::test_released_after_threshold    ... ok
test tests::test_debounce_resets_on_bounce   ... ok
test tests::test_rapid_bouncing_rejected     ... ok
...

test result: ok. 20 passed; 0 failed; 0 ignored; 0 measured
```

Because our types derive `Debug` and `PartialEq` (Chapter 5), a failing
`assert_eq!` prints both actual and expected values — readable diagnoses without
any debugger:

```
thread 'tests::test_toggle_off_to_on' panicked at ...
assertion `left == right` failed
  left: Off
 right: On
```

## A Test-Driven Culture

The strict docstring standard and the test suite are two halves of one idea:
code should explain itself and prove itself. The pattern repeats in every
single file —

```
item documented (# Details, # Arguments, # Returns)
       +
item tested (#[test] under a banner-ized module)
```

— so a new constant or method in any driver is finished only when it carries
both. Contributors and readers alike get the same two guarantees: the name says
what it does, and the tests agree.

## Summary

- Hardware is a poor harness; pure logic is testable at millisecond speed.
- `#![cfg_attr(not(test), no_std)]` makes the library `std` under test and
  `no_std` for the target.
- `make test` = `--lib --target <host> --no-default-features`, compiling only
  the pure modules for the desktop.
- Derived `Debug`/`PartialEq` make failures self-explanatory.
- Every item is documented *and* tested — the two halves of the house standard.

Part V complete. The last driver is the most interesting: UART, where interrupts
and DMA make their first appearance.