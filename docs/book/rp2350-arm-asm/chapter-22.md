# Chapter 22: constants.s - 内存地址与常量

## 引言

RP2350 上的每个外设都通过一个固定的内存地址访问. 我们不想把一堆魔数散落到各个源文件里, 而是用 `.equ` 指令把所有地址和常量集中到 constants.s. 其他每个源文件都包含这个文件, 于是整个固件有了单一的事实来源. 本章逐个剖析这些常量, 并说明它们各自对应硬件里的什么.

## 完整源码

```asm
.syntax unified                                  // 使用统一汇编语法
.cpu cortex-m33                                  // 目标核心为 Cortex-M33
.thumb                                           // 使用 Thumb 指令集

/**
 * 内存地址与常量.
 */
.equ STACK_TOP,                   0x20082000
.equ STACK_LIMIT,                 0x2007a000
.equ XOSC_BASE,                   0x40048000
.equ XOSC_CTRL,                   XOSC_BASE + 0x00
.equ XOSC_STATUS,                 XOSC_BASE + 0x04
.equ XOSC_STARTUP,                XOSC_BASE + 0x0c
.equ PPB_BASE,                    0xe0000000
.equ CPACR,                       PPB_BASE + 0x0ed88
.equ CLOCKS_BASE,                 0x40010000
.equ CLK_PERI_CTRL,               CLOCKS_BASE + 0x48
.equ RESETS_BASE,                 0x40020000
.equ RESETS_RESET,                RESETS_BASE + 0x0
.equ RESETS_RESET_CLEAR,          RESETS_BASE + 0x3000
.equ RESETS_RESET_DONE,           RESETS_BASE + 0x8
.equ IO_BANK0_BASE,               0x40028000
.equ IO_BANK0_GPIO16_CTRL_OFFSET, 0x84
.equ PADS_BANK0_BASE,             0x40038000
.equ PADS_BANK0_GPIO16_OFFSET,    0x44
```

## 前言部分

```asm
.syntax unified                                  // 使用统一汇编语法
.cpu cortex-m33                                  // 目标核心为 Cortex-M33
.thumb                                           // 使用 Thumb 指令集
```

每个 `.include` 了 constants.s 的源文件都会继承这些指令. 它们为汇编器确立了指令集的上下文.

## 栈常量

```asm
.equ STACK_TOP,                   0x20082000
.equ STACK_LIMIT,                 0x2007a000
```

| 常量 | 值 | 说明 |
|----------|-------|-------------|
| `STACK_TOP` | `0x20082000` | 栈顶 (最高地址) |
| `STACK_LIMIT` | `0x2007a000` | 栈底 (比栈顶低 32 KB) |

RP2350 上的 SRAM 从 `0x20000000` 延伸到 `0x20082000`. 栈占据最上面的 32 KB. 一旦 SP 掉到这个值以下, 栈上限寄存器就会触发一个 fault, 从而防止栈静默溢出.

## 晶振常量

```asm
.equ XOSC_BASE,                   0x40048000
.equ XOSC_CTRL,                   XOSC_BASE + 0x00
.equ XOSC_STATUS,                 XOSC_BASE + 0x04
.equ XOSC_STARTUP,                XOSC_BASE + 0x0c
```

| 常量 | 地址 | 说明 |
|----------|---------|-------------|
| `XOSC_BASE` | `0x40048000` | XOSC 外设基地址 |
| `XOSC_CTRL` | `0x40048000` | 控制寄存器 |
| `XOSC_STATUS` | `0x40048004` | 状态寄存器 (bit 31 = STABLE) |
| `XOSC_STARTUP` | `0x4004800C` | 启动延时寄存器 |

这些地址都来自 RP2350 数据手册. 汇编器在汇编阶段就算出了派生地址 (例如 `XOSC_BASE + 0x04` = `0x40048004`).

## 系统寄存器

```asm
.equ PPB_BASE,                    0xe0000000
.equ CPACR,                       PPB_BASE + 0x0ed88
```

| 常量 | 地址 | 说明 |
|----------|---------|-------------|
| `PPB_BASE` | `0xE0000000` | 私有外设总线基地址 |
| `CPACR` | `0xE000ED88` | 协处理器访问控制寄存器 |

PPB 区域存放 ARM 定义的系统寄存器. CPACR 控制固件可以访问哪些协处理器. 我们的固件把 bit [1:0] 置位, 从而启用 CP0 (SIO).

## 时钟常量

```asm
.equ CLOCKS_BASE,                 0x40010000
.equ CLK_PERI_CTRL,               CLOCKS_BASE + 0x48
```

| 常量 | 地址 | 说明 |
|----------|---------|-------------|
| `CLOCKS_BASE` | `0x40010000` | 时钟控制器基地址 |
| `CLK_PERI_CTRL` | `0x40010048` | 外设时钟控制 |

CLK_PERI_CTRL 选择外设的时钟源, 并打开时钟输出.

## 复位控制器常量

```asm
.equ RESETS_BASE,                 0x40020000
.equ RESETS_RESET,                RESETS_BASE + 0x0
.equ RESETS_RESET_CLEAR,          RESETS_BASE + 0x3000
.equ RESETS_RESET_DONE,           RESETS_BASE + 0x8
```

| 常量 | 地址 | 说明 |
|----------|---------|-------------|
| `RESETS_BASE` | `0x40020000` | 复位控制器基地址 |
| `RESETS_RESET` | `0x40020000` | 复位控制寄存器 |
| `RESETS_RESET_CLEAR` | `0x40023000` | 原子清零别名 |
| `RESETS_RESET_DONE` | `0x40020008` | 复位完成状态 |

这些寄存器里的 bit 6 对应 IO_BANK0 (GPIO 控制器). 把 RESETS_RESET 里的 bit 6 清零, 就把 GPIO 从复位中释放出来.

## GPIO 常量

```asm
.equ IO_BANK0_BASE,               0x40028000
.equ IO_BANK0_GPIO16_CTRL_OFFSET, 0x84
.equ PADS_BANK0_BASE,             0x40038000
.equ PADS_BANK0_GPIO16_OFFSET,    0x44
```

| 常量 | 值 | 说明 |
|----------|-------|-------------|
| `IO_BANK0_BASE` | `0x40028000` | IO 控制基地址 |
| `IO_BANK0_GPIO16_CTRL_OFFSET` | `0x84` | GPIO16 控制寄存器偏移 |
| `PADS_BANK0_BASE` | `0x40038000` | pad 控制基地址 |
| `PADS_BANK0_GPIO16_OFFSET` | `0x44` | GPIO16 pad 寄存器偏移 |

控制寄存器偏移 `0x84` 来自这个公式: 每个 GPIO 有一对 8 字节的寄存器 (status + ctrl), GPIO16 就落在偏移 `16 * 8 + 4 = 0x84` 处 (那个 +4 用来选中 ctrl 寄存器).

pad 偏移 `0x44` 则来自: 每个 GPIO 有一个 4 字节的 pad 寄存器, 从偏移 4 开始 (GPIO0 在 0x04), 所以 GPIO16 在 `4 + 16 * 4 = 0x44`.

## `.include` 是如何工作的

每个源文件都以这一行开头:

```asm
.include "constants.s"
```

汇编器会在那个位置把 constants.s 的全部内容原样插入进来. 这意味着每个文件都能访问所有常量, 而且没有运行时开销 - `.equ` 定义不会产生任何代码.

## 设计原则

把常量集中起来有三个好处:

1. **单一事实来源** - 在一个地方改地址, 所有文件都能看到更新
2. **可读性** - `ldr r0, =XOSC_BASE` 比 `ldr r0, =0x40048000` 更清楚
3. **正确性** - 派生地址 (基地址 + 偏移) 由汇编器计算, 消除了手工算错的可能

## 小结

- constants.s 定义了 19 个 `.equ` 常量, 覆盖栈, XOSC, 系统, 时钟, 复位和 GPIO 地址.
- 所有地址都直接来自 RP2350 数据手册.
- 派生地址使用汇编器算术 (例如 `XOSC_BASE + 0x04`).
- 每个源文件里的 `.include "constants.s"` 提供了通用访问, 且运行时开销为零.
- GPIO16 的偏移由 GPIO 编号按数据手册里的寄存器布局公式算出.
