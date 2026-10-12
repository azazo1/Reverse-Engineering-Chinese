# Chapter 26: UART Fundamentals and the Echo Protocol

## Introduction

UART (Universal Asynchronous Receiver/Transmitter) is the oldest, simplest,
most universal way to move bytes between two systems. The RP2350 is born with
UART0 and UART1; the UART driver uses UART0 on GPIO0 (TX) and GPIO1 (RX) to
build an **echo terminal**: every character you type comes back to you, and a
backspace erases the previous character. This chapter lays down the protocol,
the wiring, and the design before the code.

## The Protocol

UART sends bytes one bit at a time beside a shared clock-free wire pair.
"Asynchronous" means there is no clock line: both ends must agree on speed and
frame shape in advance.

A single frame looks like:

```
| START |  D0  |  D1  |  D2  |  D3  |  D4  |  D5  |  D6  |  D7  | STOP |
|   0   | lsb  |  .   |  .   |  .   |  .   |  .   |  .   | msb  |  1   |
```

- Idle wire is HIGH.
- START pulls it LOW for one bit time — the receiver's trigger.
- Eight data bits follow, least significant first.
- STOP returns the wire HIGH.

Two resident RP2350 UARTs are available; the driver uses UART0. Its pins:

```
+-------------------------------+
|         RP2350 Pico 2         |
|                               |
|  GPIO0  -------- UART0_TX     |----> to USB-serial (TX -> RX)
|  GPIO1  -------- UART0_RX     |<---- from host (RX -> TX)
|                               |
+-------------------------------+
  Host terminal @ 115200 8N1
```

Because Linux terminals on the Pico are reached through a USB-UART bridge, the
pins cross: the chip's **TX** feeds the bridge's **RX**, and its **RX** takes the
bridge's **TX**. The driver therefore declares the pins in the order `(TX, RX)`:

```rust
Uart::new(p.UART0, p.PIN_0, p.PIN_1, Irqs, p.DMA_CH0, p.DMA_CH1, config);
```

## Baud Rate and 8N1

The only handshake is timing. Both ends must agree on the bit clock — the
**baud rate** — and the frame format. The protocol shorthand **8N1** reads "eight
data bits, No parity, 1 stop bit", and with 115200 baud a bit lasts ~8.7 µs.

The rate lives in `config.rs` as a documented constant, so the terminal and the
firmware cannot disagree by accident:

```rust
/// Default UART baud rate.
///
/// # Details
/// Configures the UART communication speed.
/// Standard baud rate for serial communication.
///
/// # Value
/// 115200 baud
#[allow(dead_code)]
pub const UART_BAUD_RATE: u32 = 115200;
```

On the host side the recipe is `stty -F /dev/ttyACM0 115200 raw -echo`. Every
runtime knob the firmware needs — baud, backspace identity, erase pattern —
lives in `config.rs`, so tuning a UART never requires editing logic.

## The Echo Protocol

A terminal is a dumb wire plus a screen: it sends each keystroke as a byte and
relies on the far side to echo it back so the user sees what they typed. The
driver's protocol is a tiny ASCII contract:

```
Host sends            Firmware echoes
---------------       ---------------
'A'                   'A'
backspace (0x08)      backspace + space + backspace   (erase)
delete    (0x7F)      backspace + space + backspace   (erase)
'n' etc.              itself
unknown (0x01)        nothing
```

Why is the erase three bytes? A terminal cursor sits to the right of a printed
character. To delete it, the firmware must move the cursor left (backspace),
print a blank to cover the letter, and move left again for the next erase.
`config.rs` bundles the pattern once:

```rust
/// Backspace erase sequence: backspace, space, backspace.
///
/// # Details
/// When echoed to a terminal this sequence erases the previous character.
///
/// # Value
/// [0x08, b' ', 0x08]
#[allow(dead_code)]
pub const BACKSPACE_SEQ: [u8; 3] = [0x08, b' ', 0x08];
```

ASCII matching brings in two backspace spellings (`BACKSPACE = 0x08` and
`DELETE = 0x7F`) because terminals disagree about which one a backspace key
produces. The firmware treats both as erases — a `match` that is still
exhaustive because `process_char` falls back to `b""` for anything else.

## Async Receive and Transmit

The UART driver's `main` reads one byte at a time with an async `await`:

```rust
if uart.read(&mut buf).await.is_ok() {
    let echo_bytes = controller.process_char(buf[0]);
    let _ = uart.write(echo_bytes).await;
}
```

While waiting, the `.await` yields to the executor — the CPU is free. Behind the
scenes, hardware is doing almost everything:

- **Interrupts** — the UART peripheral raises `UART0_IRQ` on new data; the
  `InterruptHandler<UART0>` bounces it into the executor's wakeups.
- **DMA** — `p.DMA_CH0` and `p.DMA_CH1` let the two DMA controllers shuttle
  bytes between memory and the UART FIFO with no CPU involvement.

The interplay of those two pieces is Chapter 28's subject. For protocol
purposes, what matters is the clean async surface: `read` sleeps until a byte
lands, `write` sleeps until bytes are flushed.

## The Controller Role

As in every driver, a pure, testable controller holds the logic and is tested
on the host. `UartController` keeps just one counter — `echo_count` — and maps
every input byte to the bytes that must be echoed:

```
+------------+     +-----------------+     +-----------------+
| UART rx    | --> | UartController  | --> | bytes to       |
| byte       |     | process_char    |     | echo back (TX) |
+------------+     +-----------------+     +-----------------+
```

Nothing about RPC devices or FIFOs leaks into the controller; it is a function
from `u8` to `&'static [u8]` with a running total. That purity is what makes a
twenty-test suite possible.

## Summary

- UART is a two-wire, clock-free, byte-by-byte protocol; the RP2350 provides
  UART0/UART1, and the driver uses UART0 on GPIO0 (TX) and GPIO1 (RX).
- Both ends agree on the frame — 115200 8N1 — via `UART_BAUD_RATE`.
- The echo protocol maps keystrokes to responses: identity, a three-byte
  erase for either backspace spelling, and silence for unknown bytes.
- Async `read`/`write` pause the executor, not the CPU, while interrupts and
  DMA do the physical work.
- The testable core is `process_char`, a pure function from byte to response.

Next, the state machine itself — `uart.rs`.