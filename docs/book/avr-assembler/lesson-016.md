# Lesson 016 - 74HC595 Shift Register

## What Are We Building Today?

Our microcontroller only has a limited number of digital pins. What happens if we want to control 8 LEDs, but we don't have 8 pins to spare?

Enter the **74HC595 Shift Register**! This brilliant microchip acts like a pin-multiplier. It takes data in *Serially* (one bit at a time over a single wire) and outputs it *Parallelly* (all 8 bits at the exact same time over 8 physical pins). 

Today we will write a software `shiftOut` driver from scratch to serially push an 8-bit number into the chip. We will program a bouncing "Knight Rider" LED chaser animation using logical bitwise shifting!

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/016/lesson.s)

---

## Hardware Check: The 74HC595 

To talk to the Shift Register, we use 3 pins:
- **DS (Data Pin) on PB0**: This is the wire where we send our 1s and 0s.
- **SH_CP (Clock Pin) on PB1**: Every time we flip this pin HIGH then LOW, the 595 grabs whatever is on the Data pin and pushes it into its internal memory buffer.
- **ST_CP (Latch Pin) on PB2**: When we are completely done sending all 8 bits, we pulse this pin to command the chip to display the new data on its 8 output pins!

## The Code Walkthrough

### 1. The `shift_out` Subroutine
How do we send 8 bits serially over one wire? We use a loop!
```assembly
shift_out:
  LDI    R17, 8                        ; Loop 8 times for 8 bits
.shift_loop:                           
  SBRC   R16, 7                        ; Check bit 7 (MSB). Skip next if 0.
  RJMP   .set_high                     ; If 1, jump to set HIGH
  CBI    PORTB, PB0                    ; If 0, clear Data pin (LOW)
  RJMP   .clock_pulse                  ; Jump to clocking
.set_high:                             
  SBI    PORTB, PB0                    ; Set Data pin HIGH
```
We look exclusively at the Most Significant Bit (Bit 7). We use `SBRC` (Skip if Bit in Register is Cleared). If it's a `0`, we set the Data wire `LOW`. If it's a `1`, we set it `HIGH`.

```assembly
.clock_pulse:                          
  SBI    PORTB, PB1                    ; Clock pin HIGH (Rising Edge shifts bit)
  NOP                                  ; Tiny wait
  CBI    PORTB, PB1                    ; Clock pin LOW
  
  LSL    R16                           ; Shift the next bit into MSB position
  DEC    R17                           ; Decrement loop counter
  BRNE   .shift_loop                   ; Loop if not zero
```
Then, we pulse the Clock wire (`PB1`) by pulling it `HIGH` then `LOW`. This mathematically shoves the bit into the chip. 
Finally, we use `LSL` (Logical Shift Left) to slide all the bits in `R16` to the left. The old Bit 6 is now the new Bit 7, ready for the next iteration of the loop!

### 2. Bouncing Animation (Knight Rider)
We want a single LED to bounce back and forth from left to right.
```assembly
  LDI    R18, 0x01                     ; Start with LED 0 ON
  
.shift_left:                           
  ... ; (shift_out, latch, delay)
  LSL    R18                           ; Logical Shift Left
  SBRC   R18, 7                        ; Skip next if bit 7 is clear 
  RJMP   .shift_right                  ; If we hit bit 7, bounce and go right!
  RJMP   .shift_left                   ; Otherwise, keep going left
```
We start with the binary number `00000001`. 
In our `.shift_left` loop, we send the number to the LEDs, delay so you can see it, and then execute an `LSL` (Logical Shift Left). 
`00000001` becomes `00000010`. The LED physically moves!
We use `SBRC` to check if the `1` has hit the very end (Bit 7). If it has, we dynamically branch into the `.shift_right` loop, which uses `LSR` (Logical Shift Right) to bounce the light back!

---

Congratulations! You have successfully implemented Serial Peripheral Communication (`SPI` bit-banging) and animated physical hardware arrays in pure assembly!
