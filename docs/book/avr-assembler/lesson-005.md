# Lesson 005 - Digital Inputs (Buttons)

## What Are We Building Today?

Welcome to Lesson 5! In previous lessons, our code ran automatically and didn't care about what was happening outside. Today, we are going to make our microcontroller **interactive**!

We will wire up two push buttons (Button A and Button B) and use them to control the built-in LED on Arduino Pin 13.
- Pressing **Button A** turns the LED **ON**.
- Pressing **Button B** turns the LED **OFF**.

By the end of this lesson, you'll know how to read electrical inputs and make decisions in your code using Assembly!

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/005/lesson.s)

---

## Hardware Check: Internal Pull-Up Resistors

To read a button, we connect one side of the button to an input pin, and the other side to **Ground (GND)**. When we press the button, the pin connects directly to GND (0 Volts).

But wait! What happens when the button is *not* pressed? The pin isn't connected to anything at all! It's "floating" in the air like an antenna, picking up random electrical noise. It might read 0 Volts, or 5 Volts, randomly jumping back and forth. 

To fix this, we need a **Pull-Up Resistor**. This is a resistor connected to 5 Volts that "pulls" the pin up to a solid HIGH state when nothing else is connected. 

The brilliant engineers who designed the ATmega328P included a tiny, secret pull-up resistor *inside* the chip for every single pin! We just have to tell the microcontroller to turn it on.

## The Code Walkthrough

Let's look at how we set this up in Assembly.

### 1. The Defines
```assembly
.equ DDRB,   0x04                      ; Data Direction Register for Port B
.equ PORTB,  0x05                      ; Data Register for Port B
.equ PB5,    5                         ; Pin 5 on Port B (Arduino Pin 13 LED)
.equ PIND,   0x09                      ; Input Pins Register for Port D
.equ DDRD,   0x0A                      ; Data Direction Register for Port D
.equ PORTD,  0x0B                      ; Data Register for Port D
.equ PD2,    2                         ; Pin 2 on Port D (Button A)
.equ PD3,    3                         ; Pin 3 on Port D (Button B)
```
We define our old friend `PB5` (Pin 13) for the LED. 
For the buttons, we use a new Port: **Port D**.
- `DDRD` is the gatekeeper for Port D.
- `PORTD` is used to turn on those secret internal pull-up resistors!
- `PIND` (Pin Input Register) is the sensor we use to **read** the electrical voltage on the pins.

### 2. Setting Up the Inputs and Pull-Ups
```assembly
  SBI    DDRB, PB5                     ; Set PB5 (LED) as an output

  CBI    DDRD, PD2                     ; Set PD2 (Button A) as an input
  SBI    PORTD, PD2                    ; Enable internal pull-up resistor on PD2

  CBI    DDRD, PD3                     ; Set PD3 (Button B) as an input
  SBI    PORTD, PD3                    ; Enable internal pull-up resistor on PD3
```
To configure a pin as an input, we use `CBI` to tell the gatekeeper (`DDRD`) to block outgoing electricity.
Then we use a cool trick: if a pin is an input, using `SBI` on `PORTD` turns on the internal pull-up resistor! Now our buttons will safely read HIGH (not pressed) until we physically push them to GND (LOW).

### 3. Reading the Buttons and Making Decisions
Here is our infinite loop:
```assembly
.loop:                                 
  SBIC   PIND, PD2                     ; Skip next if Button A is pressed (LOW)
  RJMP   .check_b                      ; Jump to check Button B if not pressed
  SBI    PORTB, PB5                    ; Turn LED ON
  RJMP   .loop                         ; Restart loop
```
We use a very powerful new command called `SBIC` (Skip if Bit in I/O Register is Cleared).
It looks at `PIND`, pin `PD2`. 
- If the button is NOT pressed, it is HIGH (Set). `SBIC` does nothing, and the code runs the next line: `RJMP .check_b` which skips turning the LED on.
- If the button IS pressed, it is LOW (Cleared). `SBIC` magically **skips** the `RJMP` instruction! The code falls right through to `SBI PORTB, PB5`, which turns the LED ON!

```assembly
.check_b:                              
  SBIC   PIND, PD3                     ; Skip next if Button B is pressed (LOW)
  RJMP   .loop                         ; Jump to loop if not pressed
  CBI    PORTB, PB5                    ; Turn LED OFF
  RJMP   .loop                         ; Restart loop
```
We do the exact same check for Button B on pin `PD3`. If it's pressed (LOW), `SBIC` skips the jump, and we run `CBI PORTB, PB5` to turn the LED OFF!

---

Congratulations! You now know how to read digital inputs, use internal pull-up resistors, and write conditional logic (if/then statements) directly in Assembly!
