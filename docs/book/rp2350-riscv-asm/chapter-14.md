# Chapter 14: 汇编器指示符

## 引言

汇编器指示符 (directive) 是给汇编器本身的命令 - 它们不会产生机器指令. 它们控制的是汇编器如何组织代码, 分配数据, 定义符号, 以及如何构造输出的目标文件. 我们的闪烁驱动靠指示符来建立段, 导出符号, 对齐数据, 以及引入共享常量. 本章逐一列出固件里用到的每一条指示符, 并说明它的作用.

## 段指示符

### `.section`

```asm
.section .text                                   # 代码段
.section .rodata                                 # 只读数据段
.section .data                                   # 数据段
.section .bss                                    # BSS 段
```

`.section` 把后面跟着的代码或数据放进一个具名的段里. 段可以带标志:

```asm
.section .vectors, "ax"                          # 向量表段
.section .picobin_block, "a"                     # 可分配, 不可执行
```

| 标志 | 含义 |
|------|---------|
| `a` | 可分配 (会占用内存) |
| `x` | 可执行 |
| `w` | 可写 |

我们的固件用到好几个段:

| 段 | 作用 | 用在哪里 |
|---------|---------|---------|
| `.text` | 可执行代码 | 所有 .s 文件 |
| `.rodata` | 只读常量 | main.s |
| `.data` | 已初始化变量 | main.s |
| `.bss` | 未初始化变量 | main.s |
| `.picobin_block` | 启动镜像元数据 | image_def.s |
| `.vectors` | 向量表 | vector_table.s |

### `.align`

```asm
.align 2                                         # 对齐到 4 字节边界
```

`.align N` 用零填充, 直到当前地址是 2^N 字节的整数倍. `.align 2` 就是 4 字节对齐 (2^2 = 4).

每个源文件都在 `.section .text` 之后用 `.align 2`, 确保指令从字边界开始. 在 vector_table.s 里:

```asm
.section .vectors, "ax"                          # 向量表段
.align 2                                         # 4 字节对齐
```

向量表必须对齐, 因为硬件是按 32 位字来读它的.

## 符号指示符

### `.global`

```asm
.global GPIO_Config                              # 导出符号
.global GPIO_Set                                 # 导出符号
.global GPIO_Clear                               # 导出符号
```

`.global` 让符号对链接器可见. 没有它, 符号就只存在于当前这个汇编文件里. 凡是要被别的文件调用的函数都必须导出:

| 符号 | 定义在 | 被谁调用 |
|--------|-----------|------------|
| `Reset_Handler` | reset_handler.s | vector_table.s, image_def.s |
| `Default_Trap_Handler` | reset_handler.s | vector_table.s |
| `Init_Trap_Vector` | reset_handler.s | (文件内部) |
| `Init_Stack` | stack.s | reset_handler.s |
| `Init_XOSC` | xosc.s | reset_handler.s |
| `Enable_XOSC_Peri_Clock` | xosc.s | reset_handler.s |
| `Init_Subsystem` | reset.s | reset_handler.s |
| `Enable_Coprocessor` | coprocessor.s | reset_handler.s |
| `main` | main.s | reset_handler.s |
| `GPIO_Config` | gpio.s | main.s |
| `GPIO_Set` | gpio.s | main.s |
| `GPIO_Clear` | gpio.s | main.s |
| `Delay_MS` | delay.s | main.s |

### `.type`

```asm
.type GPIO_Config, @function                     # 标记为函数符号
```

`.type` 告诉链接器这个符号是函数 (而不是数据). 在 RISC-V 上语法用 `@function` (不是 ARM 的 `%function`). 这些元数据能让调试器和反汇编器把代码显示正确.

### `.size`

```asm
.size Reset_Handler, . - Reset_Handler           # 记录函数大小
```

`.size` 把函数的字节大小记录到符号表里. 表达式 `. - Reset_Handler` 算的是当前位置到函数起始处的距离. 固件里只对 Reset_Handler 用了它.

### `.equ`

```asm
.equ STACK_TOP, 0x20082000                       # 定义常量
.equ XOSC_BASE, 0x40048000                       # 定义常量
```

`.equ` 定义一个具名常量. 它既不产生代码也不产生数据 - 符号在出现的地方直接被它的值替换掉. 我们的 constants.s 文件整个都是 `.equ` 指示符:

```asm
.equ IO_BANK0_BASE, 0x40028000                   # GPIO 控制基地址
.equ PADS_BANK0_BASE, 0x40038000                 # GPIO pad 基地址
.equ SIO_BASE, 0xd0000000                        # SIO GPIO 基地址
.equ SIO_GPIO_OUT_SET, SIO_BASE + 0x018          # GPIO 输出置位
.equ SIO_GPIO_OUT_CLR, SIO_BASE + 0x020          # GPIO 输出清零
.equ SIO_GPIO_OE_SET, SIO_BASE + 0x038           # GPIO 输出使能置位
```

## 数据指示符

### `.word`

```asm
.word Reset_Handler                              # 发出 32 位值
.word STACK_TOP                                  # 发出 32 位值
```

`.word` 往当前段里放一个 32 位值. 向量表用 `.word` 存放处理程序地址, PICOBIN 块则用它放入口点:

```asm
_vectors:
  .word Reset_Handler                            # 复位处理程序地址
  .word Default_Trap_Handler                     # 默认陷阱处理程序
```

注意: 和 ARM 不同, RISC-V 的向量表项不需要加 1 那个 Thumb 位. RISC-V 的地址是直接使用的.

### `.byte`

```asm
.byte 0x42                                       # 发出 8 位值
```

用在 image_def.s 里, 表示 PICOBIN 块结构中的字节级字段.

### `.hword`

```asm
.hword 0x1101                                    # 发出 16 位值
```

用在 image_def.s 里表示镜像类型字段: `0x1101` = EXE + RISCV + RP2350.

## 包含指示符

### `.include`

```asm
.include "constants.s"                           # 引入共享常量
```

`.include` 把另一个文件按文本原样插入到当前位置. 每个源文件都包含 constants.s, 以便使用共享的 `.equ` 定义. 这相当于 C 的 `#include` - 文件被逐字粘贴进来.

## 标签

标签给地址起名字. 标签就是任意标识符后面跟一个冒号:

```asm
main:                                            # 函数入口点
GPIO_Config:                                     # 函数入口点
.Loop:                                           # 局部跳转目标
.Delay_MS_Loop:                                  # 局部循环目标
```

### 全局标签与局部标签

**全局标签**在链接之后对所有目标文件都可见 (需要搭配 `.global`):

```asm
.global main                                     # 对链接器可见
main:                                            # 地址被记录为全局
```

**局部标签** (以 `.` 开头) 是文件私有的 - 在目标文件外面看不见:

```asm
.Loop:                                           # 只属于本文件
  li    a0, 16
  call  GPIO_Set
  ...
  j     .Loop                                    # 文件内部跳转
```

## 符号表

汇编器会为每个目标文件建一张符号表. 每个表项包含:

| 字段 | 说明 |
|-------|-------------|
| Name | 标签字符串 |
| Value | 地址或常量值 |
| Section | 它位于哪个段 |
| Binding | 局部还是全局 |
| Type | 函数, 对象, 或 notype |

链接器把所有目标文件的符号表合并起来, 解决跨文件引用, 并把最终地址回填到指令里.

## 跨文件解析

当 main.s 引用 `GPIO_Set` 时:

```asm
  call  GPIO_Set                                 # 引用外部符号
```

汇编器会生成一条重定位记录. 链接器读取 main.o 和 gpio.o, 在 gpio.o 的符号表里找到 `GPIO_Set`, 算出最终地址, 然后用正确的偏移回填 `auipc`+`jalr` 这一对指令.

## 与 ARM 对照

| 特性 | ARM | RISC-V |
|---------|-----|--------|
| 指令集指示符 | `.syntax unified` + `.thumb` | 不需要 |
| 函数标记 | `.thumb_func` | `.type name, @function` |
| 函数类型语法 | `%function` | `@function` |
| 向量表地址 | 需要加 1 那个 Thumb 位 | 直接用地址 |
| 代码里的注释符 | `//` | `#` |

RISC-V 需要的指示符更少, 因为它的 ISA 没有 Thumb/ARM 模式切换这回事.

## 小结

- `.section` 把代码和数据组织成链接器能识别的具名区域.
- `.align 2` 保证指令和数据 4 字节对齐.
- `.global` 和 `.type` 控制符号的可见性与元数据.
- `.equ` 定义具名常量, 但不产生代码.
- `.word`, `.byte` 和 `.hword` 发出原始数据值.
- `.include` 让所有源文件共享常量.
- 标签给地址起名; 全局标签对链接器可见, 局部标签是文件私有的.
