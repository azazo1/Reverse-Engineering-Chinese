# Chapter 8: RISC-V 立即数与高位立即数指令

## 引言

处理器要处理数据, 首先得把数据弄进寄存器. 在 RISC-V 机器上, 把常量送进寄存器是最常见的操作之一. 本章考察 Hazard3 内核如何加载立即数, 编码本身带来了哪些限制, 以及我们闪烁固件高度依赖的汇编器伪指令 `li` 和 `la` 扮演什么角色.

## 立即数编码的难题

一条 RISC-V 指令宽 32 位. 其中一部分位要用来编码操作码, 寄存器和功能字段 - 留给立即数常量的空间就很有限了. I-type 格式只给立即数留了 12 位 (范围: -2048 到 2047). 而 `0x40048000` 这样的外设地址是 32 位值, 12 位根本装不下.

RISC-V 用一个两条指令的序列来解决: `lui` 加载高 20 位, 然后 `addi` 补上低 12 位.

## `lui` - 加载高位立即数

`lui` (Load Upper Immediate) 把一个 20 位立即数放进目标寄存器的高 20 位, 低 12 位清零:

```
lui   rd, imm20

rd = imm20 << 12
```

例子:

```
lui   t0, 0x40048       =>  t0 = 0x40048000
```

结果的低 12 位是零. 如果目标值的低位不全为零, 后面还要跟一条 `addi`.

## `addi` - 加立即数

`addi` 把一个有符号 12 位立即数加到源寄存器上:

```
addi  rd, rs1, imm12

rd = rs1 + sign_extend(imm12)
```

和 `lui` 搭配使用时:

```
lui   t0, 0x40048       =>  t0 = 0x40048000
addi  t0, t0, 0x00c     =>  t0 = 0x4004800c   (XOSC_STARTUP)
```

## `li` 伪指令

汇编器提供 `li` (Load Immediate) 来把 `lui`+`addi` 这个序列封装起来. 程序员只要写:

```asm
  li    t0, XOSC_STARTUP                         # 加载 XOSC_STARTUP 地址
```

汇编器会根据这个值把它展开成:

| 取值范围 | 展开结果 |
|-------------|-----------|
| -2048 到 2047 | `addi rd, x0, imm` (单条指令) |
| 高 20 位装得下 (低 12 位为 0) | `lui rd, imm20` (单条指令) |
| 任意 32 位值 | `lui rd, upper20` + `addi rd, rd, lower12` (两条指令) |

### 符号扩展带来的麻烦

因为 `addi` 会对它的 12 位立即数做符号扩展, 所以当低位部分的第 11 位被置位时, 汇编器必须调整高位立即数. 例如:

```
Target: 0x40048800
Lower 12 bits: 0x800 = -2048 (sign-extended)
Adjusted upper: 0x40049 (0x40048 + 1)
```

```
lui   t0, 0x40049       =>  t0 = 0x40049000
addi  t0, t0, -2048     =>  t0 = 0x40048800
```

`li` 伪指令会自动处理这一切.

## `auipc` - 把高位立即数加到 PC

`auipc` (Add Upper Immediate to PC) 加载的是 PC 加上一个 20 位高位立即数:

```
auipc  rd, imm20

rd = PC + (imm20 << 12)
```

它用于 PC 相对寻址. `la` 和 `call` 伪指令内部都使用 `auipc`.

## `la` 伪指令

`la` (Load Address) 加载一个符号的地址:

```asm
  la    t0, Default_Trap_Handler                 # 陷阱目标
```

汇编器把它展开成:

```
auipc  t0, %pcrel_hi(Default_Trap_Handler)
addi   t0, t0, %pcrel_lo(Default_Trap_Handler)
```

这样就得到了一个相对当前 PC 的, 与位置无关的地址计算. 我们的固件在 Init_Trap_Vector 里用 `la` 把陷阱处理程序的地址加载进 `mtvec`.

## 固件里立即数的用法

在闪烁驱动里, 常量通过几种方式进入寄存器:

### 1. 用 `li` 加载外设地址

每个源文件里都用它来加载基地址和寄存器偏移:

```asm
  li    t0, XOSC_BASE                            # t0 = 0x40048000
  li    t0, RESETS_RESET                         # t0 = 0x40020000
  li    t0, SIO_GPIO_OUT_SET                     # t0 = 0xd0000018
```

### 2. 用 `li` 加载小常量

当值能用 12 位表示时, `li` 展开成一条 `addi`:

```asm
  li    t1, 0x00c4                               # t1 = 196 (能用 12 位表示)
  li    a0, 500                                  # a0 = 500 (延时毫秒数)
  li    a2, 16                                   # a2 = 16 (GPIO 编号)
  li    t0, 3600                                 # t0 = 3600 (每毫秒循环数)
  li    t1, 1                                    # t1 = 1 (位值)
```

### 3. 用 `li` 加载大常量

对于需要 `lui`+`addi` 的值:

```asm
  li    t1, 0x00FABAA0                           # XOSC_CTRL 的值
```

它会展开成:

```
lui   t1, 0x00FAB       =>  t1 = 0x00FAB000
addi  t1, t1, -1376     =>  t1 = 0x00FABAA0  (since 0xAA0 sign-extends)
```

### 4. 用 `li` 生成位掩码

用来为位操作生成掩码:

```asm
  li    t2, ~(1<<7)                              # 清除 OD 位的掩码
  li    t2, (1<<11)                              # ENABLE 位掩码
```

## 与 ARM 的对比

在 ARM Cortex-M33 上, 等价操作使用 `ldr Rd, =value`, 它把常量放进文字池 (数据区), 然后生成一次 PC 相对加载. RISC-V 完全不需要文字池 - 常量通过 `lui`+`addi` 直接编码在指令流里.

| 特性 | ARM | RISC-V |
|---------|-----|--------|
| 加载 32 位常量 | `ldr Rd, =value` (文字池) | `li rd, value` (`lui`+`addi`) |
| 数据存放 | 常量放在内存里 | 常量编码在指令里 |
| 访存次数 | 从 flash 加载一次 | 零次加载 (立即数在指令中) |
| 代码局部性 | 文字池可能在很远处 | 指令是顺序排列的 |

## 小结

- `lui` 加载 20 位高位立即数, 低 12 位清零.
- `addi` 补上低 12 位, 符号扩展由汇编器处理.
- `li` 是加载任意 32 位常量的主要伪指令 - 它会展开成一到两条真实指令.
- `auipc` 计算 PC 相对地址; `la` 把它包装起来用于加载符号地址.
- 我们的固件大量依赖 `li` 来加载外设基地址, 控制值和位掩码.
