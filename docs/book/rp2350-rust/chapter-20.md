# Chapter 20: led.rs — The LED State Machine

## Introduction

`led.rs` is the brain of the blink driver: a two-state machine plus a controller
that toggles it. The file is pure logic — no Embassy, no registers, no `unsafe`.
That is deliberate: it is the file you can run on a desktop and prove correct.
This chapter walks through the complete source and then dissects each piece.

## Complete Source Code

Here is `src/led.rs` in full:

```rust
/*
 * @file led.rs
 * @brief LED state management
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

//! FILE: led.rs
//!
//! DESCRIPTION:
//! LED State Management for RP2350.
//!
//! BRIEF:
//! Provides LED state enumeration and blink controller.
//!
//! AUTHOR: Kevin Thomas
//! CREATION DATE: December 5, 2025
//! UPDATE DATE: December 6, 2025

use crate::config::BLINK_DELAY_MS;

/// LED state enumeration.
///
/// # Details
/// Represents the current state of the LED.
/// Used for state tracking and transitions.
///
/// # Variants
/// * `On` - LED is currently on (high)
/// * `Off` - LED is currently off (low)
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[allow(dead_code)]
pub enum LedState {
    On,
    Off,
}

/// LED controller with state tracking.
///
/// # Details
/// Maintains LED state and blink timing configuration.
/// Provides methods for state transitions and queries.
///
/// # Fields
/// * `state` - Current LED state
/// * `delay_ms` - Blink delay in milliseconds
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[allow(dead_code)]
pub struct LedController {
    state: LedState,
    delay_ms: u64,
}

impl Default for LedController {
    /// Returns default LedController instance.
    ///
    /// # Details
    /// Delegates to new() for initialization.
    ///
    /// # Returns
    /// * `Self` - New LedController with default values
    #[allow(dead_code)]
    fn default() -> Self {
        Self::new()
    }
}

impl LedController {
    /// Creates new LED controller with default settings.
    ///
    /// # Details
    /// Initializes controller with LED off.
    ///
    /// # Returns
    /// * `Self` - New LedController instance
    #[allow(dead_code)]
    pub fn new() -> Self {
        Self {
            state: LedState::Off,
            delay_ms: BLINK_DELAY_MS,
        }
    }

    /// Toggles LED state and returns new state.
    ///
    /// # Details
    /// Transitions LED from On to Off or Off to On.
    ///
    /// # Returns
    /// * `LedState` - New LED state after toggle
    #[allow(dead_code)]
    pub fn toggle(&mut self) -> LedState {
        self.state = match self.state {
            LedState::On => LedState::Off,
            LedState::Off => LedState::On,
        };
        self.state
    }

    /// Returns current blink delay.
    ///
    /// # Details
    /// Delay used for blink timing in milliseconds.
    ///
    /// # Returns
    /// * `u64` - Delay in milliseconds
    #[allow(dead_code)]
    pub fn delay_ms(&self) -> u64 {
        self.delay_ms
    }
}

/// Converts LedState to boolean for GPIO control.
///
/// # Details
/// Maps On state to true (high), Off state to false (low).
///
/// # Arguments
/// * `state` - LED state to convert
///
/// # Returns
/// * `bool` - true for On, false for Off
#[allow(dead_code)]
pub fn led_state_to_level(state: LedState) -> bool {
    matches!(state, LedState::On)
}

#[cfg(test)]
mod tests {
    use super::*;

    // ==================== LedState Enum Tests ====================

    #[test]
    fn test_led_state_equality() {
        assert_eq!(LedState::On, LedState::On);
        assert_eq!(LedState::Off, LedState::Off);
        assert_ne!(LedState::On, LedState::Off);
    }

    #[test]
    fn test_led_state_copy() {
        let state = LedState::On;
        let copy = state;
        assert_eq!(state, copy);
    }

    #[test]
    fn test_led_state_to_level_on() {
        assert!(led_state_to_level(LedState::On));
    }

    #[test]
    fn test_led_state_to_level_off() {
        assert!(!led_state_to_level(LedState::Off));
    }

    // ==================== LedController Tests ====================

    #[test]
    fn test_new_controller() {
        let ctrl = LedController::new();
        assert_eq!(ctrl.delay_ms(), BLINK_DELAY_MS);
    }

    #[test]
    fn test_default_equals_new() {
        let default = LedController::default();
        let new = LedController::new();
        assert_eq!(default.delay_ms(), new.delay_ms());
    }

    #[test]
    fn test_toggle_off_to_on() {
        let mut ctrl = LedController::new();
        assert_eq!(ctrl.toggle(), LedState::On);
    }

    #[test]
    fn test_toggle_on_to_off() {
        let mut ctrl = LedController::new();
        ctrl.toggle();
        assert_eq!(ctrl.toggle(), LedState::Off);
    }

    #[test]
    fn test_multiple_toggles() {
        let mut ctrl = LedController::new();
        assert_eq!(ctrl.toggle(), LedState::On);
        assert_eq!(ctrl.toggle(), LedState::Off);
        assert_eq!(ctrl.toggle(), LedState::On);
        assert_eq!(ctrl.toggle(), LedState::Off);
    }

    #[test]
    fn test_initial_state_off() {
        let ctrl = LedController::new();
        let expected = LedController {
            state: LedState::Off,
            delay_ms: BLINK_DELAY_MS,
        };
        assert_eq!(ctrl, expected);
    }

    // ==================== Trait Implementation Tests ====================

    #[test]
    fn test_led_state_debug() {
        let state = LedState::On;
        let debug_str = format!("{:?}", state);
        assert!(debug_str.contains("On"));
    }

    #[test]
    fn test_led_controller_clone() {
        let ctrl1 = LedController::new();
        let ctrl2 = ctrl1;
        assert_eq!(ctrl1.delay_ms(), ctrl2.delay_ms());
    }

    #[test]
    fn test_led_controller_partial_eq() {
        let ctrl1 = LedController::new();
        let ctrl2 = LedController::new();
        assert_eq!(ctrl1, ctrl2);
    }

    #[test]
    fn test_led_controller_debug() {
        let ctrl = LedController::new();
        let debug_str = format!("{:?}", ctrl);
        assert!(debug_str.contains("LedController"));
    }
}
```

This is the complete driver brain: one enum, one struct, one helper, and a test
suite that proves the transitions. Everything else in the blink driver is
plumbing.

## The LedState Enum

The two shades of blink, defined exhaustively:

```rust
pub enum LedState {
    On,
    Off,
}
```

Because the enum derives `PartialEq` and `Debug`, the test suite can write
`assert_eq!(ctrl.toggle(), LedState::On)` and get a readable failure if wrong.
Because it derives `Copy`, passing it by value (`led_state_to_level(state)`)
does not consume it. The `# Variants` docstring bills each variant — On is high,
Off is low — so the mapping to GPIO never surprises anyone.

## The LedController Struct

The controller bundles the current state with the timing policy:

```rust
pub struct LedController {
    state: LedState,
    delay_ms: u64,
}
```

Both fields are **private** and the struct constructor `new()` is the only way
in. Invariants therefore cannot be broken from outside: a `LedController` always
starts Off at the configured delay, and only `toggle` can change its state.

Deriving `Clone, Copy, Debug, PartialEq, Eq` on a struct with two `Copy` fields
is free, and the derives equalize real work: `test_led_controller_clone`
assigns `ctrl2 = ctrl1` and both remain usable.

## The Default Trait

```rust
impl Default for LedController {
    fn default() -> Self {
        Self::new()
    }
}
```

`Default` is the trait behind `LedController::default()`. It simply delegates to
`new()`, keeping one canonical initializer. Why implement it at all? Because
once a type implements `Default`, it composes with the ecosystem — collections,
optionals, and generic code that demand `T: Default`. It is a one-line bridge
between our controller and the broader trait world of Chapter 6.

## toggle and delay_ms

`toggle` is the whole state machine dressed as a table:

```rust
pub fn toggle(&mut self) -> LedState {
    self.state = match self.state {
        LedState::On => LedState::Off,
        LedState::Off => LedState::On,
    };
    self.state
}
```

Required pieces:

- `&mut self` — Because the method reassigns `self.state`; the borrow checker
  admitted us because we asked for exclusive access.
- `match self.state` — Exhaustive: both variants handled, both map to a
  variant. The comment banner under the `}` documents nothing because the code
  is self-evident; the docstring above declares the contract: transitions On↔Off.
- Returns the *new* state — `main` uses the return value to drive the pin in
  the same expression sequence.

`delay_ms` is the read side of the policy: `&self`, a plain getter, returning
`self.delay_ms`. `main` calls it in the `Timer` expression every loop, so the
configured period is the single source of truth.

## led_state_to_level

The tiny bridge from `LedState` to electronics:

```rust
pub fn led_state_to_level(state: LedState) -> bool {
    matches!(state, LedState::On)
}
```

`LedState` is a "what we want" concept; GPIO's `Level` is a "what the wire sees"
concept. The helper makes `main` read like English: `if led_state_to_level(state)
{ led.set_high() }`. The pattern action for the button driver is
`led_state_to_level` from this same module reused unchanged — both drivers share
it.

## The Tests

Twenty tests in three banners. The banners group by concern:

- **`LedState Enum Tests`** — Equality, copy, and the conversion helper.
- **`LedController Tests`** — Construction, defaults, and every state
  transition.
- **`Trait Implementation Tests`** — The derived traits behave.

The transition tests are the valuable ones. `test_initial_state_off` builds the
expected struct by hand and compares — proving `new()` sets exactly `state:
Off, delay_ms: BLINK_DELAY_MS`. `test_multiple_toggles` proves alternation:
On, Off, On, Off, forever. These tests pin the blink rhythm as data, and the
whole suite runs on a laptop in under a second.

## Summary

- `LedState` is an exhaustive On/Off enum; `LedController` wraps it with
  private state and timing fields.
- `Default` delegates to `new()`; `toggle` is a state-transition table;
  `delay_ms` is a pure getter.
- `led_state_to_level` converts state to a boolean for GPIO, shared by both the
  blink and button drivers.
- The test suite — grouped by banner — proves construction, transition, and
  trait behavior on the host.

Next, the last piece of the blink driver: `main.rs`, the async shell.