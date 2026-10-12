# Chapter 28: GPIO 置位/清零, 延时与协处理器 - `gpio.s` 第 2 部分, `delay.s`, `coprocessor.s`

## 简介

GPIO 配置完成之后, 我们还需要三块积木: 把引脚拉高和拉低的函数, 一个控制闪烁速度的定时函数, 以及协处理器模块的兼容占位. 本章讲 `GPIO_Set`, `GPIO_Clear` (`gpio.s` 里剩下的两个函数), `delay.s` 的全部内容, 以及 `coprocessor.s`.

## GPIO_Set 完整源码

```asm
.global GPIO_Set
.type GPIO_Set, @function
GPIO_Set:
  li    t0, SIO_GPIO_OUT_SET                     # 装入 SIO GPIO_OUT_SET 的地址
  li    t1, 1                                    # 位值
  sll   t1, t1, a0                               # 移到对应的 GPIO 位置
  sw    t1, 0(t0)                                # 把 GPIO 输出拉高
  ret                                            # 返回
```

### 它是怎么工作的

`GPIO_Set` 通过 SIO 的原子置位寄存器把一个 GPIO 引脚拉高.

**第 1 步: 装入寄存器地址**
```asm
  li    t0, SIO_GPIO_OUT_SET                     # 装入 SIO GPIO_OUT_SET 的地址
```
`SIO_GPIO_OUT_SET` 位于 `0xd0000018`. 往这个寄存器某一位写 1, 就会把对应的 GPIO 输出拉高.

**第 2 步: 构造位掩码**
```asm
  li    t1, 1                                    # 位值
  sll   t1, t1, a0                               # 移到对应的 GPIO 位置
```
`a0` 里放的是 GPIO 编号 (我们的 LED 是 16). `sll` 把值 1 左移 16 位: `1 << 16 = 0x00010000`.

**第 3 步: 原子写**
```asm
  sw    t1, 0(t0)                                # 把 GPIO 输出拉高
  ret                                            # 返回
```
把 `0x00010000` 写进 `SIO_GPIO_OUT_SET` 就会把 GPIO16 拉高. 写 0 的那些位没有任何效果 - 其他引脚不受影响.

### 不需要读-改-写

`SIO_GPIO_OUT_SET` 寄存器是只写的, 而且是原子的. 和 APB 寄存器不同, 我们不需要先读出当前状态. 硬件会把我写入的位和现有的 GPIO 输出状态做 OR.

## GPIO_Clear 完整源码

```asm
.global GPIO_Clear
.type GPIO_Clear, @function
GPIO_Clear:
  li    t0, SIO_GPIO_OUT_CLR                     # 装入 SIO GPIO_OUT_CLR 的地址
  li    t1, 1                                    # 位值
  sll   t1, t1, a0                               # 移到对应的 GPIO 位置
  sw    t1, 0(t0)                                # 把 GPIO 输出拉低
  ret                                            # 返回
```

### 它是怎么工作的

`GPIO_Clear` 就是 `GPIO_Set` 的镜像. 唯一的不同是目标寄存器:

| 函数 | 寄存器 | 地址 | 效果 |
|----------|----------|---------|--------|
| `GPIO_Set` | `SIO_GPIO_OUT_SET` | `0xd0000018` | 把引脚拉高 |
| `GPIO_Clear` | `SIO_GPIO_OUT_CLR` | `0xd0000020` | 把引脚拉低 |

把 `0x00010000` 写进 `SIO_GPIO_OUT_CLR` 会清掉 GPIO16 的输出, 把引脚拉低.

### 与 ARM 的对比

在 ARM 上, `GPIO_Set` 和 `GPIO_Clear` 都用 `mcrr p0` 协处理器指令访问 SIO 块. 在 RISC-V 上, 同一套 SIO 硬件改用内存映射的存储指令访问 - 概念上更简单, 功能上完全等价.

## delay.s 完整源码

```asm
.include "constants.s"

.section .text                                   # 代码段
.align 2                                         # 对齐到 4 字节边界

.global Delay_MS
.type Delay_MS, @function
Delay_MS:
.Delay_MS_Check:
  blez  a0, .Delay_MS_Done                       # 如果毫秒数不合法, 直接返回
.Delay_MS_Setup:
  li    t0, 3600                                 # 基于 14.5MHz 时钟的每毫秒循环次数
  mul   t1, a0, t0                               # 毫秒数 * 3600
.Delay_MS_Loop:
  addi  t1, t1, -1                               # 计数器减一
  bnez  t1, .Delay_MS_Loop                       # 不为零就继续循环
.Delay_MS_Done:
  ret                                            # 返回
```

### 参数校验

```asm
.Delay_MS_Check:
  blez  a0, .Delay_MS_Done                       # 如果毫秒数不合法, 直接返回
```

`blez` (小于等于零则跳转) 用来挡住非法输入. 如果 `a0` 是零或者负数, 函数立刻返回. 这样就避免了 `mul` 算出一个零或者负的计数值, 否则循环会跑上几十亿次 (因为 `bnez` 判断的是非零, 而从零往下减会回绕到 `0xFFFFFFFF`).

### 延时计算

```asm
.Delay_MS_Setup:
  li    t0, 3600                                 # 基于 14.5MHz 时钟的每毫秒循环次数
  mul   t1, a0, t0                               # 毫秒数 * 3600
```

常量 `3600` 是按 XOSC 派生出来的时钟频率标定的. `Init_XOSC` 之后, CPU 大约运行在 14.5 MHz 的环形振荡器频率上 (XOSC 只是提供了参考, 此时系统时钟仍然来自环形振荡器).

每次循环迭代大约花 4 个周期 (`addi` 和 `bnez` 两条指令, 再加上流水线效应). 所以 3600 次迭代 × 约 4 个周期 ≈ 14,400 个周期 ≈ 14.5 MHz 下的 1 ms.

`mul t1, a0, t0` 把毫秒数乘以每毫秒的循环次数. 对 `a0 = 500` (我们闪烁的半周期) 来说: `500 × 3600 = 1,800,000` 次迭代.

能使用 `mul` 指令, 是因为我们的 `-march=rv32imac_zicsr` 目标里包含了 M (乘除) 扩展.

### 倒计时循环

```asm
.Delay_MS_Loop:
  addi  t1, t1, -1                               # 计数器减一
  bnez  t1, .Delay_MS_Loop                       # 不为零就继续循环
.Delay_MS_Done:
  ret                                            # 返回
```

这是能做到的最紧凑的循环了 - 只有两条指令:

1. `addi t1, t1, -1` - 计数器减 1
2. `bnez t1, .Delay_MS_Loop` - 不为零就跳回去

等 `t1` 减到零, `bnez` 就顺序往下走到 `ret`.

### 定时精度

这个延时是近似的. 影响精度的因素有:

| 因素 | 影响 |
|--------|--------|
| 时钟频率波动 | 环形振荡器有 ±10% 的偏差 |
| 流水线效应 | 分支预测会影响周期数 |
| 函数调用开销 | `call`/`ret` 会多花几个周期 |
| 中断 | 我们的系统里没有 (没使能) |

对于 LED 闪烁来说, 近似定时完全够用. 如果要精确定时, 就需要一个专门的定时器外设了.

### 与 ARM 版延时的对照

| 方面 | ARM | RISC-V |
|--------|-----|--------|
| 循环常量 | 2400 | 3600 |
| 乘法 | `mul r1, r0, r2` | `mul t1, a0, t0` |
| 减一 | `subs r1, r1, #1` | `addi t1, t1, -1` |
| 跳转 | `bne .loop` (基于标志) | `bnez t1, .loop` (基于数值) |
| 保护 | 相同 (`cmp`/`ble`) | `blez a0, .done` |

循环常量不同 (3600 对 2400), 反映的是 ARM 核心和 RISC-V 核心在时钟频率和指令时序上的差异.

## coprocessor.s 完整源码

```asm
.include "constants.s"

.section .text                                   # 代码段
.align 2                                         # 对齐到 4 字节边界

.global Enable_Coprocessor
.type Enable_Coprocessor , @function
Enable_Coprocessor:
  ret                                            # RISC-V 版本里是空操作
```

### 为什么是空操作?

在 ARM Cortex-M33 上, 访问协处理器 0 必须先写 CPACR (协处理器访问控制寄存器) 显式使能. 不然任何 `mcrr p0` 指令 (用于访问 SIO) 都会触发 UsageFault.

在 RISC-V 上根本没有协处理器. SIO 块通过 `0xd0000000` 处的内存映射寄存器访问 - 就是普通的 `lw`/`sw` 指令, 不需要任何特殊的权限设置.

这个函数作为兼容占位存在, 是为了让 `reset_handler.s` 能保持和 ARM 版本一样的调用序列. 它只有一条 `ret` 指令 - 零开销.

## 所有 GPIO 函数汇总

| 函数 | 参数 | 寄存器 | 动作 |
|----------|-----------|----------|--------|
| `GPIO_Config` | a0=pad, a1=ctrl, a2=pin | PADS + IO_BANK0 + SIO_OE_SET | 完整的引脚设置 |
| `GPIO_Set` | a0=引脚编号 | SIO_GPIO_OUT_SET | 拉高 |
| `GPIO_Clear` | a0=引脚编号 | SIO_GPIO_OUT_CLR | 拉低 |

## SIO 寄存器映射

```
SIO_BASE (0xd0000000)
  │
  ├── +0x018  GPIO_OUT_SET     GPIO_Set writes here
  ├── +0x020  GPIO_OUT_CLR     GPIO_Clear writes here
  └── +0x038  GPIO_OE_SET      GPIO_Config writes here
```

这三个 SIO 寄存器都是原子的 - 写入的 1 位只影响对应的 GPIO, 0 位则被忽略.

## 小结

- `GPIO_Set` 和 `GPIO_Clear` 是一对对称的函数, 通过 SIO 的原子寄存器把引脚拉高或拉低.
- 两者都用 `sll` 从 GPIO 编号参数生成动态位掩码.
- `Delay_MS` 提供按约 14.5 MHz 运行标定的近似毫秒延时.
- `blez` 挡住零或负的输入, 防止计数器回绕.
- `mul` (M 扩展) 用一条指令算出总的循环次数.
- 倒计时循环只有两条指令: `addi` + `bnez`, 已经是最紧凑的形式.
- `Enable_Coprocessor` 只有一条 `ret` - 一个为 ARM 兼容而存在空操作占位.
- 在 RISC-V 上, SIO 的访问用内存映射存储指令, 而不是协处理器指令.
