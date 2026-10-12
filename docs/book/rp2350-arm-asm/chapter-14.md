# Chapter 14: 标签, 符号与符号表

## 引言

标签给内存地址起了名字. 闪烁驱动里每一个函数入口, 每一个循环目标, 每一个数据项, 都用标签标识. 汇编器把这些标签记录在符号表里, 链接器再用符号表解析跨文件引用并计算跳转目标. 本章考察标签和符号表在实际中是怎么工作的.

## 定义标签

标签就是一个标识符后面跟一个冒号:

```asm
main:                                            // 函数入口
  push  {r4-r12, lr}                             // 保存寄存器
```

汇编器把当前地址记录为标签 `main` 的值. 当别的指令引用 `main` 时, 汇编器或链接器就把这个地址代进去.

## 全局标签与局部标签

### 全局标签

全局标签在链接之后对所有目标文件可见. 它们必须用 `.global` 声明:

```asm
.global main                                     // 对链接器可见
main:                                            // 地址被全局记录
```

每个会被别的文件调用的函数都必须是全局的. 固件里有这些全局符号:

```
Reset_Handler    main
Init_Stack       GPIO_Config       GPIO_Set
Init_XOSC        GPIO_Clear        Delay_MS
Enable_XOSC_Peri_Clock
Init_Subsystem   Enable_Coprocessor
```

### 局部标签

没有 `.global` 的标签是文件局部的 - 在目标文件之外看不见:

```asm
.Loop:                                           // 只属于本文件
  mov   r0, #16
  bl    GPIO_Set
  ...
  b     .Loop                                    // 文件内部跳转
```

按惯例, 固件里的局部标签都以点开头 (`.Loop`, `.Wait_XOSC`, `.Delay_Loop`). 这样一眼就能看出区别.

## 固件里的标签类型

| 标签 | 文件 | 类型 | 用途 |
|-------|------|------|---------|
| `main` | main.s | 全局 | 程序入口 |
| `.Loop` | main.s | 局部 | 无限闪烁循环 |
| `GPIO_Config` | gpio.s | 全局 | GPIO 初始化函数 |
| `.Wait_XOSC` | xosc.s | 局部 | XOSC 轮询循环 |
| `.Wait_Reset` | reset.s | 局部 | 复位轮询循环 |
| `.Delay_Loop` | delay.s | 局部 | 延时计数循环 |
| `.Delay_Done` | delay.s | 局部 | 提前退出的目标 |
| `_vectors` | vector_table.s | 局部 | 向量表起始 |

## 符号表

汇编器会在每个目标文件 (.o) 里建立一张符号表. 每个表项包含:

| 字段 | 说明 |
|-------|-------------|
| Name | 标签字符串 |
| Value | 地址或常量值 |
| Section | 它位于哪个段 |
| Binding | 局部还是全局 |
| Type | 函数, 对象, 或者无类型 |

汇编完成之后, gpio.o 的符号表大致是这样:

```
Symbol           Value  Section  Bind    Type
GPIO_Config      0x00   .text    GLOBAL  FUNC
GPIO_Set         0x38   .text    GLOBAL  FUNC
GPIO_Clear       0x48   .text    GLOBAL  FUNC
```

在链接器分配最终地址之前, 这些值都是相对于段的.

## 符号表里的 `.equ` 常量

`.equ` 定义同样会在符号表里产生表项, 只不过值是绝对的:

```asm
.equ IO_BANK0_BASE, 0x40028000                   // 绝对符号
```

这类符号不属于任何段 - 它们是纯粹的数值常量. 汇编器在汇编期就把符号出现的位置替换成对应的值.

## 跨文件解析

当 main.s 引用 `GPIO_Set` 时:

```asm
  bl    GPIO_Set                                 // 引用外部符号
```

汇编器无法解析这个引用, 因为 `GPIO_Set` 定义在 gpio.s 里. 它在 main.o 里生成一条**重定位表项**:

```
Relocation: offset=0x10, type=R_ARM_THM_CALL, symbol=GPIO_Set
```

链接器读取 main.o 和 gpio.o, 在 gpio.o 的符号表里找到 `GPIO_Set`, 算出最终地址, 再用正确的偏移把 `bl` 指令打上补丁.

## 链接过程

```
+----------+       +----------+       +----------+
| main.o   |       | gpio.o   |       | delay.o  |
| (symbols |       | (symbols |       | (symbols |
|  + reloc)|       |  + reloc)|       |  + reloc)|
+----+-----+       +----+-----+       +----+-----+
     |                  |                  |
     +--------+---------+------------------+
                     LINKER
              |
        +-----+-------+
        | blink.elf   |
        | (all symbols|
        |  resolved)  |
        +-------------+
```

链接器做的事情是:

1. 收集所有目标文件里的所有段
2. 按链接脚本分配最终地址
3. 用合并后的符号表解析所有重定位
4. 生成最终的 ELF 二进制

## Thumb 位

在 Cortex-M 上, 所有函数地址的 bit 0 都必须置位, 用来表示 Thumb 模式. 对于 `bl` 的目标, 汇编器和链接器会自动处理. 在向量表里, 我们要显式设置:

```asm
  .word Reset_Handler + 1                        // 手动置 Thumb 位
```

硬件读到这个向量之后, 用 bit 0 来选择 Thumb 执行状态. 如果 bit 0 是清的, 就会触发 HardFault.

## 小结

- 标签给地址起名字; 它们是一切控制流和数据引用的基础.
- 全局标签 (`.global`) 跨文件可见; 局部标签只在文件内部可见.
- 符号表把每个标签映射到它的地址, 段和类型.
- `.equ` 创建绝对符号 - 不属于任何段的数值常量.
- 链接器通过合并符号表并修补重定位来解析跨文件引用.
- 在 Cortex-M 上, 函数地址必须置 Thumb 位 (bit 0), 执行才正确.
