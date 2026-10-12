# Chapter 18: RP2350 硬件架构

## 引言

RP2350 是 Raspberry Pi 推出的双核微控制器, 既能跑 ARM Cortex-M33 内核, 也能跑 RISC-V Hazard3 内核. 我们的闪烁驱动针对 ARM Cortex-M33 内核, 只用到芯片外设中的一小部分: 晶振 (XOSC), 时钟系统, 复位控制器, GPIO pad 与 IO bank, 以及 SIO 协处理器. 本章把固件接触到的硬件梳理一遍, 并解释那段让芯片从复位走到 LED 闪烁的初始化流程.

## RP2350 框图

```
+--------------------------------------------------+
|                      RP2350                      |
|                                                  |
|        +-------------+  +-------------+          |
|        | Cortex-M33  |  | Cortex-M33  |          |
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

## 内存映射

RP2350 使用统一的内存映射, 外设都通过固定地址访问:

| 地址范围 | 外设 | 我们的常量 |
|---------------|-----------|-------------|
| `0x10000000` - `0x11FFFFFF` | 外部 Flash | - |
| `0x20000000` - `0x2007FFFF` | SRAM (512 KB) | STACK_TOP, STACK_LIMIT |
| `0x40010000` | 时钟控制器 | CLOCKS_BASE |
| `0x40020000` | 复位控制器 | RESETS_BASE |
| `0x40028000` | IO Bank 0 | IO_BANK0_BASE |
| `0x40038000` | Pads Bank 0 | PADS_BANK0_BASE |
| `0x40048000` | 晶振 | XOSC_BASE |
| `0xE0000000` | 私有外设总线 | PPB_BASE |

## 晶振 (XOSC)

RP2350 Pico 2 板子上有一颗 12 MHz 晶振. XOSC 外设负责驱动这颗晶振, 提供一个稳定的时钟基准.

### XOSC 寄存器

| 寄存器 | 偏移 | 用途 |
|----------|--------|---------|
| XOSC_CTRL | +0x00 | 控制: 使能与频率范围 |
| XOSC_STATUS | +0x04 | 状态: STABLE 位 (bit 31) |
| XOSC_STARTUP | +0x0C | 启动延时计数 |

### 初始化流程

1. 写入启动延时 (0x00C4 = 196 个周期 × 256, 在环形振荡器速度下约 4 ms)
2. 写入控制字 (0x00FABAA0 = ENABLE + 频率范围 1-15 MHz)
3. 轮询 STATUS 的 bit 31, 直到 STABLE = 1

## 时钟系统

时钟系统把时钟信号分发给所有外设. 我们的固件只配置了外设时钟 (CLK_PERI):

### CLK_PERI_CTRL 寄存器

| 位 | 字段 | 值 | 含义 |
|-----|-------|-------|---------|
| 11 | ENABLE | 1 | 使能外设时钟 |
| 7:5 | AUXSRC | 4 | 选择 XOSC 作为时钟源 |

这样配置之后, 所有外设 (包括 GPIO) 都跑在 12 MHz 的 XOSC 上. 处理器内核跑在片内环形振荡器上, 大约 14.5 MHz (这是复位后的默认状态), 这也是我们的延时标定取每毫秒 3600 次循环的原因.

## 复位控制器

复位控制器会让外设一直处于复位状态, 直到软件显式地把它们放开. 这样既能省电, 也能避免启动期间的 bus 冲突.

### 复位寄存器

| 寄存器 | 地址 | 用途 |
|----------|---------|---------|
| RESETS_RESET | BASE + 0x00 | 复位控制 (1 = 保持在复位状态) |
| RESETS_RESET_CLEAR | BASE + 0x3000 | 原子清除 (写 1 即释放) |
| RESETS_RESET_DONE | BASE + 0x08 | 状态 (1 = 复位完成) |

### 固件里的复位流程

我们把 IO_BANK0 从复位状态释放出来 (bit 6):

```
1. Read RESETS_RESET
2. Clear bit 6 (release IO_BANK0)
3. Write back
4. Poll RESETS_RESET_DONE bit 6 until set
```

这样 GPIO 控制寄存器才可用. 少了这一步, 任何对 IO_BANK0 的访问都只会读到 0.

## GPIO 架构

RP2350 有 48 个 GPIO 引脚. 每个引脚都有两个控制点:

### Pads Bank 0

pad 寄存器控制物理引脚上的电气特性:

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

要做输出, 我们就清掉 OD (允许输出), 置起 IE (使能输入 - 回读时需要), 再清掉 ISO (解除隔离).

### IO Bank 0

IO 控制寄存器决定由哪个内部外设来驱动这个引脚:

```
Bits [4:0]: FUNCSEL - Function Select
  0 = SPI
  1 = UART
  2 = I2C
  3 = PWM
  4 = SIO (Single-cycle IO) ← reserved for PIO
  5 = SIO ← our selection
  ...
  31 = NULL (disabled)
```

我们把 FUNCSEL 设成 5, 从而把 GPIO16 接到 SIO 块上.

### 经由协处理器的 SIO (单周期 IO)

一旦 FUNCSEL 把引脚路由到 SIO, 我们就可以通过协处理器 0 控制它:

```
mcrr p0, #4, Rn, Rv, c4   → Output Enable (Rv: 1=enable, 0=disable)
mcrr p0, #4, Rn, Rv, c0   → Output Value  (Rv: 1=high, 0=low)
```

其中 Rn 保存 GPIO 编号, Rv 保存数值. 这样得到的 GPIO 访问既快又确定.

## GPIO16 与 LED

在 Raspberry Pi Pico 2 上, GPIO16 并没有接到板载 LED (板载 LED 在 GPIO25 上). 我们的闪烁驱动是在 GPIO16 上外接一颗 LED, 并串一个限流电阻:

```
GPIO16 (Pin 21) ---[330 ohm]---[LED]--- GND (Pin 23)
```

当 GPIO16 被驱动到高电平 (3.3V) 时, 电流经过电阻和 LED 流向地, LED 点亮. 驱动到低电平 (0V) 时没有电流, LED 熄灭.

## 启动流程

上电之后, RP2350 按下面的顺序执行:

```
1. Boot ROM runs (internal to chip)
2. Boot ROM finds PICOBIN block in flash
3. Boot ROM validates image and jumps to Reset_Handler
4. Reset_Handler: Init_Stack
5. Reset_Handler: Init_XOSC (crystal oscillator)
6. Reset_Handler: Enable_XOSC_Peri_Clock (peripheral clock)
7. Reset_Handler: Init_Subsystem (release GPIO from reset)
8. Reset_Handler: Enable_Coprocessor (allow CP0 access)
9. Reset_Handler: branch to main
10. main: configure GPIO16, enter blink loop
```

每一步都建立在前一步之上 - 时钟必须先稳定才能配置外设, 外设必须先脱离复位才能访问它们的寄存器, 协处理器必须先使能才能使用 `mcrr`.

## 小结

- RP2350 的外设都内存映射在 `0x4xxx_xxxx` 范围内的固定地址上.
- XOSC 借助外部晶振提供稳定的 12 MHz 时钟.
- 时钟系统通过 CLK_PERI_CTRL 把 XOSC 接到各个外设.
- 复位控制器必须先释放外设, 它们才能使用.
- GPIO 引脚通过两套寄存器组配置: pads (电气特性) 与 IO (功能选择).
- SIO 协处理器 (CP0) 通过 `mcrr` 指令提供快速的 GPIO 置位/清除.
- 启动流程依次是: 引导 ROM → Reset_Handler → 初始化外设 → main → 闪烁循环.
