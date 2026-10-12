# Lesson 012 - Analog Joystick

## What Are We Building Today?

So far, we have only worked with **Digital** inputs (0 Volts or 5 Volts). But the real world is not just ON and OFF! What if we want to measure an exact voltage, like a steering wheel that can be turned a little bit, or a lot?

To do this, we use the microcontroller's **Analog to Digital Converter (ADC)**. 
Today, we are going to connect a 2-axis Joystick. Moving the joystick alters the physical resistance of two built-in potentiometers, sending a variable voltage from 0V to 5V on the X and Y axis wires. We will use the ADC to measure these voltages precisely, and we will turn ON the built-in LED (Pin 13) if you push the joystick in *any* direction or press it down like a button!

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/012/lesson.s)

---

## Hardware Check: The ADC

The ATmega328P has a 10-bit ADC. This means it can measure a voltage between 0V and 5V and convert it into a number between `0` and `1023`. 
- **0 Volts** = `0`
- **2.5 Volts (Dead center)** = `512`
- **5 Volts** = `1023`

The Joystick uses three pins we need to read:
- **X-Axis**: Connected to `A0` (Analog Channel 0)
- **Y-Axis**: Connected to `A1` (Analog Channel 1)
- **Button (SW)**: Connected to `PD2` (Digital Pin 2)

## The Code Walkthrough

### 1. Setting Up the ADC
```assembly
  LDI    R16, (1<<ADEN) | (1<<ADPS2) | (1<<ADPS1) | (1<<ADPS0)
  STS    ADCSRA, R16                   ; Write to ADCSRA
```
Before we can measure analog voltage, we have to turn the ADC engine ON.
We use the `ADCSRA` register to enable the ADC (`ADEN`) and set a "Prescaler" of 128 (`ADPS2/1/0`). The prescaler slows down the clock specifically for the ADC so it can take its time to get an extremely accurate reading.

### 2. Reading a Voltage (Our adc_read Subroutine)
```assembly
adc_read:
  ANDI   R16, 0x07                     ; Ensure channel is only 0-7
  ORI    R16, (1<<REFS0)               ; Add AVCC reference bit
  STS    ADMUX, R16                    ; Set ADMUX
```
We created a subroutine `adc_read` that takes the requested channel (0 for X, 1 for Y) in `R16`. 
It configures the `ADMUX` register to select the pin, and adds the `REFS0` bit to tell the ADC to use 5V as its maximum reference.

```assembly
  LDS    R17, ADCSRA                   ; Read current ADCSRA
  ORI    R17, (1<<ADSC)                ; Set the Start Conversion bit
  STS    ADCSRA, R17                   ; Write back to ADCSRA
.wait_adc:                             
  LDS    R17, ADCSRA                   ; Read ADCSRA
  SBRC   R17, ADSC                     ; Skip next if ADSC is Cleared
  RJMP   .wait_adc                     ; Keep waiting
```
We set the `ADSC` (Start Conversion) bit to `1`. The ADC engine will instantly start measuring the voltage. When it finishes, the hardware automatically flips the `ADSC` bit back to `0`. We simply use `SBRC` (Skip if Bit in Register is Cleared) to wait patiently!

```assembly
  LDS    R24, ADCL                     ; IMPORTANT: Must read ADCL before ADCH
  LDS    R25, ADCH                     ; Read ADCH
```
Once the measurement is done, the 10-bit result is split across two registers: `ADCL` (Low) and `ADCH` (High). **Hardware Rule:** You MUST read `ADCL` first! When you read `ADCL`, the hardware freezes `ADCH` so it can't change while you are reading it. 

### 3. Comparing 16-Bit Numbers
```assembly
  LDI    R16, 0x9C                     ; Low byte of 412 (0x019C)
  CP     R24, R16                      ; Compare low bytes
  LDI    R16, 0x01                     ; High byte of 412
  CPC    R25, R16                      ; Compare high bytes
  BRLO   .turn_on                      ; If < 412, turn ON
```
If the joystick is sitting still in the center, it reads roughly `512`. If we push it left/down, it drops toward 0. We use `CP` and `CPC` to compare our 16-bit measurement to `412` (our "deadzone" threshold). If the value drops lower than 412 (`BRLO`), we know the user pushed the joystick, and we branch to turn on the LED!

---

Congratulations! You have successfully interfaced with the analog world by commanding the ADC hardware engine in pure assembly!
