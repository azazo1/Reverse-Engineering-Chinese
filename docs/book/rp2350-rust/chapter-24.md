# Chapter 24: main.rs — The Button Polling Loop

## Introduction

The button driver's `main.rs` is only eleven lines longer than the blink one,
and nine of those are the wiring of a new input pin. It samples the button on a
5 ms cadence, feeds each sample to the debounce filter, and drives the LED from
the filter's verdict. This chapter walks through the final file of the second
driver.

## Complete Source Code

Here is `src/main.rs` for the button driver, in full:

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
//! RP2350 Embedded Rust Embassy Button Driver Application.
//!
//! BRIEF:
//! Main application entry point for RP2350 GPIO button driver using Embassy.
//! Implements button input on GPIO 15 controlling LED on GPIO 16.
//! Button is active-low (tied to GND when pressed).
//!
//! AUTHOR: Kevin Thomas
//! CREATION DATE: November 28, 2025
//! UPDATE DATE: December 5, 2025

#![no_std]
#![no_main]

mod button;
mod config;
mod led;

use button::ButtonController;
use config::DEBOUNCE_DELAY_MS;
use embassy_executor::Spawner;
use embassy_rp::gpio::{Input, Level, Output, Pull};
use embassy_time::Timer;
use led::{led_state_to_level, LedState};
use panic_halt as _;

/// Main application entry point.
///
/// # Details
/// Initializes Embassy runtime and runs the main button polling loop.
/// Uses ButtonController for state management with debouncing.
/// Button on GPIO15 (active-low) controls LED on GPIO16.
///
/// # Arguments
/// * `_spawner` - Embassy task spawner (reserved for future async tasks).
///
/// # Returns
/// * `()` - Never returns (infinite loop).
#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let p = embassy_rp::init(Default::default());
    let button = Input::new(p.PIN_15, Pull::Up);
    let mut led = Output::new(p.PIN_16, Level::Low);
    let mut controller = ButtonController::new();
    loop {
        controller.update(button.is_high());
        let state = if controller.is_pressed() {
            LedState::On
        } else {
            LedState::Off
        };
        if led_state_to_level(state) {
            led.set_high();
        } else {
            led.set_low();
        }
        Timer::after_millis(DEBOUNCE_DELAY_MS).await;
    }
}
```

The structure is the blink main's, with one input added and the controller
swapped. Everything new lives in how the loop consumes `button`.

## Configuration Locality

Three modules, one convention:

```rust
mod button;
mod config;
mod led;
```

`config` is imported from directly this time — its `DEBOUNCE_DELAY_MS` appears
in the loop. The active-low comment appears both in `button.rs`'s docs and in
`main`'s BRIEF: the convention is repeated wherever it governs behavior.

## Configuring the Input

```rust
let button = Input::new(p.PIN_15, Pull::Up);
```

One line configures an input on GPIO15 with an internal pull-up (Chapters 17
and 22). The initial state: the line is held HIGH by the pull-up, so `is_high()`
returns `true` — exactly what the debounce filter expects for "released".
No pad-level code, no function-select dance; the HAL folded it all into
`Input::new`.

The output pin is created exactly as in the blink driver:

```rust
let mut led = Output::new(p.PIN_16, Level::Low);
```

and the filter starts fresh:

```rust
let mut controller = ButtonController::new();
```

## Sampling With Debounce

The loop's first act is the sample-and-filter:

```rust
loop {
    controller.update(button.is_high());
```

`button.is_high()` reads the pad and returns a bool; `controller.update(...)`
applies the active-low inversion and the counter logic from Chapter 23. The
sample cadence comes from the bottom of the loop — the `Timer` wait — so every
iteration is one sample at `DEBOUNCE_DELAY_MS` spacing:

```
sample  update   is_pressed   set LED   sleep 5ms
   |       |         |            |          |
   +-------+---------+------------+----------+----> repeat
```

Because the whole loop runs in microseconds except the 5 ms sleep, the filter
samples at a steady ~200 Hz. The executor idles for the money.

## Driving the LED

The verdict is translated through the shared helper:

```rust
let state = if controller.is_pressed() {
    LedState::On
} else {
    LedState::Off
};
if led_state_to_level(state) {
    led.set_high();
} else {
    led.set_low();
}
```

Two decision points, one obvious reading:

1. Filter verdict → `LedState` (pressed lights the LED, `LedState::On`).
2. `LedState` → GPIO level via the reusable `led_state_to_level` from the blink
   driver (now part of this binary's `mod led`).

Holding the button keeps `pressed == true`, so the LED stays lit; releasing
reverses the dance symmetrically. There is no edge-triggered latch — the state
follows the filter directly.

## The Whole Program in One View

The driver is sensor → filter → decision → actuator, in a circle:

```
+--------+      +------------------+      +---------------+
| GPIO15 | --→  | ButtonController | --→  | LedState      |
| is_high|      | (debounce)       |      | (on/off)      |
+--------+      +------------------+      +---------------+
                                                |
                                                v
+--------+      +------------------+      +---------------+
| Timer  | ←--  | 5 ms cadence     |      | GPIO16 output |
+--------+      +------------------+      +---------------+
```

Blink proved a state machine could drive an output on a timer. Button proves an
input can drive the same state machine through a filter. The UART driver,
which completes the course, follows the identical shape.

## Summary

- `Input::new(p.PIN_15, Pull::Up)` configures the button input in one line.
- The loop samples once per `DEBOUNCE_DELAY_MS` (5 ms), feeding the filter
  through `controller.update(button.is_high())`.
- The filter's verdict selects `LedState::On/Off`, and the shared
  `led_state_to_level` drives GPIO16.
- Entire driver = sensor → debounce → decision → actuator → timer.

Now we step back and look at the trick that made all of these files testable on
a laptop: the host test harness.