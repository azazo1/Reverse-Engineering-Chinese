# Lesson 001 - Serial

## What Are We Building Today?

Welcome to Lesson 1! Today, we are going to teach our ATmega328P microcontroller how to "talk" to our computer. Have you ever wondered how a USB cable sends text between devices? We are going to build the lowest-level code that makes that happen using **Serial Communication**. 

By the end of this lesson, our microcontroller will send a welcome message: `Lesson 001 - Serial Monitor Ready!` to our computer's Serial Monitor, and then it will print a dot (`.`) every half second forever.

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/001/lesson.s)

---

## The Brain of the Operation: What is a Register?

Before we look at the code, we need to understand how the brain of our ATmega328P works. 

Imagine you are solving a massive math problem. You can't do it all in your head, so you use a piece of scratch paper to write down small numbers while you work. The microcontroller has its own "scratch paper" called **Registers**. 

A register is a tiny, super-fast memory box inside the processor. It holds exactly 8 bits of data (a number from 0 to 255). To make the microcontroller do *anything*—like turn on an LED or send a letter to your computer—we have to write specific numbers into specific registers.

### General Purpose Registers (The Scratchpads)
- **R16, R17, R18**: These are general-purpose registers. We can put whatever numbers we want in them to do math, count down time, or hold a letter before sending it.
- **R30 & R31 (The Z-Pointer)**: Sometimes we need to point to a massive sentence in memory (like our welcome message). Because our memory addresses are larger than 8 bits, we combine two 8-bit registers (R30 and R31) into a single 16-bit super-register called the **Z-Pointer**.

### The Stack Pointer (SPL & SPH)
Imagine a stack of plates at a buffet. You can only put a plate on the top, and take a plate off the top. This is exactly how the **Stack** works in a computer! 
When our code jumps to a "Subroutine" (a mini-program like `delay_500ms`), the computer needs to remember where it came from so it can go back. It places a "bookmark" on the top of the stack. 
- **SPL and SPH**: These registers hold the "Stack Pointer", which tells the computer exactly where the top of the plate stack is.
- **RAMEND**: This is the very last address in our SRAM (memory). We always set the stack pointer to start at the very back of memory so it has plenty of room to grow.

### The Serial Mailbox (USART Registers)
To send text, we use a piece of hardware inside the chip called the **USART** (Universal Synchronous and Asynchronous Receiver and Transmitter). Think of it as a post office.
- **UBRR0H & UBRR0L**: These set the "Baud Rate" (the speed limit of our communication). Both sides (the Arduino and your PC) must agree on the speed, or the text will look like gibberish! We will set it to 9600 bits per second.
- **UCSR0A, UCSR0B, UCSR0C**: These are the Control and Status registers. They are like the switches and dials on the post office wall. We use them to turn the transmitter ON, check if the mailbox is empty, and set our data size to 8 bits.
- **UDR0**: The Data Register. This is the actual mailbox! When we drop a letter (like the character `A`) into UDR0, the hardware automatically ships it down the USB wire to your computer.

---

## Step-by-Step Code Walkthrough

Let's break down every single line of our assembly code so you can see exactly how it works.

### 1. The Defines
At the very top of our code, we use `.equ` (which stands for "equals"). This doesn't write any actual code; it just gives easy-to-read names to raw memory addresses.
```assembly
.equ RAMEND, 0x08FF                    ; Last SRAM address (ATmega328P)
.equ SPL,    0x3D                      ; Stack Pointer Low register
```
Instead of trying to memorize that the Stack Pointer Low is at address `0x3D`, we just name it `SPL`. 

### 2. The Reset Vector
```assembly
.org 0x0000                            ; Program starts at address 0
  RJMP   main                          ; Jump to main program
```
When you plug in your Arduino, the processor wakes up and immediately looks at address `0x0000` to figure out what to do. `.org 0x0000` tells the assembler to put our very first instruction here. `RJMP main` tells it to "Relative Jump" down to our main program.

### 3. The Main Program
```assembly
main:                                  
  LDI    R16, lo8(RAMEND)              ; R16 = low byte of last RAM addr
  OUT    SPL, R16                      ; Stack Pointer Low = R16
  LDI    R16, hi8(RAMEND)              ; R16 = high byte of last RAM addr
  OUT    SPH, R16                      ; Stack Pointer High = R16
```
This is where we set up the Stack! `LDI` means "Load Immediate" (put a number directly into a register). `OUT` means send that number out to a hardware register. We split `RAMEND` into a low byte and high byte, and push them into `SPL` and `SPH`. Now our stack is ready!

```assembly
  RCALL  init_usart                    ; Initialize USART0
  RCALL  delay_100ms                   ; Wait 100ms
```
`RCALL` means "Relative Call". We pause what we are doing, jump to the `init_usart` mini-program to turn on the serial post office, and then come back. Then we jump to `delay_100ms` to give the hardware a tiny fraction of a second to wake up.

```assembly
  LDI    R30, lo8(msg_greeting)        ; Load low byte of string to Z
  LDI    R31, hi8(msg_greeting)        ; Load high byte of string to Z
  RCALL  print_string                  ; Print greeting message
```
Here, we load the location of our welcome message into the Z-pointer (R30 and R31). Then we call `print_string`, which will use that pointer to read and send our sentence.

```assembly
.loop:                                 
  LDI    R16, '.'                      ; Load dot character
  RCALL  tx_char                       ; Transmit character
  RCALL  delay_500ms                   ; Wait 500ms
  RJMP   .loop                         ; Infinite loop
```
This is our infinite loop! We load the dot character `.` into `R16`, call `tx_char` to send it, wait half a second, and then `RJMP .loop` to do it all over again forever.

### 4. Setting up the Serial Post Office (init_usart)
```assembly
init_usart:                            
  LDI    R16, 207                      ; UBRR = 207 for 9600 baud
  STS    UBRR0L, R16                   ; Set UBRR0L
```
To talk at 9600 speed on a 16 MHz chip, math tells us we need to put the number `207` into the UBRR registers. 

```assembly
  LDI    R16, (1<<TXEN0)               ; Enable transmitter
  STS    UCSR0B, R16                   ; Write to UCSR0B
```
This flips the switch to turn the transmitter ON. `(1<<TXEN0)` is just a fancy way of saying "flip the specific bit that controls the transmitter".

```assembly
  LDI    R16, (1<<UCSZ01)|(1<<UCSZ00)  ; 8 data, 1 stop, no parity
  STS    UCSR0C, R16                   ; Write to UCSR0C
  RET                                  ; Return to caller
```
This sets our data size to 8 bits (one standard byte per character). Finally, `RET` tells the computer to take the bookmark off the stack and return to `main`!

### 5. Sending a Single Character (tx_char)
```assembly
tx_char:                               
  LDS    R17, UCSR0A                   ; Read UCSR0A
  SBRS   R17, UDRE0                    ; Skip if UDRE0 is set
  RJMP   tx_char                       ; Loop until buffer is empty
  STS    UDR0, R16                     ; Write character to UDR0
  RET                                  ; Return to caller
```
This is the mailbox check! Before we can drop a letter into `UDR0`, we have to make sure the mailman has emptied it. 
We read the status register (`LDS R17, UCSR0A`). 
`SBRS` stands for "Skip if Bit in Register is Set". It checks the `UDRE0` bit (Data Register Empty). If the mailbox is empty, it skips the next instruction! If it is *not* empty, it does not skip, and the `RJMP tx_char` forces it to loop back and check again. 
Once empty, we write our character to the mailbox (`STS UDR0, R16`) and return!

### 6. Printing an Entire Sentence (print_string)
```assembly
print_string:                          
  LPM    R16, Z+                       ; Load char from flash and inc Z
  CPI    R16, 0                        ; Check if null terminator
  BREQ   .print_done                   ; If null, we are done
  RCALL  tx_char                       ; Otherwise, transmit the char
  RJMP   print_string                  ; Loop for next character
.print_done:                           
  RET                                  ; Return to caller
```
This subroutine is a loop that prints an entire sentence. 
`LPM R16, Z+` means "Load Program Memory". It looks at wherever our Z-pointer is pointing, grabs that letter, puts it in `R16`, and then automatically moves the Z-pointer to the next letter!
`CPI R16, 0` checks if the letter is a `0`. In C and Assembly, we put a `0` at the very end of our sentences to let the computer know it's time to stop reading. 
`BREQ .print_done` means "Branch if Equal". If the letter was a 0, we jump to the end and `RET`. If it wasn't a 0, we send the character, and jump back to read the next one!

### 7. Time Travel (Delays)
```assembly
delay_500ms:                           
  LDI    R18, 0x18                     ; High byte of delay counter
  LDI    R17, 0x69                     ; Mid byte of delay counter
  LDI    R16, 0xFE                     ; Low byte of delay counter
.d500_loop:                            
  SUBI   R16, 1                        ; Subtract 1 from low byte
  SBCI   R17, 0                        ; Subtract carry from mid byte
  SBCI   R18, 0                        ; Subtract carry from high byte
  BRNE   .d500_loop                    ; Branch if not zero
  NOP                                  ; Pad out exact cycle count
  RET                                  ; Return to caller
```
The ATmega328P runs at 16 MHz (16 Million instructions per second!). To wait for half a second, we literally have to force the processor to count backwards from a massive number (like 1.6 million) to zero. 
Because registers only hold numbers up to 255, we have to link three registers together (R16, R17, R18) to hold a massive 24-bit number. 
`SUBI` subtracts 1. `SBCI` subtracts with carry (borrowing from the next register if the first one drops below zero). It repeats this loop until all three registers hit exactly zero!

### 8. Our Sentence in Flash Memory
```assembly
msg_greeting:                          
.asciz "Lesson 001 - Serial Monitor Ready!\r\n"
```
Finally, this is where we store our message! `.asciz` tells the assembler to convert our text into ASCII bytes and store it directly in the Flash memory of the chip. The `z` at the end of `.asciz` automatically adds that hidden `0` (null terminator) to the end of the sentence so our `print_string` loop knows when to stop! `\r\n` is just code for "hit the Enter key" so the next text appears on a new line.
