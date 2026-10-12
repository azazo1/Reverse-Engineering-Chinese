# Chapter 22: 常量文件 - `constants.s`

## 简介

闪烁驱动里每一个内存映射寄存器地址和魔数, 都集中定义在一个地方: `constants.s`. 其他每个源文件都用 `.include "constants.s"` 把它包含进来, 从而拿到所有具名常量. 本章逐条走一遍每个 `.equ` 指令, 解释每个常量代表什么, 并说明这些常量如何对应到 RP2350 上的硬件寄存器.

## 完整源码

```asm
.equ STACK_TOP,                   0x20082000
.equ STACK_LIMIT,                 0x2007a000
.equ VECTOR_TABLE_BASE,           0x20000000
.equ XOSC_BASE,                   0x40048000
.equ XOSC_CTRL,                   XOSC_BASE + 0x00
.equ XOSC_STATUS,                 XOSC_BASE + 0x04
.equ XOSC_STARTUP,                XOSC_BASE + 0x0c
.equ PPB_BASE,                    0xe0000000
.equ MSTATUS_MIE,                 (1<<3)
.equ MTVEC_MODE_DIRECT,           0
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
.equ SIO_BASE,                    0xd0000000
.equ SIO_GPIO_OUT_SET,            SIO_BASE + 0x018
.equ SIO_GPIO_OUT_CLR,            SIO_BASE + 0x020
.equ SIO_GPIO_OE_SET,             SIO_BASE + 0x038
```

## `.equ` 的工作原理

```asm
.equ XOSC_BASE, 0x40048000
```

`.equ` 给一个名字赋予常量值. 汇编器在汇编期间把每一处 `XOSC_BASE` 替换成 `0x40048000`. 它不分配任何内存 - `.equ` 的值完全在汇编阶段解析完成. 这等价于 C 语言里的 `#define`.

表达式同样受支持:

```asm
.equ XOSC_CTRL, XOSC_BASE + 0x00
```

汇编器算出 `0x40048000 + 0x00 = 0x40048000`, 然后在所有出现 `XOSC_CTRL` 的地方代入这个值.

## 栈常量

```asm
.equ STACK_TOP,                   0x20082000
.equ STACK_LIMIT,                 0x2007a000
.equ VECTOR_TABLE_BASE,           0x20000000
```

| 常量 | 值 | 用途 |
|----------|-------|---------|
| `STACK_TOP` | `0x20082000` | 初始栈指针 (520 KB SRAM 的顶部) |
| `STACK_LIMIT` | `0x2007a000` | 栈溢出边界 (顶部往下 32 KB) |
| `VECTOR_TABLE_BASE` | `0x20000000` | SRAM 的基地址 (RISC-V 运行时用不到) |

栈从 `STACK_TOP` 向下生长. `STACK_TOP` 和 `STACK_LIMIT` 之间的 32 KB, 对我们这条调用链来说绰绰有余, 它从来不会超过几层栈帧.

## XOSC 常量

```asm
.equ XOSC_BASE,                   0x40048000
.equ XOSC_CTRL,                   XOSC_BASE + 0x00
.equ XOSC_STATUS,                 XOSC_BASE + 0x04
.equ XOSC_STARTUP,                XOSC_BASE + 0x0c
```

| 常量 | 值 | 用途 |
|----------|-------|---------|
| `XOSC_BASE` | `0x40048000` | 晶体振荡器外设基地址 |
| `XOSC_CTRL` | `0x40048000` | 控制寄存器 (频率范围 + 使能) |
| `XOSC_STATUS` | `0x40048004` | 状态寄存器 (第 31 位 = 稳定) |
| `XOSC_STARTUP` | `0x4004800c` | 启动延时计数 |

这些寄存器位于 APB 外设总线地址空间. XOSC 硬件靠外部晶振提供稳定的 12 MHz 时钟.

## RISC-V 专有常量

```asm
.equ PPB_BASE,                    0xe0000000
.equ MSTATUS_MIE,                 (1<<3)
.equ MTVEC_MODE_DIRECT,           0
```

| 常量 | 值 | 用途 |
|----------|-------|---------|
| `PPB_BASE` | `0xe0000000` | 私有外设总线基地址 (保留) |
| `MSTATUS_MIE` | `0x08` | mstatus CSR 里的机器模式中断使能位 |
| `MTVEC_MODE_DIRECT` | `0` | 陷阱向量的直接模式 |

这些常量和 RISC-V 特权架构有关. `MSTATUS_MIE` 和 `MTVEC_MODE_DIRECT` 只是出于完整性的考虑才定义 - 我们的陷阱处理程序直接用 `csrw mtvec` 安装陷阱向量.

## 时钟常量

```asm
.equ CLOCKS_BASE,                 0x40010000
.equ CLK_PERI_CTRL,               CLOCKS_BASE + 0x48
```

| 常量 | 值 | 用途 |
|----------|-------|---------|
| `CLOCKS_BASE` | `0x40010000` | 时钟控制器基地址 |
| `CLK_PERI_CTRL` | `0x40010048` | 外设时钟控制寄存器 |

外设时钟控制寄存器用来选择哪个时钟源驱动外设. 我们把它设成以 XOSC 作为时钟源.

## 复位常量

```asm
.equ RESETS_BASE,                 0x40020000
.equ RESETS_RESET,                RESETS_BASE + 0x0
.equ RESETS_RESET_CLEAR,          RESETS_BASE + 0x3000
.equ RESETS_RESET_DONE,           RESETS_BASE + 0x8
```

| 常量 | 值 | 用途 |
|----------|-------|---------|
| `RESETS_BASE` | `0x40020000` | 复位控制器基地址 |
| `RESETS_RESET` | `0x40020000` | 复位寄存器 (1 = 保持复位) |
| `RESETS_RESET_CLEAR` | `0x40023000` | 复位寄存器的原子清零别名 |
| `RESETS_RESET_DONE` | `0x40020008` | 复位完成状态 (1 = 已释放) |

每个外设在复位寄存器里都占一位. 要使用某个外设, 我们必须清掉它的复位位, 然后等 `RESET_DONE` 确认释放完成.

## GPIO 常量

```asm
.equ IO_BANK0_BASE,               0x40028000
.equ IO_BANK0_GPIO16_CTRL_OFFSET, 0x84
.equ PADS_BANK0_BASE,             0x40038000
.equ PADS_BANK0_GPIO16_OFFSET,    0x44
```

| 常量 | 值 | 用途 |
|----------|-------|---------|
| `IO_BANK0_BASE` | `0x40028000` | IO Bank 0 基地址 (功能选择) |
| `IO_BANK0_GPIO16_CTRL_OFFSET` | `0x84` | GPIO16 CTRL 寄存器偏移 |
| `PADS_BANK0_BASE` | `0x40038000` | Pads Bank 0 基地址 (电气配置) |
| `PADS_BANK0_GPIO16_OFFSET` | `0x44` | GPIO16 pad 寄存器偏移 |

GPIO 配置需要两组寄存器:

1. **PADS_BANK0**: 控制电气属性 (输出禁用, 输入使能, 隔离)
2. **IO_BANK0**: 控制功能选择 (由哪个外设驱动这个引脚)

每个 GPIO 引脚在 IO_BANK0 里有一个 CTRL 寄存器, 在 PADS_BANK0 里有一个 pad 寄存器, 两者都通过基地址加偏移来访问.

### 偏移量计算

对于 GPIO N:
- IO_BANK0 CTRL 偏移: `0x04 + (N * 0x08)` → GPIO16: `0x04 + (16 * 0x08) = 0x84`
- PADS_BANK0 偏移: `0x04 + (N * 0x04)` → GPIO16: `0x04 + (16 * 0x04) = 0x44`

## SIO 常量

```asm
.equ SIO_BASE,                    0xd0000000
.equ SIO_GPIO_OUT_SET,            SIO_BASE + 0x018
.equ SIO_GPIO_OUT_CLR,            SIO_BASE + 0x020
.equ SIO_GPIO_OE_SET,             SIO_BASE + 0x038
```

| 常量 | 值 | 用途 |
|----------|-------|---------|
| `SIO_BASE` | `0xd0000000` | 单周期 IO 块基地址 |
| `SIO_GPIO_OUT_SET` | `0xd0000018` | 原子置位 GPIO 输出 |
| `SIO_GPIO_OUT_CLR` | `0xd0000020` | 原子清零 GPIO 输出 |
| `SIO_GPIO_OE_SET` | `0xd0000038` | 原子置位 GPIO 输出使能 |

SIO 块提供对 GPIO 引脚的单周期访问. 在 ARM 上, SIO 通过协处理器指令 (`mcrr p0`) 访问. 在 RISC-V 上, 同一套硬件通过 `0xd0000000` 处的内存映射寄存器访问.

### 原子置位与清零寄存器

SIO 提供了专用的置位寄存器和清零寄存器. 向 `GPIO_OUT_SET` 的某一位写 `1` 会把对应引脚拉高. 向 `GPIO_OUT_CLR` 的某一位写 `1` 会把它拉低. 写成 `0` 的那些位不受影响. 这样就省掉了读-改-写序列, 也避免了竞态条件.

## 地址映射总览

| 基地址 | 外设 | 用到的常量 |
|-------------|-----------|----------------|
| `0x10000000` | Flash (XIP) | `image_def.s` 里的入口点 |
| `0x20000000` | SRAM | `STACK_TOP`, `STACK_LIMIT` |
| `0x40010000` | Clocks | `CLK_PERI_CTRL` |
| `0x40020000` | Resets | `RESETS_RESET`, `RESETS_RESET_DONE` |
| `0x40028000` | IO Bank 0 | `IO_BANK0_GPIO16_CTRL_OFFSET` |
| `0x40038000` | Pads Bank 0 | `PADS_BANK0_GPIO16_OFFSET` |
| `0x40048000` | XOSC | `XOSC_CTRL`, `XOSC_STATUS`, `XOSC_STARTUP` |
| `0xd0000000` | SIO | `SIO_GPIO_OUT_SET`, `SIO_GPIO_OUT_CLR`, `SIO_GPIO_OE_SET` |

## 为什么只用一个文件?

把所有常量集中到一个文件里有三个好处:

1. **单一事实来源**: 改一处寄存器地址, 所有地方都跟着更新.
2. **没有重复**: 每个 `.s` 文件都包含 `constants.s`, 而不是各自定义一份副本.
3. **代码可读**: `li t0, XOSC_CTRL` 本身就说明了意图, 而 `li t0, 0x40048000` 没有.

## 小结

- `constants.s` 定义了闪烁驱动里用到的每一个内存映射地址和魔数.
- `.equ` 创建的是汇编期常量, 不占内存.
- 常量按外设组织: 栈, XOSC, 时钟, 复位, GPIO (IO + pads), SIO.
- SIO 那组常量 (`SIO_BASE` 加偏移) 是 RISC-V 独有的 - ARM 改用协处理器指令.
- 其他每个源文件都用 `.include "constants.s"` 包含这个文件.
