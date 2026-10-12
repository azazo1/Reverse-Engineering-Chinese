# Chapter 29: main.rs — The UART Echo Loop

## Introduction

The UART driver's `main.rs` is the whole course in one file: `no_std`
attributes, module wiring, a `bind_interrupts!` binding, a configurable UART
built from eight arguments, and an async loop that reads a byte, transforms it,
and writes the result. It is only 87 lines, and this chapter walks every one of
them.

## Complete Source Code

Here is `src/main.rs` for the UART driver, in full:

```rust
/*
 * @file main.rs
 * @brief Microcontroller entry point
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

//! FILE: main.rs
//!
//! DESCRIPTION:
//! RP2350 Embedded Rust Embassy UART Echo Application.
//!
//! BRIEF:
//! Main application entry point for RP2350 UART echo driver using Embassy.
//! Implements async UART character echo on GPIO 0 (TX) and GPIO 1 (RX).
//!
//! AUTHOR: Kevin Thomas
//! CREATION DATE: December 4, 2025
//! UPDATE DATE: December 5, 2025

#![no_std]
#![no_main]

mod config;
mod uart;

use config::UART_BAUD_RATE;
use embassy_executor::Spawner;
use embassy_rp::uart::{Config, Uart};
use embassy_rp::{bind_interrupts, peripherals::UART0, uart::InterruptHandler};
use panic_halt as _;
use uart::UartController;

bind_interrupts!(struct Irqs {
    UART0_IRQ => InterruptHandler<UART0>;
});

/// Main application entry point.
///
/// # Details
/// Initializes Embassy runtime and runs the main UART echo loop.
/// Uses UartController for state management.
///
/// # Arguments
/// * `_spawner` - Embassy task spawner (reserved for future async tasks).
///
/// # Returns
/// * `()` - Never returns (infinite loop).
#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let p = embassy_rp::init(Default::default());
    let mut config = Config::default();
    config.baudrate = UART_BAUD_RATE;
    let mut uart = Uart::new(
        p.UART0, p.PIN_0, p.PIN_1, Irqs, p.DMA_CH0, p.DMA_CH1, config,
    );
    let mut controller = UartController::new();
    let mut buf = [0u8; 1];
    loop {
        if uart.read(&mut buf).await.is_ok() {
            let echo_bytes = controller.process_char(buf[0]);
            let _ = uart.write(echo_bytes).await;
        }
    }
}
```

Against the previous drivers, two things are genuinely new: the
`bind_interrupts!` block (Chapter 28) and the argument list of `Uart::new`.
The loop itself is smaller than the button's.

## Imports and the IRQ Binding

The imports pair Embassy's UART surface with the controller and config:

```rust
use embassy_rp::uart::{Config, Uart};
use embassy_rp::{bind_interrupts, peripherals::UART0, uart::InterruptHandler};
```

Then the one macro call the whole driver depends on:

```rust
bind_interrupts!(struct Irqs {
    UART0_IRQ => InterruptHandler<UART0>;
});
```

As Chapter 28 demonstrated, this creates the statically-registered `Irqs`
binding and hands it to `Uart::new`. It is written once, near the top, before
any execution — so the interrupt linkage exists before `main` begins.

## Constructing the UART

Eight arguments, four conceptual groups:

```rust
let mut config = Config::default();
config.baudrate = UART_BAUD_RATE;
let mut uart = Uart::new(
    p.UART0,          // the UART peripheral token
    p.PIN_0,          // TX pin
    p.PIN_1,          // RX pin
    Irqs,             // the interrupt binding from above
    p.DMA_CH0,        // DMA controller 0 (receive)
    p.DMA_CH1,        // DMA controller 1 (transmit)
    config,           // settings: baud 115200, 8N1
);
```

`Config::default()` already encodes a sane UART profile; the driver changes
exactly one field — `baudrate` — from the config module. The pin order `(TX,
RX)` matches the datasheet's `UART0_TX`/`UART0_RX` designation (Chapter 26),
and the DMA channels complete the interrupt+DMA story. Setup is complete in
nine lines; no registers were touched by hand.

## The Controller and the Buffer

```rust
let mut controller = UartController::new();
let mut buf = [0u8; 1];
```

The controller tracks echo statistics. The buffer is a single byte on the
stack — exactly one RX byte in flight. Embassy's DMA writes into its own
internal static first and copies here, so a stack array of size one is all the
application ever needs.

## The Echo Loop

```rust
loop {
    if uart.read(&mut buf).await.is_ok() {
        let echo_bytes = controller.process_char(buf[0]);
        let _ = uart.write(echo_bytes).await;
    }
}
```

Four steps, the whole application:

1. `uart.read(&mut buf).await` — suspend until a byte arrives (hardware
   interrupt + DMA as in Chapter 28); `Ok` means a byte sits in `buf`.
2. `controller.process_char(buf[0])` — translate the byte into echo bytes and
   bump the count (Chapter 27).
3. `uart.write(echo_bytes).await` — transmit and wait for the FIFO to drain.
4. Loop — the executor absorbed every pause; the CPU never polled a register.

The read `Result` is checked so error frames (parity, overrun, break) never
reach the echo — and the write result is consciously discarded with `let _`,
documenting that a full wire is not recoverable at this layer.

Running the driver with a host terminal at 115200, each keystroke returns
immediately, and the backspace key visibly erases the previous character.

## Summary

- Imports + one `bind_interrupts!` establish the UART IRQ linkage before
  anything runs.
- `Config` + `Uart::new` with eight arguments build the entire UART in nine
  lines, changing only the baud rate from defaults.
- A one-byte buffer and a shared controller are the loop's only state.
- The loop reads, translates, writes, and repeats — sleeping on each `await`.
- Reads check `Ok`; writes acknowledge errors consciously.

Part VI complete. The final chapter assembles all three drivers into a single
integrated application.