# Lesson 023 - Stepper Motor

## What Are We Building Today?

A DC Motor (like we used in Lesson 21) is great for spinning things fast, but it is terrible for precision. If you want a robot arm to rotate exactly 90 degrees and stop, a DC motor will overshoot or undershoot.

To solve this, we use a **Stepper Motor**. A Stepper Motor doesn't just spin wildly; it moves in discrete, perfect "steps". Every time we send it a signal, it rotates exactly `0.175` degrees!

Today, we will learn the fundamental physics of Stepper Motors and write a "Wave Drive" algorithm in assembly to manually rotate the motor step-by-step!

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/023/lesson.s)

---

## Hardware Check: The 28BYJ-48 Stepper & ULN2003 Driver
Inside our Stepper Motor, there is a central magnetic rotor surrounded by 4 independent Electromagnets (Coils). 
To make the motor spin, we have to turn these 4 magnets on and off in a circle. The rotor will literally "chase" the magnetic field as it moves around!

Because Stepper Motors draw a lot of current, we must use a driver board. We will use the **ULN2003 Darlington Array Driver**.
We connect `IN1`, `IN2`, `IN3`, and `IN4` on the driver board to `PD2`, `PD3`, `PD4`, and `PD5` on our ATmega328P.

## The Code Walkthrough

### The Wave-Drive Algorithm
The simplest way to drive a stepper motor is called the **Wave Drive** (or 1-Phase On). 
The algorithm is simple:
1. Turn ON Magnet 1. (Wait 5ms for the rotor to snap to it).
2. Turn OFF Magnet 1, and Turn ON Magnet 2. (Wait 5ms).
3. Turn OFF Magnet 2, and Turn ON Magnet 3. (Wait 5ms).
4. Turn OFF Magnet 3, and Turn ON Magnet 4. (Wait 5ms).
5. Repeat!

If we write directly to the `PORTD` register, we can control all 4 pins simultaneously in a single clock cycle!

```assembly
.loop:
  ; Step 1: Fire Coil 1 (IN1 is on PD2)
  LDI    R16, 0b00000100               ; Set bit 2 HIGH
  OUT    PORTD, R16                    ; Overwrite all PORTD pins instantly
  RCALL  delay_5ms

  ; Step 2: Fire Coil 2 (IN2 is on PD3)
  LDI    R16, 0b00001000               ; Set bit 3 HIGH
  OUT    PORTD, R16
  RCALL  delay_5ms

  ; Step 3: Fire Coil 3 (IN3 is on PD4)
  LDI    R16, 0b00010000               ; Set bit 4 HIGH
  OUT    PORTD, R16
  RCALL  delay_5ms

  ; Step 4: Fire Coil 4 (IN4 is on PD5)
  LDI    R16, 0b00100000               ; Set bit 5 HIGH
  OUT    PORTD, R16
  RCALL  delay_5ms

  RJMP   .loop                         ; Do it again!
```

This sequence repeats endlessly, causing the magnetic field to spin around the stator, dragging the physical rotor with it! 

**Note on Timing:** If you make the delay too short (e.g., 1ms), the magnetic field will spin faster than the physical mass of the rotor can move. The motor will just vibrate and screech without spinning at all! 5ms is a safe, stable speed for the 28BYJ-48.

---

Congratulations! You have successfully mastered Electromagnet Sequencing and Stepper Motor Wave-Drives in bare metal assembly!
