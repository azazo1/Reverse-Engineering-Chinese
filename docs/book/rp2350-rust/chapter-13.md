# Chapter 13: Futures and async/await

## Introduction

`async` and `await` look like magic but are built from one honest primitive: the
**future** — a value that represents work that is not finished yet. Understanding
futures is understanding what `.await` does, which is understanding the heart of
Embassy. This chapter converts each keyword into what really executes.

## What Is a Future?

A `Future` is a Rust trait with one method:

```rust
pub trait Future {
    type Output;
    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output>;
}
```

Three facts matter for us:

- A future has an **Output** type — the value it eventually produces
  (`Timer` produces `()`, read produces a `Result`).
- Calling `poll` makes progress. The future either returns `Ready(output)` —
  done — or `Pending` — waiting for something, come back later.
- A future is a **state machine**, not a thread. It occupies one fixed-size
  struct and stores nothing beyond its `.await` bookkeeping.

This is why futures are cheap on a microcontroller: no thread stacks, no heap, no
kernel. Every `.await` is just a state in a small struct the executor holds.

## Polling

When a future returns `Pending`, what makes it run again? Something must call
`poll` again once its condition holds. In Embassy that "something" is the
executor (Chapter 14), woken by a hardware interrupt. The future is polled,
finds its condition now true, and returns `Ready`.

```
poll #1  ->  Pending        (need the timer to tick)
               ...CPU sleeps, interrupt fires...
poll #2  ->  Ready(())      (500 ms elapsed, yield the result)
```

The cost of `Pending` transitions is zero hardware work: the future merely
stores "I am waiting" and returns. The machine burns nothing while it sleeps.

## The State Machine

The compiler turns an `async fn` into a struct with a field per local variable
and an internal state per `.await` point:

```rust
async fn blink_once() {
    led.set_high();                     // state S0
    Timer::after_millis(500).await;     // state S1 (suspended here)
    led.set_low();                      // state S2
}
```

Conceptually:

```
S0: set high, build the Timer future, poll it  -> enter S1
S1: Timer pending?  -> stay S1.  Timer ready?  -> S2
S2: set low, return Ready
```

The `.await` on the timer becomes "poll the timer; if Pending, save my state and
return Pending." When polled again, execution resumes exactly at that `.await`,
not at the top. That serial resume is the entirety of async's magic.

## async and await

- **`async fn`** — Declares a function that returns a future; the body runs only
  when the future is polled, not when the function is called.
- **`.await`** — Poll the inner future to completion, suspending the enclosing
  future if the inner one is `Pending`. `.await` is only valid **inside** an
  `async` context.

```rust
async fn routine() {
    set_led_high();
    Timer::after_millis(500).await;   // suspend here for 500 ms
    set_led_low();
}
```

`Timer::after_millis(500)` *returns a future*; the `.await` drives it. Without
the `.await` the future would be created and dropped, timing would never start,
and nothing would happen — a classic bug with a clean fix.

You cannot `.await` from `main` unless `main` is async and there is an executor
to poll it. That is exactly why every driver writes
`#[embassy_executor::main] async fn main(...)`: the attribute attaches an
executor so the `async fn` has something to run on.

## Blocking vs Non-Blocking

The UART driver gives us a perfect contrast. The HAL offers blocking and async
forms of the same operation:

```
Blocking call:  uart.blocking_write(&buf)   // task spins until sent
Async call:     uart.write(&buf).await      // yields; others run
```

In the echo loop we use the async forms for both directions:

```rust
loop {
    if uart.read(&mut buf).await.is_ok() {   // wait, neuron IDLE, run others
        let echo_bytes = controller.process_char(buf[0]);
        let _ = uart.write(echo_bytes).await; // wait, again idles
    }
}
```

While `read(...).await` is pending, the executor runs the blink task if it is
ready, or sleeps the core. That shared-idle behavior is the entire reason
Embassy firmware can appear to do many things at once — nothing busy-waits; the
waiting IS the cooperative yield.

## Summary

- A future is a pollable state machine: `poll` returns `Ready` or `Pending`.
- `Pending` means "come back later"; the executor resumes us when hardware
  signals an event.
- The compiler encodes every `.await` as a state in a fixed-size struct.
- `async fn` returns a future; `.await` drives it to completion from within an
  async context.
- Async waiting yields the core to other tasks — no busy-wait, no wasted
  cycles.

Next: the executor itself, and the `#[embassy_executor::main]` attribute that
starts everything.