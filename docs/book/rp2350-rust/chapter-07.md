# Chapter 7: no_std and no_main

## Introduction

Every firmware crate in this course starts with the same two lines:

```rust
#![no_std]
#![no_main]
```

These two crate attributes are the moment a program leaves the host and becomes
bare metal. This chapter explains what each one really does, what we give up,
and what we get in return.

## What Does no_main Mean?

A normal Rust program's entry point is a `main` function named and executed
before anything else. On a microcontroller there is no operating system to
call it, and the CPU does not boot into Rust at all.

The boot sequence starts in **assembly** and a **startup routine** (provided by
`cortex-m-rt`) that:

```
+----------------+     +------------------+     +------------------+
|   Hardware     | --> |   Vector Table   | --> |   Reset Handler  |
|    reset       |     |  (first word SP, |     |  (sets up stack, |
|                |     |   second PC)     |     |   SVC, sections) |
+----------------+     +------------------+     +------------------+
                                                       |
                                                       v
                                              +------------------+
                                              |  Rust init code  |
                                              |  (embassy_rp)    |
                                              +------------------+
```

`#![no_main]` tells the Rust compiler: "do not expect a `main` function from
the standard library, we are defining our own entry point." Combined with
`cortex-m-rt`'s `entry` machinery, our Rust code gets called after the CPU is in
a known state.

In Embassy the precise entry point is invented by the executor. The
`#[embassy_executor::main]` attribute on an `async fn` replaces `main` (Chapter
14). That function never returns — the executor runs forever.

## What Does no_std Mean?

The Rust standard library `std` assumes an operating system: it brings threads,
a heap allocator, `println!`, files, networking — all provided by a kernel. A
microcontroller has no kernel, so we opt out with `#![no_std]`, and suddenly we
have access to only the **core** library.

`core` is the part of the standard library that needs no OS:

```
+----------------------+     +-----------------------------+
|  std  (needs OS)     |     |  core (no OS required)      |
+----------------------+     +-----------------------------+
|  Vec, String, Box    |     |  integer types, slices,     |
|  HashMap, threads    |     |  Option, Result, iterators, |
|  println!, files     |     |  traits (Copy, Debug, ...)  |
|  heap allocator      |     |  panic machinery (hook)     |
+----------------------+     +-----------------------------+
```

Everything we used in Part I — ownership, borrowing, structs, enums, `match`,
traits, generics — lives in `core` and works unchanged in `no_std`. What we
lose, we do not need: `Vec` and `String` require an allocator and dynamic
memory; firmware that avoids them has deterministic, bounded memory usage.

Note the escape hatch. Our `lib.rs` writes:

```rust
#![cfg_attr(not(test), no_std)]
```

Under `test` — when we compile for the host to run tests — the crate is `std`.
That is the entire trick behind the host test suite in Chapter 25.

## Panic Handling

What happens when a program must give up? On the host, `panic!` unwinds the
stack. In `no_std` there may be no stack unwinding, and in any case there is no
console to print to.

Every driver imports a panic handler with a trick import:

```rust
use panic_halt as _;
```

The `as _` means "bring the crate in solely for its side effects." `panic-halt`
installs a **panic handler**: when a panic occurs, it simply halts the CPU —
typically waiting forever (`wfi`/`b`). On our boards, the LED simply stops
blinking and the chip rests. That is the correct default for a bare-metal
library: halt rather than corrupt.

```rust
#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}
```

Only one panic handler may exist per binary, which is why the imported crate
ships the `#[panic_handler]` and we never write our own.

## Channels of Output

Without `println!`, how do we see anything? Firmware has its own channels:

```
+----------------+     +----------------+     +----------------+
|  GPIO + LED    |     |  UART (serial) |     |  SWD debugger |
|  blink patterns|     |  printf-style  |     |  probe-rs     |
+----------------+     +----------------+     +----------------+
```

The blink driver's rhythm of on/off is its output channel. The UART driver
writes real bytes to a terminal over TX/RX — the same channel a desktop `print`
uses, wired through a physical serial cable.

## Summary

- `#![no_main]` surrenders the standard entry point; the CPU boots through a
  vector table and reset handler, then into Embassy's executor.
- `#![no_std]` drops the OS-dependent standard library but keeps `core`, which
  contains everything from Part I.
- Panics halt the CPU by default (`panic-halt`), the safe bare-metal choice.
- Output happens through hardware — LEDs, UART, and debug probes — not stdout.

Next we install the toolchain and build our first firmware target.