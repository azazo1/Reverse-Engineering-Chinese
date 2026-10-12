# Chapter 19: config.rs — Blink Configuration

## Introduction

`config.rs` is the first file of the blink driver and the smallest. It contains
three constants and their tests — but reading it carefully teaches you the
entire **docstring standard** this course is built around. Every constant,
every function, and every type across all three drivers documents itself the way
the file below does.

## Complete Source Code

Here is `src/config.rs` in full — the exact file the blink driver ships:

```rust
/*
 * @file config.rs
 * @brief Application configuration constants
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

//! FILE: config.rs
//!
//! DESCRIPTION:
//! RP2350 Blink Configuration Constants.
//!
//! BRIEF:
//! Defines configuration constants for LED blink timing.
//! Contains delay intervals and GPIO pin configuration.
//!
//! AUTHOR: Kevin Thomas
//! CREATION DATE: November 28, 2025
//! UPDATE DATE: December 4, 2025

/// Default LED blink delay in milliseconds.
///
/// # Details
/// Configures the delay between LED state transitions.
/// Used for both ON and OFF durations.
///
/// # Value
/// 500 milliseconds
#[allow(dead_code)]
pub const BLINK_DELAY_MS: u64 = 500;

/// Minimum allowed blink delay in milliseconds.
///
/// # Details
/// Prevents excessively fast blinking which may cause issues.
///
/// # Value
/// 10 milliseconds
#[allow(dead_code)]
pub const MIN_BLINK_DELAY_MS: u64 = 10;

/// Maximum allowed blink delay in milliseconds.
///
/// # Details
/// Prevents excessively slow blinking for practical use.
///
/// # Value
/// 10000 milliseconds (10 seconds)
#[allow(dead_code)]
pub const MAX_BLINK_DELAY_MS: u64 = 10000;

#[cfg(test)]
mod tests {
    use super::*;

    // ==================== LED Configuration Tests ====================

    #[test]
    fn test_blink_delay_default() {
        assert_eq!(BLINK_DELAY_MS, 500);
    }

    #[test]
    fn test_min_delay_less_than_default() {
        assert!(MIN_BLINK_DELAY_MS < BLINK_DELAY_MS);
    }

    #[test]
    fn test_max_delay_greater_than_default() {
        assert!(MAX_BLINK_DELAY_MS > BLINK_DELAY_MS);
    }

    #[test]
    fn test_delay_range_valid() {
        assert!(MIN_BLINK_DELAY_MS < MAX_BLINK_DELAY_MS);
    }
}
```

A tiny file with a strict structure. We now decompose each of its
three layers: the license header, the inner module documentation, and the
per-item docstrings.

## The License Header

Every source file begins with the identical block comment:

```
/*
 * @file config.rs
 * @brief Application configuration constants
 * @author Kevin Thomas
 * @date 2025
 *
 * MIT License
 * ... full license text ...
 */
```

The four `@` tags are the file's identity card:

| Tag       | Meaning                                  |
|-----------|------------------------------------------|
| `@file`   | The file's name — trivial, but scannable |
| `@brief`  | One line describing the file's role      |
| `@author` | Who wrote and owns it                    |
| `@date`   | The year of authorship                   |

Below them sits the full MIT license text. Every driver file — Rust, Makefile,
and all — repeats this exact header, so any file is self-attributing and
self-licensing no matter how it is redistributed.

## The Inner Module Docs

Immediately after the license header, the inner documentation comment describes
the module as a whole. Note this is `//!`, making it *module* documentation
attached to the file, in a strict block format:

```
//! FILE: config.rs
//!
//! DESCRIPTION:
//! RP2350 Blink Configuration Constants.
//!
//! BRIEF:
//! Defines configuration constants for LED blink timing.
//! Contains delay intervals and GPIO pin configuration.
//!
//! AUTHOR: Kevin Thomas
//! CREATION DATE: November 28, 2025
//! UPDATE DATE: December 4, 2025
```

The block is a fixed contract: `FILE`, `DESCRIPTION`, `BRIEF`, `AUTHOR`,
`CREATION DATE`, `UPDATE DATE`. The `UPDATE DATE` is bumped whenever the file
changes. This is the human-readable index that makes a 30-file multi-driver
project scannable at a glance.

## Documenting Constants

Each constant carries the same item documentation pattern — `///` (outer doc
attached to the item), then a `#`-section ledger, with `# Details`, a
`# Value` for constants (or `# Arguments`/`# Returns` for functions), and a
concrete value line:

```rust
/// Default LED blink delay in milliseconds.
///
/// # Details
/// Configures the delay between LED state transitions.
/// Used for both ON and OFF durations.
///
/// # Value
/// 500 milliseconds
```

The three constants teach the pattern with different shades:

- **`BLINK_DELAY_MS`** — The one real value the driver uses: 500 ms.
- **`MIN_BLINK_DELAY_MS`** — 10 ms; a floor that prevents absurdly fast
  toggling.
- **`MAX_BLINK_DELAY_MS`** — 10000 ms; a ceiling for practical blinking.

`#[allow(dead_code)]` appears above each one. The blink `main` loop only reads
`BLINK_DELAY_MS` today, so the min/max guards would otherwise warn about unused
code. The attribute is the deliberate trade: keep the complete, documented
config surface and silence the linter's noise.

## Why Constants Live Here

Two reasons beyond tidiness:

1. **Single source of truth.** `led.rs` reads `BLINK_DELAY_MS` by import; the
   hardware driver never names a magic number. Change one constant, every caller
   follows.
2. **Testability.** Constants are `pub` and reach the test module via
   `use super::*`. The four tests below pin both the exact values and the
   invariants *between* them.

## The Tests

The test module keeps the file honest:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    // ==================== LED Configuration Tests ====================
    ...
}
```

Note the **section banner** — `// ==================== NAME Tests
====================` — that groups tests by concern. Every driver file uses the
same banner style, loosely mirroring the Rust "tests as documentation" ethos.

The tests assert three kinds of truth:

- **Exact values** — `assert_eq!(BLINK_DELAY_MS, 500)` catches eager edits that
  would silently change firmware timing.
- **Ordering** — `MIN < DEFAULT` and `DEFAULT < MAX` guard the intended
  hierarchy.
- **Range sanity** — `MIN < MAX` protects the whole configuration space.

None of these tests touch hardware; they run on the host in milliseconds. That
is the entire point — config typos become test failures, not mystery hardware.

## Summary

- Every source file opens with the `@file/@brief/@author/@date` license header.
- Inner module docs follow a fixed `FILE/DESCRIPTION/BRIEF/AUTHOR/CREATION
  DATE/UPDATE DATE` block.
- Constants document `# Details` and `# Value` with concrete numbers.
- `#[allow(dead_code)]` keeps documented-but-unused configuration silent.
- The test module pins values and cross-constant invariants with slice banners.

Next: the state machine at the heart of the blink driver — `led.rs`.