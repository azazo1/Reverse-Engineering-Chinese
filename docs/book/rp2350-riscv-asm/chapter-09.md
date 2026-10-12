# Chapter 9: RISC-V 算术与逻辑指令

## 引言

算术和逻辑指令构成了任何处理器的运算核心. 在 Hazard3 内核上, 这些指令只在寄存器上操作 - 从不直接操作内存 - 这与加载-存储的设计理念一致. 我们的闪烁驱动用算术指令做延时计时和地址计算, 用逻辑指令操作硬件寄存器的各个位. 本章考察固件里出现的每一条算术和逻辑指令.

## 算术指令

### `add` - 加法

```asm
  add   t0, t0, a0                               # t0 = t0 + a0
```

`add` 是 R-type 指令, 把两个源寄存器相加, 结果放进目标寄存器. 在 gpio.s 里, 它用来算出 pad 寄存器的地址:

```asm
  li    t0, PADS_BANK0_BASE                      # t0 = 0x40038000
  add   t0, t0, a0                               # t0 = 基地址 + PAD_OFFSET
```

GPIO_Config 就是这样找到 GPIO16 的 pad 控制寄存器的.

### `addi` - 加立即数

```asm
  addi  t1, t1, -1                               # t1 = t1 - 1
```

`addi` 把一个有符号 12 位立即数加到寄存器上. 它是 RISC-V 里最万能的指令之一, 因为减法不过就是加一个负的立即数. RISC-V 里没有单独的 "减立即数" 指令.

在 delay.s 里, `addi` 用来给循环计数器减一:

```asm
.Delay_MS_Loop:
  addi  t1, t1, -1                               # 计数器减一
  bnez  t1, .Delay_MS_Loop                       # 循环直到为零
```

在 gpio.s 里, `addi` 用来调整栈指针:

```asm
  addi  sp, sp, -4                               # 分配栈帧
  addi  sp, sp, 4                                # 释放栈帧
```

### `mul` - 乘法

```asm
  mul   t1, a0, t0                               # t1 = a0 * t0
```

`mul` 是来自 M 扩展的 R-type 指令. 在 delay.s 里, 它算出循环迭代的总次数:

```asm
  li    t0, 3600                                 # 每毫秒的循环数
  mul   t1, a0, t0                               # 总数 = 毫秒数 * 3600
```

在 12 MHz 的 XOSC 时钟下 (算上内部容差大约是 14.5 MHz), 3,600 次内层迭代大致相当于一毫秒.

## 逻辑指令

### `and` - 按位与

```asm
  and   t1, t1, t2                               # t1 = t1 & t2
```

`and` 是执行按位与的 R-type 指令. 在 gpio.s 里, 它用一个预先算好的掩码清除特定的位:

```asm
  li    t2, ~(1<<7)                              # 掩码 = 0xFFFFFF7F
  and   t1, t1, t2                               # 清除 OD 位 7
```

在 reset.s 里, 它清除 IO_BANK0 的复位位:

```asm
  li    t2, (1<<6)                               # IO_BANK0 复位掩码
  not   t2, t2                                   # 取反: 0xFFFFFFBF
  and   t1, t1, t2                               # 清除 IO_BANK0 位
```

### `andi` - 与立即数

```asm
  andi  t1, t1, (1<<6)                           # t1 = t1 & 0x40
```

`andi` 用一个经过符号扩展的 12 位立即数做按位与. 在 reset.s 里, 它检测 IO_BANK0 的复位是否完成:

```asm
  andi  t1, t1, (1<<6)                           # 测试 IO_BANK0 复位是否完成
  beqz  t1, .GPIO_Subsystem_Reset_Wait           # 等待直到完成
```

在 gpio.s 里, 它清除 FUNCSEL 字段:

```asm
  andi  t1, t1, ~0x1f                            # 清除 FUNCSEL [4:0]
```

这里 `~0x1f` = `0xFFFFFFE0`, 但因为 `andi` 会对 12 位立即数做符号扩展, 汇编器把它编码成 -32 (符号扩展后正是 0xFFFFFFE0).

### `or` - 按位或

```asm
  or    t1, t1, t2                               # t1 = t1 | t2
```

`or` 是用于置位的 R-type 指令. 在 xosc.s 里, 它使能外设时钟:

```asm
  li    t2, (1<<11)                              # ENABLE 位掩码
  or    t1, t1, t2                               # 置位 ENABLE 位
```

### `ori` - 或立即数

```asm
  ori   t1, t1, (1<<6)                           # 置位第 6 位
```

`ori` 用一个经过符号扩展的 12 位立即数做按位或. 在 gpio.s 里, 它置位输入使能位:

```asm
  ori   t1, t1, (1<<6)                           # 置位 IE 位
```

它还用来设置 FUNCSEL 的值:

```asm
  ori   t1, t1, 0x05                             # 设置 FUNCSEL = 5 (SIO)
```

在 xosc.s 里, 它设置 AUXSRC 的位:

```asm
  ori   t1, t1, 128                              # 设置 AUXSRC: XOSC_CLKSRC 位
```

### `not` - 按位取反 (伪指令)

```asm
  not   t2, t2                                   # t2 = ~t2
```

`not` 把所有位取反. 它是一条伪指令, 展开为 `xori rd, rs1, -1`:

```
not   t2, t2   =>   xori  t2, t2, -1
```

因为补码里的 -1 就是 0xFFFFFFFF, 与 -1 做 XOR 会把每一位都取反. 在 reset.s 里, 它用来生成清除掩码:

```asm
  li    t2, (1<<6)                               # IO_BANK0 复位掩码
  not   t2, t2                                   # 取反: 0xFFFFFFBF
  and   t1, t1, t2                               # 清除 IO_BANK0 位
```

### `sll` - 逻辑左移

```asm
  sll   t1, t1, a2                               # t1 = t1 << a2
```

`sll` 把源寄存器左移, 移位量来自第二个源寄存器. 在 gpio.s 里, 它生成一个正好落在 GPIO 位置上的单位掩码:

```asm
  li    t1, 1                                    # 位值
  sll   t1, t1, a2                               # 移到 GPIO 对应的位置
```

如果 `a2` = 16, 结果就是 `0x00010000` - 一个只有第 16 位置位的掩码. GPIO_OE_SET, GPIO_OUT_SET 和 GPIO_OUT_CLR 这些操作都用它.

## 没有条件标志位

和 ARM 不同 (ARM 用带 N, Z, C, V 标志的 APSR), RISC-V **没有条件标志寄存器**. 分支直接比较寄存器:

| ARM 写法 | RISC-V 写法 |
|-------------|----------------|
| `subs r5, r5, #1` 然后 `bne .Loop` | `addi t1, t1, -1` 然后 `bnez t1, .Loop` |
| `tst r1, #mask` 然后 `beq .Wait` | `andi t1, t1, mask` 然后 `beqz t1, .Wait` |
| `cmp r0, #0` 然后 `ble .Done` | `blez a0, .Done` |

这简化了硬件 - 没有标志寄存器要更新, 也没有经由标志位的依赖链 - 但代价是每次比较都必须把参与比较的寄存器写出来.

## 读-改-写模式

在整个固件里, 硬件寄存器的操作都遵循同一个模式:

```asm
  li    t0, PADS_BANK0_BASE                      # 计算地址
  add   t0, t0, a0                               # 加上偏移
  lw    t1, 0(t0)                                # READ 当前值
  li    t2, ~(1<<7)                              # 生成掩码
  and   t1, t1, t2                               # MODIFY: 清除位
  ori   t1, t1, (1<<6)                           # MODIFY: 置位
  sw    t1, 0(t0)                                # WRITE 写回
```

这个模式出现在 gpio.s (pad 配置, CTRL 寄存器), xosc.s (时钟使能) 和 reset.s (子系统复位) 里. 它会保留所有我们不打算改动的位.

## 小结

- 算术指令 (`add`, `addi`, `mul`) 负责地址计算, 延时循环和栈调整.
- 逻辑指令 (`and`, `andi`, `or`, `ori`, `not`, `sll`) 操作硬件寄存器里的单个位.
- RISC-V 没有条件标志位 - 分支直接比较寄存器值.
- 读-改-写模式 (li -> lw -> and/or -> sw) 是操作硬件寄存器最基础的惯用法.
