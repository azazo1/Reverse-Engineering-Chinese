# Lesson 024 - IR Controlled Stepper

## What Are We Building Today?

Welcome to the Grand Finale! Over the past 23 lessons, you have mastered everything from flipping simple bits in registers to time-domain multiplexing and analog-to-digital conversions. 

Today, we will tie everything together by combining the **IR Receiver** (from Lesson 13) with the **Stepper Motor** (from Lesson 23).
We are going to build a completely wireless, remote-controlled motorized system in pure assembly! 

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/024/lesson.s)

---

## Hardware Check: Combining the Systems
We will use the same hardware from our previous lessons:
1. **The ULN2003 Stepper Driver**: Connected to `PD2`, `PD3`, `PD4`, and `PD5`.
2. **The IR Receiver Module**: Connected to `PD6`.

## The Code Walkthrough

In Lesson 13, we learned that the IR Receiver module idles at `HIGH` (5V). When invisible infrared light hits the sensor, it drops to `LOW` (0V).
We can use a single instruction, `SBIC` (Skip if Bit in I/O Register is Cleared), to constantly poll the sensor and wait for a signal.

```assembly
.loop:
  ; Wait for an IR signal (LOW means light is hitting the receiver)
  SBIC   PIND, PD6                     ; Skip next instruction if IR Receiver is LOW
  RJMP   .loop                         ; If it's HIGH, just keep waiting
```

While the room is dark (infrared speaking), the microcontroller executes this `RJMP .loop` millions of times per second, trapped in a tiny waiting pattern.
The instant you point your TV Remote at the sensor and press a button, infrared light floods the sensor, `PD6` drops to LOW, and the CPU skips the `RJMP` instruction!

It breaks out of the waiting pattern and immediately begins executing our Wave-Drive stepper algorithm:

```assembly
  ; Signal Detected! Spin the Stepper Motor!
  
  ; Step 1: Fire Coil 1 (IN1)
  LDI    R16, 0b01000100               ; PD2 HIGH, PD6 pull-up maintained
  OUT    PORTD, R16
  RCALL  delay_5ms
```

**CRITICAL RULE:** Because both the Stepper Motor and the IR Receiver share `PORTD`, we must be extremely careful! 
The IR Receiver requires an internal pull-up resistor on `PD6`. If we write `0b00000100` to `PORTD`, we would accidentally turn OFF the pull-up resistor on bit 6!
To fix this, our masks are `0b01000100` (Bit 6 is kept HIGH to maintain the pull-up resistor while Bit 2 fires the motor).

The motor will execute one full 4-step sequence (turning exactly 0.7 degrees) and then return to the top of the loop to check the IR receiver again. 
If you hold down a button on your remote, the motor will continuously spin!

---

Congratulations! You have completed the AVR Assembler series. You have written drivers, multiplexers, and hardware controllers from scratch using nothing but pure binary machine instructions. 

You are now a true Bare-Metal Engineer!
