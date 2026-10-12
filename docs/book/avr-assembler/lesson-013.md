# Lesson 013 - Infrared (IR) Receiver

## What Are We Building Today?

Have you ever wondered how a TV remote actually works? It blasts invisible infrared light in rapid pulses. The TV has a receiver that catches this invisible light and converts it into electrical `0`s and `1`s.

Today, we are going to build an **Infrared Visualizer**! 
We are going to write a lightning-fast assembly loop that watches the IR Receiver module. Whenever it detects a pulse of infrared light from your TV remote, it will instantly flash the built-in LED (Pin 13) on your microcontroller! By pointing a remote at your circuit and pressing a button, you will be able to literally *see* the invisible data pulsing before your very eyes.

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/013/lesson.s)

---

## Hardware Check: The IR Receiver

The IR Receiver module has 3 pins:
- **VCC** (5 Volts)
- **GND** (Ground)
- **OUT**: The digital signal wire, which we connect to **PD2 (Digital Pin 2)**.

The IR receiver is **Active-Low**. This means:
- When there is **NO** infrared light, the `OUT` pin stays `HIGH` (5 Volts).
- When a pulse of infrared light hits the sensor, the `OUT` pin gets pulled `LOW` (0 Volts).

So to detect light, we must look for a `LOW` signal!

## The Code Walkthrough

This is one of our simplest, yet most educational, assembly programs. It perfectly highlights how fast assembly language is. It runs at the true 16 MHz speed of the microcontroller, meaning it checks the sensor millions of times a second and reacts instantly to a light pulse.

### 1. Setting up the Pins
```assembly
  SBI    DDRB, PB5                     ; Set PB5 (LED) as output
  CBI    DDRD, PD2                     ; Set PD2 (IR Receiver) as input
  SBI    PORTD, PD2                    ; Enable internal pull-up resistor on PD2
```
We set `PB5` (the built-in LED) as an Output so we can turn it on and off.
We set `PD2` as an Input to listen to the IR receiver, and importantly, we turn on the internal pull-up resistor by writing a `1` to the `PORTD` register. This keeps the pin stable when no light is present.

### 2. The High-Speed Visualizer Loop
```assembly
.loop:                                 
  SBIC   PIND, PD2                     ; Skip next instruction if IR Receiver is LOW
  RJMP   .turn_off                     ; If HIGH (no signal), jump to turn off
```
Inside our infinite loop, we use our favorite instruction: `SBIC` (Skip if Bit in I/O Register is Cleared).
If the sensor pin (`PD2`) is `LOW` (cleared), it means infrared light is currently hitting the sensor! The microcontroller will skip the next instruction (`RJMP .turn_off`) and fall straight down into `.turn_on`.

### 3. Flashing the LED
```assembly
.turn_on:                              
  SBI    PORTB, PB5                    ; Turn ON LED (Signal detected)
  RJMP   .loop                         ; Loop forever
.turn_off:                             
  CBI    PORTB, PB5                    ; Turn OFF LED
  RJMP   .loop                         ; Loop forever
```
If we skipped the jump, we land at `.turn_on`, which instantly turns on the LED, and jumps back to the top of the loop.
If there is no light, `SBIC` does *not* skip, and we jump to `.turn_off`, keeping the LED off.

---

### Challenge!
Point any household TV remote at your circuit and press a button! You will see the LED flash rapidly. That flashing is the actual digital "NEC Protocol" data packets being transmitted through the air!
