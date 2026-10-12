# Chapter 27: GPIO 配置 - `gpio.s` 第 1 部分

## 简介

GPIO 配置是闪烁驱动里最复杂的函数. `GPIO_Config` 必须改动三块独立的硬件 - pad 控制, IO 功能选择, 以及 SIO 输出使能 - 才能把一个默认状态的引脚变成受驱动的输出. 本章逐条走一遍 `GPIO_Config` 的每条指令, 展示它如何配置电气属性, 选择 SIO 功能, 并使能输出驱动器.

## GPIO_Config 完整源码

```asm
.global GPIO_Config
.type GPIO_Config, @function
GPIO_Config:
  addi  sp, sp, -4                               # 分配栈帧
  sw    ra, 0(sp)                                # 保存返回地址
.GPIO_Config_Modify_Pad:
  li    t0, PADS_BANK0_BASE                      # 装入 PADS_BANK0_BASE 的地址
  add   t0, t0, a0                               # PADS_BANK0_BASE + PAD_OFFSET
  lw    t1, 0(t0)                                # 读出 pad 寄存器的值
  li    t2, ~(1<<7)                              # 用于清掉 OD 位的掩码
  and   t1, t1, t2                               # 清掉 OD 位
  ori   t1, t1, (1<<6)                           # 置上 IE 位
  li    t2, ~(1<<8)                              # 用于清掉 ISO 位的掩码
  and   t1, t1, t2                               # 清掉 ISO 位
  sw    t1, 0(t0)                                # 写回 pad 配置
.GPIO_Config_Modify_CTRL:
  li    t0, IO_BANK0_BASE                        # 装入 IO_BANK0 基地址
  add   t0, t0, a1                               # IO_BANK0_BASE + CTRL_OFFSET
  lw    t1, 0(t0)                                # 读出 CTRL 寄存器
  andi  t1, t1, ~0x1f                            # 清掉 FUNCSEL 字段
  ori   t1, t1, 0x05                             # 把 FUNCSEL 设为 SIO (5)
  sw    t1, 0(t0)                                # 写回 CTRL 配置
.GPIO_Config_Enable_OE:
  li    t0, SIO_GPIO_OE_SET                      # 装入 SIO GPIO_OE_SET 的地址
  li    t1, 1                                    # 位值
  sll   t1, t1, a2                               # 移到对应的 GPIO 位置
  sw    t1, 0(t0)                                # 使能该 GPIO 的输出
  lw    ra, 0(sp)                                # 恢复返回地址
  addi  sp, sp, 4                                # 释放栈帧
  ret                                            # 返回
```

## 参数

`GPIO_Config` 接收三个参数:

| 寄存器 | 参数 | GPIO16 对应的值 |
|----------|-----------|-------------------|
| `a0` | PAD_OFFSET | `0x44` (`PADS_BANK0_GPIO16_OFFSET`) |
| `a1` | CTRL_OFFSET | `0x84` (`IO_BANK0_GPIO16_CTRL_OFFSET`) |
| `a2` | GPIO 编号 | `16` |

用偏移量加 GPIO 编号作为参数, 这个函数就能复用到任意引脚上.

## 栈帧

### 序言

```asm
  addi  sp, sp, -4                               # 分配栈帧
  sw    ra, 0(sp)                                # 保存返回地址
```

`GPIO_Config` 是由 `main` 通过 `call GPIO_Config` 调用的. `call` 指令会把返回地址写进 `ra`. 但 `GPIO_Config` 自己也是被 `main` 调用的 (`main` 则是从 `Reset_Handler` 经 `j` 跳转过来的), 所以我们必须把 `ra` 保存到栈上.

虽然 `GPIO_Config` 在当前代码里并没有调用任何函数, 这个栈帧仍然遵循了非叶子函数的保守做法. 这个 4 字节的栈帧正好装一个 word - 保存下来的 `ra`.

```
Before:  sp → [...]
After:   sp → [saved ra]  ← sp decreased by 4
```

### 尾声

```asm
  lw    ra, 0(sp)                                # 恢复返回地址
  addi  sp, sp, 4                                # 释放栈帧
  ret                                            # 返回
```

尾声把序言反过来做一遍: 从栈上取回 `ra`, 恢复 `sp`, 然后返回.

## 阶段 1: Pad 配置

```asm
.GPIO_Config_Modify_Pad:
  li    t0, PADS_BANK0_BASE                      # 装入 PADS_BANK0_BASE 的地址
  add   t0, t0, a0                               # PADS_BANK0_BASE + PAD_OFFSET
  lw    t1, 0(t0)                                # 读出 pad 寄存器的值
```

`PADS_BANK0_BASE` + `a0` 算出该 GPIO 专属的 pad 寄存器地址. 对 GPIO16 来说: `0x40038000 + 0x44 = 0x40038044`.

### 清掉输出禁用 (OD)

```asm
  li    t2, ~(1<<7)                              # 用于清掉 OD 位的掩码
  and   t1, t1, t2                               # 清掉 OD 位
```

第 7 位是输出禁用 (Output Disable) 标志. 一旦置上, 不管其他设置如何, 这个 pad 的输出驱动器都会被关掉. 我们清掉它, 才能输出.

`~(1<<7)` = `0xFFFFFF7F` - 除了第 7 位, 其他位全是 1. `li` 伪指令负责装入这个 32 位常量.

### 置上输入使能 (IE)

```asm
  ori   t1, t1, (1<<6)                           # 置上 IE 位
```

第 6 位是输入使能 (Input Enable) 标志. 虽然我们配置的是输出, 但使能输入之后就能回读 GPIO 状态 - 调试时很有用. `(1<<6) = 64`, 落在 `ori` 的 12 位有符号立即数范围内.

### 清掉隔离 (ISO)

```asm
  li    t2, ~(1<<8)                              # 用于清掉 ISO 位的掩码
  and   t1, t1, t2                               # 清掉 ISO 位
```

第 8 位是隔离 (Isolation) 标志. 一旦置上, pad 就和内部逻辑电气隔离. 这是一个省电特性, 正常工作前必须清掉.

### 写回

```asm
  sw    t1, 0(t0)                                # 写回 pad 配置
```

修改后的值被写回 pad 寄存器.

### Pad 寄存器位图

| 位 | 名称 | 默认值 | 我们的设置 | 用途 |
|-----|------|---------|-------------|---------|
| 7 | OD | 0 | **0** (清掉) | 输出禁用 - 要输出就必须为 0 |
| 6 | IE | 1 | **1** (置上) | 输入使能 - 允许回读 |
| 8 | ISO | 1 | **0** (清掉) | 隔离 - 要工作就必须为 0 |

## 阶段 2: 功能选择

```asm
.GPIO_Config_Modify_CTRL:
  li    t0, IO_BANK0_BASE                        # 装入 IO_BANK0 基地址
  add   t0, t0, a1                               # IO_BANK0_BASE + CTRL_OFFSET
  lw    t1, 0(t0)                                # 读出 CTRL 寄存器
  andi  t1, t1, ~0x1f                            # 清掉 FUNCSEL 字段
  ori   t1, t1, 0x05                             # 把 FUNCSEL 设为 SIO (5)
  sw    t1, 0(t0)                                # 写回 CTRL 配置
```

### 地址计算

`IO_BANK0_BASE` + `a1` = 对 GPIO16 来说是 `0x40028000 + 0x84 = 0x40028084`.

### 清掉 FUNCSEL

```asm
  andi  t1, t1, ~0x1f                            # 清掉 FUNCSEL 字段
```

CTRL 寄存器的 [4:0] 位用来选择由哪个外设功能驱动这个引脚. `~0x1f = 0xFFFFFFE0` 把最低 5 位清掉.

### 设置 SIO 功能

```asm
  ori   t1, t1, 0x05                             # 把 FUNCSEL 设为 SIO (5)
```

FUNCSEL 值 5 选择 SIO (Single-cycle IO, 单周期 IO). 这把引脚接到 SIO 块上, 后者通过专用的置位/清零寄存器提供快速的 GPIO 输出.

### FUNCSEL 取值

| 值 | 功能 | 使用场景 |
|-------|----------|----------|
| 0 | JTAG | 调试 |
| 1 | SPI | 串行外设 |
| 2 | UART | 串口通信 |
| 3 | I2C | 总线通信 |
| 4 | PWM | 脉宽调制 |
| **5** | **SIO** | **通用 GPIO** |
| 7 | PIO0 | 可编程 IO |
| 31 | NULL | 禁用 |

## 阶段 3: 使能输出

```asm
.GPIO_Config_Enable_OE:
  li    t0, SIO_GPIO_OE_SET                      # 装入 SIO GPIO_OE_SET 的地址
  li    t1, 1                                    # 位值
  sll   t1, t1, a2                               # 移到对应的 GPIO 位置
  sw    t1, 0(t0)                                # 使能该 GPIO 的输出
```

### 动态位位置

```asm
  li    t1, 1                                    # 位值
  sll   t1, t1, a2                               # 移到对应的 GPIO 位置
```

`sll` (逻辑左移) 把值 1 左移 `a2` 位. 对 GPIO16 来说: `1 << 16 = 0x00010000`. 这样就得到一个只有目标 GPIO 位为 1 的位掩码.

### SIO 原子写

```asm
  sw    t1, 0(t0)                                # 使能该 GPIO 的输出
```

`SIO_GPIO_OE_SET` (`0xd0000038`) 是一个原子置位寄存器. 写入 `0x00010000` 会置上第 16 位 (从而打开 GPIO16 的输出驱动器), 同时不影响任何其他 GPIO 输出. 这里不需要读-改-写 - 原子性由 SIO 硬件保证.

### SIO 与 APB 的对比

| 特性 | APB (Pads, IO_BANK0) | SIO |
|---------|---------------------|-----|
| 访问方式 | 读-改-写 | 原子置位/清零 |
| 速度 | 多周期 (APB 总线) | 单周期 |
| 地址 | `0x4xxxxxxx` | `0xd0000000` |
| 竞态安全 | 需要手工保证 (必须先读) | 硬件原子 |

## 三块配置

```
GPIO_Config
  │
  ├── Phase 1: PADS_BANK0 (electrical)
  │     └── Clear OD, set IE, clear ISO
  │
  ├── Phase 2: IO_BANK0 (function)
  │     └── Set FUNCSEL = 5 (SIO)
  │
  └── Phase 3: SIO (output enable)
        └── Set OE bit for target GPIO
```

## 与 ARM 版 GPIO_Config 的对照

| 方面 | ARM | RISC-V |
|--------|-----|--------|
| Pad 配置 | 同样的寄存器, 同样的位 | 同样的寄存器, 同样的位 |
| FUNCSEL | 同样的寄存器, 同样的值 (5) | 同样的寄存器, 同样的值 (5) |
| 输出使能 | `mcrr p0` 协处理器指令 | 向 `SIO_GPIO_OE_SET` 内存地址 `sw` |
| 栈帧 | `push {lr}` / `pop {pc}` | `addi sp`/`sw ra` / `lw ra`/`addi sp` |

唯一的架构差异在输出使能这一步. 在 ARM 上, SIO 通过协处理器指令访问. 在 RISC-V 上, 同一套 SIO 硬件映射在 `0xd0000000`.

## 小结

- `GPIO_Config` 分三个阶段配置一个 GPIO 引脚: pad 控制, 功能选择, 输出使能.
- 栈帧保存 `ra`, 因为 `GPIO_Config` 是被 `main` 调用的.
- Pad 配置清掉 OD (第 7 位) 和 ISO (第 8 位), 置上 IE (第 6 位).
- 功能选择把 FUNCSEL 的 [4:0] 位设为 5 (SIO).
- 输出使能用 `sll` 生成动态位掩码, 再写进 `SIO_GPIO_OE_SET`.
- SIO 的原子寄存器省掉了输出使能这一步的读-改-写.
- 这个函数用偏移量作为参数, 因此可以复用到任意 GPIO 引脚.
