# Chapter 13: 汇编器伪指令

## 引言

汇编器伪指令是发给汇编器本身的命令 - 它们不产生机器指令. 它们控制的是汇编器如何组织代码, 分配数据, 定义符号, 以及如何构造输出的目标文件. 我们的闪烁驱动依赖伪指令来建立段, 导出符号, 对齐数据和预留空间. 本章逐一记录固件里用到的伪指令, 并解释它们各自的作用.

## 语法与指令集伪指令

### `.syntax unified`

```asm
.syntax unified                                  // 使用统一的 ARM/Thumb 语法
```

每个源文件都以这条伪指令开头. 它告诉汇编器接受统一指令语法, 16 位和 32 位的 Thumb-2 编码会被自动选择. 没有它, 汇编器就会按旧的分离语法来解析.

### `.thumb`

```asm
.thumb                                           // 生成 Thumb 指令
```

它指定后面所有代码都汇编成 Thumb (16/32 位) 指令. Cortex-M33 只执行 Thumb 代码, 所以这条伪指令是必须的.

## 段伪指令

### `.section`

```asm
.section .text, "ax"                             // 可执行代码段
.section .rodata, "a"                            // 只读数据段
.section .data, "aw"                             // 可读写数据段
.section .bss, "aw", %nobits                     // 未初始化数据段
```

`.section` 把后面的代码或数据放进一个具名段里. 各个标志的含义是:

| 标志 | 含义 |
|------|---------|
| `a` | 可分配 (会占用内存) |
| `x` | 可执行 |
| `w` | 可写 |
| `%nobits` | 没有初始内容 (BSS) |

我们的固件用到了好几个段:

| 段 | 用途 | 使用位置 |
|---------|---------|---------|
| `.text` | 可执行代码 | 所有 .s 文件 |
| `.rodata` | 只读常量 | main.s |
| `.data` | 已初始化的变量 | main.s |
| `.bss` | 未初始化的变量 | main.s |
| `.picobin_block` | 引导镜像元数据 | image_def.s |
| `.vectors` | 中断向量表 | vector_table.s |

### `.align`

```asm
.align 2                                         // 对齐到 4 字节边界
```

`.align N` 用零填充, 直到当前地址是 2^N 字节的整数倍. `.align 2` 就是 4 字节对齐 (2^2 = 4).

在 vector_table.s 里:

```asm
.section .vectors, "a"                           // 向量表段
.align 2                                         // 4 字节对齐
```

向量表必须对齐, 因为 Cortex-M33 硬件是按 32 位字来读取它的.

## 符号伪指令

### `.global`

```asm
.global GPIO_Config                              // 导出符号
.global GPIO_Set                                 // 导出符号
.global GPIO_Clear                               // 导出符号
```

`.global` 让符号对链接器可见. 没有它, 符号就只存在于当前这个汇编文件里. 每个会被别的文件调用的函数都必须导出:

| 符号 | 定义位置 | 调用来源 |
|--------|-----------|------------|
| `Reset_Handler` | reset_handler.s | vector_table.s |
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

### `.extern`

```asm
.extern GPIO_Config                              // 导入外部符号
```

`.extern` 声明某个符号定义在别的文件里. 严格来说它是可选的 (汇编器默认把未知符号当作外部符号), 但它把意图写清楚了, 可读性更好.

### `.equ`

```asm
.equ STACK_TOP, 0x20082000                       // 定义常量
.equ XOSC_BASE, 0x40048000                       // 定义常量
```

`.equ` 定义一个具名常量. 它不产生任何代码或数据 - 符号出现的地方会被替换成它的值. 我们的 constants.s 整个文件都是 `.equ` 伪指令:

```asm
.equ IO_BANK0_BASE, 0x40028000                   // GPIO 控制基地址
.equ PADS_BANK0_BASE, 0x40038000                 // GPIO pad 基地址
.equ IO_BANK0_GPIO16_CTRL_OFFSET, 0x84           // GPIO16 控制寄存器偏移
.equ PADS_BANK0_GPIO16_OFFSET, 0x44              // GPIO16 pad 寄存器偏移
```

## 数据伪指令

### `.word`

```asm
.word STACK_TOP                                  // 写入 32 位值
.word Reset_Handler + 1                          // 写入带 Thumb 位的地址
```

`.word` 往当前段里写入一个 32 位值. 向量表用 `.word` 放置初始栈指针和复位处理程序地址:

```asm
_vectors:
  .word STACK_TOP                                // 初始 SP 值
  .word Reset_Handler + 1                        // 复位向量 (Thumb)
```

那个 `+ 1` 把 Thumb 位置起来, 告诉处理器以 Thumb 模式执行.

### `.byte`

```asm
.byte 0x42                                       // 写入 8 位值
```

用在 image_def.s 里, 负责 PICOBIN 块结构中的字节级字段.

### `.hword`

```asm
.hword 0x2101                                    // 写入 16 位值
```

用在 image_def.s 里, 负责半字 (16 位) 字段.

## 函数伪指令

### `.type` 与 `.thumb_func`

```asm
.type Reset_Handler, %function                   // 标记为函数符号
.thumb_func                                      // 在符号地址里置 Thumb 位
```

`.type` 告诉链接器这个符号是函数 (而不是数据). `.thumb_func` 保证符号地址的 bit 0 被置位, 这是在 Cortex-M 上正确跳转所必需的.

### `.size`

```asm
.size Reset_Handler, .-Reset_Handler             // 记录函数大小
```

`.size` 把函数的字节大小记录到符号表里. 表达式 `.-Reset_Handler` 算的是当前位置到函数起始处的距离.

## 包含伪指令

### `.include`

```asm
.include "constants.s"                           // 包含共享常量
```

`.include` 把另一个文件按文本插入到当前位置. 每个源文件都包含 constants.s, 以便使用共享的 `.equ` 定义.

## 小结

- `.syntax unified` 与 `.thumb` 确立指令集的上下文.
- `.section` 把代码和数据组织成具名区域, 供链接器使用.
- `.global` 与 `.extern` 控制符号跨文件的可见性.
- `.equ` 定义具名常量, 不产生任何代码.
- `.word`, `.byte` 与 `.hword` 写入原始数据值.
- `.type`, `.thumb_func` 与 `.size` 为链接器和调试器提供元数据.
- `.include` 让所有源文件共享同一份常量.
