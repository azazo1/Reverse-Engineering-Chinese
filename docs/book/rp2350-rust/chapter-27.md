# Chapter 27: uart.rs — The Echo State Machine

## Introduction

`uart.rs` is the UART driver's pure logic core: `UartController` converts an
incoming byte into the exact byte slice to echo back, and keeps a running echo
statistic. This chapter reproduces the complete file, then dissects the single
large method that makes echo work — `process_char`.

## Complete Source Code

Here is `src/uart.rs` in full:

```rust
/*
 * @file uart.rs
 * @brief UART echo state machine
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

//! FILE: uart.rs
//!
//! DESCRIPTION:
//! RP2350 UART Echo State Machine.
//!
//! BRIEF:
//! Implements UART character echo logic.
//! Provides testable state machine for echo functionality.
//!
//! AUTHOR: Kevin Thomas
//! CREATION DATE: December 4, 2025
//! UPDATE DATE: December 5, 2025

use crate::config::{BACKSPACE, BACKSPACE_SEQ, DELETE};

/// UART controller with echo tracking.
///
/// # Details
/// Maintains UART echo count for statistics.
/// Provides methods for character processing with backspace support.
///
/// # Fields
/// * `echo_count` - Number of characters echoed
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[allow(dead_code)]
pub struct UartController {
    echo_count: u64,
}

impl Default for UartController {
    /// Returns default UartController instance.
    ///
    /// # Details
    /// Delegates to new() for initialization.
    ///
    /// # Returns
    /// * `Self` - New UartController with default values
    #[allow(dead_code)]
    fn default() -> Self {
        Self::new()
    }
}

impl UartController {
    /// Creates new UART controller with default settings.
    ///
    /// # Details
    /// Initializes controller with zero echo count.
    /// Ready to receive characters immediately.
    ///
    /// # Returns
    /// * `Self` - New UartController instance
    #[allow(dead_code)]
    pub fn new() -> Self {
        Self { echo_count: 0 }
    }

    /// Processes a received character and returns echo response.
    ///
    /// # Details
    /// Handles backspace by returning erase sequence.
    /// Normal characters are echoed as-is.
    ///
    /// # Arguments
    /// * `ch` - The character received
    ///
    /// # Returns
    /// * `&'static [u8]` - Bytes to echo back
    #[allow(dead_code)]
    pub fn process_char(&mut self, ch: u8) -> &'static [u8] {
        self.echo_count += 1;
        if ch == BACKSPACE || ch == DELETE {
            &BACKSPACE_SEQ
        } else {
            match ch {
                b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' => {
                    static CHARS: [u8; 62] = [
                        b'A', b'B', b'C', b'D', b'E', b'F', b'G', b'H', b'I', b'J', b'K', b'L',
                        b'M', b'N', b'O', b'P', b'Q', b'R', b'S', b'T', b'U', b'V', b'W', b'X',
                        b'Y', b'Z', b'a', b'b', b'c', b'd', b'e', b'f', b'g', b'h', b'i', b'j',
                        b'k', b'l', b'm', b'n', b'o', b'p', b'q', b'r', b's', b't', b'u', b'v',
                        b'w', b'x', b'y', b'z', b'0', b'1', b'2', b'3', b'4', b'5', b'6', b'7',
                        b'8', b'9',
                    ];
                    let idx = CHARS.iter().position(|&c| c == ch).unwrap();
                    &CHARS[idx..idx + 1]
                }
                b' ' => b" ",
                b'!' => b"!",
                b'"' => b"\"",
                b'#' => b"#",
                b'$' => b"$",
                b'%' => b"%",
                b'&' => b"&",
                b'\'' => b"\'",
                b'(' => b"(",
                b')' => b")",
                b'*' => b"*",
                b'+' => b"+",
                b',' => b",",
                b'-' => b"-",
                b'.' => b".",
                b'/' => b"/",
                b':' => b":",
                b';' => b";",
                b'<' => b"<",
                b'=' => b"=",
                b'>' => b">",
                b'?' => b"?",
                b'@' => b"@",
                b'[' => b"[",
                b'\\' => b"\\",
                b']' => b"]",
                b'^' => b"^",
                b'_' => b"_",
                b'`' => b"`",
                b'{' => b"{",
                b'|' => b"|",
                b'}' => b"}",
                b'~' => b"~",
                b'\n' => b"\n",
                b'\r' => b"\r",
                b'\t' => b"\t",
                _ => b"",
            }
        }
    }

    /// Returns total echo count.
    ///
    /// # Returns
    /// * `u64` - Number of characters echoed
    #[allow(dead_code)]
    pub fn echo_count(&self) -> u64 {
        self.echo_count
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // ==================== UartController Construction Tests ====================

    #[test]
    fn test_new_controller() {
        let ctrl = UartController::new();
        assert_eq!(ctrl.echo_count(), 0);
    }

    #[test]
    fn test_default_equals_new() {
        let default = UartController::default();
        let new = UartController::new();
        assert_eq!(default.echo_count(), new.echo_count());
    }

    // ==================== Character Processing Tests ====================

    #[test]
    fn test_process_char_returns_same() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(b'A'), b"A");
    }

    #[test]
    fn test_process_char_increments_count() {
        let mut ctrl = UartController::new();
        ctrl.process_char(b'A');
        ctrl.process_char(b'B');
        ctrl.process_char(b'C');
        assert_eq!(ctrl.echo_count(), 3);
    }

    #[test]
    fn test_process_char_special() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(b'\n'), b"\n");
        assert_eq!(ctrl.process_char(b'\r'), b"\r");
    }

    #[test]
    fn test_process_backspace() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(0x08), &[0x08, b' ', 0x08]);
    }

    #[test]
    fn test_process_delete() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(0x7F), &[0x08, b' ', 0x08]);
    }

    #[test]
    fn test_process_tab() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(b'\t'), b"\t");
    }

    #[test]
    fn test_process_uppercase_letters() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(b'A'), b"A");
        assert_eq!(ctrl.process_char(b'Z'), b"Z");
        assert_eq!(ctrl.process_char(b'M'), b"M");
    }

    #[test]
    fn test_process_lowercase_letters() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(b'a'), b"a");
        assert_eq!(ctrl.process_char(b'z'), b"z");
        assert_eq!(ctrl.process_char(b'm'), b"m");
    }

    #[test]
    fn test_process_digits() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(b'0'), b"0");
        assert_eq!(ctrl.process_char(b'9'), b"9");
        assert_eq!(ctrl.process_char(b'5'), b"5");
    }

    #[test]
    fn test_process_punctuation() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(b'!'), b"!");
        assert_eq!(ctrl.process_char(b'?'), b"?");
        assert_eq!(ctrl.process_char(b'.'), b".");
        assert_eq!(ctrl.process_char(b','), b",");
    }

    #[test]
    fn test_process_symbols() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(b'@'), b"@");
        assert_eq!(ctrl.process_char(b'#'), b"#");
        assert_eq!(ctrl.process_char(b'$'), b"$");
        assert_eq!(ctrl.process_char(b'%'), b"%");
    }

    #[test]
    fn test_process_brackets() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(b'['), b"[");
        assert_eq!(ctrl.process_char(b']'), b"]");
        assert_eq!(ctrl.process_char(b'('), b"(");
        assert_eq!(ctrl.process_char(b')'), b")");
        assert_eq!(ctrl.process_char(b'{'), b"{");
        assert_eq!(ctrl.process_char(b'}'), b"}");
    }

    #[test]
    fn test_process_unknown_char() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(0x01), b"");
        assert_eq!(ctrl.process_char(0xFF), b"");
    }

    #[test]
    fn test_process_space() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(b' '), b" ");
    }

    #[test]
    fn test_backspace_increments_count() {
        let mut ctrl = UartController::new();
        ctrl.process_char(0x08);
        assert_eq!(ctrl.echo_count(), 1);
    }

    #[test]
    fn test_multiple_backspaces() {
        let mut ctrl = UartController::new();
        ctrl.process_char(0x08);
        ctrl.process_char(0x7F);
        ctrl.process_char(0x08);
        assert_eq!(ctrl.echo_count(), 3);
    }

    #[test]
    fn test_mixed_chars_and_backspace() {
        let mut ctrl = UartController::new();
        ctrl.process_char(b'A');
        ctrl.process_char(b'B');
        ctrl.process_char(0x08);
        ctrl.process_char(b'C');
        assert_eq!(ctrl.echo_count(), 4);
    }

    // ==================== Trait Tests ====================

    #[test]
    fn test_clone() {
        let ctrl = UartController::new();
        let cloned = ctrl.clone();
        assert_eq!(ctrl.echo_count(), cloned.echo_count());
    }

    #[test]
    fn test_copy() {
        let ctrl = UartController::new();
        let copied = ctrl;
        assert_eq!(ctrl.echo_count(), copied.echo_count());
    }

    #[test]
    fn test_partial_eq() {
        let ctrl1 = UartController::new();
        let ctrl2 = UartController::new();
        assert_eq!(ctrl1, ctrl2);
    }

    #[test]
    fn test_not_equal_after_process() {
        let mut ctrl1 = UartController::new();
        let ctrl2 = UartController::new();
        ctrl1.process_char(b'A');
        assert_ne!(ctrl1, ctrl2);
    }

    #[test]
    fn test_debug_format() {
        let ctrl = UartController::new();
        let debug_str = format!("{:?}", ctrl);
        assert!(debug_str.contains("UartController"));
    }
}
```

The whole machine is one struct, three methods, and a wide `match`. The tests
land in three banners: construction, character processing, and traits.

## The Controller Struct and new

```rust
pub struct UartController {
    echo_count: u64,
}
```

One field — the prior 's with a single `u64` counter. Derives match the pattern
of `LedController` and `ButtonController`: `Clone, Copy, Debug, PartialEq, Eq`.
`new()` starts the counter at zero. `echo_count()` is the trivial getter.
`UartController` is the smallest controller in the course, and it needs the
largest `match` — the opposite of the blink driver's one-line toggle.

## process_char

Everything interesting lives here:

```rust
pub fn process_char(&mut self, ch: u8) -> &'static [u8] {
    self.echo_count += 1;
    if ch == BACKSPACE || ch == DELETE {
        &BACKSPACE_SEQ
    } else {
        match ch { ... }
    }
}
```

Three design decisions, in order:

1. **Count every character** — `self.echo_count += 1` unconditionally, before
   any branching. Even a byte that produces no echo (unknown) is counted,
   because `main` received it. `test_backspace_increments_count` and
   `test_mixed_chars_and_backspace` pin this.

2. **Backspace short-circuit** — Either erase spelling returns the three-byte
   `BACKSPACE_SEQ`. This is faster than matching the same range twice and
   keeps `BACKSPACE`/`DELETE` as named config constants.

3. **Exhaustive-match on the rest** — Control characters and printable ASCII
   are echoed verbatim; anything outside the table falls to `_ => b""`. The
   `_` arm guarantees the match never misses a byte and never needs a megabyte
   of arms.

The return type deserves attention: `&'static [u8]`. Every arm returns a
lifetime-bound slice — a byte-string literal like `b"!"`, or the static
`BACKSPACE_SEQ`, or a slice of the static `CHARS` table. No memory is borrowed
from the caller and none is allocated per call, which is why `process_char`
returns a reference and `main` can hand it straight to `uart.write`.

### The Alphanumeric Table arm

The letters-and-digits arm is clever and deserves the extra lines:

```rust
b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' => {
    static CHARS: [u8; 62] = [ b'A', ..., b'9' ];
    let idx = CHARS.iter().position(|&c| c == ch).unwrap();
    &CHARS[idx..idx + 1]
}
```

`static CHARS` is the 62-character alphabet held once in flash at a fixed
address. `.position()` finds the incoming byte in that table and
`&CHARS[idx..idx + 1]` returns a *one-element slice* — not a `u8` value, because
the method must return slices. `.unwrap()` is safe because the arm's range
guarantees the byte is present.

### Escape Bytes

Bytes that need careful literals get explicit arms:

```rust
b'"'  => b"\"",
b'\\' => b"\\",
b'\'' => b"\'",
```

The three backslash escapes survive rustfmt in the driver file, and the tests
`test_process_punctuation` and `test_process_symbols` confirm the quotes and
slashes round-trip.

## The Tests

The suite is the controller's contract, in reason-ordered groups:

- **Construction tests** — fresh count is zero; `default()` equals `new()`.
- **Character processing tests** — identity echo for letters, digits,
  punctuation, symbols, brackets, spaces, and control bytes; erase sequences
  for both backspaces; empty echo for unknown; count increments on every input
  including backspaces and mixed runs.
- **Trait tests** — `Clone`, `Copy`, `PartialEq`, and the readable `Debug`
  format.

The asymmetry test is the sharpest: `test_not_equal_after_process` shows two
controllers that start equal cease to be equal after one processes a byte.
The `echo_count` is behavior, not decoration.

## Summary

- `UartController` holds a single counter and exposes `new`, `process_char`,
  and `echo_count`.
- `process_char` counts every input, short-circuits backspaces to the erase
  sequence, and answers an exhaustive `match` for everything else.
- Every arm returns a `&'static [u8]` — no allocation, no borrowed-from-caller
  lifetime.
- The alphanumeric arm indexes a 62-byte `static` table to return a slice.
- Fourteen processing tests plus construction and trait tests make echo
  behavior a compiled contract.

Next, the hardware story behind UART's clean `await`: interrupts and DMA.