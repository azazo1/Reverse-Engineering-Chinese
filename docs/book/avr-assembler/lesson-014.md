# Lesson 014 - LCD Display

## What Are We Building Today?

It's time to give our microcontroller a voice that doesn't just beep or blink, but actually speaks English! Today we are going to write a custom software driver for an **HD44780-compatible 16x2 Character LCD Display**. 

We will learn how to interface with the display in "4-bit mode", send it initialization commands, and then print the word **HELLO** on the screen using pure assembly language!

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/014/lesson.s)

---

## Hardware Check: The LCD Interface

The LCD requires 6 wires to control it from our ATmega328P:
- **RS (Register Select)**: Connected to `PD7`. If `0`, we are sending a Command. If `1`, we are sending Character Data (ASCII).
- **E (Enable)**: Connected to `PD6`. We quickly pulse this pin HIGH then LOW to tell the LCD, "Read the data now!"
- **D4 to D7 (Data Bus)**: Connected to `PD5` through `PD2`. This is where we send the 4-bit data "nibble".

Wait, look at the data bus carefully:
- LCD `D4` is wired to Microcontroller `PD5`
- LCD `D5` is wired to Microcontroller `PD4`
- LCD `D6` is wired to Microcontroller `PD3`
- LCD `D7` is wired to Microcontroller `PD2`

The wires are entirely backwards! This is very common in hardware hacking when wires are plugged in where they physically fit best, rather than in perfectly logical order. We will have to fix this hardware mess in our software using bit manipulation!

## The Code Walkthrough

### 1. Bit Surgery (BST and BLD)
To send a 4-bit "nibble", we wrote the `lcd_send_nibble` subroutine. It takes a nibble in `R16` and meticulously surgically implants it into the `PORTD` register backwards!

```assembly
  BST    R16, 0                        ; Store bit 0 in T flag
  BLD    R17, 5                        ; Load T flag into bit 5 (D4)
  BST    R16, 1                        ; Store bit 1 in T flag
  BLD    R17, 4                        ; Load T flag into bit 4 (D5)
```
We use two brand new, incredibly powerful assembly instructions:
- **BST (Bit Store from Register to T Flag)**: Copies a single bit from our register and saves it in a special temporary holding cell in the CPU called the "T Flag".
- **BLD (Bit Load from T Flag to Register)**: Takes the bit sitting in the T Flag and injects it into a specific slot in another register!

We do this 4 times to flawlessly reverse the 4 bits in software to match our backwards hardware wiring!

### 2. High and Low Nibbles (SWAP)
Because we are using 4-bit mode (to save pins), sending a full 8-bit command (like `0x28`) requires sending it in two chunks: the High Nibble (`0x2`) and then the Low Nibble (`0x8`).

```assembly
lcd_write_command:
  CBI    PORTD, PD7                    ; Set RS LOW (Instruction mode)
  MOV    R18, R16                      ; Backup full byte
  SWAP   R16                           ; Swap high and low nibbles
  RCALL  lcd_send_nibble               ; Send high nibble
  MOV    R16, R18                      ; Restore full byte
  RCALL  lcd_send_nibble               ; Send low nibble
```
To get the High Nibble into position, we use the `SWAP` instruction. It magically swaps the left 4 bits with the right 4 bits in a single clock cycle!

### 3. Printing HELLO
Once the complex multi-step Initialization Sequence is complete (which takes about 50 milliseconds of precise delays and configuration commands), writing to the screen is incredibly easy!

```assembly
  LDI    R16, 'H'                      ; ASCII for 'H'
  RCALL  lcd_write_data                ; Send Data
  LDI    R16, 'E'                      ; ASCII for 'E'
  RCALL  lcd_write_data                ; Send Data
```
We simply load the ASCII character (in single quotes) into `R16` and call `lcd_write_data`. The assembler automatically turns `'H'` into its ASCII numerical value (`0x48`) for us!

---

Congratulations! You have successfully tamed a complex parallel communication protocol and performed advanced bit manipulation to display text on a physical screen in bare metal assembly!
