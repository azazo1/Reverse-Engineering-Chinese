# Chapter 17: 位操作套路

## 引言

裸机固件说到底就是在控制硬件, 而控制硬件的方式, 就是对内存映射寄存器里一个个位做置位, 清零和测试. RP2350 上每个外设都是通过位域 - 一组有特定含义的位 - 来暴露功能的. 本章盘点闪烁驱动里用到的各种位操作套路, 帮你把这些写法读得顺, 写得熟.

## 三个基本操作

位操作只有三种原语:

| 操作 | 指令 | 写法 | 效果 |
|-----------|-------------|---------|--------|
| 置位 | `orr` | `orr Rd, Rd, #(1<<N)` | 把第 N 位强制成 1 |
| 清零 | `bic` | `bic Rd, Rd, #(1<<N)` | 把第 N 位强制成 0 |
| 测试 | `tst` | `tst Rn, #(1<<N)` | 第 N 位为 0 时置起 Z 标志 |

## 置单个位

要在不影响其他位的前提下把第 N 位置 1, 就和一个只有第 N 位为 1 的掩码做 OR:

```asm
  orr   r5, r5, #(1<<6)                          // 置 bit 6 (IE)
```

OR 的真值表:

```
  Original bit:  0  1  0  1
  Mask bit:      1  1  0  0
  Result:        1  1  0  1
```

掩码为 0 的位保持不变. 掩码为 1 的位被强制成 1.

### 在我们的固件里

gpio.s 把 pad 寄存器里的输入使能位置起来:

```asm
  orr   r5, r5, #(1<<6)                          // 置 IE (输入使能)
```

xosc.s 使能外设时钟:

```asm
  orr   r1, r1, #(1<<11)                         // 置 ENABLE 位
```

coprocessor.s 使能 CP0 访问:

```asm
  orr   r1, r1, #(1<<1)                          // 置 CP0 访问位 1
  orr   r1, r1, #(1<<0)                          // 置 CP0 访问位 0
```

## 清单个位

要在不影响其他位的前提下把第 N 位清 0, 就用掩码做 BIC (位清除):

```asm
  bic   r5, r5, #(1<<7)                          // 清 bit 7 (OD)
```

BIC 执行的是 `Rd = Rn AND NOT mask`:

```
  Original bit:  0  1  0  1
  NOT Mask:      0  0  1  1    (mask was 1  1  0  0)
  Result:        0  0  0  1
```

掩码为 0 的位保持不变. 掩码为 1 的位被强制成 0.

### 在我们的固件里

gpio.s 清掉 pad 寄存器里的输出禁止位和隔离位:

```asm
  bic   r5, r5, #(1<<7)                          // 清 OD (输出禁止)
  bic   r5, r5, #(1<<8)                          // 清 ISO (隔离)
```

## 清一个多位域

要清掉几个连续的位 (也就是一个 "域"), 用一个更宽的掩码:

```asm
  bic   r5, r5, #0x1f                            // 清 bits [4:0]
```

掩码 `0x1f` = `0b00011111`, 清掉最低的 5 位. gpio.s 在写入新值之前就是用它清掉 FUNCSEL 域的:

```asm
  bic   r5, r5, #0x1f                            // 清 FUNCSEL [4:0]
  orr   r5, r5, #0x05                            // 置 FUNCSEL = 5 (SIO)
```

这个"先清后置"的两步套路, 是写多位域又不影响周边位的标准做法.

## 测试某一位

要检查某一位是否置起, 同时不改动任何寄存器:

```asm
  tst   r1, #(1<<31)                             // 测试 STABLE 位
  beq   .Wait_XOSC                              // 该位为 0 就跳转
```

`tst` 做一次 `AND` 然后丢掉结果, 只更新标志:

- 如果 bit 31 是 0: 结果是 0, Z=1, `beq` 跳转
- 如果 bit 31 是 1: 结果非零, Z=0, `beq` 不跳转

### 轮询循环

两个硬件轮询循环用的都是 `tst` + `beq`:

**XOSC 稳定等待:**

```asm
.Wait_XOSC:
  ldr   r1, [r0]                                 // 读取 XOSC_STATUS
  tst   r1, #(1<<31)                             // STABLE 位?
  beq   .Wait_XOSC                              // 还没好 - 继续轮询
```

**复位完成等待:**

```asm
.Wait_Reset:
  ldr   r1, [r0]                                 // 读取 RESET_DONE
  tst   r1, #(1<<6)                              // IO_BANK0 完成了吗?
  beq   .Wait_Reset                             // 还没好 - 继续轮询
```

## 组合套路

### 读-改-写 (单个位)

```asm
  ldr   r1, [r0]                                 // READ
  orr   r1, r1, #(1<<11)                         // MODIFY: set bit
  str   r1, [r0]                                 // WRITE
```

### 读-改-写 (多个位)

```asm
  ldr   r5, [r3]                                 // READ
  bic   r5, r5, #(1<<7)                          // MODIFY: clear OD
  orr   r5, r5, #(1<<6)                          // MODIFY: set IE
  bic   r5, r5, #(1<<8)                          // MODIFY: clear ISO
  str   r5, [r3]                                 // WRITE
```

### 先清域再写值

```asm
  ldr   r5, [r6]                                 // READ
  bic   r5, r5, #0x1f                            // clear field [4:0]
  orr   r5, r5, #0x05                            // set value 5
  str   r5, [r6]                                 // WRITE
```

## 寄存器里的位域

### PADS_BANK0 pad 寄存器 (GPIO16)

```
Bit 8: ISO  (Isolation)         - clear to 0
Bit 7: OD   (Output Disable)    - clear to 0
Bit 6: IE   (Input Enable)      - set to 1
Bit 5: DRIVE[1]                  - unchanged
Bit 4: DRIVE[0]                  - unchanged
Bit 3: PUE  (Pull-Up Enable)    - unchanged
Bit 2: PDE  (Pull-Down Enable)  - unchanged
Bit 1: SCHMITT                   - unchanged
Bit 0: SLEWFAST                  - unchanged
```

### IO_BANK0 控制寄存器 (GPIO16)

```
Bits [4:0]: FUNCSEL - cleared to 0, then set to 5 (SIO)
```

### CPACR 协处理器访问

```
Bits [1:0]: CP0 access - set to 0b11 (full access)
```

### CLK_PERI_CTRL

```
Bit 11:    ENABLE   - set to 1
Bits [7:5]: AUXSRC  - set to 4 (XOSC)
```

## 为什么这很重要

弄懂位操作, 是裸机编程里最重要的一项技能. RP2350 上的每个外设 - GPIO, UART, SPI, I2C, 定时器, DMA - 都是靠读写内存映射寄存器里的位域来控制的. 本章讲的这些套路 (`orr` 置位, `bic` 清零, `tst` 测试, 写域时先清后置) 对芯片上每一个寄存器都适用.

## 小结

- `orr Rd, Rd, #(1<<N)` 置第 N 位: 最基本的使能操作.
- `bic Rd, Rd, #(1<<N)` 清第 N 位: 最基本的关闭操作.
- `tst Rn, #(1<<N)` 测试第 N 位: 所有轮询循环都要用.
- 多位域用"先清后置"的套路写入: 先用域掩码 `bic`, 再用数值 `orr`.
- 读-改-写套路 (ldr → 修改 → str) 能保住那些我们不想动的位.
- 这三个操作合起来, 就是控制硬件寄存器的全部词汇.
