# Lesson 008 - Tilt Switch

## What Are We Building Today?

Have you ever wondered how your smartphone knows when you turn it sideways to watch a video, or how a digital level works? 

Today, we are going to build a very simple orientation sensor using a **Tilt Ball Switch**. When the sensor is held upright, a little metal ball inside rolls away from the electrical contacts, breaking the circuit. When you tilt it upside down, the metal ball rolls onto the contacts, completing the circuit!

We will use this sensor to turn our built-in LED (Pin 13) ON when the sensor is tilted, and OFF when it is upright.

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/008/lesson.s)

---

## Hardware Check: It's Just A Button!

From the perspective of our microcontroller, a Tilt Switch is exactly the same thing as the Push Buttons we used in Lesson 005. 

Instead of you pushing a button with your finger to connect a pin to Ground, gravity pushes a metal ball to connect the pin to Ground. 

Because it acts like a switch, we will wire it up the exact same way:
- One leg connects to **Pin 2 (PD2)** on the Arduino.
- The other leg connects to **Ground (GND)**.
- We will turn on the **internal pull-up resistor** on PD2 so that when the ball is *not* touching the contacts (upright), the pin reads HIGH (5 Volts).

## The Code Walkthrough

Since this is basically a button, the code is going to be a breeze!

### 1. The Defines
```assembly
.equ DDRB,   0x04                      ; Data Direction Register for Port B
.equ PORTB,  0x05                      ; Data Register for Port B
.equ PB5,    5                         ; Pin 5 on Port B (Arduino Pin 13 LED)
.equ PIND,   0x09                      ; Input Pins Register for Port D
.equ DDRD,   0x0A                      ; Data Direction Register for Port D
.equ PORTD,  0x0B                      ; Data Register for Port D
.equ PD2,    2                         ; Pin 2 on Port D (Tilt Sensor)
```
We define `PB5` for our LED output, and `PD2` for our Tilt Sensor input.

### 2. Setting Up the Inputs and Pull-Ups
```assembly
  SBI    DDRB, PB5                     ; Set PB5 (LED) as an output
  CBI    DDRD, PD2                     ; Set PD2 (Tilt Switch) as an input
  SBI    PORTD, PD2                    ; Enable internal pull-up resistor on PD2
```
Just like Lesson 5, we make `PB5` an output, make `PD2` an input, and turn on the internal pull-up for `PD2`. Now, when upright, `PD2` is HIGH. When tilted, the ball completes the circuit to ground, making `PD2` LOW.

### 3. Reading the Sensor
```assembly
.loop:                                 
  SBIC   PIND, PD2                     ; Skip next if tilted (LOW)
  RJMP   .turn_off                     ; Jump to turn OFF if HIGH (upright)
  SBI    PORTB, PB5                    ; Turn LED ON
  RJMP   .loop                         ; Restart loop
```
We use `SBIC` (Skip if Bit is Cleared) to check the sensor.
If the sensor is tilted, the pin connects to GND and becomes LOW (Cleared). `SBIC` magically skips the `RJMP .turn_off` instruction and falls through to `SBI PORTB, PB5`, turning the LED ON!

If the sensor is upright, the pull-up resistor keeps the pin HIGH (Set). `SBIC` does nothing, and the code runs `RJMP .turn_off`, completely skipping the code that turns the LED on.

```assembly
.turn_off:                             
  CBI    PORTB, PB5                    ; Turn LED OFF
  RJMP   .loop                         ; Restart loop
```
If we jumped here, we turn the LED OFF. Then we loop forever!

---

Congratulations! You now know how to detect orientation and gravity using a simple mechanical switch!
