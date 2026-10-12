# Lesson 018 - Photocell (Light Sensor)

## What Are We Building Today?

Today we will combine three powerful concepts we have learned: The Analog-to-Digital Converter (ADC), the 74HC595 Shift Register, and the Photocell (Light Dependent Resistor). 

We will create a live, glowing **Light-Level Bar Graph**! When the room gets brighter, more LEDs on our 8-LED array will magically light up in sequence! 

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/018/lesson.s)

---

## Hardware Check: The Voltage Divider
A Photocell is a resistor whose resistance decreases when light shines on it. We wire it into a Voltage Divider circuit and connect the middle point to the **A0 (Analog 0)** pin of the ATmega328P.
When the room is dark, the ADC will read a very low number. When you shine a flashlight on it, the ADC will read a number closer to `1023`.

## The Code Walkthrough

### 1. Division by Subtraction
We read a 10-bit number from the ADC (0 to 1023), but we only have 8 LEDs. We need to convert `0 - 1023` into an "LED Count" from `0 - 8`. 

We divide the ADC value by `114` using our trusty Repeated Subtraction algorithm!

```assembly
.div_loop:
  LDI    R16, 114                      
  CP     R24, R16                      
  LDI    R16, 0                        
  CPC    R25, R16                      
  BRLO   .div_done                     ; If ADC < 114, division is done
  
  LDI    R16, 114                      
  SUB    R24, R16                      ; ADC = ADC - 114
  ...
  INC    R20                           ; Count++
  RJMP   .div_loop
```
When this loop finishes, `R20` holds our perfect "LED Count", a number between 0 and 8!

### 2. Building a Bar Graph (SEC and ROL)
If our LED Count is `3`, we want the Shift Register to light up 3 LEDs (`00000111`). If it's `5`, we want `00011111`. How do we programmatically build this binary mask?

We use two of the most clever bit-manipulation instructions in the entire AVR instruction set!

```assembly
.build_mask:
  LDI    R16, 0                        ; Start with a blank mask (00000000)
...
.mask_loop:
  SEC                                  ; Set Carry Flag (C=1)
  ROL    R16                           ; Rotate Left through Carry
  DEC    R20                           ; Decrement our LED count
  BRNE   .mask_loop                    ; Repeat for each LED count
```

- **SEC (Set Carry)**: This immediately turns the Carry Flag in the CPU Status Register to a `1`.
- **ROL (Rotate Left through Carry)**: This slides all the bits in `R16` to the left. The `1` that was sitting in the Carry Flag falls directly into Bit 0!

If we run this loop 3 times, `R16` transforms:
1. `00000000` -> `00000001`
2. `00000001` -> `00000011`
3. `00000011` -> `00000111`

It acts like a perfect snow-plow, building a beautiful bar graph mask that we send directly to our Shift Register!

---

Congratulations! You have successfully mathematically divided sensor data and used Rotate instructions to create dynamic visual representations in pure assembly!
