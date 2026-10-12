# Lesson 002 - Blink

## What Are We Building Today?

Welcome to Lesson 2! Have you ever wanted to control physical things with code? Today, we are going to do exactly that by writing a program that turns a real, physical LED on and off! 

By the end of this lesson, the tiny built-in LED on your ATmega328P board (which is connected to Pin 13) will blink on and off every half second forever.

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/002/lesson.s)

---

## Hardware Check: Where is the LED?

If you look closely at your Arduino UNO or compatible board, you'll see a tiny LED labeled "L" right next to the number 13 on the side headers. 
This LED is physically wired to **Pin 5 on Port B** of the ATmega328P microcontroller (we call it `PB5` for short). 
To turn it on, we just have to tell the microcontroller to send 5 Volts of electricity to that specific pin.

## Setting Up the Registers (The Switches)

In Lesson 1, we learned that the microcontroller uses **Registers** (tiny, fast memory boxes) to do things. 
To control pins on the microcontroller, we use two very special hardware registers:

1. **DDRB (Data Direction Register B)**: This register acts like a gatekeeper for the pins on Port B. By default, pins are "Inputs" (like a microphone listening for a signal). If we want to push electricity *out* to turn on an LED, we have to tell the gatekeeper to switch that specific pin to be an "Output".
2. **PORTB (Data Register B)**: Once a pin is an output, we use this register to control the electricity. If we write a `1` to the pin in this register, it turns ON (5 Volts). If we write a `0`, it turns OFF (0 Volts).

---

## Step-by-Step Code Walkthrough

Let's break down the assembly code that makes this happen!

### 1. The Defines
At the very top of our code, we use `.equ` to give easy-to-read names to raw memory addresses.
```assembly
.equ DDRB,   0x04                      ; Data Direction Register for Port B
.equ PORTB,  0x05                      ; Data Register for Port B
.equ PB5,    5                         ; Pin 5 on Port B
```
Instead of memorizing that the Data Register for Port B is at memory address `0x05`, we just name it `PORTB`. And since the LED is connected to pin number 5 on that port, we name it `PB5`.

### 2. The Main Program
After setting up our stack (just like we did in Lesson 1), we hit this line of code:
```assembly
main:                                  
...
  SBI    DDRB, PB5                     ; Set PB5 as an output pin
```
`SBI` stands for **Set Bit in I/O Register**. It goes to the `DDRB` register (the gatekeeper), looks at bit number 5 (`PB5`), and sets it to a `1`. 
Boom! The pin is now an Output. It is ready to send electricity out to the LED.

### 3. The Infinite Blink Loop
Now we want the LED to blink forever, so we create a loop:
```assembly
.loop:                                 
  SBI    PORTB, PB5                    ; Set PB5 high (turn LED on)
```
Here is that `SBI` instruction again! This time we are setting bit 5 in the `PORTB` register. This tells the microcontroller to push 5 Volts of electricity out of Pin 13. The LED turns ON!

```assembly
  RCALL  delay_500ms                   ; Wait 500ms
```
We use `RCALL` to jump to our delay subroutine. If we didn't wait, the LED would turn on and off millions of times a second, and it would just look like it was dimly lit! We wait 500 milliseconds (half a second) so our human eyes can see it.

```assembly
  CBI    PORTB, PB5                    ; Set PB5 low (turn LED off)
```
`CBI` stands for **Clear Bit in I/O Register**. It does the exact opposite of `SBI`. It goes to `PORTB`, looks at bit 5, and clears it to `0`. The electricity stops flowing, and the LED turns OFF.

```assembly
  RCALL  delay_500ms                   ; Wait 500ms
  RJMP   .loop                         ; Infinite loop
```
We wait another half second while the LED is off. Finally, `RJMP .loop` (Relative Jump) forces the processor to jump all the way back up to `.loop:` so it can do the whole thing again. Forever!

---

## Time Travel (Delays)
Just like in Lesson 1, we use the `delay_500ms` subroutine to pause time.
```assembly
delay_500ms:                           
  LDI    R18, 0x18                     ; High byte of delay counter
  LDI    R17, 0x69                     ; Mid byte of delay counter
  LDI    R16, 0xFE                     ; Low byte of delay counter
```
Because the ATmega328P processes 16 million instructions every single second, waiting half a second requires it to count backwards from a massive number. We link three 8-bit registers (R16, R17, and R18) together to hold that huge number, and then use `SUBI` and `SBCI` to subtract 1 over and over until they hit zero. 

Congratulations! You've just controlled physical hardware using pure Assembly!
