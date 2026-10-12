# Chapter 24: reset_handler.s - 引导流程

## 引言

硬件装入栈指针并跳到复位向量之后, 就轮到 `Reset_Handler` 接管了. 它是我们写的第一段真正会执行的代码. 它的任务简单但关键: 按正确的顺序调用各个初始化函数, 然后把控制权交给主程序. 本章剖析这段引导流程, 并说明为什么顺序很重要.

## 完整源码

```asm
.syntax unified                                  // 使用统一汇编语法
.cpu cortex-m33                                  // 目标核心为 Cortex-M33
.thumb                                           // 使用 Thumb 指令集

.include "constants.s"

.section .text                                   // 代码段
.align 2                                         // 对齐到 4 字节边界

.global Reset_Handler                            // 导出 Reset_Handler 符号
.type Reset_Handler, %function
Reset_Handler:
  bl    Init_Stack                               // 初始化 MSP/PSP 与上限
  bl    Init_XOSC                                // 初始化外部晶振
  bl    Enable_XOSC_Peri_Clock                   // 使能 XOSC 外设时钟
  bl    Init_Subsystem                           // 初始化各子系统
  bl    Enable_Coprocessor                       // 启用 CP0 协处理器
  b     main                                     // 跳转到主循环
.size Reset_Handler, . - Reset_Handler
```

## 符号元数据

```asm
.global Reset_Handler                            // 导出 Reset_Handler 符号
.type Reset_Handler, %function
```

`Reset_Handler` 是全局符号, 因为 vector_table.s 引用了它. `.type` 指令把它标记为函数, 供链接器和调试器使用.

```asm
.size Reset_Handler, . - Reset_Handler
```

`.size` 计算函数的字节大小 (当前地址减去起始地址), 并把它记录到符号表里. 这有助于调试器显示函数的边界.

## 初始化顺序

每个 `bl` (带链接的分支) 调用完成一个初始化步骤:

### 第 1 步: Init_Stack (stack.s)

```asm
  bl    Init_Stack                               // 初始化 MSP/PSP 与上限
```

设置 MSP, PSP, MSPLIM 和 PSPLIM. 这一步必须放在最前面, 因为后面每个函数都要用栈 (push/pop).

**为什么要第一个?** 硬件已经从向量表装入了 MSP, 所以严格说栈已经能用. 但 Init_Stack 还会设置上限寄存器, 用来捕获溢出. 先调用它, 才能保证后续所有调用都处在溢出保护之下.

### 第 2 步: Init_XOSC (xosc.s)

```asm
  bl    Init_XOSC                                // 初始化外部晶振
```

配置外部晶振并等待它稳定. 芯片起初运行在内部环形振荡器上 (约 14.5 MHz). XOSC 提供一个稳定的 12 MHz 参考时钟.

**为什么要第二个?** 只有 XOSC 稳定之后, 才能把它当作外设的时钟源.

### 第 3 步: Enable_XOSC_Peri_Clock (xosc.s)

```asm
  bl    Enable_XOSC_Peri_Clock                   // 使能 XOSC 外设时钟
```

把 CLK_PERI 的时钟源配置为 XOSC, 并打开时钟输出.

**为什么要第三个?** 必须等 XOSC 稳定 (第 2 步) 之后, 才能把它接到外设上. 外设需要时钟才能工作.

### 第 4 步: Init_Subsystem (reset.s)

```asm
  bl    Init_Subsystem                           // 初始化各子系统
```

把 IO_BANK0 从复位中释放, 并等待复位过程完成.

**为什么要第四个?** 必须先让外设时钟跑起来 (第 3 步), 才能把外设从复位中释放. 没有时钟的外设无法完成它的复位流程.

### 第 5 步: Enable_Coprocessor (coprocessor.s)

```asm
  bl    Enable_Coprocessor                       // 启用 CP0 协处理器
```

通过修改 CPACR 并执行屏障指令, 授予对协处理器 0 (SIO) 的完全访问权限.

**为什么要第五个?** main 里的 GPIO 操作要用到协处理器. 必须保证在任何 `mcrr` 指令执行之前, 它已经被启用.

### 第 6 步: 跳到 main

```asm
  b     main                                     // 跳转到主循环
```

注意这里用的是 `b` (分支), 而不是 `bl` (带链接的分支). `b` 不保存返回地址, 因为 main 永远不会返回 - 它里面是一个死循环. 用 `b` 还有一个好处: Reset_Handler 也不必保存 LR, 因为它同样永不返回.

## 依赖链

初始化的顺序不是随便定的 - 每一步都依赖前一步:

```
Init_Stack
  |  (stack works)
  v
Init_XOSC
  |  (crystal stable)
  v
Enable_XOSC_Peri_Clock
  |  (peripheral clock running)
  v
Init_Subsystem
  |  (GPIO released from reset)
  v
Enable_Coprocessor
  |  (CP0 accessible)
  v
main
  |  (GPIO set/clear via mcrr)
```

如果跳过或调换任何一步:

| 缺失的步骤 | 后果 |
|-------------|-------------|
| Init_Stack | 栈溢出无法被发现 |
| Init_XOSC | 外设时钟没有稳定的时钟源 |
| Enable_XOSC_Peri_Clock | 外设没有时钟 |
| Init_Subsystem | GPIO 寄存器读出全零 |
| Enable_Coprocessor | `mcrr` 触发 UsageFault |

## Reset_Handler 不是普通函数

Reset_Handler 有几个特殊之处:

1. **永远不会被软件调用** - 只由硬件通过复位向量调用
2. **永远不会返回** - 它跳到 main, 而 main 会一直循环
3. **不保存/恢复寄存器** - 没有调用者需要它保留状态
4. **初始化调用用 `bl`** - 每个初始化函数都用 `bx lr` 返回
5. **main 用 `b`** - 这是尾调用, 不是函数调用

## 小结

- Reset_Handler 是硬件读完向量表之后执行的第一段代码.
- 它按严格的依赖顺序调用五个初始化函数.
- 每个 `bl` 调用的函数都用 `bx lr` 返回.
- 最后的 `b main` 是单向分支 - 固件从此不会再返回.
- 调换或跳过任何一步都会导致硬件异常或行为错误.
- `.size` 记录函数大小, 供调试器使用.
