# Chapter 12: Real-Time and Concurrency

## Introduction

A microcontroller must do many things at once: blink an LED, sample a button,
echo serial data, and maybe steer servo outputs — all on one core, interleaved
in microseconds. This chapter defines the concurrency problem and argues for the
solution the rest of the course uses: **cooperative async scheduling**, as
provided by Embassy.

## One Core, Many Tasks

The RP2350 has two cores, but each core runs exactly one instruction stream at a
time. "Many tasks" really means: interleave them quickly enough that the
hardware world sees each one making progress when it needs to.

Consider three jobs:

```
+----------------+   +----------------+   +----------------+
|  Blink LED     |   |  Sample Button |   |  Echo UART     |
|  every 500 ms  |   |  every 5 ms    |   |  continuously  |
+----------------+   +----------------+   +----------------+
```

None of them is doing useful work most of the time. A blink is a 500 ms wait
with a 1 us toggle. A button sample is a 5 ms wait around a 1 us read. The core
is idle for 99.99% of the time; the challenge is where the waits live and who
orchestrates the interleaving.

## Cooperative Scheduling

There are two ways to share one core. **Preemptive** scheduling lets the
kernel/RTOS force a task to pause at any instruction (`SysTick` interrupt +
context switch). With **cooperative** scheduling, a task runs until it
voluntarily yields, then another task runs.

```
Cooperative:      A runs | A yields | B runs | B waits | A runs ...
                            ^
                        tasks must grant the CPU themselves
```

Async Rust and Embassy are cooperative: an `async fn` yields at each `.await`.
Nobody can seize the CPU mid-operation; code runs atomically from one `.await`
to the next. This makes shared data dramatically safer — no two tasks ever touch
the same variable concurrently at the instruction level within one core.

## Busy-Waiting

The naive delay is a **busy-wait**: the core does nothing but count, a few
million times, until enough clock cycles pass:

```rust
fn delay_ms(ms: u64) {
    for _ in 0..(ms * 150_000) { }   // waste 150k cycles per ms
}
```

Busy-waiting has two costs:

1. **The core is useless during the wait.** While one task spins, the button is
   never sampled and incoming UART bytes overflow the FIFO.
2. **Timing is fragile.** The loop's cycle count depends on compiler
   optimization and features.

Firmware uses busy-waits only where strict, short, loop-accurate timing is
required — and even then carefully. For ordinary delays we use the hardware
timer instead.

## Events, Interrupts, and the Async Model

The hardware itself solves the waiting problem. Peripherals raise **interrupts**
when an event happens: a byte arrived, a timer expired, a DMA transfer finished.
The CPU then runs a short **interrupt handler** and returns.

Async Rust is the elegant generalization. Think of each interrupt as a signal
that an event occurred; the executor sleeps until some event fires, then wakes
the specific future that was waiting on it:

```
+-------------+         +--------------+         +--------------+
| Task A      |         |   Executor   |         |  Peripheral  |
| await x     | ------->| (sleeps on   |<-------|  event (IRQ) |
|             |         |  interrupt)  |         |  x happened  |
+-------------+         +--------------+         +--------------+
```

The CPU is genuinely asleep (`wfi` — wait for interrupt) between events,
consuming ~no power and no cycles. When a byte arrives, the UART interrupt wakes
the executor, which resumes the exact task that was waiting for that byte. This
is the model `Timer::after_millis(...).await`, `uart.read(...).await`, and
every other Embassy call uses.

## The Embassy Approach

Embassy packages all of this into the primitives we program with:

```
+------------------+
| embassy-executor |   the cooperative scheduler
+------------------+
| embassy-time     |   timers and delays on the time driver
+------------------+
| embassy-rp       |   the RP2350 HAL: GPIO, UART, DMA, ...
+------------------+
```

Application code writes ordinary-looking async functions; the executor
interleaves them, the time driver covers delays, and the HAL bridges async
futures to hardware events. In the next four chapters we meet each component:
futures and `async`/`await` (Chapter 13), the executor (Chapter 14), time
(Chapter 15), and the HAL (Chapters 16–17).

## Summary

- One core means one instruction stream; concurrency is fast interleaving.
- Embassy uses cooperative scheduling — tasks yield at `.await`.
- Busy-waiting wastes the only core and is used sparingly.
- Peripherals signal completion via interrupts; async Rust turns those signals
  into resumable waits.
- Embassy = executor (scheduling) + time driver (delays) + HAL (hardware),
  which is exactly the stack all three drivers are built on.

Next we open the box on Rust's async machinery: futures and `poll`.