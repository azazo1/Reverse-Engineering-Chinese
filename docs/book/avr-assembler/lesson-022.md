# Lesson 022 - Relay Module

## What Are We Building Today?

Sometimes, you need to control a device that uses a completely different power source. What if you want your tiny 5V microcontroller to turn on a giant 12V water pump, or a 120V desk lamp? 

If you connect 12V or 120V to your ATmega328P, it will literally explode. 
To safely control massive voltages, we use an ancient but incredibly reliable component: **The Electromechanical Relay**.

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/022/lesson.s)

---

## Hardware Check: The Relay
A Relay is literally just a physical light switch... but instead of a plastic lever that you flip with your finger, the lever is made of magnetic metal, and it is flipped by an **Electromagnet**!

The Relay Module has two completely separate, isolated sides:
1. **The Low Voltage Side (Control)**: Connects to your Microcontroller. We connect `IN` to `PD5`, `VCC` to 5V, and `GND` to Ground.
2. **The High Voltage Side (Load)**: Connects to your giant motor or appliance. It has three terminals:
   - **COM (Common)**: The power source (e.g. 12V battery).
   - **NO (Normally Open)**: The device that should be off until the relay clicks.
   - **NC (Normally Closed)**: The device that should be on until the relay clicks.

When we send a `HIGH` logic signal to `PD5`, current flows through the electromagnet. The magnet activates and *physically pulls* the metal switch inside the box! You will hear a loud physical *CLICK* when this happens!

## The Code Walkthrough

Because a Relay Module expects a simple logic `HIGH` or `LOW` to turn on or off, the Assembly code is identical to turning on an LED! 

```assembly
  ; Set PD5 as output for the Relay Module
  SBI    DDRD, PD5                     

.loop:
  ; --- Turn Relay ON ---
  ; This energizes the electromagnet, closing the circuit!
  SBI    PORTD, PD5                    
  RCALL  delay_2000ms                  

  ; --- Turn Relay OFF ---
  ; This de-energizes the electromagnet, opening the circuit!
  CBI    PORTD, PD5                    
  RCALL  delay_2000ms                  

  RJMP   .loop
```

- We use `SBI` (Set Bit in I/O Register) to configure the pin as an output.
- We use `SBI` again on the `PORT` register to send 5V to the electromagnet, generating a magnetic field that closes the high-voltage switch!
- We use `CBI` (Clear Bit in I/O Register) to drop the pin to 0V. The magnetic field collapses, and a mechanical spring violently pulls the switch back open!

---

Congratulations! You have successfully mastered Electromechanical Relays and Galvanic Isolation in bare metal assembly!
