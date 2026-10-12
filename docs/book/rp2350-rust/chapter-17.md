# Chapter 17: GPIO with embassy-rp

## Introduction

Two of our three drivers are GPIO programs. The blink driver owns an **output**
pin and flips it. The button driver owns an **input** pin, reads it, and flips
the same kind of output. This chapter explores `embassy_rp::gpio` — the four
pieces (`Level`, `Output`, `Input`, `Pull`) and the calls every driver makes.

## Level

`Level` is the electrical truth we converted to a boolean in `led.rs`:

```rust
pub enum Level {
    High,
    Low,
}
```

Two lines of code, two voltage states on the pin:

```
+-----+        +-- HIGH (~3.3 V)
|     |       |
+-----+       |      +-- LOW (~0 V)
      |       |     |
      +-------+-----+
      Time        -->
```

Construction takes the initial state: `Output::new(p.PIN_16, Level::Low)` starts
the pin low. Our `led_state_to_level` maps a `LedState` to 0/1 (Chapter 5); 
GPIO maps that bool back to a `Level`-like decision when calling `set_high`/
`set_low`.

## Output Pins

An output pin is created once, configured fully, and then used for its whole
life:

```rust
let mut led = Output::new(p.PIN_16, Level::Low);
```

- `Output::new(pin, level)` — Claims the pin, configures the pad (Chapter 11),
  sets the initial level.
- `led.set_high()` — Drive the pin high.
- `led.set_low()` — Drive the pin low.
- `led.toggle()` — Invert the current state (available on the `ToggleableOutputPin`
  trait).

The `mut` is required because these methods take `&mut self` — the pin's state
changes. The blink loop leans on exactly two calls:

```rust
if led_state_to_level(state) {
    led.set_high();
} else {
    led.set_low();
}
```

The `Output<'d, T>` generic remembers which pin it owns (`'d` is the pin's
lifetime), so the compiler checks you never mix up GPIO16 and GPIO17.

## Input Pins and Pull

Reading a pin needs the electrical *opposite* setup: the pad must float or be
held, and the chip samples the level. That floating question is where `Pull`
enters:

```rust
pub enum Pull {
    None,
    Up,     // hold the line HIGH when nothing drives it
    Down,   // hold the line LOW when nothing drives it
}
```

The button driver configures its input:

```rust
let button = Input::new(p.PIN_15, Pull::Up);
```

With `Pull::Up` the pin reads high when the button is open. Pressing the button
grounds it, so the pin reads low — the **active-low** wiring of Chapter 22.
Without the pull-up, a floating input reads random noise and the whole debounce
design falls apart.

## Reading and Writing

The two reading calls available on `Input`:

- **`is_high()`** — `true` if the input level is high.
- **`is_low()`** — the complement.

The button loop samples with `is_high`:

```rust
controller.update(button.is_high());
```

After waking from its `Timer`, the loop asks the pin "high or low?" and feeds
the answer into the debounce filter as "released or pressed?" The bool is the
interface — no bit, no register, no pad knowledge ever appears in application
code.

## GPIO in Our Drivers

Put the pieces together for both loops:

```
Blink:                          Button:
+-------------+                 +---------------+
| Output::new |                 | Input::new    |
| PIN_16, Low |                 | PIN_15, Up    |
+-------------+                 +---------------+
      |                               |
      v                               v
+-------------+                 +---------------+
| toggle state|                 | update(sample)|
+-------------+                 +---------------+
      |                               |
      v                               v
+-------------+                 +---------------+
| set_high/   |                 | set_high/     |
| set_low     |                 | set_low       |
+-------------+                 +---------------+
```

Every driver touches GPIO at the same three moments: construct the pin once,
read or write it in a loop, and let Embassy own the registers forever after.

## Summary

- `Level::High/Low` is the electrical state of a pin.
- `Output::new(pin, level)` configures and claims an output pin; methods are
  `set_high`, `set_low`, and `toggle`.
- `Input::new(pin, pull)` configures an input pin; `is_high`/`is_low` sample it.
- `Pull::Up` holds the line high when nothing drives it — the foundation of the
  button driver.
- Overly precise types (`Output<'d, T>`) let the compiler catch pin misuse at
  build time.

Part III is complete: you can now read any Embassy GPIO program. Part IV builds
the first complete driver on top of it — the blink driver, file by file.