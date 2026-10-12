# Chapter 29: main.s - 闪烁循环

## 引言

main.s 是应用程序的入口 - 它把各个驱动函数串在一起, 让一颗 LED 闪起来. Reset_Handler 完成所有初始化之后, 就跳转到 `main`; `main` 先把 GPIO16 配置一次, 然后进入一个无限循环: 置高, 延时, 拉低, 延时, 重复. 本章逐行走一遍.

## 完整源码

```asm
.syntax unified                                  // 使用统一汇编语法
.cpu cortex-m33                                  // 目标核心为 Cortex-M33
.thumb                                           // 使用 Thumb 指令集

.include "constants.s"

.section .text                                   // 代码段
.align 2                                         // 对齐到 4 字节边界

.global main                                     // 导出 main
.type main, %function                            // 标记为函数
main:
.Push_Registers:
  push  {r4-r12, lr}                             // 把寄存器 r4-r12, lr 压入栈
.GPIO16_Config:
  ldr   r0, =PADS_BANK0_GPIO16_OFFSET            // 加载 PADS_BANK0_GPIO16_OFFSET
  ldr   r1, =IO_BANK0_GPIO16_CTRL_OFFSET         // 加载 IO_BANK0_GPIO16_CTRL_OFFSET
  ldr   r2, =16                                  // 加载 GPIO 编号
  bl    GPIO_Config                              // 调用 GPIO_Config
.Loop:
  ldr   r0, =16                                  // 加载 GPIO 编号
  bl    GPIO_Set                                 // 调用 GPIO_Set
  ldr   r0, =500                                 // 500ms
  bl    Delay_MS                                 // 调用 Delay_MS
  ldr   r0, =16                                  // 加载 GPIO 编号
  bl    GPIO_Clear                               // 调用 GPIO_Clear
  ldr   r0, =500                                 // 500ms
  bl    Delay_MS                                 // 调用 Delay_MS
  b     .Loop                                    // 永远循环
.Pop_Registers:
  pop   {r4-r12, lr}                             // 把寄存器 r4-r12, lr 弹出栈
  bx    lr                                       // 返回调用者

.section .rodata                                 // 只读数据段

.section .data                                   // 数据段

.section .bss                                    // BSS 段
```

## 函数元数据

```asm
.global main                                     // 导出 main
.type main, %function                            // 标记为函数
```

`main` 是全局符号, 因为 reset_handler.s 用 `b main` 引用了它. `.type` 指令把它标记为函数, 供链接器和调试器使用.

## 寄存器保存

```asm
.Push_Registers:
  push  {r4-r12, lr}                             // 保存 10 个寄存器 (40 字节)
```

main 是一个非叶子函数 - 它调用 `GPIO_Config`, `GPIO_Set`, `GPIO_Clear` 和 `Delay_MS`, 而这些函数都会覆盖 LR. 压入 LR 保存了返回地址, 压入 r4-r12 则遵循 AAPCS 的被调用者保存约定.

实际上 main 永远不会返回 (因为那个死循环), 但这一对 push/pop 保持了正确的函数结构.

## GPIO16 配置 (一次性设置)

```asm
.GPIO16_Config:
  ldr   r0, =PADS_BANK0_GPIO16_OFFSET            // r0 = 0x44 (pad 偏移)
  ldr   r1, =IO_BANK0_GPIO16_CTRL_OFFSET         // r1 = 0x84 (ctrl 偏移)
  ldr   r2, =16                                  // r2 = 16 (GPIO 编号)
  bl    GPIO_Config                              // 配置 GPIO16
```

这段代码只运行一次, 在循环之前. 它传入三个参数:

| 寄存器 | 值 | 用途 |
|----------|-------|---------|
| r0 | `0x44` | GPIO16 的 pad 寄存器偏移 |
| r1 | `0x84` | GPIO16 的控制寄存器偏移 |
| r2 | `16` | GPIO 引脚编号 |

`GPIO_Config` 返回之后, GPIO16 就完全配置好了: pad 已接通, 功能选择设为 SIO, 输出已使能.

## 无限闪烁循环

```asm
.Loop:
  ldr   r0, =16                                  // r0 = 16 (GPIO 编号)
  bl    GPIO_Set                                 // 把 GPIO16 拉高 (LED 亮)
  ldr   r0, =500                                 // r0 = 500 (毫秒)
  bl    Delay_MS                                 // 等待 500ms
  ldr   r0, =16                                  // r0 = 16 (GPIO 编号)
  bl    GPIO_Clear                               // 把 GPIO16 拉低 (LED 灭)
  ldr   r0, =500                                 // r0 = 500 (毫秒)
  bl    Delay_MS                                 // 等待 500ms
  b     .Loop                                    // 永远重复
```

### 迭代时间线

```
Time (ms):  0     500    1000   1500   2000   2500
            |------|------|------|------|------|
LED:        ON     OFF    ON     OFF    ON     OFF
            Set    Clear  Set    Clear  Set    Clear
```

LED 以 1 Hz 闪烁: 亮 500 ms, 灭 500 ms, 总周期 = 1 秒.

### 为什么每轮都要重新加载 r0?

```asm
  ldr   r0, =16                                  // 每次重新加载 GPIO 编号
```

r0 是临时寄存器 (调用者保存). 每次 `bl` 调用都可能在内部修改它. 所以每次函数调用前都必须重新加载.

### 这个循环永远不会退出

```asm
  b     .Loop                                    // 无条件跳回去
```

`b .Loop` 是一条无条件的向后分支. 处理器会一直执行这个循环, 直到:

- 断电
- 芯片被复位
- 调试器暂停执行

## 不可达代码

```asm
.Pop_Registers:
  pop   {r4-r12, lr}                             // 把寄存器 r4-r12, lr 弹出栈
  bx    lr                                       // 返回调用者
```

由于那个死循环, 这两条指令永远不会执行. 它们的存在是为了保持结构完整 - 万一循环被删掉或能退出, 函数也能正确返回.

## 数据段

```asm
.section .rodata                                 // 只读数据段
.section .data                                   // 数据段
.section .bss                                    // BSS 段
```

这些段被声明了, 但都是空的. 我们的闪烁驱动没有全局变量, 没有已初始化数据, 也没有未初始化数据. 这些段只是为将来扩展预留的位置.

## 完整执行流程

```
Power On
  |
  v
Boot ROM → finds PICOBIN → jumps to Reset_Handler
  |
  v
Reset_Handler
  bl Init_Stack            → stack configured
  bl Init_XOSC             → crystal running
  bl Enable_XOSC_Peri_Clock → peripheral clock on
  bl Init_Subsystem        → GPIO released from reset
  bl Enable_Coprocessor    → CP0 accessible
  b  main
  |
  v
main
  push {r4-r12, lr}
  GPIO_Config(0x44, 0x84, 16)  → GPIO16 ready
  |
  +--→ GPIO_Set(16)        → LED ON
  |    Delay_MS(500)        → wait 500ms
  |    GPIO_Clear(16)       → LED OFF
  |    Delay_MS(500)        → wait 500ms
  |    b .Loop ─────────────+
```

## 小结

- main.s 把 GPIO16 配置一次, 然后进入无限闪烁循环.
- 循环依次调用 GPIO_Set, Delay_MS, GPIO_Clear, Delay_MS.
- 每次函数调用前都要重新加载 r0, 因为它是临时寄存器.
- `b .Loop` 构成无限循环 - LED 以 1 Hz 闪烁.
- 循环之后的 pop/bx 指令在结构上是正确的, 但永远不会执行到.
- 空的 `.rodata`, `.data` 和 `.bss` 段是为完整性而声明的.
