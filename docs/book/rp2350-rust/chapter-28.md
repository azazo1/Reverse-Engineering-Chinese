# Chapter 28: Interrupts and DMA — Interrupt-Driven UART

## Introduction

UART `read(...).await` looks like magic: bytes land, the future completes, no
inputs wasted — because the hardware does not touch the CPU. Two RP2350
mechanisms make that possible: interrupts, which route "a byte arrived" into
the executor, and DMA, which moves bytes itself. This chapter connects
`bind_interrupts!`, `InterruptHandler`, and the two DMA channels in
`main.rs` to the `await` calls the driver makes.

## The CPU Would Waste Its Whole Loop

A **polling** receiver busy-loops sampling status bits waiting for a byte,
burning a hundred percent of the CPU:

```
CPU:        [read status] [no] [read status] [no] [read status] [no] ...
UART RX:    ..... ......... came! ............................. (missed or
                                                              polled late)
```

The driver never does that. It wires the UART peripheral's own signaling so the
CPU is interrupted *by the hardware* only when there is real work:

```
CPU:        [await]  ... [wakeup] echo [await] ... [wakeup] echo
UART RX:    ...... byte!   ...................  byte!  .........
```

Interrupts let the CPU sleep (or run other tasks) between bytes; this is the
interrupt-driven half of the design.

## bind_interrupts!

The driver only tells Embassy which peripheral owns which IRQ line once:

```rust
use embassy_rp::{bind_interrupts, peripherals::UART0, uart::InterruptHandler};

bind_interrupts!(struct Irqs {
    UART0_IRQ => InterruptHandler<UART0>;
});
```

Reading the macro block: "RP2350's `UART0_IRQ` vector fires `InterruptHandler`
with the `UART0` peripheral token." The macro-generates a struct `Irqs` that
statically registers the handler in the vector table and holds up to
`embassy_rp::init`. `InterruptHandler` wakes the executor's `Uart` future when
the FIFO signals a byte has been received or a transmission completes —
the exact moment the future's readiness flips from pending to ready.

Because the binding is called on the macro line (not at runtime) and `Irqs` is
consumed by `Uart::new`, the linkage is checked at compile time: a typo in the
IRQ name simply refuses to build.

## The Two DMA Channels

`Uart::new` takes two more peripherals after the pins:

```rust
let mut uart = Uart::new(
    p.UART0, p.PIN_0, p.PIN_1, Irqs, p.DMA_CH0, p.DMA_CH1, config,
);
```

`p.DMA_CH0` and `p.DMA_CH1` are the RP2350's two DMA controllers. Embassy
assigns one to reception and one to transmission, and once configured the DMA
engine drives the data bus on its own:

```
                in / out                           CPU: off doing math
Host <-> UART FIFO <--DMA0--< RAM (buf)   or   RAM (echo_bytes) -->DMA1--> UART FIFO
```

The result is a **DMA UART**: the peripheral hands bytes to a memory buffer
without the CPU ever copying them. That is the DMA half of the design.

## Interrupts + DMA + Async = The Whole Story

Both halves land in one `await`:

```rust
if uart.read(&mut buf).await.is_ok() { ... }
```

Step by step:

1. Embassy configures `DMA_CH0` to move the next RX byte into `buf[0]`, and
   takes the "wait" branch — the future registers interest.
2. The DMA engine fills `buf[0]` with no CPU help (when exactly one byte is
   requested).
3. The UART raises `UART0_IRQ`; the registered `InterruptHandler` marks the
   waiter ready.
4. The executor resumes the future; `.await` returns `Ok`.

`write` is the mirror: Embassy configures `DMA_CH1` to move `echo_bytes` to the
UART FIFO, the DMA drains it with the CPU watching no registers, and the write
future completes when the FIFO empties.

Nothing blocked, nothing polled, nothing hand-copied — and the whole arrangement
is expressed as ordinary-looking async code.

## Error Paths

`read` returns a `Result`, and the driver discards nothing silently:

```rust
if uart.read(&mut buf).await.is_ok() {
    let echo_bytes = controller.process_char(buf[0]);
    let _ = uart.write(echo_bytes).await;
}
```

On read errors the byte is skipped — safer than echoing garbage. The write's
`let _ = ...` acknowledges we do not recover if the wire is pulled; a future
driver could log the error. Embassy's error type (overrun, break, framing, or
parity conditions) is available whenever the code decides to care.

## Summary

- Waiting on UART by polling wastes the CPU; interrupts wake it only when a
  byte matters.
- `bind_interrupts!` statically routes `UART0_IRQ` to
  `InterruptHandler<UART0>`, compile time-checked.
- `DMA_CH0`/`DMA_CH1` move bytes between RAM and the FIFO without CPU copies.
- Asynchronous `read`/`write` are the fusion: await, DMA fills, IRQ wakes,
  future completes.
- Result-typed reads keep runaway errors from becoming silent garbage.

The finale of the UART driver is wiring all of it in `main.rs`.