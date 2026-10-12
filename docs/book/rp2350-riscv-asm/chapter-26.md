# Chapter 26: 复位控制器 - `reset.s`

## 简介

RP2350 上的每个外设启动时都处于保持复位的状态. 在配置 GPIO 引脚之前, 必须先把 IO_BANK0 外设从复位中释放出来, 并给它时间完成初始化. `reset.s` 里包含 `Init_Subsystem`, 它清掉 IO_BANK0 的复位位, 然后轮询直到硬件确认释放完成.

## 完整源码

```asm
.include "constants.s"

.section .text                                   # 代码段
.align 2                                         # 对齐到 4 字节边界

.global Init_Subsystem
.type Init_Subsystem, @function
Init_Subsystem:
.GPIO_Subsystem_Reset:
  li    t0, RESETS_RESET                         # 装入 RESETS->RESET 的地址
  lw    t1, 0(t0)                                # 读出 RESETS->RESET 的值
  li    t2, (1<<6)                               # IO_BANK0 复位掩码
  not   t2, t2                                   # 掩码取反
  and   t1, t1, t2                               # 清掉 IO_BANK0 那一位
  sw    t1, 0(t0)                                # 把值写进 RESETS->RESET 地址
.GPIO_Subsystem_Reset_Wait:
  li    t0, RESETS_RESET_DONE                    # 装入 RESETS->RESET_DONE 的地址
  lw    t1, 0(t0)                                # 读出 RESETS->RESET_DONE 的值
  andi  t1, t1, (1<<6)                           # 测试 IO_BANK0 复位是否完成
  beqz  t1, .GPIO_Subsystem_Reset_Wait           # 一直等到完成
  ret                                            # 返回
```

## 复位控制器

RP2350 的复位控制器管理所有外设的复位状态. 每个外设占一位:

| 位 | 外设 |
|-----|-----------|
| 0 | ADC |
| 1 | BUSCTRL |
| 2 | DMA |
| 3 | HSTX |
| 4 | I2C0 |
| 5 | I2C1 |
| **6** | **IO_BANK0** |
| 7 | IO_QSPI |
| 8 | JTAG |
| ... | ... |

上电时, `RESETS_RESET` 里的所有位都是 `1`, 也就是说每个外设都被保持在复位状态. 要使用某个外设, 我们必须清掉它对应的那一位.

## 阶段 1: 从复位中释放

### 装入并读取

```asm
  li    t0, RESETS_RESET                         # 装入 RESETS->RESET 的地址
  lw    t1, 0(t0)                                # 读出 RESETS->RESET 的值
```

`RESETS_RESET` 位于 `0x40020000`. 我们读出当前值, 是因为我们只想改第 6 位 - 其他外设应该继续保持在复位状态.

### 构造取反后的掩码

```asm
  li    t2, (1<<6)                               # IO_BANK0 复位掩码
  not   t2, t2                                   # 掩码取反
```

`li t2, (1<<6)` 装入 `0x00000040` - 只在第 6 位上是 1.

`not t2, t2` 把所有位取反, 得到 `0xFFFFFFBF` - 除了第 6 位, 其他位全是 1.

这个两步套路是必需的, 因为 RISC-V 没有和 ARM `bic` 等价的 "位清零" 指令. 要清掉某一位, 我们必须:
1. 构造一个该位为 1 的掩码
2. 取反, 得到 "除了那一位全是 1" 的掩码
3. 和原值做 AND

### 清掉那一位

```asm
  and   t1, t1, t2                               # 清掉 IO_BANK0 那一位
  sw    t1, 0(t0)                                # 把值写进 RESETS->RESET 地址
```

`and t1, t1, t2` 清掉第 6 位, 同时保留其他所有位.

| 位 | `t1` (之前) | `t2` (掩码) | `t1` (之后) |
|-----|---------------|-------------|--------------|
| 5 | 1 | 1 | 1 (保留) |
| **6** | **1** | **0** | **0** (已清) |
| 7 | 1 | 1 | 1 (保留) |

`sw` 执行之后, 复位控制器就开始了 IO_BANK0 的释放流程. 硬件需要时间才能完成, 所以我们必须轮询.

## 阶段 2: 等待完成

```asm
.GPIO_Subsystem_Reset_Wait:
  li    t0, RESETS_RESET_DONE                    # 装入 RESETS->RESET_DONE 的地址
  lw    t1, 0(t0)                                # 读出 RESETS->RESET_DONE 的值
  andi  t1, t1, (1<<6)                           # 测试 IO_BANK0 复位是否完成
  beqz  t1, .GPIO_Subsystem_Reset_Wait           # 一直等到完成
  ret                                            # 返回
```

### 读取状态

`RESETS_RESET_DONE` 位于 `0x40020008`. 每一位都和 `RESETS_RESET` 里对应的位一一对应, 但它表示的是释放是否已经完成 (1 = 完成).

### 测试指定的位

```asm
  andi  t1, t1, (1<<6)                           # 测试 IO_BANK0 复位是否完成
```

`andi` 配合 `(1<<6) = 64` 把第 6 位单独挑出来. 结果要么是 `64` (该位为 1, 已完成), 要么是 `0` (该位为 0, 还在复位中).

注意 `(1<<6) = 64` 落在 `andi` 的 12 位有符号立即数范围内 (范围: -2048 到 2047), 所以可以直接用立即数形式.

### 为零则跳转

```asm
  beqz  t1, .GPIO_Subsystem_Reset_Wait           # 一直等到完成
```

`beqz` (等于零则跳转) 在复位还没完成时跳回去继续循环. 等第 6 位变成 `1`, 结果非零, 执行就顺序往下走到 `ret`.

### 轮询循环的结构

```
         ┌─────────────────────┐
         │ Load RESET_DONE     │
         │ Read register       │
         │ Test bit 6          │
         │ beqz → loop back    │──── bit 6 = 0 (not done)
         └──────────┬──────────┘
                    │ bit 6 = 1 (done)
                    ▼
                  ret
```

这和在 `Init_XOSC` 里用的轮询套路是一样的, 只不过这里测试的是某一个具体的位, 而不是用符号位技巧.

## 寄存器汇总

| 寄存器 | 地址 | 访问 | 用途 |
|----------|---------|--------|---------|
| `RESETS_RESET` | `0x40020000` | 读/写 | 外设复位控制 (1 = 保持复位) |
| `RESETS_RESET_DONE` | `0x40020008` | 读 | 释放状态 (1 = 完成) |
| `RESETS_RESET_CLEAR` | `0x40023000` | 写 | 原子清零别名 |

### 原子清零的替代方案

常量 `RESETS_RESET_CLEAR` (`0x40023000`) 提供了一个原子清零别名. 往这个地址写 `(1<<6)` 就能清掉第 6 位, 不需要先读. 不过我们的代码用的是显式的读-改-写方式, 因为它更有教学意义:

```asm
# 替代方案 (原子清零):
li    t0, RESETS_RESET_CLEAR
li    t1, (1<<6)
sw    t1, 0(t0)
```

两种做法结果一样. 原子别名更简单, 但它把读-改-写的机制藏起来了, 而那正是我们想讲的东西.

## 位清零套路

由于 RISC-V 缺少 ARM 的 `bic` (位清零) 指令, 清掉一位需要三条指令:

```asm
# ARM (一条指令):
bic   r1, r1, #(1<<6)

# RISC-V (三条指令):
li    t2, (1<<6)
not   t2, t2
and   t1, t1, t2
```

这是 RISC-V 裸机编程里很常见的套路. 只要需要清掉寄存器里某一位, 你就会见到它.

## 与 ARM 的对照

| 方面 | ARM | RISC-V |
|--------|-----|--------|
| 清位 | `bic r1, r1, #(1<<6)` | `li`+`not`+`and` (三条指令) |
| 测试位 | `tst r1, #(1<<6)` | `andi t1, t1, (1<<6)` |
| 跳转 | `beq .wait` (基于标志) | `beqz t1, .wait` (基于数值) |
| 寄存器地址 | 完全相同 | 完全相同 |
| 位的位置 | 完全相同 | 完全相同 |

硬件是一样的 - 复位控制器并不关心是哪个 CPU 在访问它. 不同的只有指令序列.

## 小结

- `Init_Subsystem` 通过清掉 `RESETS_RESET` 里的第 6 位, 把 IO_BANK0 从复位中释放出来.
- `li` → `not` → `and` 这个套路, 就是 RISC-V 里对应 ARM `bic` 指令的做法.
- 写完修改后的值之后, 函数会轮询 `RESETS_RESET_DONE` 的第 6 位, 直到硬件确认释放完成.
- `andi` + `beqz` 用来测试单独一位, 并在它仍为零时继续循环.
- 这个函数是叶子函数, 只使用临时寄存器.
- 这个函数返回之后, IO_BANK0 就处于活动状态, GPIO 引脚可以配置了.
