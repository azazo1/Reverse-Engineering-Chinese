# Chapter 1: What Is Embedded Rust?

## Introduction

Rust is a systems programming language designed for safety and speed. It gives
you the low-level control of C — direct memory access, no garbage collector, no
hidden runtime — while eliminating entire classes of bugs at compile time.
Embedded Rust is simply Rust running on a microcontroller: a small computer on a
chip with its own CPU, memory, and I/O peripherals, with no operating system.

In this course we write firmware for the **Raspberry Pi RP2350** using the
**Embassy** async framework. Embassy is the Rust async runtime for embedded
systems. It lets us write firmware the way we would write a modern application:
concurrent tasks, timers, and hardware drivers, all expressed with `async` and
`await`.

## Why Rust for Embedded?

Microcontroller firmware runs close to the metal. There is no operating system
to protect you from your own mistakes. A stray pointer can silently corrupt a
register. A buffer overrun can reboot the chip. In C this is accepted risk. In
Rust, the compiler refuses to accept it.

Three properties make Rust ideal for embedded work:

```
+---------------------------+
|        Rust's Gifts       |
+---------------------------+
| 1. Memory safety          |
| 2. No garbage collector   |
| 3. Zero-cost abstractions |
+---------------------------+
```

- **Memory safety** — The borrow checker guarantees you cannot use freed
  memory, read past a buffer, or race two writes to the same value. These are
  caught at compile time, not when the board misbehaves.
- **No runtime overhead** — There is no garbage collector, no virtual machine.
  Nothing runs unless you write it. This matters on a microcontroller with a few
  hundred kilobytes of RAM and a 150 MHz clock.
- **Zero-cost abstractions** — Traits, generics, closures, and `async` compile
  down to the same machine code you would write by hand. Elegant source code
  does not cost extra memory or cycles.

## Memory Safety Without an OS

A desktop application relies on a kernel to isolate processes. Embedded firmware
has no kernel. Rust replaces that protection with *compile-time* protection: the
borrow checker, type system, and lifetime rules. When your code compiles, the
compiler has already proven that:

```
+-----------------------------+
|   What the Compiler Proves  |
+-----------------------------+
| No use-after-free           |
| No data races               |
| No out-of-bounds access     |
| No concurrent mutable aliasing |
+-----------------------------+
```

The cost of these guarantees is a steeper learning curve. That is exactly what
this course is for: we build the mental model step by step before we touch a
real peripheral.

## The RP2350

The RP2350 is the microcontroller at the heart of the Raspberry Pi Pico 2. Key
facts:

- **Dual-core CPU** — The chip ships with two cores. A board can run them as
  either two ARM Cortex-M33 cores or two RISC-V Hazard3 cores.
- **150 MHz** — A small but capable clock for a microcontroller.
- **520 KB SRAM** — Fast volatile memory for code and data.
- **4 MB on-chip flash** — Where firmware is stored and executed in place (XIP).
- **Rich peripheral set** — GPIO, UART, SPI, I2C, PWM, ADC, DMA, timers, and
  more.

The memory is mapped at fixed addresses:

```
0x10000000 +---------------------------+
           |  FLASH  (XIP, 4 MB)       |
           +---------------------------+
0x20000000 |  SRAM   (main, 512 KB)    |
           +---------------------------+
0x20080000 |  SRAM8 (bootrom scratch)  |
0x20081000 |  SRAM9 (bootrom scratch)  |
           +---------------------------+
0x40000000 |  Peripherals (registers)  |
           +---------------------------+
```

We examine this map in detail in Chapter 2.

## What Is Embassy?

Embassy is a set of crates for embedded async:

- **`embassy-executor`** — A cooperative async executor for microcontrollers.
- **`embassy-time`** — Timers and delays without busy-waiting.
- **`embassy-rp`** — A hardware abstraction layer (HAL) for the RP2040/RP2350.
- **`embassy-rs`** — The umbrella community and repository that maintains them.

With Embassy, a blink driver reads like a high-level loop:

```
+------------+     +-------------+     +-------------+
|  Init HAL  | --> |   Toggle    | --> |    Timer    |
| (GPIO16)   |     |    LED      |     |  500 ms     |
+------------+     +-------------+     +-------------+
     |                                      |
     +---------------(loop)-----------------+
```

The loop runs forever, yielding to the executor between iterations so other
tasks can run. This is the model used by all three drivers you will build.

## What We Will Build

This course ends with three complete, host-tested drivers. They share one
architecture and one strict docstring standard:

```
+----------------+      +----------------+      +----------------+
|  Blink Driver  |      | Button Driver  |      |  UART Driver   |
|  GPIO16 -> LED |      | GPIO15 button  |      | GPIO0/1 UART   |
|                |      | GPIO16 -> LED  |      | character echo |
+----------------+      +----------------+      +----------------+
```

1. **The Blink Driver** — Toggles an LED on GPIO 16 every 500 ms using
   `embassy-time`.
2. **The Button Driver** — Reads a button on GPIO 15 (active-low, debounced) and
   lights an LED on GPIO 16 while pressed.
3. **The UART Driver** — Echoes characters received on UART0 (GPIO 0 TX, GPIO 1
   RX) with terminal backspace support.

Along the way you will master the four ideas at the heart of every embedded Rust
program: the language, the bare-metal build system, memory-mapped I/O, and the
Embassy runtime.

## Summary

- Rust gives embedded programmers memory safety and zero-cost abstractions with
  no runtime.
- The RP2350 is a dual-core microcontroller with 4 MB flash, 512 KB SRAM, and a
  rich peripheral set.
- Embassy brings `async`/`await` to embedded, replacing busy-wait loops with
  cooperative concurrent tasks.
- This course builds three drivers — blink, button, and UART echo — each fully
  tested on the host.

Next up, we learn to think in the numbers and addresses that underpin every
register we will touch.