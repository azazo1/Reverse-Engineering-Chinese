# Chapter 13: RISC-V 伪指令

## 引言

伪指令是给程序员用的助记符, 汇编器会把它翻译成一条或多条真正的机器指令. 它们让汇编代码更好读, 却没有给硬件增加任何新功能. RISC-V 非常依赖伪指令, 因为它的基础 ISA 是刻意做得很精简的 - 很多常见写法都需要特定的寄存器选择或指令组合, 而伪指令把这些细节都藏了起来. 本章逐一列出闪烁驱动里用到的每一条伪指令.

## `li` - 加载立即数

```asm
  li    t0, XOSC_STARTUP                         # 加载 XOSC_STARTUP 地址
```

`li` 把任意 32 位常数装进寄存器. 汇编器会挑最短的展开方式:

| 取值范围 | 展开形式 | 指令条数 |
|-------------|-----------|-------------|
| -2048 到 2047 | `addi rd, x0, imm` | 1 |
| 只有高 20 位 (低 12 位为 0) | `lui rd, imm20` | 1 |
| 任意 32 位 | `lui rd, upper20` + `addi rd, rd, lower12` | 2 |

我们固件里的例子:

```asm
  li    a2, 16                                   # addi a2, x0, 16
  li    t0, 3600                                 # lui t0, 1 + addi t0, t0, -496
  li    t0, XOSC_BASE                            # lui t0, 0x40048 + addi t0, t0, 0
  li    t1, 0x00FABAA0                           # lui t1, upper + addi t1, t1, lower
```

`li` 是我们固件里用得最多的伪指令 - 每个源文件里都有它.

## `la` - 加载地址

```asm
  la    t0, Default_Trap_Handler                 # 陷阱目标地址
```

`la` 用 PC 相对寻址加载一个符号的地址. 它展开成:

```
auipc  t0, %pcrel_hi(Default_Trap_Handler)
addi   t0, t0, %pcrel_lo(Default_Trap_Handler)
```

`li` 编码的是一个绝对值, `la` 不一样, 它算出来的是相对于当前 PC 的地址. 我们的固件在 Init_Trap_Vector 里用 `la` 加载陷阱处理程序的地址.

## `call` - 函数调用

```asm
  call  GPIO_Config                              # 调用 GPIO_Config
```

`call` 把返回地址保存到 `ra` 里, 然后跳到目标, 从而完成一次函数调用. 它展开成:

```
auipc  ra, %pcrel_hi(GPIO_Config)
jalr   ra, %pcrel_lo(GPIO_Config)(ra)
```

如果目标离得近 (在 ±1 MB 之内), 汇编器可能会优化成单独一条 `jal ra, offset`.

固件里每一次函数调用都用的 `call`:

| 调用者 | 目标 | 文件 |
|--------|--------|------|
| Reset_Handler | Init_Stack | reset_handler.s |
| Reset_Handler | Init_Trap_Vector | reset_handler.s |
| Reset_Handler | Init_XOSC | reset_handler.s |
| Reset_Handler | Enable_XOSC_Peri_Clock | reset_handler.s |
| Reset_Handler | Init_Subsystem | reset_handler.s |
| Reset_Handler | Enable_Coprocessor | reset_handler.s |
| main | GPIO_Config | main.s |
| main | GPIO_Set | main.s |
| main | GPIO_Clear | main.s |
| main | Delay_MS | main.s |

## `ret` - 从函数返回

```asm
  ret                                            # 返回调用者
```

`ret` 跳到 `ra` 里的地址, 从而返回调用者. 它展开成:

```
jalr  x0, 0(ra)
```

写到 `x0` 就丢弃了链接 - 这是一条纯跳转, 不是调用. 固件里每个函数都以 `ret` 结尾.

## `j` - 无条件跳转

```asm
  j     .Loop                                    # 无限循环
```

`j` 执行无条件跳转, 不保存返回地址. 它展开成:

```
jal  x0, offset
```

我们的固件在三处用到 `j`:

1. main.s 里的 `j .Loop` - 无限闪烁循环
2. reset_handler.s 里的 `j main` - 进入 main (不需要返回)
3. `j Default_Trap_Handler` - 陷阱处理程序里的无限循环

## `not` - 按位取反

```asm
  not   t2, t2                                   # t2 = ~t2
```

`not` 把寄存器所有位取反. 它展开成:

```
xori  t2, t2, -1
```

由于补码里的 -1 就是 `0xFFFFFFFF`, 与 -1 做 XOR 就等于把每一位都翻转.

在 reset.s 里, `not` 用来造清零掩码:

```asm
  li    t2, (1<<6)                               # IO_BANK0 复位掩码
  not   t2, t2                                   # 取反: 0xFFFFFFBF
  and   t1, t1, t2                               # 清掉 IO_BANK0 那一位
```

## 分支伪指令

### `beqz` - 为零则分支

```asm
  beqz  t1, .GPIO_Subsystem_Reset_Wait           # 位未置位就继续循环
```

展开成 `beq t1, x0, label`.

### `bnez` - 不为零则分支

```asm
  bnez  t1, .Delay_MS_Loop                       # 循环到计数器减为 0
```

展开成 `bne t1, x0, label`.

### `bgez` - 大于等于零则分支

```asm
  bgez  t1, .Init_XOSC_Wait                      # 第 31 位为 0 就继续循环
```

展开成 `bge t1, x0, label`.

### `blez` - 小于等于零则分支

```asm
  blez  a0, .Delay_MS_Done                       # 毫秒数 <= 0 就跳过
```

展开成 `bge x0, a0, label`. 注意操作数换了个位置: 基础指令判断的是 `x0 >= a0`, 这等价于 `a0 <= 0`.

## CSR 伪指令

### `csrw` - 写 CSR

```asm
  csrw  mtvec, t0                                # mtvec = t0
```

展开成 `csrrw x0, mtvec, t0`. `csrrw` 指令会原子地把 CSR 的值和寄存器交换, 但由于目标是 `x0`, 旧值被丢弃 - 于是它成了一次纯粹的写.

固件里只在一处用到 `csrw`, 就是在 Init_Trap_Vector 里设置机器陷阱向量.

## 伪指令速查表

| 伪指令 | 展开形式 | 用在哪里 |
|--------------------|-----------|---------|
| `li rd, imm` | `lui`+`addi` 或 `addi` | 所有文件 |
| `la rd, symbol` | `auipc`+`addi` | reset_handler.s |
| `call label` | `auipc ra`+`jalr ra` | reset_handler.s, main.s |
| `ret` | `jalr x0, 0(ra)` | 所有函数 |
| `j label` | `jal x0, offset` | main.s, reset_handler.s |
| `not rd, rs` | `xori rd, rs, -1` | reset.s |
| `beqz rs, label` | `beq rs, x0, label` | reset.s |
| `bnez rs, label` | `bne rs, x0, label` | delay.s |
| `bgez rs, label` | `bge rs, x0, label` | xosc.s |
| `blez rs, label` | `bge x0, rs, label` | delay.s |
| `csrw csr, rs` | `csrrw x0, csr, rs` | reset_handler.s |

## 伪指令为什么重要

没有伪指令的话, 程序员就得这样写:

```
lui   t0, %hi(0x40048000)
addi  t0, t0, %lo(0x40048000)
```

而不是:

```asm
  li    t0, XOSC_BASE                            # 加载 XOSC 基地址
```

还有:

```
auipc ra, %pcrel_hi(GPIO_Set)
jalr  ra, %pcrel_lo(GPIO_Set)(ra)
```

而不是:

```asm
  call  GPIO_Set                                 # 调用 GPIO_Set
```

伪指令让源码保持好读, 同时汇编器仍然生成最优的机器码.

## 小结

- `li` 和 `la` 用来加载常数和地址 - 最常用的两条伪指令.
- `call` 和 `ret` 借助 `ra` 实现函数调用与返回.
- `j` 提供不保存返回地址的无条件跳转.
- `not` 通过与 -1 做 XOR 把所有位取反.
- 分支伪指令 (`beqz`, `bnez`, `bgez`, `blez`) 都是与 `x0` 比较.
- `csrw` 用来写控制/状态寄存器.
- 伪指令让 RISC-V 汇编保持好读, 同时展开成最优的基础指令.
