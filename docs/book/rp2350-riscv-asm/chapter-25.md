# Chapter 25: 振荡器初始化 - `xosc.s`

## 简介

RP2350 从内部环形振荡器启动, 它速度快但不精确. 为了让外设可靠工作, 我们切换到外部的 12 MHz 晶体振荡器 (XOSC). `xosc.s` 里包含两个函数: `Init_XOSC` 配置晶体并等待它稳定, `Enable_XOSC_Peri_Clock` 把稳定的时钟接到外设总线上. 本章把每条指令都拆开讲清楚.

## 完整源码

```asm
.include "constants.s"

.section .text                                   # 代码段
.align 2                                         # 对齐到 4 字节边界

.global Init_XOSC
.type Init_XOSC, @function
Init_XOSC:
  li    t0, XOSC_STARTUP                         # 装入 XOSC_STARTUP 的地址
  li    t1, 0x00c4                               # 把延时设为 50,000 个周期
  sw    t1, 0(t0)                                # 把值写进 XOSC_STARTUP
  li    t0, XOSC_CTRL                            # 装入 XOSC_CTRL 的地址
  li    t1, 0x00FABAA0                           # 设为 1_15MHz, 频率范围, 实际 14.5MHz
  sw    t1, 0(t0)                                # 把值写进 XOSC_CTRL
.Init_XOSC_Wait:
  li    t0, XOSC_STATUS                          # 装入 XOSC_STATUS 的地址
  lw    t1, 0(t0)                                # 读出 XOSC_STATUS 的值
  bgez  t1, .Init_XOSC_Wait                      # bit31 为 0 -> 还没稳定, 继续等
  ret                                            # 返回

.global Enable_XOSC_Peri_Clock
.type Enable_XOSC_Peri_Clock, @function
Enable_XOSC_Peri_Clock:
  li    t0, CLK_PERI_CTRL                        # 装入 CLK_PERI_CTRL 的地址
  lw    t1, 0(t0)                                # 读出 CLK_PERI_CTRL 的值
  li    t2, (1<<11)                              # ENABLE 位掩码
  or    t1, t1, t2                               # 置上 ENABLE 位
  ori   t1, t1, 128                              # 设置 AUXSRC: XOSC_CLKSRC 位
  sw    t1, 0(t0)                                # 把值写进 CLK_PERI_CTRL
  ret                                            # 返回
```

## Init_XOSC - 逐行讲解

### 第 1 步: 设置启动延时

```asm
  li    t0, XOSC_STARTUP                         # 装入 XOSC_STARTUP 的地址
  li    t1, 0x00c4                               # 把延时设为 50,000 个周期
  sw    t1, 0(t0)                                # 把值写进 XOSC_STARTUP
```

`XOSC_STARTUP` 位于 `0x4004800c`. 值 `0x00c4` (十进制 196) 用来编程启动延时计数器. 晶体需要时间才能以稳定的频率起振 - 这个寄存器告诉硬件, 在宣布振荡器稳定之前要等多少个参考时钟周期.

这个延时值与内部环形振荡器的频率有关. `0x00c4` 大约提供 50,000 个周期的建立时间, 对 Pico 2 板子上的 12 MHz 晶体来说足够了.

**指令套路**: `li` 把地址装入 `t0`, 然后 `sw` 通过这个指针写值. 这是 RISC-V 标准的内存写套路 - 每一次内存映射寄存器的写操作都遵循 `li address` → `li value` → `sw value, 0(address)`.

### 第 2 步: 配置并使能 XOSC

```asm
  li    t0, XOSC_CTRL                            # 装入 XOSC_CTRL 的地址
  li    t1, 0x00FABAA0                           # 设为 1_15MHz, 频率范围, 实际 14.5MHz
  sw    t1, 0(t0)                                # 把值写进 XOSC_CTRL
```

`XOSC_CTRL` 位于 `0x40048000`. 值 `0x00FABAA0` 编码了两个字段:

| 字段 | 位 | 值 | 含义 |
|-------|------|-------|---------|
| FREQ_RANGE | [11:0] | `0xAA0` | 1 - 15 MHz 晶振范围 |
| ENABLE | [23:12] | `0xFAB` | 魔数使能值 |

RP2350 要求这两个魔数必须完全正确 - 往 ENABLE 字段写任何别的值都不会激活振荡器. FREQ_RANGE 表明我们的晶体落在 1 - 15 MHz 这个频段 (我们的晶振是 12 MHz).

### 第 3 步: 等待稳定

```asm
.Init_XOSC_Wait:
  li    t0, XOSC_STATUS                          # 装入 XOSC_STATUS 的地址
  lw    t1, 0(t0)                                # 读出 XOSC_STATUS 的值
  bgez  t1, .Init_XOSC_Wait                      # bit31 为 0 -> 还没稳定, 继续等
  ret                                            # 返回
```

`XOSC_STATUS` 位于 `0x40048004`. 第 31 位是 STABLE 标志.

**`bgez` 的小技巧**: `bgez t1, .Init_XOSC_Wait` 在 `t1 ≥ 0` (按有符号解释) 时跳转. 在补码表示里, 第 31 位就是符号位:

| 第 31 位 | 有符号解释 | XOSC 状态 | `bgez` 结果 |
|--------|----------------------|------------|---------------|
| 0 | 非负 (≥ 0) | 未稳定 | 跳转 (继续等) |
| 1 | 负数 (< 0) | 已稳定 | 顺序执行 (结束) |

这比先装入掩码再用 `and`/`beqz` 测试要高效. 一条条件跳转就替代了两条指令.

### 寄存器使用

`Init_XOSC` 只用到 `t0` 和 `t1` - 两者都是调用者保存的临时寄存器. 它不碰 `sp`, 也不保存 `ra`, 因为它是一个叶子函数 (不调用任何其他函数).

## Enable_XOSC_Peri_Clock - 逐行讲解

### 第 1 步: 读出当前值

```asm
  li    t0, CLK_PERI_CTRL                        # 装入 CLK_PERI_CTRL 的地址
  lw    t1, 0(t0)                                # 读出 CLK_PERI_CTRL 的值
```

`CLK_PERI_CTRL` 位于 `0x40010048`. 我们先读出当前值, 因为我们要改的是特定的几位, 不能惊动其他位.

### 第 2 步: 置上 ENABLE 位

```asm
  li    t2, (1<<11)                              # ENABLE 位掩码
  or    t1, t1, t2                               # 置上 ENABLE 位
```

第 11 位是时钟 ENABLE 位. `or` 把它置成 1, 同时不影响任何其他位. 这里用 `li` + `or` 而不是 `ori`, 是因为立即数 `(1<<11) = 2048` 超出了 `ori` 的 12 位有符号范围 (-2048 到 2047).

### 第 3 步: 设置时钟源

```asm
  ori   t1, t1, 128                              # 设置 AUXSRC: XOSC_CLKSRC 位
```

`CLK_PERI_CTRL` 的 [7:5] 位用来选择辅助时钟源. 值 128 (`0x80`, 第 7 位) 选择 XOSC 作为时钟源. 由于 128 落在 12 位有符号立即数范围内, 这里可以直接用 `ori`.

### 第 4 步: 写回

```asm
  sw    t1, 0(t0)                                # 把值写进 CLK_PERI_CTRL
  ret                                            # 返回
```

修改后的值被写回 `CLK_PERI_CTRL`. 这个函数返回之后, APB 总线上的所有外设都由稳定的 12 MHz 晶体时钟驱动.

### 读-改-写套路

这个函数展示了 RISC-V 上 APB 寄存器的标准读-改-写套路:

```
li    t0, REGISTER_ADDRESS
lw    t1, 0(t0)                                  # READ
or/and/ori t1, ...                               # MODIFY
sw    t1, 0(t0)                                  # WRITE
```

和 SIO 块 (它有原子的置位/清零寄存器) 不同, APB 外设必须走这三步.

## 寄存器映射

### 用到的 XOSC 寄存器

| 寄存器 | 地址 | 修改的位 | 用途 |
|----------|---------|---------------|---------|
| `XOSC_STARTUP` | `0x4004800c` | [15:0] | 启动延时计数 |
| `XOSC_CTRL` | `0x40048000` | [23:0] | 使能 + 频率范围 |
| `XOSC_STATUS` | `0x40048004` | [31] (读) | 稳定标志 |

### 用到的时钟寄存器

| 寄存器 | 地址 | 修改的位 | 用途 |
|----------|---------|---------------|---------|
| `CLK_PERI_CTRL` | `0x40010048` | [11], [7] | 使能 + AUXSRC |

## 时序

`Init_XOSC_Wait` 循环大约要空转 50,000 个环形振荡器周期. 在环形振荡器默认的约 150 MHz 下, 这大约是 0.3 ms. 循环体是四条指令 (三次装入加一次跳转), 所以在 STABLE 位置起来之前, 它大约执行 12,500 次迭代.

## 与 ARM 的对照

| 方面 | ARM | RISC-V |
|--------|-----|--------|
| 寄存器访问 | 同样的地址 | 同样的地址 |
| 稳定性检查 | `tst` + 基于标志的跳转 | `bgez` (符号位技巧) |
| 读-改-写 | `ldr`/`orr`/`str` | `lw`/`or`/`sw` |
| 立即数限制 | 灵活的桶形移位器 | 12 位有符号 |
| 大立即数 | 带移位的 `orr` | `li` + `or` |

硬件寄存器是一样的 - 只有指令序列不同.

## 小结

- `Init_XOSC` 编程启动延时, 用魔数使能晶体, 然后轮询 `XOSC_STATUS` 的第 31 位.
- `bgez` 用一条指令高效地测试符号位, 从而检测 STABLE 标志.
- `Enable_XOSC_Peri_Clock` 用读-改-写序列使能外设时钟, 并选择 XOSC 作为时钟源.
- 第 11 位用 `or` (超出了 `ori` 的范围), 而第 7 位用 `ori` (在 12 位立即数范围内).
- 两个函数都完成之后, APB 总线和所有外设都由晶振提供的 12 MHz 时钟驱动.
- 两个函数都是叶子函数, 只使用临时寄存器 (`t0`, `t1`, `t2`).
