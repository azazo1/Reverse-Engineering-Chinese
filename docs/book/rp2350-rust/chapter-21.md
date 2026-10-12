# Chapter 21: main.rs — The Async Blink Loop

## Introduction

`main.rs` is the only file that touches the RP2350. It initializes the HAL,
configures one GPIO output, and runs an infinite async loop that toggles a
`LedController` and writes the result to the pin. Every concept from Part III —
executor, `Timer`, GPIO, peripherals — lands here in 80 lines.

## Complete Source Code

Here is `src/main.rs` in full:

```rust
/*
 * @file main.rs
 * @brief Microcontroller entry point
 * @author Kevin Thomas
 * @date 2025
 *
 * MIT License
 *
 * Copyright (c) 2025 Kevin Thomas
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

//! FILE: main.rs
//!
//! DESCRIPTION:
//! RP2350 Embedded Rust Embassy Blink Application.
//!
//! BRIEF:
//! Main application entry point for RP2350 GPIO blink driver using Embassy.
//! Implements async LED blinking on GPIO 16.
//!
//! AUTHOR: Kevin Thomas
//! CREATION DATE: November 28, 2025
//! UPDATE DATE: December 4, 2025

#![no_std]
#![no_main]

mod config;
mod led;

use embassy_executor::Spawner;
use embassy_rp::gpio::{Level, Output};
use embassy_time::Timer;
use led::{led_state_to_level, LedController};
use panic_halt as _;

/// Main application entry point.
///
/// # Details
/// Initializes Embassy runtime and runs the main blink loop.
/// Uses BlinkController for state management.
///
/// # Arguments
/// * `_spawner` - Embassy task spawner (reserved for future async tasks).
///
/// # Returns
/// * `()` - Never returns (infinite loop).
#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let p = embassy_rp::init(Default::default());
    let mut led = Output::new(p.PIN_16, Level::Low);
    let mut controller = LedController::new();
    loop {
        let state = controller.toggle();
        if led_state_to_level(state) {
            led.set_high();
        } else {
            led.set_low();
        }
        Timer::after_millis(controller.delay_ms()).await;
    }
}
```

Every line earns its place. We work top to bottom.

## Crate Attributes

```rust
#![no_std]
#![no_main]
```

Chapter 7 in two lines. The binary runs on bare metal with no standard main.
Embedded-only dependencies — `embassy-rp`, `cortex-m-rt`, `panic-halt` — exist
because these attributes demanded them.

## Module Declarations and Imports

```rust
mod config;
mod led;
```

`mod` pulls the two library files into this binary's tree. `config` is used
indirectly (its constant flows in through `LedController::new()`); `led`
supplies `LedController`, `led_state_to_level`, and their friends.

```rust
use embassy_executor::Spawner;
use embassy_rp::gpio::{Level, Output};
use embassy_time::Timer;
use led::{led_state_to_level, LedController};
use panic_halt as _;
```

One item per dependency, exactly the surface this binary needs:

- `Spawner` — the executor handle passed to `main` (unused today).
- `Level` and `Output` — GPIO output configuration.
- `Timer` — the async wait.
- the two `led` exports — the state machine.
- `panic_halt as _` — the panic handler side-effect import.

Nothing extra compiles in; the tiny binary mirrors its tiny purpose.

## The Async Entry Point

```rust
/// Main application entry point.
///
/// # Details
/// Initializes Embassy runtime and runs the main blink loop.
/// Uses BlinkController for state management.
///
/// # Arguments
/// * `_spawner` - Embassy task spawner (reserved for future async tasks).
///
/// # Returns
/// * `()` - Never returns (infinite loop).
#[embassy_executor::main]
async fn main(_spawner: Spawner) {
```

The docstring follows the strict standard even for `main`: `# Details`,
`# Arguments`, and `# Returns` (here, "never returns"). The attribute is Chapter
14 made concrete: it starts the executor and spawns this async function. The
`_spawner` parameter is held for future tasks — the leading underscore tells the
compiler we know it is unused.

## Initializing the Peripherals

```rust
let p = embassy_rp::init(Default::default());
let mut led = Output::new(p.PIN_16, Level::Low);
let mut controller = LedController::new();
```

Three lines, three lifetimes of setup:

- `embassy_rp::init(Default::default())` — Configures clocks, releases reset,
  returns the `Peripherals` tokens (Chapter 16).
- `Output::new(p.PIN_16, Level::Low)` — Claims GPIO16 as an output and drives
  it low (Chapter 17). The token `p.PIN_16` moves into the pin; GPIO16 stays
  ours forever.
- `LedController::new()` — Starts the state machine Off at 500 ms (Chapter 20).

## The Blink Loop

```rust
loop {
    let state = controller.toggle();
    if led_state_to_level(state) {
        led.set_high();
    } else {
        led.set_low();
    }
    Timer::after_millis(controller.delay_ms()).await;
}
```

Four steps per iteration:

1. `controller.toggle()` — advance the state machine and remember the result.
2. `if led_state_to_level(state)` — translate LedState into a hardware
   decision.
3. `led.set_high()` / `set_low()` — actually drive the wire.
4. `Timer::after_millis(controller.delay_ms()).await` — sleep the cooperative
   way, letting the executor idle or run other tasks.

The loop is the heart of the program: at 500 ms per turn, the LED toggles every
half second — the blink.

## Summary

- `main.rs` is the only embedded file; it wires executor, GPIO, and controller.
- `#![no_std]` + `#![no_main]` make it bare metal; `panic_halt as _` covers
  panics.
- `#[embassy_executor::main]` starts the executor on the RP2350.
- Initialization happens once: HAL init, output pin, controller.
- The loop alternates state-machine and GPIO writes around a cooperative
  `Timer` wait.

The blink driver is complete and testable. Part V teaches the second driver —
the button — starting with the hardware reality that makes it interesting:
debouncing.