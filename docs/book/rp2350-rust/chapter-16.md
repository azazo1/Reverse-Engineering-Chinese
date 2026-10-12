# Chapter 16: The embassy-rp HAL

## Introduction

Every driver begins with the same line after entering `main`:

```rust
let p = embassy_rp::init(Default::default());
```

This small call unlocks everything else. It initializes clocks and the critical
section machinery, then returns the **`Peripherals` struct** — a set of
exclusive ownership tokens, one per hardware block. This chapter answers what
`init` does and why its return value exists.

## Peripherals

A "peripheral" is a hardware block: UART0, GPIO bank 0, DMA0, the timer, and so
on. Each has registers, an interrupt line, and a fixed address. Embassy models
each one as a **token type** — an empty struct that only this program can hold an
instance of.

`Peripherals`, the bundle `init` returns, contains one field per token:

```rust
pub struct Peripherals {
    pub PIN_0: Pin<0>,        // the GPIO 0 token
    pub PIN_1: Pin<1>,
    pub PIN_15: Pin<15>,
    pub PIN_16: Pin<16>,
    pub UART0: UART0,         // the UART 0 token
    pub DMA_CH0: DmaChannel0,
    pub DMA_CH1: DmaChannel1,
    // ... and every other pin, channel, and block
}
```

Field access is how drivers name the hardware they want:

```rust
Output::new(p.PIN_16, Level::Low)           // ownership of PIN_16 moves here
Input::new(p.PIN_15, Pull::Up)              // ownership of PIN_15 moves here
Uart::new(p.UART0, p.PIN_0, p.PIN_1, ...)   // R, TX, RX, and DMA move in
```

## embassy_rp::init

`init` does the one-time, whole-chip setup that all later calls assume:

1. **Clock configuration** — Establish reliable clocks (crystal, PLLs, reference
   clocks) so timers and peripherals run at known rates.
2. **Peripheral reset release** — The RP2350 holds most peripherals in reset on
   boot (Chapter 26 of the ASM course is exactly this dance in assembly); `init`
   releases them into a clean state.
3. **Critical section machinery** — Registers the platform's interrupt-disabled
   critical-section implementation (below), the foundation for safe shared data.
4. **Returns `Peripherals`** — and consumes all those tokens forever after.

The signature is always `init(Default::default())` in our drivers. A custom
`Config` can set clock frequencies or disable unused blocks, but the defaults
are what the three drivers use — the tutorial's canonical form.

## The Peripherals Struct

Why does *ownership* of these tokens matter so much? Because ownership = the
borrow checker's guarantee of **exclusivity** (Chapter 4). Two concurrent tasks
cannot both own `UART0`; the code that tries to write one while another reads it
simply does not compile.

Passing `p.PIN_16` into `Output::new` *moves* the token. After that line, field
`p.PIN_16` no longer exists — the driver cannot accidentally configure GPIO16
twice, and nothing else can touch it. This is memory safety applied to hardware:
the compiler enforces that every peripheral has at most one driver, for the
program's lifetime.

## Critical Sections

Some operations must not be interrupted — say, reading a shared counter while an
interrupt handler might write it. Embassy's `embedded-hal`-based `critical_section`
crate provides a mechanism: enter a region with interrupts disabled, do your
work, exit. `embassy-rp`'s `critical-section-impl` feature (Chapter 8) supplies
the actual implementation.

```
+----------------------+
|     normal code      |
|  enter critical sec. |  interrupts disabled
|  ... atomic work ... |
|  exit critical sec.  |  interrupts enabled
|     normal code      |
+----------------------+
```

Executors and HAL code use critical sections internally — for example, atomically
claiming an interrupt. Application code rarely enters one by hand, but knowing
the mechanism explains why interrupts and the executor coexist safely.

## The rp235xa Chip Feature

The `rp235xa` feature on `embassy-rp` selects the RP2350 variant. Embassy's
crate covers several chips in the RP family; this feature points the HAL at the
right memory map, the right boot sequence, and the right register set. Without
it, `init` would configure the wrong silicon — the feature gate is what makes
"RP2350" and not "RP2040" true.

## Summary

- Peripherals are hardware blocks represented as exclusive ownership tokens.
- `embassy_rp::init(Default::default())` configures clocks, releases resets,
  installs the critical-section mechanism, and yields `Peripherals`.
- Moving a token (`p.PIN_16`) into a HAL constructor makes double-configuration
  a compile-time error.
- Critical sections guarantee atomicity against interrupts; the executor
  relies on them.
- `rp235xa` pins the HAL to the RP2350 chip.

Next: the most visible HAL of all — GPIO output and input pins.