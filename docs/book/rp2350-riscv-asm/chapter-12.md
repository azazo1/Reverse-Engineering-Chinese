# Chapter 12: RISC-V 跳转, 调用与返回

## 引言

结构化的软件是由互相调用的函数搭起来的. RISC-V 用 `jal`/`jalr` (jump and link / jump and link register) 实现调用, 用 `ret` 实现返回. 当函数层层嵌套时 - 调用者调用了被调用者, 被调用者又调用了另一个被调用者 - 返回地址寄存器就必须存到栈上. 本章考察我们的闪烁驱动里, 调用, 返回和栈帧是怎样配合的.

## 返回地址寄存器

`jal` 或 `jalr` 执行时, 处理器会把下一条指令的地址存进目标寄存器. 按约定, 这个寄存器是 `ra` (x1):

```
Before call:
  PC = 0x10000100   (call GPIO_Set instruction)
  ra = (previous)

After call:
  PC = GPIO_Set     (target address)
  ra = 0x10000108   (return address, next instruction)
```

被调用者执行 `ret` 返回, 它把 `ra` 装回 PC.

## `jal` - 跳转并链接

```
jal   rd, offset
```

`jal` 把 PC+4 存进 `rd`, 然后跳到 PC+offset. J 型编码提供 21 位有符号偏移 (范围 ±1 MB).

当 `rd` 是 `ra` (x1) 时, 这就是一次函数调用. 当 `rd` 是 `x0` 时, 返回地址被丢弃 - 于是它变成一条无条件跳转 (`j`).

## `jalr` - 跳转并链接到寄存器

```
jalr  rd, offset(rs1)
```

`jalr` 把 PC+4 存进 `rd`, 然后跳到 rs1+offset. 有了它, 就可以做间接跳转, 也可以调用运行时才计算出来的地址.

## `call` 伪指令

汇编器提供了 `call`, 把细节都藏了起来. 程序员写的是:

```asm
  call  GPIO_Config                              # 调用 GPIO_Config
```

汇编器把它展开成:

```
auipc  ra, %pcrel_hi(GPIO_Config)
jalr   ra, %pcrel_lo(GPIO_Config)(ra)
```

`auipc` 把 PC 相对偏移的高位部分装进 `ra`, `jalr` 再加上低位部分并跳转. 合起来的效果是: `ra` = 返回地址, PC = GPIO_Config.

如果目标离得近, 汇编器还会优化成单独一条 `jal ra, offset` - 前提是目标在 ±1 MB 之内.

## `ret` 伪指令

`ret` 是用于从函数返回的伪指令:

```asm
  ret                                            # 返回调用者
```

它展开成:

```
jalr  x0, 0(ra)
```

这条指令跳到 `ra` 里的地址, 同时丢弃链接 (写到 `x0`). 执行会从原来那条 `call` 的下一条指令继续.

## 叶子函数与非叶子函数

**叶子函数**不调用任何其他函数. 它可以直接用 `ra`, 不需要保存:

```asm
Init_Stack:
  li    sp, STACK_TOP                            # 把 SP 设为 RAM 栈顶
  ret                                            # 返回 (ra 未被破坏)
```

Init_Stack 就是个叶子函数 - 它里面没有 `call` 指令, 所以 `ra` 全程有效.

**非叶子函数**会调用其他函数, 这就会覆盖 `ra`. 所以它必须在入口处保存 `ra`, 在出口处恢复:

```asm
GPIO_Config:
  addi  sp, sp, -4                               # 分配栈帧
  sw    ra, 0(sp)                                # 保存返回地址
  ...                                            # 函数体 (这里没有调用,
  ...                                            #   但结构上支持调用)
  lw    ra, 0(sp)                                # 恢复返回地址
  addi  sp, sp, 4                                # 释放栈帧
  ret                                            # 返回调用者
```

GPIO_Config 保存了 `ra`, 因为它是由 `main` 调用的 (main 需要保留 `ra` 以支持自己那条返回路径, 虽然 main 实际上从不返回).

## 调用链

我们的闪烁驱动有这样一个调用层次:

```
Reset_Handler
  +-- Init_Stack          (leaf)
  +-- Init_Trap_Vector    (leaf)
  +-- Init_XOSC           (leaf)
  +-- Enable_XOSC_Peri_Clock  (leaf)
  +-- Init_Subsystem      (leaf)
  +-- Enable_Coprocessor  (leaf)
  +-- main                (non-leaf, never returns)
        +-- GPIO_Config   (saves ra)
        +-- GPIO_Set      (leaf)
        +-- Delay_MS      (leaf)
        +-- GPIO_Clear    (leaf)
```

Reset_Handler 用 `call` 逐个调用初始化函数, 最后用 `j main` (是跳转, 不是调用) 进入 main, 因为 main 永远不会返回.

## 栈帧

当 GPIO_Config 执行 `addi sp, sp, -4` 和 `sw ra, 0(sp)` 时, 栈的样子是这样:

```
High addresses (STACK_TOP = 0x20082000)
+------------------+
|                  |
+------------------+
| ra               |  SP + 0   <-- SP after push
+------------------+
Low addresses
```

函数返回时, `lw ra, 0(sp)` 和 `addi sp, sp, 4` 把 `ra` 恢复出来, 并把 SP 退回去.

### 更大的栈帧

如果函数需要保存多个寄存器 (比如 `ra`, `s0`, `s1`):

```asm
  addi  sp, sp, -12                              # 分配 12 字节
  sw    ra, 8(sp)                                # 保存 ra
  sw    s0, 4(sp)                                # 保存 s0
  sw    s1, 0(sp)                                # 保存 s1
  ...
  lw    s1, 0(sp)                                # 恢复 s1
  lw    s0, 4(sp)                                # 恢复 s0
  lw    ra, 8(sp)                                # 恢复 ra
  addi  sp, sp, 12                               # 释放
  ret                                            # 返回
```

我们的固件只需要保存 `ra` (4 字节), 栈帧保持在最小.

## RISC-V 调用约定

我们的固件遵循 RISC-V 标准调用约定:

| 寄存器 | ABI 名 | 作用 | 调用者/被调用者保存 |
|----------|----------|------|-------------------|
| x0 | zero | 硬连线为零 | - |
| x1 | ra | 返回地址 | 调用者保存 |
| x2 | sp | 栈指针 | 被调用者保存 |
| x5-x7 | t0-t2 | 临时寄存器 | 调用者保存 |
| x10-x11 | a0-a1 | 参数 / 返回值 | 调用者保存 |
| x12-x17 | a2-a7 | 参数 | 调用者保存 |
| x8-x9 | s0-s1 | 保存寄存器 | 被调用者保存 |
| x18-x27 | s2-s11 | 保存寄存器 | 被调用者保存 |
| x28-x31 | t3-t6 | 临时寄存器 | 调用者保存 |

我们的函数体现了这套约定:

- `main` 通过 `a0` 传 GPIO 编号, 也通过 `a0` 传延时毫秒数
- `GPIO_Config` 接收 pad 偏移 (`a0`), ctrl 偏移 (`a1`), GPIO 编号 (`a2`)
- `GPIO_Set` 和 `GPIO_Clear` 通过 `a0` 接收 GPIO 编号
- `Delay_MS` 通过 `a0` 接收毫秒数

临时寄存器 `t0`-`t2` 用于各函数内部的临时计算.

## 参数传递示例

当 main 调用 GPIO_Config 时:

```asm
  li    a0, PADS_BANK0_GPIO16_OFFSET             # a0 = pad 偏移
  li    a1, IO_BANK0_GPIO16_CTRL_OFFSET          # a1 = ctrl 偏移
  li    a2, 16                                   # a2 = GPIO 编号
  call  GPIO_Config                              # 调用
```

被调用者直接从 `a0`, `a1`, `a2` 拿到这些值, 不需要额外的机制.

当 main 调用 GPIO_Set 时:

```asm
  li    a0, 16                                   # a0 = GPIO 编号
  call  GPIO_Set                                 # 调用
```

## Reset_Handler: 一个特例

Reset_Handler 从不返回. 它用 `call` 调用各个初始化函数, 然后用 `j` (而不是 `call`) 跳到 main:

```asm
Reset_Handler:
  call  Init_Stack                               # 通过 ret 返回
  call  Init_Trap_Vector                         # 通过 ret 返回
  call  Init_XOSC                                # 通过 ret 返回
  call  Enable_XOSC_Peri_Clock                   # 通过 ret 返回
  call  Init_Subsystem                           # 通过 ret 返回
  call  Enable_Coprocessor                       # 通过 ret 返回
  j     main                                     # 永不返回
```

用 `j` 代替 `call`, 意味着 `ra` 里还留着最后一次 `call` 的返回地址 - 但 main 里是无限循环, 所以这无所谓. 系统永远不会从 main 返回.

## 与 ARM 对照

| 特性 | ARM | RISC-V |
|---------|-----|--------|
| 调用 | `bl label` | `call label` (`auipc`+`jalr`) |
| 返回 | `bx lr` | `ret` (`jalr x0, 0(ra)`) |
| 返回地址寄存器 | `lr` (r14) | `ra` (x1) |
| 保存寄存器 | `push {r4-r12, lr}` | `addi sp` 加多条 `sw` |
| 恢复寄存器 | `pop {r4-r12, lr}` | 多条 `lw` 加 `addi sp` |
| 参数寄存器 | r0-r3 | a0-a7 |
| 被调用者保存 | r4-r11 | s0-s11 |

## 小结

- `call` 把返回地址存进 `ra`, 然后跳到目标函数.
- `ret` 跳到 `ra` 里的地址, 从而返回调用者.
- 非叶子函数用 `sw ra, 0(sp)` 保存 `ra`, 用 `lw ra, 0(sp)` 恢复它.
- 栈向下增长; 每个函数为自己的保存寄存器建一个栈帧.
- RISC-V 调用约定用 `a0`-`a7` 传参数, 用 `s0`-`s11` 作被调用者保存寄存器.
- Reset_Handler 用 `j main` (而不是 `call`), 因为系统永远不会返回.
