# Chapter 15: 调用约定与栈帧

## 引言

当一个函数调用另一个函数时, 双方必须就参数放在哪里, 哪些寄存器要保持不变, 以及栈怎么管理达成一致. 这些规则合起来就是**调用约定 (calling convention)**. RISC-V 在它的 ABI 规范里定义了一套标准调用约定, 我们的闪烁驱动严格照着它来. 本章考察参数是怎么传的, 函数怎么保存和恢复状态, 以及栈帧的结构长什么样.

## RISC-V 调用约定

### 寄存器角色

| 寄存器 | ABI 名 | 作用 | 谁保存 |
|----------|----------|------|-------|
| x0 | zero | 硬连线为零 | - |
| x1 | ra | 返回地址 | 调用者 |
| x2 | sp | 栈指针 | 被调用者 |
| x3 | gp | 全局指针 | - |
| x4 | tp | 线程指针 | - |
| x5-x7 | t0-t2 | 临时寄存器 | 调用者 |
| x8 | s0/fp | 保存寄存器 / 帧指针 | 被调用者 |
| x9 | s1 | 保存寄存器 | 被调用者 |
| x10-x11 | a0-a1 | 参数 / 返回值 | 调用者 |
| x12-x17 | a2-a7 | 参数 | 调用者 |
| x18-x27 | s2-s11 | 保存寄存器 | 被调用者 |
| x28-x31 | t3-t6 | 临时寄存器 | 调用者 |

### 关键规则

1. **参数**通过 `a0`-`a7` 传递 (最多 8 个寄存器). 我们的函数用 `a0`-`a2`.
2. **返回值**放在 `a0`-`a1` 里.
3. **调用者保存**的寄存器 (`t0`-`t6`, `a0`-`a7`, `ra`) 可能被被调用者覆盖. 如果调用之后还需要它们, 调用者必须自己先保存.
4. **被调用者保存**的寄存器 (`s0`-`s11`, `sp`) 必须由被调用者保持原值. 如果函数改动了它们, 就得自己保存再恢复.
5. **栈指针** (`sp`) 在返回之前必须恢复成原来的值.

## 固件里的参数传递

### GPIO_Config: 三个参数

```asm
  li    a0, PADS_BANK0_GPIO16_OFFSET             # a0 = pad 偏移
  li    a1, IO_BANK0_GPIO16_CTRL_OFFSET          # a1 = ctrl 偏移
  li    a2, 16                                   # a2 = GPIO 编号
  call  GPIO_Config                              # 调用
```

被调用者拿到的是 `a0` = 0x44, `a1` = 0x84, `a2` = 16 - 完全不需要访问内存.

### GPIO_Set / GPIO_Clear: 一个参数

```asm
  li    a0, 16                                   # a0 = GPIO 编号
  call  GPIO_Set                                 # 调用
```

### Delay_MS: 一个参数

```asm
  li    a0, 500                                  # a0 = 毫秒数
  call  Delay_MS                                 # 调用
```

## 叶子函数

叶子函数不调用任何其他函数. 既然 `ra` 从不会被覆盖, 也就不需要保存它:

```asm
Init_Stack:
  li    sp, STACK_TOP                            # 把 SP 设为 RAM 栈顶
  ret                                            # 返回 (ra 未被破坏)
```

```asm
GPIO_Set:
  li    t0, SIO_GPIO_OUT_SET                     # 加载 SIO GPIO_OUT_SET 地址
  li    t1, 1                                    # 位的值
  sll   t1, t1, a0                               # 移到对应 GPIO 的位置
  sw    t1, 0(t0)                                # 把 GPIO 输出拉高
  ret                                            # 返回
```

这些函数只用 `t0`-`t2` 和 `a0`-`a2` (都是调用者保存的), 所以它们没有保存寄存器的义务.

固件里的叶子函数:

| 函数 | 文件 | 用到的寄存器 |
|----------|------|---------------|
| Init_Stack | stack.s | sp |
| Init_Trap_Vector | reset_handler.s | t0 |
| Init_XOSC | xosc.s | t0, t1 |
| Enable_XOSC_Peri_Clock | xosc.s | t0, t1, t2 |
| Init_Subsystem | reset.s | t0, t1, t2 |
| Enable_Coprocessor | coprocessor.s | (无) |
| GPIO_Set | gpio.s | t0, t1, a0 |
| GPIO_Clear | gpio.s | t0, t1, a0 |
| Delay_MS | delay.s | t0, t1, a0 |

## 非叶子函数

非叶子函数会调用其他函数, 所以必须保存 `ra`:

```asm
GPIO_Config:
  addi  sp, sp, -4                               # 分配栈帧
  sw    ra, 0(sp)                                # 保存返回地址
  ...                                            # 函数体
  lw    ra, 0(sp)                                # 恢复返回地址
  addi  sp, sp, 4                                # 释放栈帧
  ret                                            # 返回调用者
```

GPIO_Config 被当作非叶子函数处理, 因为它由 main 调用, 而且要保留调用子函数的能力.

## 栈帧

### 分配

```asm
  addi  sp, sp, -4                               # sp = sp - 4
```

栈向下增长 (朝低地址方向). 从 `sp` 里减去一个数, 就是分配空间.

### 保存

```asm
  sw    ra, 0(sp)                                # memory[sp] = ra
```

返回地址被存到新栈帧的顶部.

### 恢复

```asm
  lw    ra, 0(sp)                                # ra = memory[sp]
```

返回地址被装回来.

### 释放

```asm
  addi  sp, sp, 4                                # sp = sp + 4
```

把刚才减掉的量加回去, 栈帧就撤掉了.

### 栈的布局

```
High addresses (STACK_TOP = 0x20082000)
+------------------+
|                  |
+------------------+
| ra               |  SP + 0   <-- SP (after frame allocation)
+------------------+
Low addresses
```

如果要保存多个寄存器, 栈帧就更大:

```
+------------------+
| ra               |  SP + 8
| s0               |  SP + 4
| s1               |  SP + 0   <-- SP
+------------------+
```

我们的固件只需要 4 字节的栈帧 (只存 `ra`), 栈的用量保持在最小.

## main 函数

`main` 实际上算非叶子函数 (它调用了 GPIO_Config, GPIO_Set, GPIO_Clear, Delay_MS), 但它从不返回 - 它里面是个无限循环:

```asm
main:
.GPIO16_Config:
  li    a0, PADS_BANK0_GPIO16_OFFSET             # 加载 pad 偏移
  li    a1, IO_BANK0_GPIO16_CTRL_OFFSET          # 加载 ctrl 偏移
  li    a2, 16                                   # 加载 GPIO 编号
  call  GPIO_Config                              # 配置 GPIO16
.Loop:
  li    a0, 16                                   # GPIO 编号
  call  GPIO_Set                                 # 点亮 LED
  li    a0, 500                                  # 500 毫秒
  call  Delay_MS                                 # 等待
  li    a0, 16                                   # GPIO 编号
  call  GPIO_Clear                               # 熄灭 LED
  li    a0, 500                                  # 500 毫秒
  call  Delay_MS                                 # 等待
  j     .Loop                                    # 永远重复
```

由于 `j .Loop` 保证 main 永远执行不到 `ret`, 所以没必要保存 `ra` - 它根本没有机会被恢复.

## Reset_Handler: 调用链的根

Reset_Handler 是整条调用链的根. 它对初始化函数用 `call`, 对 main 用 `j`:

```asm
Reset_Handler:
  call  Init_Stack                               # 叶子函数
  call  Init_Trap_Vector                         # 叶子函数
  call  Init_XOSC                                # 叶子函数
  call  Enable_XOSC_Peri_Clock                   # 叶子函数
  call  Init_Subsystem                           # 叶子函数
  call  Enable_Coprocessor                       # 叶子函数
  j     main                                     # 永不返回
```

每一次 `call` 都会覆盖 `ra`. 这样做是安全的, 因为 Reset_Handler 是顺序调用它们的, 而且从不需要返回 - Reset_Handler 上面根本没有调用者.

## 与 ARM 对照

| 特性 | ARM | RISC-V |
|---------|-----|--------|
| 保存/恢复 | `push {r4-r12, lr}` / `pop {r4-r12, lr}` | `addi sp` + `sw` / `lw` + `addi sp` |
| 参数 | r0-r3 | a0-a7 |
| 返回地址 | lr (r14) | ra (x1) |
| 被调用者保存 | r4-r11 | s0-s11 |
| 栈对齐 | 8 字节 (AAPCS) | 16 字节 (RISC-V ABI, 嵌入式可放宽) |

ARM 的 `push`/`pop` 一条指令就能保存多个寄存器. RISC-V 则要求每个寄存器都显式写 `sw`/`lw` - 更啰嗦, 但概念上更简单.

## 小结

- 参数通过 `a0`-`a7` 传递; 返回值放在 `a0`-`a1` 里.
- 叶子函数 (不调用别的函数) 不需要保存 `ra`.
- 非叶子函数用 `sw ra, 0(sp)` 把 `ra` 存到栈上, 用 `lw ra, 0(sp)` 恢复.
- 栈向下增长; `addi sp, sp, -N` 是分配, `addi sp, sp, N` 是释放.
- 临时寄存器 (`t0`-`t6`) 是调用者保存的 - 可以随便用, 不用保存.
- 保存寄存器 (`s0`-`s11`) 是被调用者保存的 - 一旦用到就必须保持原值.
