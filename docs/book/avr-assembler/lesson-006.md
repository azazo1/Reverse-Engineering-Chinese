# Lesson 006 - Active Buzzer

## What Are We Building Today?

Welcome to Lesson 6! We've made lights blink, fade, and change colors. We've even made them respond to buttons. Now, it's time to make some **NOISE**!

Today, we are going to use an **Active Buzzer** to beep loudly in a repetitive pattern: BEEP... silence... BEEP... silence!

By the end of this lesson, you'll see how closely related light and sound are when it comes to controlling them with digital logic.

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/006/lesson.s)

---

## Hardware Check: The Active Buzzer

An **Active Buzzer** is a small speaker component that has a built-in oscillator. 

What does that mean? It means it does the hard work for you! 
If you send 5 Volts (HIGH) to an active buzzer, the built-in oscillator automatically generates a loud tone (usually around 2.5 kHz or 2,500 beeps per second). When you send 0 Volts (LOW), it stays completely silent.

This makes it incredibly easy to use. In fact, controlling an active buzzer is exactly the same as turning an LED on and off!

*Note: There are also **Passive Buzzers**, which require you to turn the pin on and off thousands of times a second manually to make a sound. We'll play with those in a future lesson!*

## The Code Walkthrough

We are going to connect our Active Buzzer's positive leg to **Pin 5** on the Arduino, which is connected to **PD5** on the microcontroller. The negative leg goes to GND.

### 1. The Defines
```assembly
.equ DDRD,   0x0A                      ; Data Direction Register for Port D
.equ PORTD,  0x0B                      ; Data Register for Port D
.equ PD5,    5                         ; Pin 5 on Port D (Arduino Pin 5)
```
Just like blinking an LED, we need to talk to the `DDRD` gatekeeper and the `PORTD` switch. Our target pin is `PD5`.

### 2. Setting Up the Output
```assembly
  SBI    DDRD, PD5                     ; Set PD5 (Buzzer) as an output
```
Wait a second, did I say LED? This is exactly the same command we used for the LED in Lesson 2! `SBI` (Set Bit in I/O Register) tells `DDRD` to allow electricity to flow out of pin `PD5`. 

### 3. The Beeping Loop
```assembly
.loop:                                 
  SBI    PORTD, PD5                    ; Turn buzzer ON (HIGH)
  RCALL  delay_500ms                   ; Wait 500ms
  CBI    PORTD, PD5                    ; Turn buzzer OFF (LOW)
  RCALL  delay_500ms                   ; Wait 500ms
  RJMP   .loop                         ; Restart loop
```
This should look very familiar! 
1. `SBI PORTD, PD5` sends 5 Volts out. The buzzer's internal circuitry turns this into a loud beep!
2. We wait 500 milliseconds (half a second) while it beeps.
3. `CBI PORTD, PD5` turns the pin OFF (0 Volts). The buzzer goes totally silent.
4. We wait another 500 milliseconds in silence.
5. `RJMP .loop` repeats the process forever!

### Why does this look just like Lesson 2?
Because to a digital pin, **an LED and an Active Buzzer are the exact same thing**. The microcontroller just outputs 5V. It doesn't care if that 5V is turned into light (LED), sound (Buzzer), or motion (Motor). It's just sending electricity!

---

Congratulations! You've just built your first digital sound machine using pure Assembly!
