# Chapter 2: Number Systems and Memory

## Introduction

Every register, every address, and every incoming byte on a UART wire is a
number. To program a microcontroller we must be fluent in the three number
systems Rust and the hardware share: **decimal**, **binary**, and
**hexadecimal**. This chapter builds that fluency and connects it to the
RP2350's physical memory map.

## Decimal — Base 10

Decimal is the counting system we learn in school. It uses ten digits,
`0` through `9`, and each position represents a power of ten:

```
  4  8  2  6
  |  |  |  |
  |  |  |  +-- 10^0  = 6 x 1       =      6
  |  |  +----- 10^1  = 2 x 10      =     20
  |  +-------- 10^2  = 8 x 100     =    800
  +----------- 10^3  = 4 x 1000    =   4000
                            total   =   4826
```

## Binary — Base 2

A computer's memory element has exactly two states: off or on. We represent
those states with the digits `0` and `1` — one **binary digit**, one **bit**.
Every position is a power of two:

```
  0  0  0  0  1  0  1  1
  |  |  |  |  |  |  |  |
  |  |  |  |  |  |  |  +-- 2^0  = 1 x 1      =       1
  |  |  |  |  |  |  +----- 2^1  = 1 x 2      =       2
  |  |  |  |  |  +-------- 2^2  = 0 x 4      =       0
  |  |  |  |  +----------- 2^3  = 1 x 8      =       8
  |  |  |  +-------------- 2^4  = 0 x 16     =       0
  |  |  +----------------- 2^5  = 0 x 32     =       0
  |  +-------------------- 2^6  = 0 x 64     =       0
  +----------------------- 2^7  = 0 x 128    =       0
                                    total    =      11
```

So `0b00001011` is decimal 11. Eight bits form a **byte**, and a byte can hold
any value from `0` (`0b0000_0000`) to `255` (`0b1111_1111`).

## Hexadecimal — Base 16

Writing long binary values is error-prone. Hexadecimal packs four bits into one
symbol. Its digits are `0`–`9` and then `A`–`F` for the values 10–15:

```
BINARY    0000 0001 0010 0011 0100 0101 0110 0111
HEX         0    1    2    3    4    5    6    7

BINARY    1000 1001 1010 1011 1100 1101 1110 1111
HEX         8    9    A    B    C    D    E    F
```

One hex digit is exactly four bits. A byte is exactly two hex digits:

```
  0b 1100_0010    =    0xC2
      |    |
      |    +-- 0b0010 = 2
      +------- 0b1100 = C
```

This is why every peripheral register and the entire RP2350 address map are
written in hex. `0x20000000` is far easier to read, transcribe, and verify than
its binary form.

## The 0x Prefix

Rust follows C's convention for number literals. This matters because our
`config.rs` files and memory map are full of these prefixes:

```rust
let flash_base = 0x1000_0000u32;
let ram_base   = 0x2000_0000u32;   // underscores group digits, ignored by the compiler
let mask       = 0b0000_0011u8;    // binary literal
let count      = 10_000u64;        // decimal literal with grouping
```

The `u32`, `u8`, and `u64` suffixes pin the exact width of each value. Getting
the width right is essential: a `u8` can hold `0xFF` but not `0x100`.

## Bytes, Halfwords, and Words

The RP2350 addresses memory in units of eight bits, a byte. Larger units are
built from bytes:

```
+-----------------------------------+
| Byte      (u8)   8 bits          |
| Halfword  (u16)  2 bytes         |
| Word      (u32)  4 bytes         |
+-----------------------------------+
```

Rust's integer types map directly onto these hardware sizes:

| Rust type | Bits | Bytes | Max value             |
|-----------|------|-------|-----------------------|
| `u8`      | 8    | 1     | `0xFF`  (255)         |
| `u16`     | 16   | 2     | `0xFFFF` (65,535)     |
| `u32`     | 32   | 4     | `0xFFFF_FFFF`         |
| `u64`     | 64   | 8     | `0xFFFF_FFFF_FFFF_FFFF`|

Unsigned (`u`) types hold only non-negative values. Signed (`i`) types hold
positive and negative values in two's complement.

## Alignment

When the CPU reads a 32-bit word from memory, it is fastest and most natural if
that word crosses no address boundary of the word size. We say the access must
be **aligned** to a multiple of its size:

```
ALIGNED                      MISALIGNED
+---+---+---+---+            +---+---+---+---+
| W0 |     |     |           |   | W0|     |
+---+---+---+---+            +---+---+---+---+
  ^                              ^
 0x20000000                    0x20000001
 W0 = bytes 0-3               W0 = bytes 1-4
```

Rust defines each struct's layout so its fields are naturally aligned. Typical
embedded code never thinks about alignment because the compiler enforces it; we
mention it here because the hardware datasheet will.

## Little-Endian Byte Order

The RP2350 stores multi-byte values **little-endian**: the least significant
byte lives at the lowest address. The value `0xAABBCCDD` is laid out as:

```
ADDRESS   BYTE
0x00      DD   (least significant)
0x01      CC
0x02      BB
0x03      AA   (most significant)
```

Rust uses the native byte order of the target, which for the RP2350 is
little-endian. When we receive bytes over UART one at a time, we assemble them
in this same order.

## Memory-Mapped I/O

Peripherals on the RP2350 are controlled through registers that appear at fixed
addresses in the same address space as RAM and flash. Writing a 0 or 1 to a GPIO
output register is a normal memory store; the hardware reacts. This design is
called **memory-mapped I/O** and we explore it fully in Chapter 11.

For now, keep the big picture:

```
+-----------------------------+      +-----------------------------+
|       CPU/Memory Bus        |      |       Peripheral Bus        |
+-----------------------------+      +-----------------------------+
    |        |        |                  |         |        |
   RAM     FLASH     ...               GPIO      UART      DMA
0x20000000 0x10000000            0x40000000 + ...   writes here
                                            change pin states
```

## The RP2350 Address Map

The exact regions we use in all three drivers:

```
+----------------+----------------+------------------+
| Address        | Region         | Use              |
+----------------+----------------+------------------+
| 0x10000000     | FLASH          | XIP firmware     |
| 0x20000000     | SRAM (512 KB)  | Stack and heap   |
| 0x20080000     | SRAM8 (4 KB)   | Bootrom scratch  |
| 0x20081000     | SRAM9 (4 KB)   | Bootrom scratch  |
| 0x40000000 ... | Peripherals    | GPIO, UART, DMA  |
+----------------+----------------+------------------+
```

Our firmware runs from `0x10000000` (flash), places its stack at the top of
`0x20000000` (RAM), and does all hardware control through registers in the
peripheral region. You will see these three numbers in the `memory.x` linker
script in Chapter 9.

## Why This Matters

Every constant in the three drivers is a number in one of these systems:

- `BLINK_DELAY_MS: u64 = 500` — a plain decimal.
- `UART_BAUD_RATE: u32 = 115200` — a plain decimal.
- `BACKSPACE: u8 = 0x08` — a control-character hex code.
- GPIO addresses like `0x40014000` — hexadecimal region bases.

When you can translate between binary, hex, and decimal without thinking, you
can read a register dump, a linker script, or a datasheet as easily as prose.

## Summary

- Bits are the atoms of memory; 8 bits make a byte, 4 bytes make a word.
- Hexadecimal is a compact notation for binary; one hex digit is four bits.
- The RP2350 is little-endian, so least significant bytes sit at low addresses.
- Peripherals are controlled through registers in the memory-mapped address
  space.
- The address map — `0x10000000` flash, `0x20000000` RAM, `0x40000000`
  peripherals — appears throughout the rest of this course.

Next we begin the Rust language itself: variables, types, and control flow.