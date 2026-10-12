# Lesson 005 - 数字输入 (按钮)

## 今天我们要做什么?

欢迎来到第 5 课! 前面几课里, 我们的代码都是自己跑自己的, 完全不管外面发生了什么. 今天我们要让单片机**能互动**!

我们会接上两个按钮 (按钮 A 和按钮 B), 用它们来控制 Arduino Pin 13 上的板载 LED.
- 按下**按钮 A** 把 LED **点亮**.
- 按下**按钮 B** 把 LED **熄灭**.

学完这一课, 你就会用汇编读取电信号输入, 并在代码里做判断了!

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/005/lesson.s)

---

## 硬件检查: 内部上拉电阻

要读一个按钮, 我们把按钮的一边接到输入引脚, 另一边接到**地 (GND)**. 按下按钮时, 引脚就直接连到了 GND (0 伏).

但是等一下! 按钮*没*被按下的时候会发生什么? 引脚什么都没接! 它就像一根天线那样"悬空", 会捡到各种乱七八糟的电噪声. 它可能读到 0 伏, 也可能读到 5 伏, 毫无规律地乱跳.

要解决这个问题, 我们需要一个**上拉电阻**. 这是一个接到 5 伏的电阻, 当没有别的东西连上来时, 它会把引脚"拉"到一个稳稳的高电平.

设计 ATmega328P 的工程师很聪明, 他们在芯片*内部*给每一个引脚都藏了一个小小的上拉电阻! 我们只要告诉单片机把它打开就行.

## 代码讲解

我们来看看在汇编里怎么设置.

### 1. 定义部分
```assembly
.equ DDRB,   0x04                      ; Port B 的数据方向寄存器
.equ PORTB,  0x05                      ; Port B 的数据寄存器
.equ PB5,    5                         ; Port B 的第 5 脚 (Arduino Pin 13 LED)
.equ PIND,   0x09                      ; Port D 的输入引脚寄存器
.equ DDRD,   0x0A                      ; Port D 的数据方向寄存器
.equ PORTD,  0x0B                      ; Port D 的数据寄存器
.equ PD2,    2                         ; Port D 的第 2 脚 (按钮 A)
.equ PD3,    3                         ; Port D 的第 3 脚 (按钮 B)
```
我们定义了老朋友 `PB5` (Pin 13) 给 LED 用.
按钮这边我们用一个新端口: **Port D**.
- `DDRD` 是 Port D 的看门人.
- `PORTD` 用来打开那些藏在芯片里的内部上拉电阻!
- `PIND` (引脚输入寄存器) 是我们用来**读取**引脚上电压的传感器.

### 2. 设置输入和上拉
```assembly
  SBI    DDRB, PB5                     ; 把 PB5 (LED) 设为输出

  CBI    DDRD, PD2                     ; 把 PD2 (按钮 A) 设为输入
  SBI    PORTD, PD2                    ; 使能 PD2 的内部上拉电阻

  CBI    DDRD, PD3                     ; 把 PD3 (按钮 B) 设为输入
  SBI    PORTD, PD3                    ; 使能 PD3 的内部上拉电阻
```
要把一个引脚配成输入, 我们用 `CBI` 告诉看门人 (`DDRD`) 拦住往外的电流.
然后我们用一个小技巧: 如果某个引脚是输入, 那么对 `PORTD` 用 `SBI` 就会打开它的内部上拉电阻! 这样一来, 按钮在我们真正把它按到 GND (低电平) 之前, 都会稳稳地读到高电平 (没按下).

### 3. 读按钮并做判断
这是我们的无限循环:
```assembly
.loop:
  SBIC   PIND, PD2                     ; 若按钮 A 被按下 (低电平) 则跳过下一条
  RJMP   .check_b                      ; 没按下就跳去检查按钮 B
  SBI    PORTB, PB5                    ; 点亮 LED
  RJMP   .loop                         ; 重新开始循环
```
我们用了一条非常厉害的新指令, 叫 `SBIC` (Skip if Bit in I/O Register is Cleared, 即 I/O 寄存器中这一位为 0 就跳过).
它去看 `PIND` 的 `PD2` 位.
- 如果按钮没被按下, 它是高电平 (置位). `SBIC` 什么也不做, 代码就执行下一行: `RJMP .check_b`, 于是跳过了点亮 LED.
- 如果按钮被按下了, 它是低电平 (清零). `SBIC` 就会神奇地**跳过** `RJMP` 指令! 代码直接落到 `SBI PORTB, PB5`, 把 LED 点亮!

```assembly
.check_b:
  SBIC   PIND, PD3                     ; 若按钮 B 被按下 (低电平) 则跳过下一条
  RJMP   .loop                         ; 没按下就跳回循环
  CBI    PORTB, PB5                    ; 熄灭 LED
  RJMP   .loop                         ; 重新开始循环
```
我们对 `PD3` 上的按钮 B 做完全一样的检查. 如果它被按下 (低电平), `SBIC` 就跳过那次跳转, 我们执行 `CBI PORTB, PB5` 把 LED 熄灭!

---

恭喜! 你现在已经会用汇编读取数字输入, 使用内部上拉电阻, 并直接写出条件逻辑 (也就是 if/then 语句) 了!
