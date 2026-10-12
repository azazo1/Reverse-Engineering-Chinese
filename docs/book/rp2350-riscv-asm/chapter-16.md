# Chapter 16: 硬件编程中的位操作

## 引言

裸机固件说到底就是在控制硬件, 而控制硬件的方式就是设置, 清除和测试内存映射寄存器里的某一位. RP2350 上的每个外设都通过位字段来暴露自己的功能 - 位字段就是一组有特定含义的位. 本章逐一列出闪烁驱动里用到的位操作模式, 帮你练到能熟练读写它们.

## 基本操作

固件里有四种基本的位操作:

| 操作 | 指令 | 模式 | 效果 |
|-----------|-------------|---------|--------|
| 置位 | `ori` | `ori rd, rs, (1<<N)` | 把第 N 位强制设为 1 |
| 清零 | `and` + 掩码 | 先 `li mask, ~(1<<N)`, 再 `and rd, rs, mask` | 把第 N 位强制设为 0 |
| 测试 | `andi` | `andi rd, rs, (1<<N)` | 把第 N 位单独取出来 (结果为 0 或非零) |
| 取反 | `not` | `not rd, rs` | 把所有位翻转 |

## 给单独一位置位

要在不影响其他位的前提下把第 N 位置位, 就与一个只有第 N 位为 1 的掩码做 OR:

```asm
  ori   t1, t1, (1<<6)                           # 置位第 6 位 (IE)
```

OR 的真值表:

```
  Original bit:  0  1  0  1
  Mask bit:      1  1  0  0
  Result:        1  1  0  1
```

掩码为 0 的那些位保持不变. 掩码为 1 的那些位被强制设为 1.

### 在固件里

gpio.s 给 pad 寄存器置位 Input Enable:

```asm
  ori   t1, t1, (1<<6)                           # 置位 IE (输入使能)
```

gpio.s 设置 FUNCSEL 的值:

```asm
  ori   t1, t1, 0x05                             # 置位 FUNCSEL = 5 (SIO)
```

xosc.s 使能外设时钟的 AUXSRC:

```asm
  ori   t1, t1, 128                              # 置位 AUXSRC: XOSC_CLKSRC 位
```

### 掩码较大时用 `or`

当掩码超出 `ori` 的 12 位立即数范围时, 改用寄存器版的 `or`:

```asm
  li    t2, (1<<11)                              # ENABLE 位掩码
  or    t1, t1, t2                               # 置位 ENABLE 位
```

这两条指令的组合可以应付任意位的位置.

## 给单独一位清零

RISC-V 没有 ARM 那样的 `bic` (位清零) 指令. 我们的做法是先造一个取反的掩码, 再做 AND:

```asm
  li    t2, ~(1<<7)                              # 掩码 = 0xFFFFFF7F
  and   t1, t1, t2                               # 清掉 OD 第 7 位
```

AND 的真值表:

```
  Original bit:  0  1  0  1
  Mask bit:      0  0  1  1
  Result:        0  0  0  1
```

掩码为 1 的那些位保持不变. 掩码为 0 的那些位被强制设为 0.

### 在固件里

gpio.s 清掉 pad 寄存器里的 Output Disable 和 Isolation:

```asm
  li    t2, ~(1<<7)                              # 用于清 OD 位的掩码
  and   t1, t1, t2                               # 清掉 OD 位
  li    t2, ~(1<<8)                              # 用于清 ISO 位的掩码
  and   t1, t1, t2                               # 清掉 ISO 位
```

reset.s 清掉 IO_BANK0 的复位位:

```asm
  li    t2, (1<<6)                               # IO_BANK0 复位掩码
  not   t2, t2                                   # 取反: 0xFFFFFFBF
  and   t1, t1, t2                               # 清掉 IO_BANK0 那一位
```

`not` 加 `and` 这个组合, 效果等同于 ARM 的 `bic`.

## 清掉一个多位字段

要清掉连续的若干位 (也就是一个 "字段"), 用带掩码的 `andi`:

```asm
  andi  t1, t1, ~0x1f                            # 清掉 [4:0] 位
```

掩码 `~0x1f` = `0xFFFFFFE0`, 它把最低 5 位清掉. 由于 `andi` 会对 12 位立即数做符号扩展, 汇编器把它编码成 -32 (符号扩展后正好是 0xFFFFFFE0).

gpio.s 在写入新值之前, 就用它清掉 FUNCSEL 字段:

```asm
  andi  t1, t1, ~0x1f                            # 清掉 FUNCSEL [4:0]
  ori   t1, t1, 0x05                             # 置位 FUNCSEL = 5 (SIO)
```

这个先清后设的两步模式, 是写多位字段而不影响周围位的标准做法.

## 测试某一位

要检查某一位是否置位, 就与掩码做 AND, 然后根据结果分支:

```asm
  andi  t1, t1, (1<<6)                           # 取出第 6 位
  beqz  t1, .GPIO_Subsystem_Reset_Wait           # 该位为 0 就跳转
```

ARM 有 `tst`, 它只设置标志位而不保存结果; RISC-V 不一样, `andi` 会把结果存进目标寄存器. 然后我们根据结果是否为零来分支.

### 轮询循环

两个硬件轮询循环都用 `andi` 配 `beqz` 或 `bgez`:

**XOSC 稳定等待 (xosc.s):**

```asm
.Init_XOSC_Wait:
  li    t0, XOSC_STATUS                          # 加载 XOSC_STATUS 地址
  lw    t1, 0(t0)                                # 读取 XOSC_STATUS 的值
  bgez  t1, .Init_XOSC_Wait                      # 第 31 位为 0, 说明还没稳定
```

这里借用了有符号解释: 如果第 31 位为 0, 这个值就大于等于 0.

**复位完成等待 (reset.s):**

```asm
.GPIO_Subsystem_Reset_Wait:
  li    t0, RESETS_RESET_DONE                    # 加载 RESETS->RESET_DONE 地址
  lw    t1, 0(t0)                                # 读取 RESETS->RESET_DONE 的值
  andi  t1, t1, (1<<6)                           # 测试 IO_BANK0 复位是否完成
  beqz  t1, .GPIO_Subsystem_Reset_Wait           # 一直等到完成为止
```

## 用左移处理动态位的位置

当位的位置放在寄存器里 (汇编时还不知道具体是第几位) 时, 用 `sll`:

```asm
  li    t1, 1                                    # 位的值
  sll   t1, t1, a2                               # 移到对应 GPIO 的位置
  sw    t1, 0(t0)                                # 写入 SIO 寄存器
```

如果 `a2` = 16, 结果就是 `0x00010000` - 一个只有第 16 位为 1 的掩码. 这个模式在 GPIO_Config, GPIO_Set 和 GPIO_Clear 里都出现过.

## 组合起来的模式

### 读-改-写 (单位)

```asm
  li    t0, CLK_PERI_CTRL                        # 计算地址
  lw    t1, 0(t0)                                # READ
  li    t2, (1<<11)                              # ENABLE 位掩码
  or    t1, t1, t2                               # MODIFY: 置位
  sw    t1, 0(t0)                                # WRITE
```

### 读-改-写 (多位)

```asm
  lw    t1, 0(t0)                                # READ
  li    t2, ~(1<<7)                              # OD 的掩码
  and   t1, t1, t2                               # MODIFY: 清掉 OD
  ori   t1, t1, (1<<6)                           # MODIFY: 置位 IE
  li    t2, ~(1<<8)                              # ISO 的掩码
  and   t1, t1, t2                               # MODIFY: 清掉 ISO
  sw    t1, 0(t0)                                # WRITE
```

### 先清字段再设值

```asm
  lw    t1, 0(t0)                                # READ
  andi  t1, t1, ~0x1f                            # 清掉 [4:0] 字段
  ori   t1, t1, 0x05                             # 设为值 5
  sw    t1, 0(t0)                                # WRITE
```

## 寄存器里的位字段

### PADS_BANK0 Pad 寄存器 (GPIO16)

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

### CLK_PERI_CTRL

```
Bit 11:    ENABLE   - set to 1
Bits [7:5]: AUXSRC  - set to 4 (XOSC), we write 128 to bit 7
```

### SIO GPIO 寄存器

SIO 的 GPIO_OE_SET, GPIO_OUT_SET 和 GPIO_OUT_CLR 寄存器使用**原子置位/清零语义**: 往这些寄存器写一个 1 位, 就会置位或清零对应的 GPIO 输出位或使能位. 不需要读-改-写 - 一条带位掩码的 `sw` 就够了.

## 与 ARM 对照

| 操作 | ARM | RISC-V |
|-----------|-----|--------|
| 置位 | `orr r, r, #(1<<N)` | `ori r, r, (1<<N)` 或 `or r, r, mask` |
| 清零 | `bic r, r, #(1<<N)` | `li mask, ~(1<<N)` + `and r, r, mask` |
| 测试位 | `tst r, #(1<<N)` + `beq` | `andi r, r, (1<<N)` + `beqz` |
| 清字段 | `bic r, r, #0x1f` | `andi r, r, ~0x1f` |

ARM 的 `bic` 一条指令就能清位. RISC-V 需要两条指令 (`li` 造掩码, 再 `and`), 但这个模式依然很直接.

## 小结

- `ori rd, rs, (1<<N)` 给第 N 位置位: 最基础的使能操作.
- `li mask, ~(1<<N)` + `and rd, rs, mask` 给第 N 位清零: 最基础的禁用操作.
- `andi rd, rs, (1<<N)` 测试第 N 位: 所有轮询循环里都在用.
- 多位字段用先清后设的模式来写: 先用字段掩码做 `andi`, 再用值做 `ori`.
- 读-改-写模式 (li → lw → 修改 → sw) 能保住我们不想动的那些位.
- SIO 的置位/清零寄存器使用原子语义 - 不需要读-改-写.
