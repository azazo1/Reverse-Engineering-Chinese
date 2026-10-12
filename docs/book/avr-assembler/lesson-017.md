# Lesson 017 - Serial Control

## What Are We Building Today?

Our hardware array is cool, but what if we want to remotely control our microcontroller from our desktop computer? Today we are going to implement a full **two-way Serial Communications (USART)** interface. 

You will open the Serial Monitor (at 9600 Baud) on your computer and type in commands. Your computer will send characters to the ATmega328P, the microcontroller will parse them, flip the correct LED on the Shift Register, and reply back to your computer with an "OK" message!

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/017/lesson.s)

---

## The Hardware: USART (Universal Synchronous/Asynchronous Receiver-Transmitter)

The ATmega328P has dedicated hardware built in for handling serial communication. This hardware is wired directly to the USB cable of your Arduino Uno! All we have to do is configure the correct registers, and the hardware handles the electrical timing for us.

### 1. Initializing the USART (9600 Baud)
To communicate at `9600 bits per second` on a `16 MHz` processor, the AVR datasheet tells us we need to set the USART Baud Rate Register (`UBRR0`) to `103`.

```assembly
  ; Init USART to 9600 baud (UBRR = 103 for 16MHz)
  LDI    R16, hi8(103)                 ; Get the High byte of 103 (which is 0)
  STS    UBRR0H, R16                   ; Store it
  LDI    R16, lo8(103)                 ; Get the Low byte of 103 (which is 103)
  STS    UBRR0L, R16                   ; Store it
```
Next, we enable the Transmitter (`TXEN0`) and Receiver (`RXEN0`), and set the character size to 8 bits (`UCSZ01` and `UCSZ00`).

### 2. Receiving a Character
When a character arrives from your computer, a flag called `RXC0` (Receive Complete) is set HIGH inside the `UCSR0A` status register.

```assembly
uart_rx:
  LDS    R17, UCSR0A                   ; Load status register
  SBRS   R17, RXC0                     ; Skip next if Receive Complete flag is Set
  RJMP   uart_rx                       ; Loop forever until a character arrives!
  LDS    R16, UDR0                     ; Read the newly arrived character!
  RET
```
This is called a "Blocking Loop". The microcontroller spins endlessly, waiting patiently. When a key is finally pressed, it escapes the loop and reads the `UDR0` (USART Data Register).

### 3. Transmitting a Character
Transmitting works exactly the same way in reverse. We wait for the `UDRE0` (USART Data Register Empty) flag to assert that the hardware has finished sending the *previous* character, then we write the new character to `UDR0`!

```assembly
uart_tx:
  LDS    R17, UCSR0A                   ; Load status register
  SBRS   R17, UDRE0                    ; Skip next if Data Register Empty flag is Set
  RJMP   uart_tx                       ; Loop forever until ready
  STS    UDR0, R16                     ; Write the new character to send!
  RET
```

## The Command Interpreter
Once we receive a character in `R16`, we need to figure out what it means!

```assembly
  CPI    R16, 'x'                      ; Did the user type 'x'?
  BREQ   .clear_leds                   ; If so, Branch if Equal to the clear routine!
  
  CPI    R16, '0'                      ; Is it less than '0'?
  BRLO   .invalid                      ; If so, Branch if Lower to the error routine!
  CPI    R16, '8'                      ; Is it greater than or equal to '8'?
  BRSH   .invalid                      ; If so, Branch if Same or Higher to the error routine!
```

If it passes all of these checks, we know the user typed a valid number between `0` and `7`! We convert the ASCII text character into an actual integer simply by subtracting the value of `'0'`:

```assembly
  SUBI   R16, '0'                      ; Convert ASCII '0'-'7' to integer 0-7
```

We then use a bit-shifting loop to create the correct binary mask, send it to our Shift Register, and reply to the user!

---

Congratulations! You have successfully implemented a full two-way interactive Serial Communication protocol and a basic Command-Line Interpreter (CLI) in bare metal assembly!
