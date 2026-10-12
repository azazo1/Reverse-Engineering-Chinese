# Lesson 009 - Servo Motor

## What Are We Building Today?

So far, everything we have built just blinks, beeps, or reads inputs. Today, we bring our microcontroller to life with **motion**!

A standard RC Servo Motor (like the SG90 included in your kit) is a tiny geared motor that can precisely rotate to any angle between 0 and 180 degrees. Instead of turning continuously like a car wheel, it acts like a steering wheel. 

Today we will use pure AVR assembly to mathematically command a servo to slowly sweep back and forth from 0° to 180° forever, acting like an automated windshield wiper!

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/009/lesson.s)

---

## Hardware Check: The Magic of PWM

How do we tell a motor what angle to point at using a single wire? 
The answer is a very specific type of **Pulse Width Modulation (PWM)**. 

Unlike fading an LED (where the frequency doesn't really matter as long as it's fast), a servo is extremely picky!
1. The pulse must repeat exactly **50 times a second** (50 Hz). This means the period (length) of the wave is **20 milliseconds**.
2. The width of the "ON" part of the pulse determines the angle:
   - **1.0 millisecond pulse** = 0 Degrees
   - **1.5 millisecond pulse** = 90 Degrees (Middle)
   - **2.0 millisecond pulse** = 180 Degrees

## The Code Walkthrough

We will once again use the powerful 16-bit **Timer1**, but we will use a brand new mode: **Mode 14 (Fast PWM, TOP=ICR1)**. 
Why Mode 14? Because it lets us completely customize the period (50 Hz) using the `ICR1` register, leaving `OCR1A` free to customize the pulse width (the angle)!

### 1. Setting the Period (The 50 Hz Frame)
```assembly
  LDI    R16, 0x1A                     ; WGM13=1, WGM12=1, CS11=1 (Prescaler 8)
  STS    TCCR1B, R16                   ; Write to TCCR1B
  
  LDI    R16, 0x9C                     ; TOP High byte (40000 = 0x9C40)
  STS    ICR1H, R16                    ; Write to ICR1H
  LDI    R16, 0x40                     ; TOP Low byte
  STS    ICR1L, R16                    ; Write to ICR1L
```
With the clock at 16 MHz and a Prescaler of 8, our timer ticks 2,000,000 times a second. 
We want a 20ms period (50 Hz). `0.020 seconds * 2,000,000 ticks/sec = 40,000 ticks`.
So, we load `40,000` (which is `0x9C40` in hex) into the `ICR1` register. The timer now resets every 20ms perfectly!

### 2. Sweeping Up
```assembly
  ADIW   R24, 10                       ; Add 10 to R25:R24 (Increase pulse width)
  STS    OCR1AH, R25                   ; Write to OCR1AH
  STS    OCR1AL, R24                   ; Write to OCR1AL
  RCALL  delay_5ms                     ; Wait 5ms for smooth movement
```
Our angle pulse width is stored in the 16-bit register pair `R25:R24`. We use `ADIW` (Add Immediate to Word) to instantly add 10 to our 16-bit value, increasing the pulse width slightly!
Then we update `OCR1A` (remember: High byte first, then Low byte!). 

```assembly
  LDI    R16, 0xC0                     ; Low byte of 4800 (0x12C0)
  CP     R24, R16                      ; Compare low bytes
  LDI    R16, 0x12                     ; High byte of 4800
  CPC    R25, R16                      ; Compare high bytes with carry
  BRLO   .sweep_up                     ; Branch if less than 4800 (keep going up)
```
180 degrees corresponds to a pulse width of about 2.4 milliseconds. At our timer's speed, that is `4800` ticks (`0x12C0` in hex). We use `CP` (Compare) and `CPC` (Compare with Carry) to compare our 16-bit number to 4800. If we are still lower (`BRLO`), we loop back and keep sweeping up!

### 3. Sweeping Down
```assembly
.sweep_down:                           
  SBIW   R24, 10                       ; Subtract 10 from R25:R24
```
Once we hit 180 degrees, we fall into the `.sweep_down` loop where we use `SBIW` (Subtract Immediate from Word) to slowly decrease the angle back down to 1000 ticks (about 0 degrees).

---

Congratulations! You have successfully implemented precise mechanical motion control using pure mathematical timer configurations in assembly!
