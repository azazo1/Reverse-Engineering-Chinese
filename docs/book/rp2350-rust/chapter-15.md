# Chapter 15: embassy-time

## Introduction

The blink driver's heartbeat is `Timer::after_millis(controller.delay_ms())`,
and the button driver samples on `Timer::after_millis(DEBOUNCE_DELAY_MS)`. Both
calls suspend the task for a measured interval without consuming the core. This
chapter opens `embassy-time`: the time driver beneath it, the `Instant` and
`Duration` types that express times, and the `Timer` future that waits on them.

## The Time Driver

`embassy-time` itself knows no hardware. It is a portable API backed by a
**time driver** that `embassy-rp` provides when the `time-driver` feature is
enabled (Chapter 8). The driver owns the hardware timer and answers one question:
*what time is it now?*

```
+------------------+      +--------------------+
|  embassy-time    |  --> |  embassy-rp driver |
|  generic API     |      |  (RTC + timer IRQ) |
+------------------+      +--------------------+
```

The driver ticks in **microseconds**. Timing resolution of a few microseconds is
far finer than our 500 ms blink period — but the same driver can schedule a
byte-timeout of 100 us or a watchdog of 5 seconds without changing anything in
application code.

## Instant and Duration

Two types carry the units:

- **`Instant`** — A point in time on the driver's timeline. Created by
  `Instant::now()`; comparable and subtractable.
- **`Duration`** — A span of time. Built from named constructors:
  `Duration::from_micros`, `::from_millis`, `::from_secs`, and friends.

`Instant` minus `Instant` gives a `Duration` — the amount of time that passed:

```rust
let start = Instant::now();
read_sensor();
let elapsed = start.elapsed();          // Duration
if elapsed < Duration::from_millis(10) {
    // still inside the window
}
```

`Instant`/`Duration` are `Copy`, so they pass around freely in our controller
structs — a pattern you can use to add timeouts to any driver.

## Timer

`Timer` is the wait primitive. Its two most common forms:

```rust
Timer::after_millis(500).await;           // wait 500 ms from now
Timer::after(Duration::from_secs(1)).await; // wait 1 second from now
```

`Timer::after(...)` and `Timer::at(instant)` hang a future off the ticking
clock. Polling the future returns `Pending` until the deadline passes, then
`Ready(())`. While it is `Pending` the executor runs other tasks — the exact
cooperative behavior of Chapter 12:

```
Task:  set_led_high  ->  await Timer 500ms  ->  set_led_low  ...
                          |          |
                          v          v
Executor:              other work or wfi (idle)
```

## after_millis in Our Drivers

The blink loop's timing comes straight from its own state — the `delay_ms`
field of `LedController`:

```rust
loop {
    let state = controller.toggle();
    if led_state_to_level(state) {
        led.set_high();
    } else {
        led.set_low();
    }
    Timer::after_millis(controller.delay_ms()).await;
}
```

Every iteration: toggle the state, drive the pin, and sleep for the configured
interval. Because the delay is a *method*, the timing policy lives inside the
controller; `main` just reads it out.

The button driver samples on its own interval:

```rust
Timer::after_millis(DEBOUNCE_DELAY_MS).await;
```

Five milliseconds apart, the loop feeds fresh pin samples into the debounce
filter (Chapters 22–23). Both loops do the same thing: `.await` on a `Timer`
turns "wait" into "yield," and the executor proves it by running the leftover
time on useful work or nothing at all.

## Summary

- `embassy-time` is a portable API backed by the RP2350 time driver
  (`time-driver` feature).
- `Instant` is a point in time; `Duration` is a span; both are `Copy`.
- `Timer::after_*` returns a future that becomes `Ready` when the deadline
  passes.
- Waiting on a `Timer` yields the core — the cooperative heart of every driver.
- The blink and button loops both derive their period from configuration
  constants read at runtime.

Next: the HAL. How `embassy_rp::init` hands us the whole processor, safely.