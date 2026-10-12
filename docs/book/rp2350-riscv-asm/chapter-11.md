# Chapter 11: RISC-V 分支指令

## 引言

分支指令改变程序的执行流向. 没有分支, 处理器就会从复位向量开始一条一条顺序执行到 flash 末尾 - 不循环, 不调用函数, 也不做任何判断. 我们的闪烁驱动靠分支实现无限闪烁循环, 硬件轮询, 延时计数和输入检查. 本章会讲遍固件里用到的每一条分支指令.

## 无条件分支

### `j` - 跳转

```asm
  j     .Loop                                    # 永远跳转到 .Loop
```

`j` 是一条伪指令, 会被展开成 `jal x0, offset`. 由于目标是 `x0` (硬连线为零的寄存器), 返回地址被直接丢弃 - 于是它成了一条纯粹的无条件跳转.

在 main.s 里, 无限闪烁循环就用到了 `j`:

```asm
.Loop:
  li    a0, 16                                   # 加载 GPIO 编号
  call  GPIO_Set                                 # 调用 GPIO_Set
  li    a0, 500                                  # 500 毫秒
  call  Delay_MS                                 # 调用 Delay_MS
  li    a0, 16                                   # 加载 GPIO 编号
  call  GPIO_Clear                               # 调用 GPIO_Clear
  li    a0, 500                                  # 500 毫秒
  call  Delay_MS                                 # 调用 Delay_MS
  j     .Loop                                    # 无限循环
```

末尾的 `j .Loop` 造出一个无限循环 - LED 会一直闪烁, 直到断电为止.

### Reset_Handler 里的 `j`

Reset_Handler 用 `j` 跳到 main:

```asm
  j     main                                     # 跳到 main
```

这里用的是 `j` 而不是 `call`, 因为 main 永远不会返回 - 没必要保存返回地址.

### Default_Trap_Handler 里的 `j`

陷阱处理程序用 `j` 造了一个无限循环:

```asm
Default_Trap_Handler:
  j     Default_Trap_Handler                     # 出现意外陷阱时停在这里
```

一旦发生意外异常, 处理器就停在这个无限循环里, 而不是去执行后果无法预料的代码.

## 条件分支

RISC-V 的条件分支直接比较两个寄存器 - 没有条件标志寄存器. 处理器判断条件, 要么跳转 (改变 PC), 要么顺序落到下一条指令.

### `beqz` - 等于零则分支

```asm
  beqz  t1, .GPIO_Subsystem_Reset_Wait           # 位未置位就继续循环
```

`beqz rs1, label` 是一条伪指令, 会被展开成 `beq rs1, x0, label`. 寄存器等于零时就跳转.

在 reset.s 里, 它用来轮询 RESETS_RESET_DONE 寄存器:

```asm
.GPIO_Subsystem_Reset_Wait:
  li    t0, RESETS_RESET_DONE                    # 加载 RESETS->RESET_DONE 地址
  lw    t1, 0(t0)                                # 读取 RESETS->RESET_DONE 的值
  andi  t1, t1, (1<<6)                           # 取出 IO_BANK0 复位是否完成这一位
  beqz  t1, .GPIO_Subsystem_Reset_Wait           # 一直等到完成为止
```

`andi` 把第 6 位单独取出来. 如果这一位是零, 结果就是零, `beqz` 跳回去继续循环. 等 IO_BANK0 复位完成, 第 6 位置位, `andi` 得到非零结果, `beqz` 于是顺序往下走.

### `bnez` - 不等于零则分支

```asm
  bnez  t1, .Delay_MS_Loop                       # 循环到计数器减为 0
```

`bnez rs1, label` 是一条伪指令, 会被展开成 `bne rs1, x0, label`. 寄存器不等于零时就跳转.

延时循环用的就是它:

```asm
.Delay_MS_Loop:
  addi  t1, t1, -1                               # 计数器减一
  bnez  t1, .Delay_MS_Loop                       # 不为零就继续循环
```

`t1` 减到零时, `bnez` 顺序往下走, 延时结束.

### `bgez` - 大于等于零则分支

```asm
  bgez  t1, .Init_XOSC_Wait                      # 第 31 位为 0 就继续循环
```

`bgez rs1, label` 是一条伪指令, 会被展开成 `bge rs1, x0, label`. 寄存器大于等于零时跳转 (这里把它当作有符号整数看待, 也就是第 31 位为 0).

在 xosc.s 里, 它用来轮询 XOSC_STATUS 寄存器:

```asm
.Init_XOSC_Wait:
  li    t0, XOSC_STATUS                          # 加载 XOSC_STATUS 地址
  lw    t1, 0(t0)                                # 读取 XOSC_STATUS 的值
  bgez  t1, .Init_XOSC_Wait                      # 第 31 位为 0, 说明还没稳定
```

STABLE 位就是第 31 位. 第 31 位为 0 时, 这个 32 位值按有符号解释大于等于零, `bgez` 继续循环. 等 XOSC 稳定下来, 第 31 位置位, 这个有符号值变成负数, `bgez` 于是顺序往下走.

这是个很巧妙的技巧: 测寄存器的符号位, 等价于测最高位 - 不需要掩码, 也不需要移位.

### `blez` - 小于等于零则分支

```asm
  blez  a0, .Delay_MS_Done                       # 毫秒数 <= 0 就跳过
```

`blez rs1, label` 是一条伪指令, 会被展开成 `bge x0, rs1, label`. 寄存器小于等于零时跳转.

在 delay.s 里, 它用来检查传入的参数:

```asm
  blez  a0, .Delay_MS_Done                       # 毫秒数不合法就直接返回
```

这样可以挡住零和负数的延时值, 避免出现不正确的行为.

## 基础分支指令

上面那些伪指令都会展开成下面这些基础指令:

| 基础指令 | 含义 | 使用它的伪指令 |
|------------------|---------|------------------------------|
| `beq rs1, rs2, offset` | rs1 == rs2 时跳转 | `beqz rs1, label` (rs2 = x0) |
| `bne rs1, rs2, offset` | rs1 != rs2 时跳转 | `bnez rs1, label` (rs2 = x0) |
| `bge rs1, rs2, offset` | rs1 >= rs2 时跳转 (有符号) | `bgez rs1, label` (rs2 = x0), `blez rs2, label` (rs1 = x0) |
| `blt rs1, rs2, offset` | rs1 < rs2 时跳转 (有符号) | `bltz rs1, label` (rs2 = x0) |
| `bgeu rs1, rs2, offset` | rs1 >= rs2 时跳转 (无符号) | - |
| `bltu rs1, rs2, offset` | rs1 < rs2 时跳转 (无符号) | - |

它们都用 B 型编码, 带一个 13 位有符号偏移 (范围: 从分支指令算起 ±4 KB).

## 分支的编码与范围

| 指令 | 编码 | 范围 |
|-------------|----------|-------|
| `beq`/`bne`/`bge`/`blt` | B 型 (32 位) | ±4 KB |
| `c.beqz`/`c.bnez` | 压缩型 (16 位) | ±256 字节 |
| `jal` | J 型 (32 位) | ±1 MB |
| `c.j` | 压缩型 (16 位) | ±2 KB |

如果分支目标超出 ±4 KB, 汇编器就得改用间接的做法 (先把地址加载进寄存器, 再用 `jalr`). 我们的固件足够小, 所有分支都在范围内.

## 轮询循环

我们的固件里有两个硬件轮询循环:

**XOSC 稳定等待 (xosc.s):**

```
  lw → bgez → lw → bgez → ... → lw (bit set) → fall through
```

**复位完成等待 (reset.s):**

```
  lw → andi → beqz → lw → andi → beqz → ... → (bit set) → fall through
```

两者都在轮询状态寄存器里的某一位, 直到硬件表示自己就绪. 这就是 "忙等待" - 在裸机固件里很合适, 因为这里根本没有操作系统的调度器.

## 与 ARM 对照

| 特性 | ARM | RISC-V |
|---------|-----|--------|
| 条件机制 | APSR 标志位 (N,Z,C,V) | 直接比较寄存器 |
| 设置标志 | `subs`, `tst`, `cmp` 会设置标志 | 没有标志位 - 分支直接比较 |
| 无条件跳转 | `b label` | `j label` (`jal x0, label` 的伪指令) |
| 函数调用 | `bl label` | `call label` (`auipc`+`jalr` 的伪指令) |
| 返回 | `bx lr` | `ret` (`jalr x0, 0(ra)` 的伪指令) |

## 小结

- `j` 提供无条件跳转: 我们的无限闪烁循环, 以及 Reset_Handler 到 main 的切换.
- `beqz` 和 `bnez` 按寄存器是否为零来分支 - 用在轮询循环和延时循环里.
- `bgez` 借用符号位来测试 XOSC_STATUS 的第 31 位.
- `blez` 通过判断毫秒数是否 <= 0 来检查延时参数.
- RISC-V 的分支直接比较寄存器 - 没有条件标志位.
- 所有分支类伪指令都会展开成与 `x0` 比较的 B 型基础指令.
