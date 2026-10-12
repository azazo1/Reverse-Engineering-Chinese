# Lesson 007 - Passive Buzzer (Musical Tones)

## What Are We Building Today?

In Lesson 6, we used an Active Buzzer that automatically generated sound whenever it received power. But what if we want to play a song? 

Today, we will use a **Passive Buzzer**. A passive buzzer does *not* have an internal oscillator. If you just send it 5 Volts, it will only make a tiny "click" and then stay silent. To make it beep, we have to turn the power ON and OFF hundreds of times a second manually! The speed at which we turn it on and off determines the musical pitch (frequency).

We will use our friend **Timer1** to automatically toggle a pin incredibly fast, playing a perfect C-Major musical scale!

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/007/lesson.s)

---

## Hardware Check: Generating Frequencies

To play a note, we need a square wave. For example, Middle C (C4) is 262 Hz. This means we need the speaker to vibrate 262 times every second.

We can use **Timer1** in **CTC Mode (Clear Timer on Compare Match)**. 
We tell the timer: "Count up to this exact number (`OCR1A`), and when you hit it, toggle the output pin (PB1/Arduino Pin 9) and start over at 0."

By calculating the right number for `OCR1A`, we can precisely control the frequency!
- High `OCR1A` value = Slower toggle = Lower pitch
- Low `OCR1A` value = Faster toggle = Higher pitch

## The Code Walkthrough

### 1. Storing the Notes
We want to play 8 notes (C4, D4, E4, F4, G4, A4, B4, C5). We calculated the `OCR1A` values for each note and stored them in an array in Flash memory (Program Memory). The array ends with a `0` so we know when to stop.

```assembly
scale_data:                            
.word 3816, 3401, 3030, 2865, 2551, 2272, 2024, 1912, 0
```
Notice we use `.word` because these numbers are larger than 255 (they take up 16 bits or 2 bytes each).

### 2. Setting Up Timer1
```assembly
  LDI    R16, (1<<WGM12) | (1<<CS11)   ; CTC mode, Prescaler 8
  STS    TCCR1B, R16                   ; Write to TCCR1B
```
We configure Timer1 for CTC mode and set the clock prescaler to 8. This means the timer ticks 2,000,000 times a second!

### 3. Reading the Array
We use the Z-pointer (`R30` and `R31`) to point to our array in memory.
```assembly
  LPM    R16, Z+                       ; Load low byte of TOP from flash
  LPM    R17, Z+                       ; Load high byte of TOP from flash
```
Since the values are 16 bits long, we load them in two pieces: the low byte into `R16` and the high byte into `R17`. `Z+` automatically moves our pointer forward.

### 4. Playing the Note!
```assembly
  STS    OCR1AH, R17                   ; Write HIGH byte of TOP
  STS    OCR1AL, R16                   ; Write LOW byte of TOP
  LDI    R16, (1<<COM1A0)              ; Enable OC1A toggle on match
  STS    TCCR1A, R16                   ; Write to TCCR1A
```
We write the value into the `OCR1A` register. **Important rule**: In AVR assembly, when writing to a 16-bit register, you MUST write the High byte first, then the Low byte!

Next, we tell `TCCR1A` to toggle the pin on every match (`COM1A0`). The buzzer is now screaming!

We let it beep for 300ms by calling `delay_300ms`.

### 5. Silencing Between Notes
If we just played notes back-to-back, it would sound like a single blurry noise. We need to turn the buzzer off for a tiny fraction of a second to add space between the notes.

```assembly
  LDI    R16, 0                        ; Disable OC1A toggle
  STS    TCCR1A, R16                   ; Write to TCCR1A
  CBI    PORTB, PB1                    ; Ensure buzzer pin is LOW
  RCALL  delay_50ms                    ; Silence for 50ms
```
We disable the toggle, ensure the pin is pushed to 0 Volts (LOW) with `CBI`, and wait 50ms in silence before jumping back to play the next note!

---

Congratulations! You've just turned your microcontroller into a digital synthesizer!
