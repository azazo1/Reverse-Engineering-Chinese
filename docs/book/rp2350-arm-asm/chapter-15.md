# Chapter 15: 段, 内存布局与链接脚本

## 引言

汇编源文件把代码和数据组织进**段**. 链接脚本再把这些段映射到物理内存区域 - flash 和 RAM. 段和链接脚本合在一起, 决定了闪烁固件在运行时每一个字节待在哪里. 本章解释我们的 linker.ld 如何把代码放进 flash, 在 RAM 里预留栈, 并施加对齐与大小约束.

## 什么是段?

段是目标文件里一块具名的内容. 汇编器把每条指令或每个数据项放进当前段:

```asm
.section .text, "ax"                             // 代码放在这里
  push  {r4-r12, lr}                             // 这条指令位于 .text

.section .rodata, "a"                            // 只读数据放在这里
```

固件里用到的标准段:

| 段 | 内容 | 标志 | 位置 |
|---------|---------|-------|----------|
| `.picobin_block` | 引导镜像元数据 | alloc | Flash 起始处 |
| `.vectors` | 向量表 | alloc | Flash (picobin 之后) |
| `.text` | 可执行代码 | alloc, exec | Flash |
| `.rodata` | 只读常量 | alloc | Flash |
| `.data` | 已初始化的变量 | alloc, write | RAM (从 flash 复制) |
| `.bss` | 未初始化的变量 | alloc, write, nobits | RAM |
| `.stack` | 栈空间 | - | RAM (SRAM 顶部) |

## 我们的链接脚本

链接脚本 (linker.ld) 定义内存区域和段的位置:

### 内存区域

```ld
MEMORY
{
  FLASH (rx)  : ORIGIN = 0x10000000, LENGTH = 32M
  RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 512K
}
```

| 区域 | 起始地址 | 大小 | 权限 |
|--------|--------------|------|-------------|
| FLASH | `0x10000000` | 32 MB | 读, 执行 |
| RAM | `0x20000000` | 512 KB | 读, 写, 执行 |

### 段的位置

`SECTIONS` 块把每个段映射到一个内存区域:

```ld
SECTIONS
{
  .embedded_block : {
    KEEP(*(.picobin_block))
  } > FLASH

  .vectors : ALIGN(128) {
    *(.vectors)
  } > FLASH

  ASSERT(SIZEOF(.vectors) <= 4096, "Vector table too large")

  .text : {
    *(.text*)
    *(.rodata*)
  } > FLASH

  .stack (NOLOAD) : {
    . = ALIGN(8);
    . = . + STACK_SIZE;
  } > RAM
}
```

## 逐段讲解

### `.embedded_block` - PICOBIN 元数据

```ld
  .embedded_block : {
    KEEP(*(.picobin_block))
  } > FLASH
```

`KEEP` 伪指令阻止链接器在垃圾回收时丢弃这个段. PICOBIN 块必须在 flash 起始处, RP2350 的引导 ROM 才能识别这个镜像.

### `.vectors` - 向量表

```ld
  .vectors : ALIGN(128) {
    *(.vectors)
  } > FLASH
```

`ALIGN(128)` 保证向量表从 128 字节边界开始. Cortex-M33 要求向量表至少按"已实现的向量数向上取到 2 的幂"对齐.

`ASSERT` 检查向量表不超过 4096 字节 - 这是一条安全约束.

### `.text` 与 `.rodata` - 代码与常量

```ld
  .text : {
    *(.text*)
    *(.rodata*)
  } > FLASH
```

所有可执行代码和只读数据都放在 flash 里. 通配符 `*(.text*)` 能匹配 `.text`, `.text.main`, `.text.GPIO_Config` 等等.

### `.stack` - 栈的预留

```ld
  STACK_SIZE = 32K;

  .stack (NOLOAD) : {
    . = ALIGN(8);
    . = . + STACK_SIZE;
  } > RAM
```

`NOLOAD` 表示这个段占用地址空间, 但不从 flash 加载 - 栈只在运行时存在. 预留的 32 KB 对我们这个调用深度很浅的固件来说绰绰有余.

## 最终的内存映射

链接之后, 固件占据从 `0x10000000` 开始的 flash:

```
Flash (0x10000000):
+------------------------------+
| .picobin_block (metadata)    |  ~20 bytes
+------------------------------+
| .vectors (SP, Reset_Handler) |  8 bytes (2 words)
+------------------------------+
| .text (all code)             |  ~1 KB
| .rodata (constants)          |
+------------------------------+

RAM (0x20000000):
+----------------------------+
| .data / .bss               |  (unused in our firmware)
+----------------------------+
| .stack (32 KB)             |
+----------------------------+
|        ...                 |
| STACK_TOP = 0x20082000     |
+----------------------------+
```

## `ENTRY` 伪指令

```ld
ENTRY(Reset_Handler)
```

它告诉链接器哪个符号是程序入口点. 调试器和烧录工具会用到这个信息. 在 Cortex-M 上, 真正的执行是从向量表里的复位向量开始的, 但 `ENTRY` 为工具链提供了元数据.

## 链接脚本导出的符号

链接脚本可以定义能从汇编里访问的符号:

```ld
  _stack_top = ORIGIN(RAM) + LENGTH(RAM);
```

我们的固件改用 constants.s 里的 `.equ` 常量, 不过在更大的项目里, 用链接脚本定义符号来把配置和代码分开是很常见的做法.

## 段为什么重要

没有段, 链接器就无从知道:

- 哪些字节是可执行代码 (flash), 哪些是数据 (RAM)
- 什么必须排在最前面 (PICOBIN 块)
- 需要什么样的对齐 (向量表)
- 什么只在运行时存在, 不该占用 flash (栈)

段这套机制让十个独立的汇编文件各自贡献代码, 最终拼成一个顺序正确, 完整可用的二进制.

## 小结

- 段把代码和数据组织成带特定属性的具名块.
- 链接脚本把段映射到物理内存区域 (flash 与 RAM).
- `.embedded_block` (PICOBIN) 必须排在 flash 最前面, 引导 ROM 才能找到它.
- `.vectors` 按硬件要求对齐到 128 字节.
- `.text` 包含所有可执行代码, 放在 flash 里.
- `.stack` 在 RAM 里预留 32 KB, 用 `NOLOAD` 表示不含 flash 内容.
- `ENTRY` 伪指令为工具指明程序入口点.
