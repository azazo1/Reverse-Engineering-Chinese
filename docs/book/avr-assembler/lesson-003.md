# Lesson 003 - LED Fading (PWM)

## What Are We Building Today?

Welcome to Lesson 3! In our last lesson, we learned how to turn an LED completely on and completely off. But what if we want to smoothly dim the LED like a movie theater light?

Today, we are going to learn a magic trick called **PWM** (Pulse Width Modulation) to fade an LED smoothly up and down! 

By the end of this lesson, an LED connected to **Pin 9** on your Arduino will continuously breathe in and out.

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/003/lesson.s)

---

## The Magic Trick: PWM (Pulse Width Modulation)

Microcontrollers like the ATmega328P are strictly digital. That means pins can only be completely ON (5 Volts) or completely OFF (0 Volts). There is no "in-between" 2.5 Volts. 

So how do we make the LED look halfway bright? We play a trick on your eyes!

If we turn the LED ON and OFF incredibly fast—hundreds of times a second—your eyes can't see the flickering. Instead, your brain averages the light out.
- If the LED is ON for 90% of the time and OFF for 10%, it looks **very bright**.
- If the LED is ON for 10% of the time and OFF for 90%, it looks **very dim**.

This trick is called **PWM**! We change the "width" of the ON pulse to control the brightness.

## The Hardware Timer

To do this, we don't turn the pin on and off manually in our code. Instead, we use a built-in piece of hardware called **Timer 1**. It works like a background stopwatch that runs completely on its own!

We tell Timer 1 two things:
1. "Count really fast from 0 to 255, and then loop back to 0."
2. "Whenever you are lower than my secret number, turn Pin 9 ON. If you pass my secret number, turn Pin 9 OFF."

That secret number is our brightness! 

---

## Step-by-Step Code Walkthrough

Let's look at the assembly code to see how we set this up.

### 1. The Defines
```assembly
.equ DDRB,   0x04                      ; Data Direction Register for Port B
.equ PB1,    1                         ; Pin 1 on Port B (Arduino Pin 9)
```
Just like Lesson 2, we use `DDRB`. But this time we use `PB1`, which connects to physical Pin 9 on the Arduino board. Pin 9 is special because it is wired directly to Timer 1!

```assembly
.equ TCCR1A, 0x80                      ; Timer/Counter1 Control Register A
.equ TCCR1B, 0x81                      ; Timer/Counter1 Control Register B
.equ OCR1AL, 0x88                      ; Output Compare Register 1 A Low
```
These are the new Timer 1 registers. 
- `TCCR1A` and `TCCR1B` are the control panels. We use them to configure the timer.
- `OCR1AL` is the "Output Compare Register". **This is our secret brightness number!**

### 2. Setting up the Timer
In our `main` program, after setting the stack and `DDRB`, we configure the timer:
```assembly
  LDI    R16, 0x81                     ; COM1A1=1, WGM10=1 (8-bit Fast PWM)
  STS    TCCR1A, R16                   ; Store into TCCR1A
  LDI    R16, 0x0B                     ; WGM12=1, CS11=1, CS10=1 (Prescaler 64)
  STS    TCCR1B, R16                   ; Store into TCCR1B
```
This looks complicated, but it's just flipping switches on the timer's control panel.
- We set it to **8-bit Fast PWM** mode, which means it counts from 0 to 255.
- We set a **Prescaler of 64**, which slows the timer down just enough so it pulses at about 976 times per second (perfect for our eyes!).
- We tell it to connect directly to Pin 9 (`COM1A1=1`).

### 3. Fading Up!
```assembly
  LDI    R16, 0                        ; Start brightness at 0
.fade_up:                              
  STS    OCR1AL, R16                   ; Update PWM duty cycle
  RCALL  delay_10ms                    ; Wait 10ms for visible change
  INC    R16                           ; Increase brightness by 1
  BRNE   .fade_up                      ; If not rolled over to 0, loop
```
Here is where the animation happens! We start our brightness (`R16`) at 0.
1. `STS OCR1AL, R16` copies our brightness into the Timer.
2. `RCALL delay_10ms` waits a tiny fraction of a second so our eyes can see the change.
3. `INC R16` adds 1 to our brightness.
4. `BRNE .fade_up` loops back and does it again until `R16` hits 255 and rolls over!

### 4. Fading Down!
```assembly
  LDI    R16, 255                      ; Start brightness at 255
.fade_down:                            
  STS    OCR1AL, R16                   ; Update PWM duty cycle
  RCALL  delay_10ms                    ; Wait 10ms for visible change
  DEC    R16                           ; Decrease brightness by 1
  BRNE   .fade_down                    ; If not reached 0, loop
  RJMP   .fade_up                      ; Infinite loop back to fade up
```
This is the exact same thing in reverse! We start at 255, and use `DEC R16` to subtract 1 until the brightness reaches 0. Then we `RJMP .fade_up` to start the entire breathing animation over again!

---

Congratulations! You just controlled a complex hardware timer using Assembly language!
