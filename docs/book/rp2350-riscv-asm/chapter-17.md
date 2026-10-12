# Chapter 17: 内存映射 I/O

## 引言

在 RP2350 上, 每一个外设 - 振荡器, 复位控制器, GPIO pad, 时钟系统以及 SIO 块 - 都是靠读写特定的内存地址来控制的. 这里没有专门的 I/O 指令; 访问 RAM 用的 `lw` 和 `sw`, 同样也用来访问外设寄存器. 这就是**内存映射 I/O (memory-mapped I/O)**, 它是所有裸机编程的基础. 本章考察我们的固件是怎样用内存映射 I/O 来配置外设并驱动 GPIO 的.

## 内存映射

RP2350 的地址空间被划分成若干区域, 每个区域映射到不同的硬件:

```
+-------------------------------+
| 0x00000000 - 0x0FFFFFFF       |  Boot ROM
+-------------------------------+
| 0x10000000 - 0x11FFFFFF       |  External Flash (XIP)
+-------------------------------+
| 0x20000000 - 0x2007FFFF       |  SRAM (512 KB)
+-------------------------------+
| 0x40000000 - 0x4FFFFFFF       |  APB Peripherals
|   0x40010000  CLOCKS          |
|   0x40020000  RESETS          |
|   0x40028000  IO_BANK0        |
|   0x40038000  PADS_BANK0      |
|   0x40048000  XOSC            |
+-------------------------------+
| 0xD0000000 - 0xDFFFFFFF       |  SIO (Single-cycle IO)
+-------------------------------+
| 0xE0000000 - 0xE00FFFFF       |  PPB (Private Peripheral Bus)
+-------------------------------+
```

我们的固件访问六个外设块, 全部通过简单的 `lw`/`sw` 操作完成.

## 访问模式

每一次外设寄存器访问都遵循同一个模式:

```asm
  li    t0, REGISTER_ADDRESS                     # 第 1 步: 加载地址
  lw    t1, 0(t0)                                # 第 2 步: 读取当前值
  ...                                            # 第 3 步: 修改位
  sw    t1, 0(t0)                                # 第 4 步: 写回
```

这就是第 16 章讲过的读-改-写模式, 只不过用在了硬件寄存器上.

## 固件里的外设块

### XOSC (0x40048000)

晶振提供稳定的时钟. 这里访问了三个寄存器:

```asm
  li    t0, XOSC_STARTUP                         # 0x4004800C
  li    t1, 0x00c4                               # 启动延时
  sw    t1, 0(t0)                                # 只写: 设置延时

  li    t0, XOSC_CTRL                            # 0x40048000
  li    t1, 0x00FABAA0                           # 控制值
  sw    t1, 0(t0)                                # 只写: 使能 XOSC

  li    t0, XOSC_STATUS                          # 0x40048004
  lw    t1, 0(t0)                                # 只读: 轮询状态
  bgez  t1, .Init_XOSC_Wait                      # 检查第 31 位
```

注意: XOSC_STARTUP 和 XOSC_CTRL 是直接写入的 (没有读-改-写), 因为我们设置的是整个寄存器的值. XOSC_STATUS 则是只读的.

### CLOCKS (0x40010000)

时钟控制器把时钟分发给各个外设:

```asm
  li    t0, CLK_PERI_CTRL                        # 0x40010048
  lw    t1, 0(t0)                                # 读取当前值
  li    t2, (1<<11)                              # ENABLE 位
  or    t1, t1, t2                               # 置位 ENABLE
  ori   t1, t1, 128                              # 设置 AUXSRC = XOSC
  sw    t1, 0(t0)                                # 写回
```

这里必须用读-改-写, 因为 CLK_PERI_CTRL 里其他的位要保住.

### RESETS (0x40020000)

复位控制器会把外设按在复位状态, 直到被释放:

```asm
  li    t0, RESETS_RESET                         # 0x40020000
  lw    t1, 0(t0)                                # 读取当前复位状态
  li    t2, (1<<6)                               # IO_BANK0 掩码
  not   t2, t2                                   # 掩码取反
  and   t1, t1, t2                               # 清掉第 6 位
  sw    t1, 0(t0)                                # 释放 IO_BANK0
```

然后再轮询 RESETS_RESET_DONE:

```asm
  li    t0, RESETS_RESET_DONE                    # 0x40020008
  lw    t1, 0(t0)                                # 读取完成状态
  andi  t1, t1, (1<<6)                           # 测试 IO_BANK0
  beqz  t1, .GPIO_Subsystem_Reset_Wait           # 未完成就继续循环
```

### PADS_BANK0 (0x40038000)

pad 寄存器控制每个 GPIO 引脚的电气特性:

```asm
  li    t0, PADS_BANK0_BASE                      # 0x40038000
  add   t0, t0, a0                               # 加上 pad 偏移 (GPIO16 是 0x44)
  lw    t1, 0(t0)                                # 读取 pad 配置
  li    t2, ~(1<<7)                              # 清 OD
  and   t1, t1, t2                               # 修改
  ori   t1, t1, (1<<6)                           # 置位 IE
  li    t2, ~(1<<8)                              # 清 ISO
  and   t1, t1, t2                               # 修改
  sw    t1, 0(t0)                                # 写回
```

### IO_BANK0 (0x40028000)

IO 控制寄存器决定每个引脚由哪个内部外设来驱动:

```asm
  li    t0, IO_BANK0_BASE                        # 0x40028000
  add   t0, t0, a1                               # 加上 ctrl 偏移 (GPIO16 是 0x84)
  lw    t1, 0(t0)                                # 读取 CTRL 寄存器
  andi  t1, t1, ~0x1f                            # 清掉 FUNCSEL
  ori   t1, t1, 0x05                             # 设为 SIO (5)
  sw    t1, 0(t0)                                # 写回
```

### SIO (0xD0000000)

单周期 IO 块提供了对 GPIO 输出的快速访问. 和其他外设不同, SIO 用的是**原子置位/清零寄存器** - 往 GPIO_OUT_SET 写就是置位, 往 GPIO_OUT_CLR 写就是清零. 不需要读-改-写:

```asm
  li    t0, SIO_GPIO_OE_SET                      # 0xD0000038
  li    t1, 1                                    # 位的值
  sll   t1, t1, a2                               # 移到对应 GPIO 的位置
  sw    t1, 0(t0)                                # 使能输出 (只写)

  li    t0, SIO_GPIO_OUT_SET                     # 0xD0000018
  li    t1, 1                                    # 位的值
  sll   t1, t1, a0                               # 移到对应 GPIO 的位置
  sw    t1, 0(t0)                                # 输出拉高 (只写)

  li    t0, SIO_GPIO_OUT_CLR                     # 0xD0000020
  li    t1, 1                                    # 位的值
  sll   t1, t1, a0                               # 移到对应 GPIO 的位置
  sw    t1, 0(t0)                                # 输出拉低 (只写)
```

SIO 这种做法比读-改-写更简单也更快, 因为原子置位/清零是由硬件完成的.

## SIO 与 APB 外设对比

| 特性 | APB 外设 | SIO |
|---------|----------------|-----|
| 地址范围 | 0x4xxx_xxxx | 0xD000_0000 |
| 访问方式 | 读-改-写 | 原子置位/清零寄存器 |
| 总线 | APB (多周期) | 专用的单周期总线 |
| 操作 | 读写任意寄存器 | 置位/清零/翻转特定的位 |
| 速度 | 较慢 (总线仲裁) | 最快 (单周期) |

在 ARM 上, SIO 是通过协处理器指令 (`mcrr p0`) 访问的. 在 RISC-V 上, SIO 是内存映射的 - 同一条 `sw` 指令既访问 APB 寄存器也访问 SIO 寄存器, 只是硬件把 SIO 访问导到了一条更快的总线上.

## 为什么要用内存映射 I/O?

内存映射 I/O 的替代方案是独立的 I/O 指令 (比如 x86 的 `in`/`out`). 相比之下, 内存映射 I/O 有几个明显的好处:

1. **不需要特殊指令** - `lw`/`sw` 什么都能干
2. **统一的编程模型** - 内存和 I/O 用同一套工具, 同一套模式
3. **完整的地址空间** - 外设有自己的地址区间
4. **对 C 友好** - 指针解引用直接对应寄存器访问

## CSR 访问: 一个特例

Hazard3 内核的控制和状态寄存器 (CSR) **不是**内存映射的. 它们用专门的指令:

```asm
  csrw  mtvec, t0                                # 写机器陷阱向量 CSR
```

CSR 位于处理器内核内部, 不在任何总线上. `csrrw`/`csrrs`/`csrrc` 这一族指令为这些内部寄存器提供了原子的读-改-写访问.

我们的固件只访问一个 CSR: `mtvec` (机器陷阱向量基地址), 在 Init_Trap_Vector 里设置.

## 小结

- RP2350 上的每个外设都通过内存映射寄存器来访问, 用的就是 `lw`/`sw`.
- APB 外设 (XOSC, CLOCKS, RESETS, PADS, IO_BANK0) 位于 `0x4xxx_xxxx`, 使用读-改-写.
- `0xD000_0000` 处的 SIO GPIO 寄存器使用原子置位/清零 - 不需要读-改-写.
- 访问模式永远是: 加载地址 → 读 (如果需要) → 修改位 → 写回.
- CSR 是例外: 它们用专门的 `csrw`/`csrr` 指令, 不走内存映射访问.
- 内存映射 I/O 意味着同一条 `lw`/`sw` 指令既能操作数据, 也能控制硬件.
