# Chapter 23: button.rs — The Button Controller

## Introduction

`button.rs` turns the debounce theory of Chapter 22 into a host-testable
struct. `ButtonController` holds three fields of state and one method that does
all the filtering. Like `led.rs`, this file touches no hardware — it consumes
boolean samples — which is why every bounce scenario in Chapter 22 is a
`#[test]` running on a desktop.

## Complete Source Code

Here is `src/button.rs` in full:

```rust
/*
 * @file button.rs
 * @brief Button input with debouncing
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

//! FILE: button.rs
//!
//! DESCRIPTION:
//! RP2350 Button Input with Debouncing.
//!
//! BRIEF:
//! Implements button state tracking with debounce logic.
//! Button is active-low (tied to GND when pressed).
//!
//! AUTHOR: Kevin Thomas
//! CREATION DATE: December 5, 2025
//! UPDATE DATE: December 5, 2025

use crate::config::DEBOUNCE_COUNT;

/// Button controller with debouncing.
///
/// # Details
/// Maintains button state with software debouncing.
/// Uses sample-based debouncing for reliable detection.
///
/// # Fields
/// * `pressed` - Current debounced button state (true = pressed)
/// * `raw_pressed` - Current raw (unfiltered) state
/// * `debounce_count` - Current debounce counter
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[allow(dead_code)]
pub struct ButtonController {
    pressed: bool,
    raw_pressed: bool,
    debounce_count: u32,
}

impl Default for ButtonController {
    /// Returns default ButtonController instance.
    ///
    /// # Details
    /// Delegates to new() for initialization.
    ///
    /// # Returns
    /// * `Self` - New ButtonController with default values
    #[allow(dead_code)]
    fn default() -> Self {
        Self::new()
    }
}

impl ButtonController {
    /// Creates new button controller.
    ///
    /// # Details
    /// Initializes controller with button released state.
    ///
    /// # Returns
    /// * `Self` - New ButtonController instance
    #[allow(dead_code)]
    pub fn new() -> Self {
        Self {
            pressed: false,
            raw_pressed: false,
            debounce_count: 0,
        }
    }

    /// Updates button state with new GPIO sample.
    ///
    /// # Details
    /// Processes raw GPIO input through debounce filter.
    /// Active-low: false (low GPIO) means pressed.
    ///
    /// # Arguments
    /// * `gpio_high` - true if GPIO high (released), false if low (pressed)
    #[allow(dead_code)]
    pub fn update(&mut self, gpio_high: bool) {
        let new_raw = !gpio_high;
        if new_raw == self.raw_pressed {
            if self.debounce_count < DEBOUNCE_COUNT {
                self.debounce_count += 1;
            }
        } else {
            self.raw_pressed = new_raw;
            self.debounce_count = 0;
        }
        if self.debounce_count >= DEBOUNCE_COUNT {
            self.pressed = self.raw_pressed;
        }
    }

    /// Returns true if button is pressed.
    ///
    /// # Details
    /// Returns debounced button state.
    ///
    /// # Returns
    /// * `bool` - true if button is pressed
    #[allow(dead_code)]
    pub fn is_pressed(&self) -> bool {
        self.pressed
    }
}
```

The interface is just three methods — `new`, `update`, `is_pressed` — but the
debounce behavior they encode is richer than the leading test count suggests:
the file continues with a full test module that we examine after the logic.

## The ButtonController Struct

```rust
pub struct ButtonController {
    pressed: bool,
    raw_pressed: bool,
    debounce_count: u32,
}
```

Three fields, three roles (Chapter 22):

- **`pressed`** — The only field anyone reads. `true` means the button is
  debounced as pressed.
- **`raw_pressed`** — The latest unfiltered reading, active-low-corrected.
- **`debounce_count`** — How many consecutive samples agree with
  `raw_pressed`.

Private fields plus the deriving `Clone, Copy, Debug, PartialEq, Eq` mirror
`LedController` exactly — the drivers are the same pattern with different data,
which is the point of a shared architecture.

## The update Method

The whole filter is eleven lines:

```rust
pub fn update(&mut self, gpio_high: bool) {
    let new_raw = !gpio_high;                       // active-low inversion
    if new_raw == self.raw_pressed {
        if self.debounce_count < DEBOUNCE_COUNT {
            self.debounce_count += 1;               // stable run continues
        }
    } else {
        self.raw_pressed = new_raw;
        self.debounce_count = 0;                    // change detected: reset
    }
    if self.debounce_count >= DEBOUNCE_COUNT {
        self.pressed = self.raw_pressed;            // threshold reached
    }
}
```

Trace each branch:

1. `new_raw = !gpio_high` — apply the active-low convention: a LOW line
   (`gpio_high == false`) is a press (`new_raw == true`).
2. **Same as last reading** — the button is in a stable run. Increment the
   counter, capped at `DEBOUNCE_COUNT`. Cap prevents any overflow noise.
3. **Different from last** — a bounce or a real change. Adopt the new reading
   and reset the counter to zero, so a change must *persist* to count.
4. **Counter reached `DEBOUNCE_COUNT`** — commit `pressed = raw_pressed`.

The threshold test is `>=` while the increment is `< ... += 1`; together they
mean the counter reaches exactly `DEBOUNCE_COUNT` and then holds. The subtlety
pays off in the tests: one sample before the threshold must *not* press
(`test_one_sample_before_threshold`), exactly at it does.

## The is_pressed Method

```rust
pub fn is_pressed(&self) -> bool {
    self.pressed
}
```

A one-line getter. `main` consults it once per loop after feeding in a sample:

```rust
let state = if controller.is_pressed() {
    LedState::On
} else {
    LedState::Off
};
```

The read path is deliberately trivial — all the cleverness happens in
`update`, where the sample arrives.

## The Tests

The `#[cfg(test)]` module proves every scenario from Chapter 22's bounce
theory. The banner groups make them scannable; the names make them
self-describing:

- **Construction** — a fresh controller reports not pressed; `default()` equals
  `new()`.
- **Debounce logic** — GPIO held high stays released; `DEBOUNCE_COUNT + 1`
  presses press; releasing persists the same way.
- **Bounce rejection** — `test_rapid_bouncing_rejected` hammers `update(false)`,
  `update(true)` ten times and asserts the controller never presses. That is
  the whole purpose of the filter in one assertion.
- **Edge cases** — `test_exactly_at_threshold` proves the boundary, and
  `test_debounce_resets_on_bounce` proves a lone `true` sample resets progress
  toward pressing.
- **Trait implementations** — `Clone`, `PartialEq`, `Debug` behave as derived.

These tests run in microseconds on the host, but the board behaves correctly
years later because of them.

## Summary

- `ButtonController` keeps three fields: debounced `pressed`, raw state, and a
  consecutive-sample counter.
- `update` inverts the active-low sample, maintains the counter (reset on
  change, capped while stable), and commits state at the threshold.
- `is_pressed` is the single, trivial read path.
- The test suite proves construction, debounce threshold, bounce rejection, and
  edge cases — all without hardware.

Next, the button driver's `main.rs`, where the sample loop meets the filter.