# Chapter 24: 启动流程 - `reset_handler.s`

## 简介

`reset_handler.s` 是 boot ROM 把控制权交给我们的固件之后运行的第一段代码. 它统筹了整个硬件启动过程: 建立栈, 安装陷阱向量, 初始化振荡器, 使能时钟, 释放子系统, 最后跳转到 `main`. 本章逐条走一遍每条指令, 并解释塑造这个启动流程的设计取舍.

## 完整源码

```asm
.include "constants.s"

.section .text                                   # 代码段
.align 2                                         # 对齐到 4 字节边界

.global Reset_Handler                            # 导出 Reset_Handler 符号
.type Reset_Handler, @function
Reset_Handler:
  call  Init_Stack                               # 初始化 SP
  call  Init_Trap_Vector                         # 安装陷阱向量
  call  Init_XOSC                                # 初始化外部晶体振荡器
  call  Enable_XOSC_Peri_Clock                   # 使能 XOSC 外设时钟
  call  Init_Subsystem                           # 初始化子系统
  call  Enable_Coprocessor                       # RISC-V 上是空操作 (为了两边对齐才保留)
  j     main                                     # 跳转到主循环
.size Reset_Handler, . - Reset_Handler

.global Default_Trap_Handler
.type Default_Trap_Handler, @function
Default_Trap_Handler:
  j     Default_Trap_Handler                     # 遇到意外陷阱就锁在这里

.global Init_Trap_Vector
.type Init_Trap_Vector, @function
Init_Trap_Vector:
  la    t0, Default_Trap_Handler                 # 陷阱目标
  csrw  mtvec, t0                                # mtvec = 陷阱入口
  ret                                            # 返回
```

## 启动调用链

```
Reset_Handler
  ├── call Init_Stack          → stack.s
  ├── call Init_Trap_Vector    → reset_handler.s (below)
  ├── call Init_XOSC           → xosc.s
  ├── call Enable_XOSC_Peri_Clock → xosc.s
  ├── call Init_Subsystem      → reset.s
  ├── call Enable_Coprocessor  → coprocessor.s (no-op)
  └── j    main                → main.s
```

每条 `call` 都把返回地址压入链接寄存器 (`ra`), 执行完函数后通过 `ret` (也就是 `jalr x0, ra, 0`) 返回. 因为 `Reset_Handler` 本身就是入口点 - 它从来不会被别的函数调用 - 所以它永远不需要保存 `ra`.

## Reset_Handler - 逐行讲解

### 函数声明

```asm
.global Reset_Handler                            # 导出 Reset_Handler 符号
.type Reset_Handler, @function
```

`.global` 让 `Reset_Handler` 对链接器可见. `image_def.s` 引用这个符号作为入口点, 链接器把它解析成一个绝对的 flash 地址.

### 第 1 步: 栈的初始化

```asm
  call  Init_Stack                               # 初始化 SP
```

这一步必须放在最前面. 后面每一次 `call` 都要用到栈 (`call` 伪指令本身就要写 `ra`, 而保存 `ra` 的函数还需要一个合法的 `sp`). `Init_Stack` 把 `sp` 设为 `STACK_TOP` (`0x20082000`).

### 第 2 步: 设置陷阱向量

```asm
  call  Init_Trap_Vector                         # 安装陷阱向量
```

把我们的陷阱处理程序安装到 `mtvec` CSR 里. 这一步必须趁早 - 如果后面的某一步初始化触发了意外异常 (非法指令, 未对齐访问), 陷阱处理程序能接住它, 而不是从一个未定义的地址开始执行.

### 第 3 步: 晶体振荡器

```asm
  call  Init_XOSC                                # 初始化外部晶体振荡器
```

配置外部 12 MHz 晶体振荡器. 这次调用之后, XOSC 就稳定运行了.

### 第 4 步: 外设时钟

```asm
  call  Enable_XOSC_Peri_Clock                   # 使能 XOSC 外设时钟
```

把 XOSC 的输出接到外设时钟上, 由它驱动 APB 总线以及我们后面要配置的所有外设.

### 第 5 步: 释放子系统

```asm
  call  Init_Subsystem                           # 初始化子系统
```

把 IO_BANK0 从复位状态释放出来. 在外设被释放之前, GPIO 引脚是无法配置的.

### 第 6 步: 协处理器 (空操作)

```asm
  call  Enable_Coprocessor                       # RISC-V 上是空操作 (为了两边对齐才保留)
```

在 ARM 上, 这一步通过 CPACR 使能协处理器 0 的访问权限. 在 RISC-V 上没有协处理器 - SIO 通过内存映射寄存器访问. 这个函数只有一条 `ret` 指令, 保留它只是为了和 ARM 版本的工程结构保持一致.

### 第 7 步: 跳转到 main

```asm
  j     main                                     # 跳转到主循环
```

`j main` 就是 `jal x0, offset` - 一条丢弃返回地址的无条件跳转 (写到 `x0`, 也就是零寄存器). 这是有意为之: `main` 里是一个死循环, 永远不会返回. 用 `j` 而不是 `call` 把这个意图写明白了, 也省掉了压入一个没用的返回地址.

### size 指令

```asm
.size Reset_Handler, . - Reset_Handler
```

这行告诉链接器和调试器 `Reset_Handler` 的确切字节大小. `.` (当前位置) 减去标号, 就得到函数的长度.

## 为什么是这个顺序?

这个调用顺序遵循一条严格的依赖链:

| 步骤 | 函数 | 依赖 |
|------|----------|------------|
| 1 | `Init_Stack` | 无 (第一件事) |
| 2 | `Init_Trap_Vector` | 栈 (为了 `ret`) |
| 3 | `Init_XOSC` | 栈, 陷阱处理程序 |
| 4 | `Enable_XOSC_Peri_Clock` | XOSC 已在运行 |
| 5 | `Init_Subsystem` | 外设时钟 |
| 6 | `Enable_Coprocessor` | (无依赖, 为对齐而保留) |
| 7 | `j main` | 所有初始化已完成 |

任意调换其中两步, 结果要么是崩溃 (没有栈), 要么是丢掉异常 (没有陷阱处理程序), 要么是悄悄失败 (外设需要时钟时时钟还没跑起来).

## Default_Trap_Handler

```asm
.global Default_Trap_Handler
.type Default_Trap_Handler, @function
Default_Trap_Handler:
  j     Default_Trap_Handler                     # 遇到意外陷阱就锁在这里
```

这是一个死循环 - 只要有陷阱触发 (非法指令, 未对齐访问, 未处理的中断), CPU 就锁在这里. 这是一个刻意的裸机调试设计: 程序停在一个已知地址上, 而不是继续执行随机的代码.

在调试器里, 如果你看到程序计数器卡在 `Default_Trap_Handler`, 就知道发生了意外异常. 接下来你可以查看 `mcause` CSR, 判断是哪种陷阱触发的.

## Init_Trap_Vector

```asm
.global Init_Trap_Vector
.type Init_Trap_Vector, @function
Init_Trap_Vector:
  la    t0, Default_Trap_Handler                 # 陷阱目标
  csrw  mtvec, t0                                # mtvec = 陷阱入口
  ret                                            # 返回
```

### `la t0, Default_Trap_Handler`

`la` 伪指令把 `Default_Trap_Handler` 的绝对地址装入 `t0`. 汇编器会把它展开成 `auipc`/`addi`, 以便处理完整的 32 位地址.

### `csrw mtvec, t0`

`csrw` (CSR Write, 写 CSR) 把 `t0` 写进 `mtvec` (Machine Trap Vector, 机器陷阱向量) CSR. 这条指令执行之后, 任何陷阱都会把 CPU 引到 `Default_Trap_Handler`.

`mtvec` 寄存器在 [1:0] 两位上存放模式:

| 模式 | 值 | 行为 |
|------|-------|-----------|
| Direct | `0` | 所有陷阱都去同一个地址 |
| Vectored | `1` | 异常去基地址, 中断去基地址 + 4*cause |

由于我们的处理程序地址是 4 字节对齐的 (由 `.align 2` 保证), 低两位就是 `00`, 也就是选择了直接模式. 所有陷阱都路由到同一个处理程序.

### 与 ARM 的对照

在 ARM Cortex-M33 上, 向量表是一种硬件结构. CPU 读取 `vector_table[exception_number]` 处的地址并跳过去. 那里根本不需要 `Init_Trap_Vector` 这样的调用 - 硬件会自动读表.

在 RISC-V 上, `mtvec` CSR 必须由软件显式编程. 如果没有 `Init_Trap_Vector`, `mtvec` 里就是 boot ROM 留下的值.

## 完整的启动时间线

```
Power-on
  │
  ├── Boot ROM scans flash → finds IMAGE_DEF at 0x10000000
  ├── Reads entry point (Reset_Handler) and stack (STACK_TOP)
  ├── Sets sp = 0x20082000, pc = Reset_Handler
  │
  └── Reset_Handler executes:
        ├── Init_Stack         → sp = 0x20082000 (re-affirmed)
        ├── Init_Trap_Vector   → mtvec = Default_Trap_Handler
        ├── Init_XOSC          → XOSC stable at 12 MHz
        ├── Enable_XOSC_Peri_Clock → peripheral clock = XOSC
        ├── Init_Subsystem     → IO_BANK0 released from reset
        ├── Enable_Coprocessor → (no-op)
        └── j main             → LED blink loop begins
```

## 小结

- `Reset_Handler` 是 boot ROM 读完 IMAGE_DEF 块之后调用的入口点.
- 它按严格的依赖顺序执行七个步骤: 栈 → 陷阱向量 → XOSC → 时钟 → 子系统 → 协处理器 → main.
- `Default_Trap_Handler` 是一个死循环, 把任何意外陷阱都拦在一个已知地址上.
- `Init_Trap_Vector` 编程 `mtvec` CSR, 把所有陷阱都路由到 `Default_Trap_Handler`.
- 最后的 `j main` 用的是无条件跳转 (而不是 `call`), 因为 `main` 永远不会返回.
- `.size` 指令记录了函数长度, 供调试器使用.
