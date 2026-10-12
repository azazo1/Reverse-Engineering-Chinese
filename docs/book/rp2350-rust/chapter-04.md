# Chapter 4: Ownership, Borrowing, and Lifetimes

## Introduction

Ownership is the single rule that makes Rust safe without a garbage collector.
It explains why Rust code can confidently drive a GPIO pin, share a buffer with
DMA, and never corrupt memory. In this chapter we build the mental model: every
value has an owner, ownership can move, and we can lend values by borrowing.

## Ownership

Every value in Rust has exactly one **owner** — the variable that holds it.
When the owner goes out of scope, the value is dropped and its memory is
reclaimed immediately. No garbage collector is needed:

```rust
fn run() {
    let packet = [0u8; 64];      // packet owns 64 bytes on the stack
    echo(&packet);               // borrowed for the call...
}                                // ...and freed when run() returns
```

This "drop at end of scope" behavior gives embedded code deterministic timing:
we know exactly when a buffer is freed, which is essential when DMA or an
interrupt might still be looking at it.

## Move Semantics

Assigning a value or passing it to a function **moves** ownership unless the
type is `Copy`. After a move the old variable no longer exists:

```rust
let a = String::from("hello");   // String is not Copy
let b = a;                       // ownership moves to b
// println!("{a}");              // COMPILE ERROR: a was moved

let x = 5u32;                    // u32 is Copy
let y = x;                       // x is copied, still usable
```

Why does this matter on a microcontroller? It is exactly how Embassy makes
peripheral handles exclusive. When `embassy_rp::init()` hands you a
`Peripherals` struct, ownership of each peripheral token is moved into your
code. Because ownership cannot be duplicated, two tasks physically cannot both
own and fight over UART0. The compiler enforces single ownership of the
hardware.

## Borrowing and References

Instead of moving a value, you can lend it with a reference:

```rust
fn total(buf: &[u8]) -> u32 {     // & = immutable borrow
    buf.iter().fold(0u32, |s, b| s + *b as u32)
}

let data = [1u8, 2, 3];
let sum = total(&data);           // data still owned by caller
```

Rust's central safety law is the **borrow checker**:

```
+-----------------------------------------------------------+
|   The Borrowing Rules                                     |
|                                                           |
| • At any time you may have many immutable references (&)  |
|   OR one mutable reference (&mut), never both.            |
| • References must always point to valid memory.           |
+-----------------------------------------------------------+
```

A mutable borrow `&mut` is exclusive: the compiler guarantees nothing else reads
or writes the value at the same time. This turns "data race" from a runtime
nasty into a compile-time error.

## Copy and Clone

Two traits control what happens on assignment and passing:

- **`Copy`** — Cheap duplication by copying bits; the original stays usable.
  Integer types, booleans, and element-wise copies of them are `Copy`. Our
  `LedState` and `LedController` types derive `Copy` (Chapter 20).
- **`Clone`** — Explicit duplication via the `.clone()` method; the type decides
  the cost. Arrays and structs containing non-`Copy` data implement `Clone`.

```rust
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum LedState {
    On,
    Off,
}
```

Because `LedState` is `Copy`, calling `led_state_to_level(state)` passes it by
copy, and we can keep using it afterwards. All three drivers rely on this.

## Lifetimes

A **lifetime** is the compiler's label for how long a reference stays valid. Most
lifetimes are elided (inferred), but one pattern shows up constantly in our
code — returning a reference tied to an input:

```rust
pub fn process_char(&mut self, ch: u8) -> &'static [u8] {
    ...                                 // returns bytes that live forever
}
```

The `&'static [u8]` in the UART driver means "the returned byte slice lives as
long as the program." That slice points into a `static` table whose memory is
fixed for the whole firmware lifetime, so it is safe to return from a function.
The driver never owns the echoed bytes — they live in a table declared at
compile time.

When the compiler *does* need an explicit lifetime, you write a named one:

```rust
fn first<'a>(s: &'a [u8]) -> &'a u8 { &s[0] }
// 'a ties the output to the input: the result cannot outlive s
```

Lifetimes rarely need writing in normal code, but understanding them is
powerful: when an Embassy API requires a `&'static mut` buffer, you immediately
know exactly what kind of memory it needs and where it must live.

## Summary

- Every value has one owner; dropping the owner frees the value immediately.
- Moving transfers ownership; `Copy` types duplicate instead.
- Borrowing via `&` and `&mut` is governed by rules the compiler verifies,
  eliminating data races and dangling references.
- `Copy`/`Clone` choose cheap bit-copies vs explicit duplication; our driver
  types derive both families of traits.
- Lifetimes guarantee references never outlive the data they point to, and
  `'static` describes values that live for the entire program.

Next: structs, enums, and pattern matching — the types we use to model the
hardware's state.