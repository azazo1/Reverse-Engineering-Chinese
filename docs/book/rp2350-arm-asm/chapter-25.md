# Chapter 25: xosc.s - 晶振与时钟配置

## 引言

RP2350 上电后先跑在内部环形振荡器上, 频率约 14.5 MHz. 为了获得准确的定时和稳定的外设工作, 我们的固件会启动外部的 12 MHz 晶振 (XOSC), 并把它接到外设时钟上. xosc.s 里有两个函数: `Init_XOSC` 负责配置晶振并等待它稳定, `Enable_XOSC_Peri_Clock` 负责把它接到外设时钟域.

## 完整源码

```asm
.syntax unified                                  // 使用统一汇编语法
.cpu cortex-m33                                  // 目标核心为 Cortex-M33
.thumb                                           // 使用 Thumb 指令集

.include "constants.s"

.section .text                                   // 代码段
.align 2                                         // 对齐到 4 字节边界

.global Init_XOSC
.type Init_XOSC, %function
Init_XOSC:
  ldr   r0, =XOSC_STARTUP                        // 加载 XOSC_STARTUP 地址
  ldr   r1, =0x00c4                              // 设置延时 50,000 个周期
  str   r1, [r0]                                 // 把值写入 XOSC_STARTUP
  ldr   r0, =XOSC_CTRL                           // 加载 XOSC_CTRL 地址
  ldr   r1, =0x00FABAA0                          // 设置 1_15MHz, 频率范围, 实际 14.5MHz
  str   r1, [r0]                                 // 把值写入 XOSC_CTRL
.Init_XOSC_Wait:
  ldr   r0, =XOSC_STATUS                         // 加载 XOSC_STATUS 地址
  ldr   r1, [r0]                                 // 读取 XOSC_STATUS 的值
  tst   r1, #(1<<31)                             // 测试 STABLE 位
  beq   .Init_XOSC_Wait                          // 等待稳定位置位
  bx    lr                                       // 返回

.global Enable_XOSC_Peri_Clock
.type Enable_XOSC_Peri_Clock, %function
Enable_XOSC_Peri_Clock:
  ldr   r0, =CLK_PERI_CTRL                       // 加载 CLK_PERI_CTRL 地址
  ldr   r1, [r0]                                 // 读取 CLK_PERI_CTRL 的值
  orr   r1, r1, #(1<<11)                         // 置 ENABLE 位
  orr   r1, r1, #(4<<5)                          // 设置 AUXSRC: XOSC_CLKSRC 位
  str   r1, [r0]                                 // 把值写入 CLK_PERI_CTRL
  bx    lr                                       // 返回
```

## Init_XOSC - 逐行讲解

### 配置启动延时

```asm
  ldr   r0, =XOSC_STARTUP                        // r0 = 0x4004800C
  ldr   r1, =0x00c4                              // r1 = 196
  str   r1, [r0]                                 // XOSC_STARTUP = 196
```

XOSC_STARTUP 寄存器设定振荡器在宣告稳定之前必须运行的时钟周期数. 实际延时是:

```
delay = value × 256 = 196 × 256 = 50,176 cycles
```

在环形振荡器约 14.5 MHz 的频率下, 这大约是 3.5 ms - 足够 12 MHz 晶振稳定下来.

### 使能振荡器

```asm
  ldr   r0, =XOSC_CTRL                           // r0 = 0x40048000
  ldr   r1, =0x00FABAA0                          // r1 = 控制字
  str   r1, [r0]                                 // XOSC_CTRL = 0x00FABAA0
```

控制字 `0x00FABAA0` 编码了两个字段:

| 字段 | 位 | 值 | 含义 |
|-------|------|-------|---------|
| ENABLE | [23:12] | `0xFAB` | 使能振荡器 |
| FREQ_RANGE | [11:0] | `0xAA0` | 1-15 MHz 范围 |

ENABLE 字段用的是魔数值 (`0xFAB`), 而不是简单的一位 - 这是一种安全机制, 防止意外修改.

### 等待稳定

```asm
.Init_XOSC_Wait:
  ldr   r0, =XOSC_STATUS                         // r0 = 0x40048004
  ldr   r1, [r0]                                 // r1 = 当前状态
  tst   r1, #(1<<31)                             // 测试 bit 31 (STABLE)
  beq   .Init_XOSC_Wait                          // Z=1 表示尚未稳定
  bx    lr                                       // 已稳定 - 返回
```

这是一个轮询循环. `tst` 把状态寄存器与掩码 `(1<<31)` 做 AND. 如果 bit 31 是 0 (尚未稳定), 结果就是 0, Z=1, `beq` 就跳回去. 一旦晶振稳定, bit 31 变高, `tst` 的结果非零, Z=0, `beq` 不再跳转.

轮询循环的流程:

```
  +-->  ldr r1, [r0]       read status
  |     tst r1, #(1<<31)   check STABLE
  |     beq --------+
  |                 |
  +-----------------+      (loop while not stable)
        |
        v
  bx    lr                 (stable — return)
```

## Enable_XOSC_Peri_Clock - 逐行讲解

```asm
  ldr   r0, =CLK_PERI_CTRL                       // r0 = 0x40010048
  ldr   r1, [r0]                                 // 读取当前值
  orr   r1, r1, #(1<<11)                         // 置 ENABLE 位 (bit 11)
  orr   r1, r1, #(4<<5)                          // 设置 AUXSRC = 4 (bits [7:5])
  str   r1, [r0]                                 // 写回
  bx    lr                                       // 返回
```

### CLK_PERI_CTRL 寄存器

| 位 | 字段 | 设置值 | 含义 |
|--------|-------|-----------|---------|
| 11 | ENABLE | 1 | 使能外设时钟 |
| [7:5] | AUXSRC | 4 (`100`) | 选择 XOSC 作为时钟源 |

`orr r1, r1, #(4<<5)` 这个表达式把 4 左移 5 位, 得到 `0x80` (`0b10000000`). 于是 bits [7:5] 被设成二进制 `100`, 也就是 4, 选中 XOSC_CLKSRC.

可用的 AUXSRC 取值:

| 取值 | 时钟源 |
|-------|--------|
| 0 | CLK_SYS |
| 1 | PLL_SYS |
| 2 | PLL_USB |
| 3 | ROSC_CLKSRC_PH |
| 4 | XOSC_CLKSRC |
| 5 | GPIN0 |
| 6 | GPIN1 |

我们选 4 (XOSC), 因为刚刚才配置并稳定了晶振.

## 两个函数都是叶子函数

`Init_XOSC` 和 `Enable_XOSC_Peri_Clock` 都不调用其他函数. 它们不 push/pop 寄存器, 也不保存 LR. 它们只用 r0 和 r1, 而按 AAPCS 这两个都是调用者保存的临时寄存器 - 不需要额外保护.

## 配置之后的时钟域

```
               +--------+
  12 MHz       |        |    CLK_PERI
  Crystal ---->| XOSC   |--------------> Peripherals
               |        |                (GPIO, etc.)
               +--------+
                    |
                    +---> STABLE bit 31

  ~14.5 MHz    +--------+
  Ring Osc --->| ROSC   |--------------> CPU core
               +--------+                (default after reset)
```

CPU 核心仍然由环形振荡器驱动. 外设时钟现在来自 XOSC. 我们 delay.s 里的校准值 (每毫秒 3600 次循环) 就是按 CPU 所跑的约 14.5 MHz 环形振荡器速度算出来的.

## 小结

- `Init_XOSC` 配置启动延时, 使能晶振, 然后轮询直到它稳定.
- XOSC_CTRL 的使能字段使用魔数值 (`0xFAB`) 作为安全机制.
- `Enable_XOSC_Peri_Clock` 把 XOSC 的输出接到外设时钟域.
- 两者都是叶子函数, 只用临时寄存器 - 不需要栈帧.
- 这两个函数完成后, 外设就有了来自外部晶振的稳定 12 MHz 时钟.
