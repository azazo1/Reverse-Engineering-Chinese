# Lesson 020 - 4-Digit 7-Segment Display

## What Are We Building Today?

We know how to light up a single 7-segment digit. But what if we want to display a 4-digit number like "1234"?
If a 1-digit display takes 8 wires, a 4-digit display must take 32 wires, right? Wrong! 

Through the magic of a hardware optical illusion called **Persistence of Vision (POV)** and a technique called **Multiplexing**, we can drive all 4 digits using only 12 wires total!

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/020/lesson.s)

---

## The Hardware: Multiplexing

Inside a 4-Digit 7-Segment Display module, all 4 of the "A" segments are wired together. All 4 of the "B" segments are wired together. 
If we send the signal to light up segment "A", *every single digit* will light up its "A" segment simultaneously.

To solve this, the module gives us 4 separate "Common Cathode" Ground pins, one for each digit. If we disconnect the Ground for Digit 2, 3, and 4, then *only Digit 1* will light up!

We will connect these 4 Ground pins to `PD2`, `PD3`, `PD4`, and `PD5`. (We usually use NPN transistors here so the microcontroller pins don't burn out).

## The Code Walkthrough

### 1. Extracting the Digits
We want to display the number `1234`. We load it into a 16-bit virtual register (`R25:R24`):
```assembly
  LDI    R25, hi8(1234)
  LDI    R24, lo8(1234)
```
We then call our trusty `extract_digits` subroutine (which uses the Repeated Subtraction algorithm from Lesson 15). 
This rips the number `1234` apart into `1`, `2`, `3`, and `4` and stores them in `R20`, `R21`, `R22`, and `R23`!

### 2. The Optical Illusion Loop (POV)
Now, we run our display loop. The goal is to only ever have ONE single digit turned on at any given millisecond. But we switch between them so fast that the human eye is tricked into thinking they are all on at the same time!

```assembly
.loop:
  ; --- Digit 1 (Thousands) ---
  MOV    R16, R20                      ; Load thousands digit ('1')
  RCALL  get_segment_pattern           ; Convert to segment mask (0x06)
  RCALL  shift_out                     ; Send to Shift Register
  RCALL  latch                         ; Latch it
  SBI    PORTD, PD2                    ; Turn ON Digit 1 Ground
  RCALL  delay_2ms                     ; Wait 2 milliseconds
  CBI    PORTD, PD2                    ; Turn OFF Digit 1 Ground
```

1. Load the Thousands digit (`1`).
2. Convert it to a segment mask using the Flash Array we learned in Lesson 19.
3. Send it to the Shift Register.
4. Turn **ON** `PD2` (Digit 1 Ground). Now the first digit shines brightly!
5. Wait `2ms`. (This is just enough time for the LED to get fully bright and hit your retina).
6. Turn **OFF** `PD2`. The display goes completely black!

We instantly repeat this exact same process for `Digit 2`, `Digit 3`, and `Digit 4`. 
Because the whole cycle finishes in `8ms` (125 times a second), it looks like a solid, unblinking number!

---

Congratulations! You have successfully mastered time-domain hardware multiplexing and Persistence of Vision illusions in bare metal assembly!
