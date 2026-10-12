# Chapter 23: 栈与向量表 - `stack.s` 和 `vector_table.s`

## 简介

两个很小的文件搭起了其他所有函数都依赖的地基: `stack.s` 给我们一个能用的栈, `vector_table.s` 提供链接脚本所期望的向量段. 它们共同保证 `call`/`ret` 能正确工作, 也保证引导镜像具备正确的布局.

## `stack.s` 完整源码

```asm
.include "constants.s"

.section .text                                   # 代码段
.align 2                                         # 对齐到 4 字节边界

.global Init_Stack
.type Init_Stack, @function
Init_Stack:
  li    sp, STACK_TOP                            # 把 SP 设为 RAM 栈的顶部
  ret                                            # 返回
```

## 栈的初始化 - 逐行讲解

### 段与对齐

```asm
.section .text                                   # 代码段
.align 2                                         # 对齐到 4 字节边界
```

这个函数位于 `.text` (flash 中的可执行代码). `.align 2` 保证第一条指令从 4 字节边界开始, 这是标准 (非压缩) RISC-V 指令的要求.

### 函数声明

```asm
.global Init_Stack
.type Init_Stack, @function
```

`.global` 把符号导出, 这样其他文件才能 `call Init_Stack`. `.type @function` 把它标记为函数, 供链接器和调试器识别.

### 加载栈指针

```asm
Init_Stack:
  li    sp, STACK_TOP                            # 把 SP 设为 RAM 栈的顶部
  ret                                            # 返回
```

`li sp, STACK_TOP` 是一条伪指令, 它把立即数 `0x20082000` 装入寄存器 `sp` (x2). 汇编器会按需把它展开成 `lui`/`addi`, 从而拼出完整的 32 位值.

`STACK_TOP` (`0x20082000`) 是 520 KB SRAM 区域的最高地址. 栈向下生长 - 每条 `addi sp, sp, -N` 都把指针朝 `STACK_LIMIT` (`0x2007a000`) 推进, 这样我们就有了 32 KB 的栈空间.

### 为什么要写成一个函数?

在 RISC-V 上, 引导程序会在跳转到 `Reset_Handler` 之前从 IMAGE_DEF 块里加载栈指针. `Reset_Handler` 里显式调用 `Init_Stack` 会把它重新设到一个已知状态, 这既与 ARM 工程的结构保持一致, 也保证了无论引导程序怎么表现, 栈都是确定地设置好的.

## `vector_table.s` 完整源码

```asm
.include "constants.s"

.section .vectors, "ax"                          # 向量表段
.align 2                                         # 对齐到 4 字节边界

.global _vectors                                 # 导出 _vectors 符号
_vectors:
  .word Reset_Handler                            # 复位处理程序地址占位
  .word Default_Trap_Handler                     # 默认陷阱处理程序地址占位
```

## 向量表 - 逐行讲解

### 段声明

```asm
.section .vectors, "ax"                          # 向量表段
.align 2                                         # 对齐到 4 字节边界
```

`"ax"` 标志表示可分配且可执行. 链接脚本把这个段放在 IMAGE_DEF 块之后, 并按 128 字节对齐:

```ld
.vectors ALIGN(128) :
{
  KEEP(*(.vectors))
} > FLASH :text
```

链接脚本里的 `ASSERT` 会检查向量表是否仍然落在 flash 的前 4 KB 之内.

### 向量条目

```asm
.global _vectors                                 # 导出 _vectors 符号
_vectors:
  .word Reset_Handler                            # 复位处理程序地址占位
  .word Default_Trap_Handler                     # 默认陷阱处理程序地址占位
```

每个 `.word` 都会产生一个 4 字节的值 - 即某个处理程序的绝对地址, 由链接器解析.

| 偏移 | 条目 | 用途 |
|--------|-------|---------|
| `+0x00` | `Reset_Handler` | 复位后的入口点 |
| `+0x04` | `Default_Trap_Handler` | 未处理陷阱的兜底 |

### RISC-V 的陷阱处理与 ARM 向量表的区别

在 ARM Cortex-M33 上, 向量表由硬件索引 - CPU 读取 `(exception_number * 4)` 处的向量并自动跳转过去. 向量表必须为每一种可能的异常都准备条目.

在 RISC-V 上, 陷阱处理的方式不一样. `mtvec` CSR 里存放的是单个陷阱处理程序的地址. 所有陷阱 - 无论来自异常, 中断还是非法指令 - 都跳到那一个地址. 我们的向量表段主要是为了兼容链接器布局而存在的; 真正的陷阱分发是由 `Init_Trap_Vector` 里的 `csrw mtvec` 控制的.

那两个 `.word` 条目起到文档作用, 并提供了其他代码可以引用的符号.

## 它们如何配合

启动过程中, 执行顺序是:

```
Boot ROM reads IMAGE_DEF → Loads SP from STACK_TOP → Jumps to Reset_Handler
  │
  └── Reset_Handler calls Init_Stack
        │
        └── li sp, STACK_TOP    ← sp is now guaranteed set
              ret
```

`Init_Stack` 返回之后, 栈就准备好了. 之后每条 `call` 指令都把 `ra` (返回地址) 压入栈, 每条 `ret` 再把它弹回来.

## 内存布局

```
0x10000000          IMAGE_DEF block (image_def.s)
0x10000080          Vector table (vector_table.s, 128-byte aligned)
  +0x00             Reset_Handler address
  +0x04             Default_Trap_Handler address
0x10000088          .text section starts (Init_Stack, etc.)
```

`.vectors` 段只占 8 个字节, 但按链接脚本断言的要求对齐到 128 字节.

## 与 ARM 的对照

| 方面 | ARM | RISC-V |
|--------|-----|--------|
| 栈初始化 | `ldr sp, =_estack` | `li sp, STACK_TOP` |
| 向量表 | 约 16 个以上条目 (NMI, HardFault 等) | 2 个条目 (为了兼容) |
| 陷阱分发 | 硬件查向量表 | `mtvec` CSR → 单个处理程序 |
| 向量段名 | `.isr_vector` | `.vectors` |
| 对齐 | 硬件要求 | 链接脚本断言要求 |

## 小结

- `Init_Stack` 用 `li` 伪指令把栈指针设为 `STACK_TOP` (`0x20082000`).
- 栈向下生长, 在到达 `STACK_LIMIT` 之前有 32 KB 空间.
- `vector_table.s` 定义了一个 `.vectors` 段, 里面有两个条目: `Reset_Handler` 和 `Default_Trap_Handler`.
- 在 RISC-V 上, 真正的陷阱向量是通过 `csrw mtvec` 设置的, 而不是靠硬件查向量表.
- 链接脚本把 `.vectors` 对齐到 128 字节, 并断言它落在 flash 的前 4 KB 之内.
- 这两个文件都很小, 但不可或缺 - 没有它们, 栈就没有初始化, 链接布局也不完整.
