# Lesson 021 - DC Motor with L293D

## What Are We Building Today?

So far, everything we have controlled has been a low-power digital device (LEDs, LCDs, ICs). What if we want to move physical objects in the real world?
We need a **DC Motor**! 

However, DC motors require significantly more current than an ATmega328P pin can provide (a single pin provides max 40mA, but a motor can draw hundreds of milliamps!). If you connect a motor directly to your microcontroller, you will instantly destroy the chip!
To solve this, we will use an **L293D H-Bridge Motor Driver IC**.

Today, we will learn how to write 16-bit Timer configurations in assembly to generate Pulse Width Modulation (PWM) signals, which will allow us to precisely control the *speed* and *direction* of the motor!

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/021/lesson.s)

---

## Hardware Check: The L293D H-Bridge
The L293D acts as a powerful middle-man. We send it low-power logical signals, and it connects the motor to a high-power energy source.

- **IN1 (Pin 2)** and **IN2 (Pin 3)**: These control the *Direction* of the motor.
  - If `IN1` is HIGH and `IN2` is LOW, the motor spins Forward.
  - If `IN1` is LOW and `IN2` is HIGH, the motor spins in Reverse.
  - If both are LOW, the motor stops (Brakes).
- **EN1 (Pin 1)**: This is the Enable pin. If we send it a PWM signal, we can control the exact *Speed* of the motor!

We will connect `IN1` to `PD2`, `IN2` to `PD3`, and `EN1` to `PB1`.
Notice that `PB1` is specifically chosen because it is hardwired inside the silicon to **Timer 1 Channel A (OC1A)**!

## The Code Walkthrough

### 1. Configuring Timer 1 (16-Bit Timer)
Unlike Timer 0 (which is 8-bit), Timer 1 is a massive 16-bit timer. It is capable of much higher precision. To configure it for Fast PWM 8-bit mode, we must configure `TCCR1A` (Control Register A) and `TCCR1B` (Control Register B).

```assembly
  ; Configure Timer 1 for Fast PWM 8-bit mode, non-inverting on OC1A
  LDI    R16, (1<<COM1A1) | (1<<WGM10)
  STS    TCCR1A, R16
  
  LDI    R16, (1<<WGM12) | (1<<CS11)
  STS    TCCR1B, R16
```
- `COM1A1`: Tells the hardware to automatically toggle the `PB1` pin based on the timer comparison.
- `WGM10` and `WGM12`: Selects "Mode 5: Fast PWM, 8-bit".
- `CS11`: Sets the clock prescaler to 8.

### 2. The 16-Bit Register Write Sequence
To set the speed (Duty Cycle) of the PWM, we must write a value to the 16-bit Output Compare Register `OCR1A`.
Because the AVR is an 8-bit processor, it cannot write 16 bits at once! `OCR1A` is split into two 8-bit registers: `OCR1AH` (High Byte) and `OCR1AL` (Low Byte).

**CRITICAL RULE:** When writing to 16-bit registers in an AVR, you MUST write the High Byte first! The hardware stores the High Byte in a temporary hidden buffer, and only applies the full 16-bit value when you write the Low Byte.

```assembly
  LDI    R17, 0                        ; High Byte is 0 (we only need 8 bits for speed)
  LDI    R16, 200                      ; Low Byte is 200 (High Speed!)
  
  STS    OCR1AH, R17                   ; MUST write High Byte first!
  STS    OCR1AL, R16                   ; Writes Low Byte, triggering the 16-bit update
```

### 3. The Control Loop
To spin the motor Forward at high speed:
```assembly
  SBI    PORTD, PD2                    ; IN1 = HIGH
  CBI    PORTD, PD3                    ; IN2 = LOW
  
  LDI    R16, 200                      ; Speed = 200/255
  LDI    R17, 0
  STS    OCR1AH, R17
  STS    OCR1AL, R16
```
We can just as easily reverse it and slow it down by swapping the `IN1/IN2` pins and lowering the `OCR1AL` value!

---

Congratulations! You have successfully mastered 16-bit Timer configurations, buffered 16-bit register writes, and hardware H-Bridge motor control in bare metal assembly!
