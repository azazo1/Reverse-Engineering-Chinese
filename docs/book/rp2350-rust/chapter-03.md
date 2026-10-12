# Chapter 3: Rust Essentials

## Introduction

Every embedded Rust program — including the three drivers we build — is composed
of a small set of language fundamentals: variables, primitive types, control
flow, functions, and constants. This chapter covers those essentials exactly as
they appear in `no_std` firmware. If you have written Rust before, treat it as a
review that is tuned to microcontroller work.

## Variables and Mutability

Variables are introduced with `let`. By default a variable is **immutable** — it
cannot change — which matches embedded philosophy: an address or a pin mask
should not silently change behind your back.

```rust
let led_pin = 16;          // immutable
let mut count = 0;         // mutable with the mut keyword
count += 1;                // allowed because we declared mut

// A shadowing example: two different variables share a name.
let value = 10;
let value = value * 2;     // a new variable, not a mutation
```

The compiler enforces immutability at compile time. Trying to write
`led_pin = 17;` without `mut` is a compile error, not a runtime bug. That is the
Rust design: catch mistakes before the code ever reaches the chip.

## Primitive Types

The integer types map directly onto the RP2350's register widths:

```rust
let a: u8   = 0xFF;                  // 8-bit  unsigned
let b: u16  = 0x4000;                // 16-bit unsigned
let c: u32  = 0x2000_0000;           // 32-bit unsigned (an address!)
let d: u64  = 10_000;                // 64-bit unsigned (our blink delay)
let s: i32  = -5;                    // signed
let f: bool = true;                  // boolean
let ch: char = 'A';                  // a Unicode scalar value
```

The type suffix is optional when inference can determine it, but embedded code
usually writes it explicitly. A `u64` delay and a `u32` register mask have very
different ranges; letting the compiler know both keeps every operation checked.

## Control Flow

**`if`/`else if`/`else`** works as everywhere, but Rust's `if` is an
*expression* — it produces a value:

```rust
let state: u8 = if led_is_on { 1 } else { 0 };
```

This form appears constantly in our drivers. In `main.rs` we write exactly this
shape to turn a boolean into a decision about the LED.

**`loop`** is Rust's infinite loop. Firmware is an infinite program, so `loop` is
the heart of every embedded application:

```rust
loop {
    set_led_high();
    delay(500);
    set_led_low();
    delay(500);
}
```

**`for`** iterates over a range or collection; **`while`** repeats while a
condition holds:

```rust
for i in 0..5 { /* i is 0,1,2,3,4 */ }
while !uart_rx_ready() { /* spin */ }
```

## Functions

Functions are declared with `fn`. A function that returns a value states its
return type after `->`. The last expression in the body is the return value;
`return` is only needed for early exit:

```rust
/// Maps a boolean to a PWM duty cycle (0% or 100%).
fn duty(state: bool) -> u16 {
    if state {
        65535 // 100%
    } else {
        0
    }
}
```

Notice the function documents itself with the rustdoc comment above it. Every
public item in our drivers carries such a comment — this is the foundation of
our strict docstring standard, formalized in Chapter 18.

## Constants and Statics

Two ways to declare compile-time values, and they differ in exactly the way
embedded programmers care about:

```rust
pub const BLINK_DELAY_MS: u64 = 500;   // inlined at every use, no memory
pub static VOLTAGE_REF: u32 = 3300;    // a single memory cell at a fixed address
static CHARS: [u8; 3] = [b'A', b'B', b'C'];  // static array in flash
```

- **`const`** — Inlined by the compiler at each use. It costs no memory. All of
  our configuration values in `config.rs` are `const`.
- **`static`** — A fixed memory location, live for the whole program. Useful for
  tables that must have an address, such as the character table in the UART
  driver's `process_char`.

Static mutable data is a threading hazard and is the source of most safety bugs;
Rust forbids shared access to `static mut` without extra care. In this course we
never need it — Embassy's types give us safe alternatives.

A note on literals in embedded code: primitives are `Copy`, so passing a `u32`
into a function does not move or transfer ownership. That concept is the subject
of the next chapter and is central to why Rust code can be trusted at high
clock speeds.

## Summary

- `let` bindings are immutable by default; `mut` opts into change.
- Integer widths — `u8`, `u16`, `u32`, `u64` — mirror the hardware's byte
  sizes, and explicit types keep operations checked.
- `if` is an expression; `loop` is the backbone of firmware.
- Functions return with an expression and document themselves with docstrings.
- `const` values are inlined; `static` values live at a fixed address.

Next, we tackle the idea that defines Rust: ownership, borrowing, and
lifetimes.