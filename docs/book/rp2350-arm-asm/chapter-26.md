# Chapter 26: reset.s - 把外设从复位中释放

## 引言

上电之后, RP2350 上的大多数外设都保持在复位状态, 以节省功耗并避免总线冲突. 在我们的固件能够配置 GPIO 寄存器之前, 必须显式地把 IO_BANK0 从复位中释放出来, 并等待释放完成. reset.s 里只有一个函数 `Init_Subsystem`, 它做的就是这件事.

## 完整源码

```asm
.syntax unified                                  // 使用统一汇编语法
.cpu cortex-m33                                  // 目标核心为 Cortex-M33
.thumb                                           // 使用 Thumb 指令集

.include "constants.s"

.section .text                                   // 代码段
.align 2                                         // 对齐到 4 字节边界

.global Init_Subsystem
.type Init_Subsystem, %function
Init_Subsystem:
.GPIO_Subsystem_Reset:
  ldr   r0, =RESETS_RESET                        // 加载 RESETS->RESET 地址
  ldr   r1, [r0]                                 // 读取 RESETS->RESET 的值
  bic   r1, r1, #(1<<6)                          // 清除 IO_BANK0 位
  str   r1, [r0]                                 // 把值写入 RESETS->RESET 地址
.GPIO_Subsystem_Reset_Wait:
  ldr   r0, =RESETS_RESET_DONE                   // 加载 RESETS->RESET_DONE 地址
  ldr   r1, [r0]                                 // 读取 RESETS->RESET_DONE 的值
  tst   r1, #(1<<6)                              // 测试 IO_BANK0 复位完成位
  beq   .GPIO_Subsystem_Reset_Wait               // 等待完成
  bx    lr                                       // 返回
```

## 逐行讲解

### 把 IO_BANK0 从复位中释放

```asm
  ldr   r0, =RESETS_RESET                        // r0 = 0x40020000
  ldr   r1, [r0]                                 // r1 = 当前复位寄存器的值
  bic   r1, r1, #(1<<6)                          // 清除 bit 6 (IO_BANK0)
  str   r1, [r0]                                 // 写回
```

RESETS_RESET 寄存器里每个外设占一位. 某一位是 1 时, 对应外设被保持在复位状态 (不工作). 把它清成 0, 该外设就开始执行复位释放流程.

bit 6 对应 IO_BANK0, 它控制 GPIO 的功能选择和配置寄存器.

这个读-改-写模式 (`ldr` → `bic` → `str`) 保留了其他所有位. 只有 IO_BANK0 被释放, 其余外设保持原状.

### 等待复位完成

```asm
  ldr   r0, =RESETS_RESET_DONE                   // r0 = 0x40020008
  ldr   r1, [r0]                                 // r1 = 当前完成状态
  tst   r1, #(1<<6)                              // 测试 IO_BANK0 完成位
  beq   .GPIO_Subsystem_Reset_Wait               // 未完成则继续循环
  bx    lr                                       // 已完成 - 返回
```

清除复位位只是启动释放流程, 它并不是瞬间完成的. 外设需要若干个时钟周期来初始化内部状态. RESETS_RESET_DONE 寄存器报告完成情况: 当 IO_BANK0 完全可用时, bit 6 变高.

轮询的写法与 XOSC 的稳定等待循环一模一样:

```
  +-->  ldr r1, [r0]       read RESET_DONE
  |     tst r1, #(1<<6)    check bit 6
  |     beq --------+
  |                 |
  +-----------------+      (loop while not done)
        |
        v
  bx    lr                 (done — return)
```

## 复位寄存器位图

RESETS_RESET 寄存器控制着许多外设. bit 6 是我们唯一用到的:

| 位 | 外设 | 我们的用法 |
|-----|-----------|-----------|
| 0 | ADC | 未使用 |
| 1 | BUSCTRL | 未使用 |
| 2 | DMA | 未使用 |
| 3 | HSTX | 未使用 |
| 4 | I2C0 | 未使用 |
| 5 | I2C1 | 未使用 |
| **6** | **IO_BANK0** | **已释放** |
| 7 | IO_QSPI | 未使用 |
| 8 | JTAG | 未使用 |
| 9 | PADS_BANK0 | 未使用 |
| 10 | PADS_QSPI | 未使用 |
| ... | ... | ... |

## 为什么必须等待

如果不轮询 RESET_DONE, 固件可能会在 IO_BANK0 还没初始化完时就去读 GPIO 寄存器. 后果是:

- 读回全零 (寄存器还没初始化)
- 写入被静默忽略
- GPIO 配置看起来成功了, 实际毫无效果

轮询循环保证在访问任何 GPIO 寄存器之前, IO_BANK0 已经完全可用.

## 函数特征

`Init_Subsystem` 是一个叶子函数:

- **没有函数调用** - 不使用 `bl`
- **没有栈帧** - 不 push/pop 寄存器
- **只用 r0, r1** - 两者都是临时寄存器 (调用者保存)
- **通过 `bx lr` 返回** - LR 保持不变

## 局部标号

这个函数用了两个局部标号:

| 标号 | 用途 |
|-------|---------|
| `.GPIO_Subsystem_Reset` | 标记复位释放代码 |
| `.GPIO_Subsystem_Reset_Wait` | 轮询循环的目标 |

它们都是文件内局部的 (以 `.` 开头), 起到文档锚点的作用.

## 小结

- `Init_Subsystem` 通过清除 RESETS_RESET 里的 bit 6, 把 IO_BANK0 从复位中释放.
- 然后它轮询 RESETS_RESET_DONE 的 bit 6, 直到释放完成.
- 这必须发生在任何 GPIO 寄存器访问之前 - 否则读回的都是零.
- 读-改-写模式保留了其他外设的复位状态.
- 这是一个只用临时寄存器的叶子函数, 不需要栈帧.
