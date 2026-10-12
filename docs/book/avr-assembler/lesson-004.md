# Lesson 004 - RGB LED

## 今天我们要做什么?

欢迎来到第 4 课! 你有没有想过, 你的电视, 手机屏幕或者显示器是怎么造出几百万种颜色的?

其实它只用了三种颜色: **红**, **绿**和**蓝** (RGB). 把这三种光的三原色混在一起, 你几乎能造出任何想象得到的颜色!

今天我们要控制一颗 RGB LED, 让它依次亮出纯红, 纯绿, 纯蓝, 然后完全熄灭.

学完这一课, 你就会用纯汇编同时控制多个引脚了!

[CODE](https://github.com/mytechnotalent/Assembler/blob/main/lessons/004/lesson.s)

---

## 硬件检查: RGB LED

一颗 RGB LED 本质上就是把三颗小 LED 塞进同一个灯泡里. 因为里面有三颗 LED, 所以它需要 4 条金属引脚:
- 1 条引脚接**红色**正极 (阳极)
- 1 条引脚接**绿色**正极 (阳极)
- 1 条引脚接**蓝色**正极 (阳极)
- 1 条长引脚接公共的**负极**地 (共阴极)

这一课里, 我们把三颗 LED 分别接到 Port B 的三个引脚上:
- **红** 接 Pin 9 (**PB1**)
- **绿** 接 Pin 10 (**PB2**)
- **蓝** 接 Pin 11 (**PB3**)

## 代码讲解

因为有三颗 LED, 我们得把三个不同的引脚都准备好往外送电!

### 1. 定义部分
```assembly
.equ DDRB,   0x04                      ; Port B 的数据方向寄存器
.equ PORTB,  0x05                      ; Port B 的数据寄存器
.equ PB1,    1                         ; Port B 的第 1 脚 (红)
.equ PB2,    2                         ; Port B 的第 2 脚 (绿)
.equ PB3,    3                         ; Port B 的第 3 脚 (蓝)
```
我们定义 `DDRB` (把引脚设成输出的看门人) 和 `PORTB` (真正负责开关引脚的那个寄存器). 我们还给三个颜色引脚起了名字: `PB1`, `PB2` 和 `PB3`.

### 2. 设置输出
在 `main` 程序里, 搭好栈之后, 我们告诉看门人让这三个引脚都往外送电:
```assembly
  SBI    DDRB, PB1                     ; 把 PB1 (红) 设为输出
  SBI    DDRB, PB2                     ; 把 PB2 (绿) 设为输出
  SBI    DDRB, PB3                     ; 把 PB3 (蓝) 设为输出
```
我们用 `SBI` (置位 I/O 寄存器中的某一位) 三次, 分别把红, 绿, 蓝的输出开关拨上去!

### 3. 变色动画
现在我们进入无限循环! 我们想让每种颜色各显示整整 1 秒.
```assembly
.loop:
  SBI    PORTB, PB1                    ; 打开红色
  CBI    PORTB, PB2                    ; 关闭绿色
  CBI    PORTB, PB3                    ; 关闭蓝色
  RCALL  delay_1000ms                  ; 等待 1000ms
```
要显示红色, 我们用 `SBI` 把 PB1 打开, 再用 `CBI` (清零 I/O 寄存器中的某一位) 确保绿和蓝是关着的. 然后等 1000 毫秒 (整整 1 秒)!

```assembly
  CBI    PORTB, PB1                    ; 关闭红色
  SBI    PORTB, PB2                    ; 打开绿色
  CBI    PORTB, PB3                    ; 关闭蓝色
  RCALL  delay_1000ms                  ; 等待 1000ms
```
接下来, 我们关掉红色, 打开绿色, 让蓝色保持关闭, 再等一秒.

```assembly
  CBI    PORTB, PB1                    ; 关闭红色
  CBI    PORTB, PB2                    ; 关闭绿色
  SBI    PORTB, PB3                    ; 打开蓝色
  RCALL  delay_1000ms                  ; 等待 1000ms
```
最后, 我们关掉红色和绿色, 打开蓝色! 再等一秒.

```assembly
  CBI    PORTB, PB1                    ; 关闭红色
  CBI    PORTB, PB2                    ; 关闭绿色
  CBI    PORTB, PB3                    ; 关闭蓝色
  RCALL  delay_1000ms                  ; 等待 1000ms
  RJMP   .loop                         ; 无限循环
```
我们用三颗 LED 全灭一秒来收尾. `RJMP .loop` 命令把单片机送回动画的开头, 让这段漂亮的变色循环永远跑下去!

---

恭喜! 你现在已经会用纯汇编调度多个硬件引脚来做动画了!
