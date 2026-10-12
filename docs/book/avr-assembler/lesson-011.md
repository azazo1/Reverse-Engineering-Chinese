# Lesson 011 - DHT11 Temperature & Humidity Sensor

## What Are We Building Today?

Today we will tackle one of the most exciting challenges in bare metal programming: **Single-Wire Digital Protocols**.

We are using the **DHT11**, a digital temperature and humidity sensor. Unlike a simple button or LED that just turns on and off, the DHT11 actually talks to us! It sends 40 bits of digital data (1s and 0s) over a single wire. It does this by pulling the voltage LOW and HIGH at very specific microscopic time intervals.

We will write an advanced timing subroutine to measure these electrical pulses, assemble them into 8-bit bytes, and then perform a mathematical checksum to guarantee the data is correct. If the data is read perfectly, the built-in LED (Pin 13) will turn ON for 1 second. If there is an error in reading the data, it will flash rapidly!

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/011/lesson.s)

---

## Hardware Check: The Single-Wire Protocol

The DHT11 uses a single data wire connected to **PD2 (Pin 2)**.
To talk to it, we must follow a strict handshake:
1. **The Wake Up Call**: We pull the line LOW (0 Volts) for 20 milliseconds, then release it HIGH.
2. **The Acknowledgment**: The DHT11 pulls the line LOW for 80 microseconds, then HIGH for 80 microseconds.
3. **The Data Transmission**: The DHT11 immediately sends 40 bits (5 bytes) of data.
   - A logic `0` is a 50µs LOW pulse followed by a **~28µs HIGH** pulse.
   - A logic `1` is a 50µs LOW pulse followed by a **~70µs HIGH** pulse.
4. **The Bytes**: Byte 1 (Humidity Integer), Byte 2 (Humidity Decimal), Byte 3 (Temp Integer), Byte 4 (Temp Decimal), and Byte 5 (Checksum).

Our job is to measure the length of the HIGH pulses to figure out if the sensor is sending us a `0` or a `1`!

## The Code Walkthrough

### 1. The Handshake
```assembly
  SBI    DDRD, PD2                     ; PD2 as Output
  CBI    PORTD, PD2                    ; Pull line LOW for Start Signal
  RCALL  delay_20ms                    ; Wait 20ms
  SBI    PORTD, PD2                    ; Release line HIGH
  CBI    DDRD, PD2                     ; Change PD2 to Input to listen
```
We take control of the pin, drive it LOW for 20ms, release it, and immediately switch our pin to an `Input` so we can listen. We then use `SBIC` and `SBIS` in tight loops to wait for the sensor to acknowledge us.

### 2. Reading a Byte (The Magic Subroutine)
To read 8 bits, we wrote a brilliant subroutine: `dht_read_byte`.
```assembly
.inc_counter:                          
  INC    R25                           ; Increment counter (takes 5 cycles total)
  NOP                                  ; Pad for timing
  RJMP   .wait_low                     ; Loop back
```
When the pulse goes HIGH, we loop this counter. This loop takes exactly 5 clock cycles (`0.3125 microseconds`). If the pulse stays HIGH for 28µs (a logic `0`), our counter will reach about `90`. If it stays HIGH for 70µs (a logic `1`), our counter will reach about `224`.

```assembly
.eval_bit:                             
  CPI    R25, 150                      ; Compare counter to threshold (approx 47us)
  BRSH   .bit_one                      ; If counter >= 150, the bit is a 1
  CLC                                  ; Bit is 0, clear Carry flag
  RJMP   .shift_in                     ; Jump to shift
.bit_one:                              
  SEC                                  ; Bit is 1, set Carry flag
.shift_in:                             
  ROL    R18                           ; Shift the Carry flag into R18
```
We compare our counter to `150` (which sits perfectly in the middle at 47µs). 
If it is greater or equal (`BRSH`), we set the CPU's Carry Flag (`SEC`). If it is lower, we clear the Carry Flag (`CLC`). 
Then, we use the `ROL` (Rotate Left through Carry) instruction. This magically slides our new bit directly into the `R18` register! After doing this 8 times, `R18` holds our fully assembled byte!

### 3. The Checksum
The 5th byte sent by the sensor is a Checksum. The rule is: `Byte 1 + Byte 2 + Byte 3 + Byte 4` must exactly equal `Byte 5`.
```assembly
  MOV    R17, R20                      ; R17 = Humidity Int
  ADD    R17, R21                      ; Add Humidity Dec
  ADD    R17, R22                      ; Add Temp Int
  ADD    R17, R23                      ; Add Temp Dec
  CP     R17, R24                      ; Compare calculated sum with Checksum
  BRNE   .error                        ; If not equal, checksum failed!
  SBI    PORTB, PB5                    ; Success! Turn LED ON
```
We add all four data bytes together and `CP` (Compare) the result to the 5th byte. If it matches, our data is completely error-free, and we celebrate by turning on the LED!

---

Congratulations! You just wrote a fully functional software driver for a digital single-wire communications protocol using pure mathematical timing in Assembly!
