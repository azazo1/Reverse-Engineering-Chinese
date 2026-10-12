# Lesson 010 - Ultrasonic Sensor

## What Are We Building Today?

Today we are going to build a high-speed digital stopwatch in pure assembly! 

We will use an **HC-SR04 Ultrasonic Sensor** to measure distance using echolocation—exactly like a bat or a submarine. The sensor emits a pulse of high-frequency sound, and listens for the echo to bounce off an object and return. Because we know the speed of sound, we can calculate how far away the object is simply by timing how long the echo took!

We will build a "Parking Sensor". If you place an object closer than 10 centimeters, the built-in LED on Pin 13 will turn ON!

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/010/lesson.s)

---

## Hardware Check: The HC-SR04 Protocol

The HC-SR04 is a very simple module with 4 pins:
- **VCC (5V)** & **GND** for power.
- **Trigger (PD2 / Pin 2)**: We send a tiny 10-microsecond electrical pulse to this pin to tell the module, "Ping now!"
- **Echo (PD3 / Pin 3)**: Right after pinging, this pin goes HIGH (5 Volts). When the sound bounces back and hits the microphone, this pin goes LOW (0 Volts). 

Our entire job is to use our microcontroller as an insanely fast stopwatch to count how long the Echo pin stays HIGH.

## The Code Walkthrough

### 1. The 10 Microsecond Trigger Pulse
To start a measurement, we set the Trigger pin HIGH, wait exactly 10 microseconds, and set it LOW. 

```assembly
  SBI    PORTD, PD2                    ; Set Trigger HIGH
  RCALL  delay_10us                    ; Wait 10 microseconds
  CBI    PORTD, PD2                    ; Set Trigger LOW
```
We wrote a tiny `delay_10us` subroutine that loops exactly 53 times, burning just enough clock cycles at 16 MHz to take exactly 10 millionths of a second.

### 2. Waiting for the Echo to Start
```assembly
.wait_echo_high:                       
  SBIS   PIND, PD3                     ; Skip next if Echo is HIGH
  RJMP   .wait_echo_high               ; Keep waiting for Echo to go HIGH
```
We use `SBIS` (Skip if Bit is Set) to check the Echo pin. We loop infinitely in this tight two-line block until the Echo pin finally flips to HIGH, indicating the sound pulse has been fired into the air.

### 3. The 16-Cycle Microsecond Loop
This is the most beautiful part of the code! At 16 MHz, 1 microsecond is exactly 16 clock cycles. We carefully crafted a counting loop that takes exactly 16 clock cycles to execute.

```assembly
.measure_high:                         
  SBIC   PIND, PD3                     ; Skip if Echo is LOW (1 cycle if false)
  RJMP   .echo_is_high                 ; Jump if HIGH (2 cycles)
  RJMP   .done                         ; Echo went LOW, stop measuring!
.echo_is_high:                         
  ADIW   R24, 1                        ; Increment microsecond counter (2 cycles)
  NOP                                  ; Pad loop to exactly 16 cycles (1us)
  ... (8 more NOPs)
  RJMP   .measure_high                 ; Loop back (2 cycles. Total loop = 16 cycles)
```
For every time this loop runs, exactly 1 microsecond has passed. We use `ADIW` (Add Immediate to Word) to increment a 16-bit counter in `R25:R24`. 
Because our loop takes exactly 1 microsecond, the final number sitting in `R25:R24` when the Echo pin goes LOW will literally be the length of the echo in microseconds! 

### 4. Math and the Speed of Sound
The speed of sound is roughly 340 meters per second, which means sound travels 1 centimeter in about 29.4 microseconds. 
Because the sound has to travel to the object **and** back, a distance of 10 cm takes `10 * 29.4 * 2 = ~588 microseconds`.

```assembly
.done:                                 
  LDI    R16, 0x4C                     ; Low byte of 588us (10cm)
  CP     R24, R16                      ; Compare lower byte
  LDI    R16, 0x02                     ; High byte of 588us
  CPC    R25, R16                      ; Compare higher byte
  BRSH   .too_far                      ; If >= 10cm, jump
  SBI    PORTB, PB5                    ; Turn LED ON (Object is close!)
```
We simply take our counter (in `R25:R24`) and compare it to `588` (which is `0x024C` in hex).
If the echo took less than 588 microseconds, the object is closer than 10cm, so we turn on the built-in LED!

---

Congratulations! You have successfully implemented a sub-millisecond precision timing loop and radar physics in bare metal assembly!
