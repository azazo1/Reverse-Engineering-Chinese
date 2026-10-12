# Lesson 019 - 7-Segment Display

## What Are We Building Today?

A 7-Segment Display is simply 8 LEDs packed inside a plastic shell in the shape of an "8" (plus a decimal point). By selectively turning on specific LEDs, we can draw numbers! 

Since it has 8 LEDs, it requires 8 wires to control. This is the exact perfect use-case for our `74HC595 Shift Register`! We will write a program that counts from 0 to 9 over and over, drawing each number on the display.

Today, we will learn how to permanently bake an Array of data into the Microcontroller's Flash Memory using the `.text` section, and how to read from it using the legendary **Z-Pointer**!

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/019/lesson.s)

---

## Hardware Check: The 7-Segment Display
The display has 10 pins. 2 of them are tied to Ground (Common Cathode). The remaining 8 pins control the individual segments, named `A` through `G`, plus `DP` (Decimal Point).
We connect these 8 segment pins to the 8 output pins of our `74HC595` Shift Register.

To draw the number "1", we need to turn on segments `B` and `C`.
If we wire our Shift Register such that `Q0` connects to `A`, `Q1` to `B`, `Q2` to `C`, etc... then we need to send the binary number `00000110` (which is Hex `0x06`) to the Shift Register to draw a "1"!

We could hardcode this in our logic with a giant `IF` statement... or we could use an Array!

## The Code Walkthrough

### 1. Flash Memory Arrays (`.byte`)
We can declare an array of these binary patterns directly in the `.text` section of our code. The assembler will burn these bytes permanently into the silicon of the ATmega328P's program memory (Flash).

```assembly
segment_patterns:
  .byte 0b00111111                     ; 0
  .byte 0b00000110                     ; 1
  .byte 0b01011011                     ; 2
  ...
```
The label `segment_patterns` represents the physical memory address where this list of bytes begins.

### 2. The Z-Pointer and `LPM`
AVR microcontrollers are based on the Harvard Architecture, which means they have entirely separate memory spaces for RAM (where variables live) and Flash (where your code lives). Standard `LD` (Load) instructions can only read from RAM. 
To read from Flash, we *must* use a special instruction: `LPM` (Load Program Memory).

`LPM` is incredibly picky. It only ever looks at one specific place to find the address: The **Z-Pointer**. 
The Z-Pointer is a 16-bit virtual register made by combining `R31` (High Byte) and `R30` (Low Byte).

```assembly
get_segment_pattern:
  LDI    ZH, hi8(segment_patterns)     ; Load High Byte of Array Address into Z
  LDI    ZL, lo8(segment_patterns)     ; Load Low Byte of Array Address into Z
```
First, we load the base address of our array into the Z-Pointer using the `hi8` and `lo8` macros.

```assembly
  ADD    ZL, R16                       ; Add the digit offset to the Low Byte
  LDI    R17, 0                        
  ADC    ZH, R17                       ; Add Carry to the High Byte
```
Next, we add our digit (0-9) to the address! We use `ADD` for the Low Byte, and `ADC` (Add with Carry) for the High Byte in case our addition caused the Low Byte to overflow past 255.

```assembly
  LPM    R16, Z                        ; Load Program Memory!
  RET
```
Finally, we execute `LPM R16, Z`. The CPU reaches deep into the Flash memory at the exact address stored in the Z-Pointer, grabs the byte, and pulls it into `R16`!

---

Congratulations! You have successfully mastered Flash memory architecture, 16-bit pointer arithmetic, and the Z-Pointer in bare metal assembly!
