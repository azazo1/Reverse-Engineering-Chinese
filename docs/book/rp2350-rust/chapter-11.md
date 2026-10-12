# Chapter 11: Memory-Mapped I/O

## Introduction

How does software drive a physical pin high? The answer is simpler than it
sounds: the RP2350 exposes every peripheral as a block of **registers**, and
registers are just memory locations. A store to `SIO_OUT`, a load from
`UART_RDR` — these are ordinary loads and stores from the CPU's point of view.
This chapter explains memory-mapped I/O, why it needs care in Rust, and how
Embassy's types protect us from its dangers.

## Registers as Addresses

Peripheral registers live in the region of the address map we met in Chapter 2:

```
0x40000000 ... Peripherals ...
   GPIO0 pads     0x40014000 ...
   SIO            0xD0000000 ...
   UART0          0x40034000 ...
   DMA            0x50000000 ...
```

A register like "GPIO output level" has a number, an offset, and a bit layout.
In C, code touches these with a raw pointer cast. In Rust we refuse to do that
directly — which is precisely the difference Embassy makes.

## Why Volatile Matters

The optimizer can destroy naive register access. Consider this loop that reads a
status bit until it becomes 1:

```rust
fn wait(reg: *mut u32) {
    while *reg == 0 { /* spin */ }   // compiler may read once and fast-forward!
}
```

Because nothing in the loop observes `*reg` changing, the compiler is free to
hoist the load out of the loop. The hardware famously *does* change the value;
the resulting code spins forever. Writes can suffer the same fate — a store no
one reads back may be optimized away entirely.

The `volatile` qualifier tells the compiler: this read/write has **side
effects**, do not cache, combine, reorder, or remove it. Every register access
in firmware must be volatile:

```rust
let reg = 0x40014000u32 as *mut volatile u32;
reg.write_volatile(0xFF);   // goes to the bus, always
let v = reg.read_volatile(); // comes from the bus, always
```

Embassy wraps every peripheral in a register API generated from the chip's
vector table; "volatile" is baked in. By the time we write application code with
`set_high()`, the volatile machinery is already there — we never type
`unsafe` or know an address.

## Read-Modify-Write

Controlling individual bits of a status register without disturbing neighbors
requires the classic sequence:

```
+--------+     +----------+     +--------+
|  READ  | --> |  MODIFY  | --> |  WRITE |
| reg    |     |  (mask + |     | reg    |
|        |     |   shift) |     |        |
+--------+     +----------+     +--------+
```

To turn on bit 2 while leaving everything else intact:

```rust
let mut v = reg.read_volatile();
v |= 1 << 2;            // set bit 2
reg.write_volatile(v);
```

The hardware designers ship **atomic set/clear** registers on many peripherals
to avoid torn updates between two tasks. The RP2350's GPIO SIO block is the
famous example: one register sets bits, another clears them, and a single store
cannot lose a racing neighbor's update. Embassy exposes these unfriendly regions
as safe, high-level calls so application code never hand-folds bits — but this
pattern is *why* those calls exist.

## Layering Through the HAL

We never want application code touching registers directly. The layers look
like this:

```
+-----------------+   Application logic (LedController, main loop)
+-----------------+   Embassy HAL (Output, Input, Uart, Timer)
+-----------------+   PAC register API (volatile, generated)
+-----------------+   Raw hardware registers
```

Each layer sits between us and the bare register. The **PAC (Peripheral Access
Crate)** — `embassy-rp`'s register layer — gives every register a type-safe,
volatile accessor. The **HAL** builds higher behavior on top: "a GPIO pin" is a
handle to the right banks and registers. The **application** only ever says
"I want an output pin on GPIO16."

## GPIO Pads on the RP2350

Before a pin can be used as an output, the silicon must configure the pad — the
electrical interface to the outside world. The RP2350 has two register blocks:

```
+----------------+     +----------------+     +----------------+
|  PADS_BANK0    | --> |  IO_BANK0      | --> |  SIO OUTPUT   |
|  drive strength|     |  function sel  |     |  pin set/clear|
|  pull, schmitt |     |  input enable  |     |  (final stage)|
+----------------+     +----------------+     +----------------+
```

1. **PADS_BANK0** — Electrical properties: pull-up/pull-down, drive strength,
   Schmitt trigger, output enable.
2. **IO_BANK0** — Function select (GPIO, UART, SPI, ...) and input enable.
3. **SIO** — The atomic output/input registers we actually set high/low.

The ASM tutorials program these three layers by hand, register by register. In
Rust, `embassy_rp::gpio::Output::new(p.PIN_16, Level::Low)` configures all of
them for us at construction. Chapter 17 dissects that call from the other side —
what construction configures, and what reading/writing afterwards does.

## Summary

- Peripherals are memory: registers sit at fixed addresses in a peripheral
  region and react to ordinary loads and stores.
- Register access must be `volatile` so the optimizer respects hardware side
  effects.
- Read-modify-write is the fundamental bit-twiddling pattern; hardware atomic
  set/clear registers avoid races.
- Embassy layers application code over the HAL over PAC registers over raw
  silicon, so firmware never touches an unsafe address.
- Configuring a GP I/O pin means configuring the pad, the function select, and
  the SIO output stage — all folded into `Output::new`.

Bare-metal foundations are done. Now we learn the programming model that makes
Embassy special: async Rust on a single core.