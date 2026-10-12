# Chapter 18: RP2350 - 架构与硬件

## 引言

RP2350 是 Raspberry Pi 出的双核单片机, 它的独特之处在于既能跑 ARM Cortex-M33 内核, 也能跑 RISC-V Hazard3 内核. 我们的闪烁驱动针对的是 **Hazard3 RISC-V 内核**, 用到了芯片外设中的一个子集: 晶振 (XOSC), 时钟系统, 复位控制器, GPIO pad, IO bank 以及 SIO 块. 本章把我们固件碰到的硬件梳理成图, 并解释那段把芯片从复位状态带到 LED 闪烁的初始化流程.

## RP2350 框图

```
+--------------------------------------------------+
|                      RP2350                      |
|                                                  |
|        +-------------+  +-------------+          |
|        |  Hazard3    |  |  Hazard3    |          |
|        | RISC-V      |  | RISC-V      |          |
|        |   Core 0    |  |   Core 1    |          |
|        +------+------+  +------+------+          |
|               |                |                 |
|               +-------+--------+                 |
|                       |                          |
|                +------+------+                   |
|                | Bus Fabric  |                   |
|                +------+------+                   |
|                       |                          |
|     +------+------+---+--+------+------+------+  |
|     |      |      |      |      |      |      |  |
|   FLASH  SRAM   XOSC  CLOCKS RESETS  GPIO    SIO |
|   32MB   512K                                    |
+--------------------------------------------------+
```

我们的固件完全跑在 Core 0 上. Core 1 保持在默认的复位状态.

## Hazard3 RISC-V 内核

Hazard3 是专为 RP2350 设计的紧凑型 RISC-V 内核:

| 特性 | 细节 |
|---------|--------|
| ISA | RV32IMAC_Zicsr |
| 流水线 | 多级, 顺序执行 |
| 字节序 | 小端 |
| 特权级 | 机器模式 (M-mode) |
| 压缩指令 | 支持 (C 扩展) |
| 乘除法 | 支持 (M 扩展) |
| 中断 | 通过 mtvec CSR (直接或向量模式) |

和 ARM Cortex-M33 相比, Hazard3 内核:

- 没有条件标志寄存器 - 分支直接比较寄存器
- 没有专门的 push/pop 指令 - 栈要手动管理
- 没有协处理器接口 - SIO 通过内存映射寄存器访问
- 用 CSR 指令做系统配置, 而不是 MSR/MRS
- 有 32 个整数寄存器 (x0-x31), 而不是 16 个

## 内存映射

RP2350 使用统一的内存映射, 外设都落在固定的地址上:

| 地址范围 | 外设 | 我们的常量 |
|---------------|-----------|-------------|
| `0x10000000` - `0x11FFFFFF` | 外部 Flash | - |
| `0x20000000` - `0x2007FFFF` | SRAM (512 KB) | STACK_TOP, STACK_LIMIT |
| `0x40010000` | 时钟控制器 | CLOCKS_BASE |
| `0x40020000` | 复位控制器 | RESETS_BASE |
| `0x40028000` | IO Bank 0 | IO_BANK0_BASE |
| `0x40038000` | Pads Bank 0 | PADS_BANK0_BASE |
| `0x40048000` | 晶振 | XOSC_BASE |
| `0xD0000000` | SIO (单周期 IO) | SIO_BASE |
| `0xE0000000` | 私有外设总线 | PPB_BASE |

## 晶振 (XOSC)

Raspberry Pi Pico 2 板子上有一颗 12 MHz 晶振. XOSC 外设负责驱动这颗晶振, 并提供一个稳定的时钟基准.

### XOSC 寄存器

| 寄存器 | 偏移 | 作用 |
|----------|--------|---------|
| XOSC_CTRL | +0x00 | 控制: 使能与频率范围 |
| XOSC_STATUS | +0x04 | 状态: STABLE 位 (第 31 位) |
| XOSC_STARTUP | +0x0C | 启动延时计数 |

### 初始化流程

1. 写入启动延时 (0x00C4 = 196 个周期 x 256 = 在环形振荡器速度下约 4 毫秒)
2. 写入控制字 (0x00FABAA0 = ENABLE + 频率范围 1-15 MHz)
3. 轮询 STATUS 的第 31 位, 直到 STABLE = 1

## 时钟系统

时钟系统把时钟信号分发给所有外设. 我们的固件只配置了外设时钟 (CLK_PERI):

### CLK_PERI_CTRL 寄存器

| 位 | 字段 | 值 | 含义 |
|-----|-------|-------|---------|
| 11 | ENABLE | 1 | 使能外设时钟 |
| 7:5 | AUXSRC | 4 | 选择 XOSC 作为时钟源 |

配置完成之后, GPIO 和其他外设就跑在 12 MHz 的 XOSC 上. 处理器内核跑在片上环形振荡器提供的约 14.5 MHz 上 (复位后的默认值), 这也是我们的延时校准按每毫秒 3,600 次循环来算的原因.

## 复位控制器

复位控制器会把外设按在复位状态, 直到软件显式释放它们. 这样做既省电, 也能避免启动期间的总线冲突.

### 复位寄存器

| 寄存器 | 地址 | 作用 |
|----------|---------|---------|
| RESETS_RESET | BASE + 0x00 | 复位控制 (1 = 保持在复位) |
| RESETS_RESET_CLEAR | BASE + 0x3000 | 原子清零 (写 1 表示释放) |
| RESETS_RESET_DONE | BASE + 0x08 | 状态 (1 = 复位完成) |

### 固件里的复位流程

我们把 IO_BANK0 从复位中释放出来 (第 6 位):

```
1. Read RESETS_RESET
2. Clear bit 6 (release IO_BANK0)
3. Write back
4. Poll RESETS_RESET_DONE bit 6 until set
```

这样就打开了 GPIO 控制寄存器. 没有这一步, 任何对 IO_BANK0 的访问都只会读出零.

## GPIO 架构

RP2350 有 48 个 GPIO 引脚. 每个引脚有两个控制点:

### Pads Bank 0

pad 寄存器控制物理引脚的电气特性:

```
+----------------------------------+
| Bit 8: ISO (Isolation)           |
| Bit 7: OD  (Output Disable)      |
| Bit 6: IE  (Input Enable)        |
| Bit 5-4: DRIVE (strength)        |
| Bit 3: PUE (Pull-Up Enable)      |
| Bit 2: PDE (Pull-Down Enable)    |
| Bit 1: SCHMITT (trigger)         |
| Bit 0: SLEWFAST                  |
+----------------------------------+
```

要做输出, 我们清掉 OD (允许输出), 置位 IE (使能输入 - 回读时需要), 并清掉 ISO (去掉隔离).

### IO Bank 0

IO 控制寄存器决定由哪个内部外设来驱动引脚:

```
Bits [4:0]: FUNCSEL - Function Select
  0 = SPI
  1 = UART
  2 = I2C
  3 = PWM
  5 = SIO (Single-cycle IO) ← our selection
  ...
  31 = NULL (disabled)
```

我们把 FUNCSEL 设为 5, 从而把 GPIO16 接到 SIO 块上.

### SIO (单周期 IO) - 在 RISC-V 上是内存映射的

在 RISC-V 上, SIO 块通过 `0xD0000000` 处的内存映射寄存器访问:

| 寄存器 | 地址 | 作用 |
|----------|---------|---------|
| GPIO_OUT_SET | SIO_BASE + 0x018 | 输出拉高 (写 1 位) |
| GPIO_OUT_CLR | SIO_BASE + 0x020 | 输出拉低 (写 1 位) |
| GPIO_OE_SET | SIO_BASE + 0x038 | 使能输出 (写 1 位) |

这些是**原子置位/清零寄存器**: 在第 N 位写一个 1, 只影响 GPIO N. 不需要读-改-写.

```asm
  li    t0, SIO_GPIO_OUT_SET                     # 0xD0000018
  li    t1, 1                                    # 位的值
  sll   t1, t1, a0                               # 移到对应 GPIO 的位置
  sw    t1, 0(t0)                                # 把 GPIO 拉高
```

这和 ARM 版本不同, ARM 那边用协处理器指令 (`mcrr p0`) 访问 SIO. 在 RISC-V 上, 同一条 `sw` 指令既管 APB 外设也管 SIO.

## GPIO16 与 LED

在 Raspberry Pi Pico 2 上, GPIO16 并没有接到板载 LED (板载 LED 在 GPIO25 上). 为了做闪烁驱动, 我们在 GPIO16 上外接一个串了限流电阻的 LED:

```
GPIO16 (Pin 21) ---[330 ohm]---[LED]--- GND (Pin 23)
```

GPIO16 拉高 (3.3V) 时, 电流经过电阻和 LED 流向地, LED 就亮了. 拉低 (0V) 时没有电流, LED 就灭了.

## 启动流程

上电之后, RP2350 会依次执行下面的流程:

```
1.  Boot ROM runs (internal to chip)
2.  Boot ROM finds PICOBIN block in flash
3.  PICOBIN indicates RISC-V architecture (0x1101)
4.  Boot ROM starts Hazard3 core and jumps to Reset_Handler
5.  Reset_Handler: Init_Stack (set SP)
6.  Reset_Handler: Init_Trap_Vector (set mtvec CSR)
7.  Reset_Handler: Init_XOSC (crystal oscillator)
8.  Reset_Handler: Enable_XOSC_Peri_Clock (peripheral clock)
9.  Reset_Handler: Init_Subsystem (release GPIO from reset)
10. Reset_Handler: Enable_Coprocessor (no-op on RISC-V)
11. Reset_Handler: j main
12. main: configure GPIO16, enter blink loop
```

每一步都建立在上一步之上 - 配置外设之前时钟必须先稳下来, 访问外设寄存器之前外设必须先脱离复位.

### ARM 与 RISC-V 的启动差异

| 方面 | ARM 启动 | RISC-V 启动 |
|--------|----------|-------------|
| PICOBIN 镜像类型 | `0x2101` (EXE + ARM + RP2350) | `0x1101` (EXE + RISCV + RP2350) |
| 栈初始化 | `msr MSP/PSP/MSPLIM/PSPLIM` | `li sp, STACK_TOP` |
| 陷阱/中断向量 | VTOR 寄存器 (内存映射) | `mtvec` CSR (`csrw`) |
| 协处理器 | 使能 CPACR 并用 `mcrr` 访问 SIO | 无需处理 (SIO 是内存映射的) |
| GPIO 控制 | `mcrr p0` 协处理器指令 | 用 `sw` 写 SIO 内存映射寄存器 |

## 小结

- RP2350 用的是 Hazard3 RISC-V 内核 (RV32IMAC_Zicsr), 有 32 个整数寄存器, 并且支持 CSR 访问.
- 外设都内存映射在 `0x4xxx_xxxx` 范围内的固定地址上; SIO 在 `0xD000_0000`.
- XOSC 借助外部晶振提供稳定的 12 MHz 时钟.
- 外设必须先由复位控制器释放, 才能拿来用.
- GPIO 引脚通过 pad 寄存器 (电气特性) 和 IO 控制寄存器 (功能选择) 来配置.
- SIO 提供原子的 GPIO 置位/清零寄存器 - 在 RISC-V 上通过内存映射的 `sw` 访问.
- 启动流程依次是: boot ROM → Reset_Handler → 初始化外设 → main → 闪烁循环.
- PICOBIN 块的镜像类型字段 (0x1101) 告诉 boot ROM 去启动 Hazard3 内核.
