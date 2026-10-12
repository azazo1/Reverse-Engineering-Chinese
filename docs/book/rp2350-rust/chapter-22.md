# Chapter 22: Button Hardware and Debouncing

## Introduction

A mechanical button is not the clean digital switch textbooks suggest. Inside
the switch, two metal contacts close and bounce for a few milliseconds, flapping
between closed and open dozens of times before settling. A firmware that samples
naively can read a single press as five presses. This chapter teaches the
hardware reality of the button driver — the wiring, the active-low convention,
the pull-up, and the debounce strategy that makes presses trustworthy.

## The Wiring

The button driver connects exactly two things beside power:

```
Button:   one terminal  -> GPIO15
          other terminal -> GND

LED:      anode (long leg) -> GPIO16 through a 330Ω resistor
          cathode (short)  -> GND
```

And in the shape we have used all course:

```
+-------------------------------+
|         RP2350 Pico 2         |
|                               |
|  GPIO15  o--------+---[Button]---+ GND
|                   |              |
|  GPIO16  o--------+---[330Ω]-----(>|)---> LED
|                                  |     |
|                                  +-----+ GND
+-------------------------------+
```

The button shorts the line to ground when pressed. The LED lights through 330 Ω
from GPIO16 when the pin is high.

## Active-Low Logic

Look again at the button's wiring: pressing it *grounds* the input. There is no
+V to *release* — the switch is tied to GND, so:

```
Button open    -> GPIO15 reads HIGH   (released)
Button pressed -> GPIO15 reads LOW    (pressed)
```

This is **active-low** logic: LOW says "action happening". The button driver
bakes that inversion into `update(gpio_high)`, where LOW input means "pressed":

```rust
let new_raw = !gpio_high;      // active-low: LOW input => pressed
```

Every docstring in the driver repeats the convention — "Button is active-low
(tied to GND when pressed)" — because a future reader must never have to deduce
it from the schematic.

## Pull-Up Resistors

When the button is open, nothing drives GPIO15, and a floating input reads
whatever noise is in the air. The fix is a **pull-up**: a weak resistance that
holds the line HIGH until the switch pulls it LOW.

```
+3.3 V -----[pull-up]----o----- GPIO15
                          |
                        [BUTTON]
                          |
                         GND
```

The RP2350 has internal pull-ups inside its pads. Embassy exposes them as
`Pull::Up`:

```rust
let button = Input::new(p.PIN_15, Pull::Up);
```

That is Chapter 17's `Pull` becoming real: the line is defined at rest (HIGH), so
the only way it goes LOW is a deliberate ground — the button. Ambiguous
floating is eliminated before a single sample is read.

## Contact Bounce

When the button is pressed, the metal contacts converge and rebound. The
voltage doesn't snap cleanly from high to low; it oscillates:

```
PRESSURE   PRESS        SETTLE
                v
HIGH  |‾‾‾‾‾‾|___|‾|__|________
LOW   |       |   | |   |‾‾‾‾‾‾‾|
        bounce ~5-20 ms
```

For 5–20 ms the line reports an erratic sequence of highs and lows. A firmware
that samples every microsecond could count ten "presses" from one physical
press — a light turning on and off faster than the eye can follow.

## Debouncing Strategies

Debounce = refuse to trust a state change until it has *held* for a while.
Two classic approaches:

**Time-based debounce** — after detecting a change, ignore the pin for a fixed
dead time. Simple, but it misses fast subsequent presses during the ignore
window.

**Sample-count debounce** — sample on a fixed cadence and require N consecutive
identical samples before changing the reported state. This is what the button
driver uses: `DEBOUNCE_COUNT` samples at `DEBOUNCE_DELAY_MS` spacing.

```
Sample:   H H H H H L L L L L  L L L ...
Count:    0       -> raw changes to LOW, count resets
          L(1) L(2) L(3) L(4) L(5) -> threshold hit, report PRESSED
```

The two knob-like constants live in `config.rs`:

```rust
DEBOUNCE_DELAY_MS: u64 = 5;     // sample every 5 ms
DEBOUNCE_COUNT:    u32 = 5;     // require 5 consecutive stable samples
```

5 samples × 5 ms = 25 ms to confirm a press — comfortably beyond the worst
bounce, and still instant to a human. Noise immunity and responsiveness are
tuned by these two numbers, which is why both are documented, tested, and
centralized in configuration.

## Sample-Based Debouncing

The driver's filter keeps three pieces of memory:

```
pressed         the public, debounced "is it pressed?" answer
raw_pressed     the latest unfiltered reading
debounce_count  consecutive identical samples so far
```

Each call to `update(sample)`:

```
+----------------+       +-----------------+       +-----------------+
|  New sample    |   ==  |  Same as last?  |   NO  |  Reset: raw =   |
|  (active-low)  |       |                 |       |  new, count = 0 |
+----------------+       +-----------------+       +-----------------+
                              | YES
                              v
                       +------------------+
                       | increment count  |
                       | (capped)         |
                       +---------+--------+
                                v
                       +------------------+
                       | count >= 5?      |  YES -> pressed = raw
                       +------------------+
```

A bounce produces samples that keep changing (`H L H L H`), so `raw_pressed`
keeps flipping and the count keeps resetting to zero. Only a stable run of five
identical samples lets the count reach the threshold and commits the state.

## Summary

- The button is wired active-low: press ground GPIO15, releasing reads HIGH.
- Internal pull-ups (`Pull::Up`) keep the line defined at rest — no floating.
- Contacts bounce for 5–20 ms, so raw readings are not trustworthy directly.
- The driver samples every `DEBOUNCE_DELAY_MS` and requires
  `DEBOUNCE_COUNT` stable samples before reporting a change.
- Both knobs are documented constants in `config.rs`, tunable per design.

Next we write the filter itself — `button.rs`, the file that turns raw
samples into a debounced truth.