# Chapter 23: vector_table.s 与 stack.s - 引导基础

## 引言

Cortex-M33 退出复位后做的第一件事, 就是从向量表里读两个 32 位字: 初始栈指针和复位处理程序的地址. 这两个值都定义在 vector_table.s 里, 它们决定了栈在哪里, 以及执行从哪里开始. 随后 stack.s 用上限寄存器进一步完善栈的配置, 用来捕获溢出. 这两个文件一起构成了固件的引导基础.

## vector_table.s - 完整源码

```asm
.syntax unified                                  // 使用统一汇编语法
.cpu cortex-m33                                  // 目标核心为 Cortex-M33
.thumb                                           // 使用 Thumb 指令集

.include "constants.s"

.section .vectors, "ax"                          // 向量表段
.align 2                                         // 对齐到 4 字节边界

.global _vectors                                 // 导出 _vectors 符号
_vectors:
  .word STACK_TOP                                // 初始栈指针
  .word Reset_Handler + 1                        // 复位处理程序 (已置 Thumb 位)
```

### 段与对齐

```asm
.section .vectors, "ax"                          // 向量表段
.align 2                                         // 对齐到 4 字节边界
```

向量表放在自己的段 (`.vectors`) 里, 这样链接器就能精确地放置它. `"ax"` 标志表示可分配且可执行. `.align 2` 保证 4 字节对齐 (2^2 = 4), 这是必须的, 因为硬件按 32 位字读取这些内容.

链接脚本把这个段对齐到 128 字节, 并校验它落在 flash 的前 4 KB 之内:

```ld
.vectors ALIGN(128) : { KEEP(*(.vectors)) } > FLASH :text
ASSERT(((ADDR(.vectors) - ORIGIN(FLASH)) < 0x1000), ...)
```

### 向量表条目

```asm
_vectors:
  .word STACK_TOP                                // 初始栈指针
  .word Reset_Handler + 1                        // 复位处理程序 (已置 Thumb 位)
```

| 索引 | 内容 | 值 | 用途 |
|-------|---------|-------|---------|
| 0 | 初始 SP | `0x20082000` | 复位时装入 MSP |
| 1 | 复位处理程序 | `Reset_Handler + 1` | 要执行的第一条指令 |

**条目 0 - 初始栈指针:** 硬件在执行任何指令之前, 会把这个值装入主栈指针 (MSP). 这意味着从 Reset_Handler 的第一条指令开始, 栈就是可用的.

**条目 1 - 复位向量:** 硬件会把这个地址装入程序计数器 (PC). 那个 `+ 1` 把 bit 0 置位, 告诉处理器以 Thumb 模式执行. 如果没有这个 Thumb 位, 会立刻触发 HardFault.

### 为什么只有两个条目?

完整的 Cortex-M33 向量表最多可以有 496 个条目 (16 个系统异常 + 480 个外部中断). 我们的固件不使用中断, 所以只需要这两个强制条目. 只有当中断发生时, 硬件才会去读表里剩下的部分.

## stack.s - 完整源码

```asm
.syntax unified                                  // 使用统一汇编语法
.cpu cortex-m33                                  // 目标核心为 Cortex-M33
.thumb                                           // 使用 Thumb 指令集

.include "constants.s"

.section .text                                   // 代码段
.align 2                                         // 对齐到 4 字节边界

.global Init_Stack
.type Init_Stack, %function
Init_Stack:
  ldr   r0, =STACK_TOP                           // 加载栈顶
  msr   PSP, r0                                  // 设置 PSP
  ldr   r0, =STACK_LIMIT                         // 加载栈上限
  msr   MSPLIM, r0                               // 设置 MSP 上限
  msr   PSPLIM, r0                               // 设置 PSP 上限
  ldr   r0, =STACK_TOP                           // 重新加载栈顶
  msr   MSP, r0                                  // 设置 MSP
  bx    lr                                       // 返回
```

### 逐行讲解

**设置进程栈指针:**

```asm
  ldr   r0, =STACK_TOP                           // r0 = 0x20082000
  msr   PSP, r0                                  // PSP = 0x20082000
```

进程栈指针 (PSP) 在线程模式下使用, 前提是 CONTROL 寄存器被配置为使用进程栈. 我们的固件用的是 MSP, 但设置 PSP 能保证状态干净.

**设置栈上限:**

```asm
  ldr   r0, =STACK_LIMIT                         // r0 = 0x2007a000
  msr   MSPLIM, r0                               // MSPLIM = 0x2007a000
  msr   PSPLIM, r0                               // PSPLIM = 0x2007a000
```

栈上限寄存器是 ARMv8-M 的特性. 一旦 SP 掉到上限以下, 处理器就会产生 UsageFault. 这样可以防止栈静默覆盖低地址 SRAM 里的数据.

上限 `0x2007a000` 比 `STACK_TOP` (`0x20082000`) 低 32 KB, 也就是说我们有一个 32 KB 的栈.

**设置主栈指针:**

```asm
  ldr   r0, =STACK_TOP                           // r0 = 0x20082000
  msr   MSP, r0                                  // MSP = 0x20082000
```

硬件其实已经从向量表里装入了 MSP, 但我们还是再设一次, 以确保在经过调试探针操作或热复位之后, 状态仍然是已知的.

**返回:**

```asm
  bx    lr                                       // 返回 Reset_Handler
```

Init_Stack 是一个叶子函数 - 它不调用其他函数, 所以 LR 保持不变.

### 栈布局

```
RAM:
+----------------------------+ 0x20000000
| (available SRAM)           |
+----------------------------+
|                            |
| ...                        |
|                            |
+----------------------------+ 0x2007a000  ← STACK_LIMIT
| Stack (32 KB)              |
|   grows downward ↓         |
|                            |
+----------------------------+ 0x20082000  ← STACK_TOP (MSP/PSP initial)
```

## 引导流程

```
Power On / Reset
  |
  v
Hardware reads _vectors[0] → loads MSP = 0x20082000
Hardware reads _vectors[1] → loads PC = Reset_Handler
  |
  v
Reset_Handler executes
  |
  +→ bl Init_Stack
  |    Sets PSP, MSPLIM, PSPLIM, MSP
  |    Returns via bx lr
  v
  (continues initialization...)
```

## 小结

- vector_table.s 定义了向量表里两个强制条目: 初始栈指针和复位向量.
- Reset_Handler 后面的 `+ 1` 设置 Thumb 位, 这是 Cortex-M 执行所必需的.
- 链接器把向量表对齐到 128 字节, 并保证它落在 flash 的前 4 KB 内.
- stack.s 初始化 PSP, MSP, MSPLIM 和 PSPLIM, 在 SRAM 顶部划出 32 KB 的栈.
- 栈上限寄存器 (ARMv8-M 特性) 用 UsageFault 捕获栈溢出.
- 这两个文件一起保证处理器从第一条指令起就有可用的栈.
