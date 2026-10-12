# Lesson 015 - Thermometer (Thermistor + LCD)

## What Are We Building Today?

In our last lesson, we learned how to write the word "HELLO" to an LCD screen by sending hardcoded ASCII characters. But what if we want to display a *variable*? Like a changing sensor value?

Today, we are combining our ADC (Analog to Digital Converter) knowledge with our LCD knowledge. We will use a **Thermistor**—a special resistor whose resistance changes based on temperature. We will measure the voltage across it using the ADC, mathematically convert the 16-bit binary integer into four ASCII text digits, and print the live, updating value directly to the LCD screen! 

Pinch the thermistor with your fingers and watch the numbers on the screen change!

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/015/lesson.s)

---

## Hardware Check: The Thermistor

A Thermistor (NTC) is wired into a "voltage divider" circuit alongside a standard 10k resistor. 
As the temperature changes, the resistance of the thermistor changes, which causes the voltage in the middle of the divider to shift up or down. 
We connect this middle wire to **A0 (Analog Channel 0)**. 

When we read the ADC, we get a 10-bit number between `0` and `1023`. We want to display this exact number on the screen.

## The Code Walkthrough

### The "Repeated Subtraction" Algorithm
How do we turn the binary number `00000011 11111111` (which is `1023` in decimal) into the four distinct ASCII text characters `'1'`, `'0'`, `'2'`, and `'3'`?

Microcontrollers don't have a hardware `divide` instruction! So we have to do it the old-fashioned way: **Repeated Subtraction**.

```assembly
bin_to_ascii:
  LDI    R20, '0'                      ; Thousands digit starts at ASCII '0'
.sub_1000:                             
  LDI    R16, lo8(1000)                
  CP     R24, R16                      
  LDI    R16, hi8(1000)                
  CPC    R25, R16                      
  BRLO   .done_1000                    ; If we drop below 1000, we are done!
  
  LDI    R16, lo8(1000)                
  SUB    R24, R16                      ; Subtract 1000
  LDI    R16, hi8(1000)                
  SBC    R25, R16                      
  
  INC    R20                           ; Increment the Thousands ASCII character
  RJMP   .sub_1000                     ; Try subtracting 1000 again
.done_1000:
```

1. We start the thousands digit at the ASCII character `'0'` (`0x30`).
2. We compare our 16-bit number in `R25:R24` to `1000`. 
3. If it is greater than or equal to 1000, we **subtract 1000** from our number, and we **increment** our text character from `'0'` to `'1'`.
4. We loop and try again! 
5. When our number finally drops below 1000, we jump down and repeat the exact same process for `100` to find the Hundreds digit!
6. Then we do it for `10` to find the Tens digit.
7. Whatever is left over at the very end is our Ones digit!

### Printing the Results
Once `bin_to_ascii` runs, our four pristine ASCII text characters are sitting in `R20`, `R21`, `R22`, and `R23`. We can just blast them straight to the LCD!

```assembly
  ; Print 'V' 'A' 'L' ':' ' '
  LDI    R16, 'V'
  RCALL  lcd_write_data
  ...
  
  ; Print our 4 newly calculated digits
  MOV    R16, R20
  RCALL  lcd_write_data
  MOV    R16, R21
  RCALL  lcd_write_data
  MOV    R16, R22
  RCALL  lcd_write_data
  MOV    R16, R23
  RCALL  lcd_write_data
```

---

Congratulations! You have successfully implemented Binary-to-ASCII string conversion algorithms and built a live, dynamic sensor dashboard in pure assembly!
