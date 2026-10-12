# Lesson 004 - RGB LED

## What Are We Building Today?

Welcome to Lesson 4! Have you ever wondered how your TV, phone screen, or computer monitor creates millions of different colors? 

It actually only uses three colors: **Red**, **Green**, and **Blue** (RGB). By mixing these three primary colors of light, you can create almost any color imaginable!

Today, we are going to control an RGB LED to cycle through solid Red, Green, and Blue, and then turn completely off. 

By the end of this lesson, you'll know how to control multiple pins at the exact same time using pure Assembly!

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/004/lesson.s)

---

## Hardware Check: The RGB LED

An RGB LED is essentially three tiny LEDs squished into a single bulb. Because there are three LEDs inside, it needs 4 metal legs:
- 1 leg for the **Red** positive (Anode)
- 1 leg for the **Green** positive (Anode)
- 1 leg for the **Blue** positive (Anode)
- 1 long leg for the shared **Negative** ground (Common Cathode)

In this lesson, we will wire the LEDs to three separate pins on Port B:
- **Red** is wired to Pin 9 (**PB1**)
- **Green** is wired to Pin 10 (**PB2**)
- **Blue** is wired to Pin 11 (**PB3**)

## The Code Walkthrough

Since we have three LEDs, we have to prepare three different pins to output electricity!

### 1. The Defines
```assembly
.equ DDRB,   0x04                      ; Data Direction Register for Port B
.equ PORTB,  0x05                      ; Data Register for Port B
.equ PB1,    1                         ; Pin 1 on Port B (Red)
.equ PB2,    2                         ; Pin 2 on Port B (Green)
.equ PB3,    3                         ; Pin 3 on Port B (Blue)
```
We define `DDRB` (the gatekeeper that sets pins to output) and `PORTB` (the register that actually turns the pins on and off). We also give names to our three color pins: `PB1`, `PB2`, and `PB3`.

### 2. Setting Up the Outputs
In our `main` program, after setting up the stack, we tell the gatekeeper to let electricity out of all three pins:
```assembly
  SBI    DDRB, PB1                     ; Set PB1 (Red) as output
  SBI    DDRB, PB2                     ; Set PB2 (Green) as output
  SBI    DDRB, PB3                     ; Set PB3 (Blue) as output
```
We use `SBI` (Set Bit in I/O Register) three times to flip the output switches for Red, Green, and Blue!

### 3. The Color Cycle Animation
Now we enter our infinite loop! We want to show one color at a time for exactly 1 second.
```assembly
.loop:                                 
  SBI    PORTB, PB1                    ; Turn Red ON
  CBI    PORTB, PB2                    ; Turn Green OFF
  CBI    PORTB, PB3                    ; Turn Blue OFF
  RCALL  delay_1000ms                  ; Wait 1000ms
```
To show Red, we use `SBI` to turn PB1 ON, and `CBI` (Clear Bit in I/O Register) to make sure Green and Blue are OFF. Then we wait 1000 milliseconds (1 full second)!

```assembly
  CBI    PORTB, PB1                    ; Turn Red OFF
  SBI    PORTB, PB2                    ; Turn Green ON
  CBI    PORTB, PB3                    ; Turn Blue OFF
  RCALL  delay_1000ms                  ; Wait 1000ms
```
Next, we turn Red OFF, turn Green ON, keep Blue OFF, and wait another second.

```assembly
  CBI    PORTB, PB1                    ; Turn Red OFF
  CBI    PORTB, PB2                    ; Turn Green OFF
  SBI    PORTB, PB3                    ; Turn Blue ON
  RCALL  delay_1000ms                  ; Wait 1000ms
```
Finally, we turn Red and Green OFF, and turn Blue ON! We wait one more second.

```assembly
  CBI    PORTB, PB1                    ; Turn Red OFF
  CBI    PORTB, PB2                    ; Turn Green OFF
  CBI    PORTB, PB3                    ; Turn Blue OFF
  RCALL  delay_1000ms                  ; Wait 1000ms
  RJMP   .loop                         ; Infinite loop
```
We finish the animation by turning all three LEDs OFF for one second. The `RJMP .loop` command forces the microcontroller back to the top of the animation, running our beautiful color cycle forever!

---

Congratulations! You now know how to orchestrate multiple hardware pins to create animations in pure Assembly!
