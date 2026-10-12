# Chapter 19: 链接脚本

## 引言

链接脚本是一张蓝图, 它把一堆目标文件变成 RP2350 能执行的单一二进制. 它决定代码在 flash 里的位置, 栈在 RAM 里的位置, 以及各个段出现的顺序. 链接脚本写错了, 引导 ROM 就找不到 PICOBIN 块, 向量表可能没对齐, 处理器永远也到不了我们的代码. 本章逐行讲解我们的 linker.ld.

## 入口点

```ld
ENTRY(Reset_Handler)
```

它告诉链接器以及各类工具链程序 (调试器, 烧录工具): `Reset_Handler` 是程序的入口点. 在 Cortex-M 上, 真正执行的第一条指令来自向量表里的复位向量, 但 `ENTRY` 为工具链提供了元数据.

## 内存常量

```ld
__XIP_BASE   = 0x10000000;
__XIP_SIZE   = 32M;

__SRAM_BASE  = 0x20000000;
__SRAM_SIZE  = 512K;                             /* 非安全窗口 */
__STACK_SIZE = 32K;
```

它们定义了 RP2350 的物理内存布局:

| 符号 | 值 | 说明 |
|--------|-------|-------------|
| `__XIP_BASE` | `0x10000000` | Flash 起始 (XIP = Execute In Place, 原地执行) |
| `__XIP_SIZE` | 32 MB | Flash 容量 |
| `__SRAM_BASE` | `0x20000000` | SRAM 起始 |
| `__SRAM_SIZE` | 512 KB | SRAM 容量 |
| `__STACK_SIZE` | 32 KB | 栈的预留大小 |

## 内存区域

```ld
MEMORY
{
  RAM   (rwx) : ORIGIN = __SRAM_BASE, LENGTH = __SRAM_SIZE
  FLASH (rx)  : ORIGIN = __XIP_BASE,  LENGTH = __XIP_SIZE
}
```

`MEMORY` 块定义了两个区域:

- **FLASH**: 只读可执行 - 存放所有代码和常量
- **RAM**: 可读可写可执行 - 存放栈和数据

链接器用它们来校验各个段是否放得下, 并计算绝对地址.

## 程序头

```ld
PHDRS
{
  text PT_LOAD FLAGS(5);                         /* RX */
}
```

程序头描述可加载段, 供烧录 flash 的工具使用. `FLAGS(5)` 表示可读 (4) + 可执行 (1). 我们的固件只有一个可加载段, 里面是全部 flash 内容.

## 段的位置

### `.embedded_block` - PICOBIN 元数据

```ld
  . = ORIGIN(FLASH);

  .embedded_block :
  {
    KEEP(*(.embedded_block))
  } > FLASH :text
```

位置计数器 (`.`) 从 flash 起始处 (`0x10000000`) 开始. `.embedded_block` 段被放在最前面. `KEEP` 阻止链接器在垃圾回收时丢弃这个段, 尽管没有任何代码直接引用它 - 引导 ROM 是按位置读取它的.

这个段里放着来自 image_def.s 的 PICOBIN 块, 引导 ROM 用它来识别并校验固件镜像.

### `.vectors` - 向量表

```ld
  .vectors ALIGN(128) :
  {
    KEEP(*(.vectors))
  } > FLASH :text

  ASSERT(((ADDR(.vectors) - ORIGIN(FLASH)) < 0x1000),
         "Vector table must be in first 4KB of flash")
```

`ALIGN(128)` 保证向量表从 128 字节边界开始. Cortex-M33 的 VTOR 寄存器要求向量表至少按"已实现的向量数向上取到 2 的幂再乘以 4"对齐.

`ASSERT` 校验向量表落在 flash 的前 4 KB 之内. RP2350 的引导 ROM 只在前 4 KB 里搜索向量表.

### `.text` - 代码与只读数据

```ld
  .text :
  {
    . = ALIGN(4);
    *(.text*)
    *(.rodata*)
    KEEP(*(.ARM.attributes))
  } > FLASH :text
```

所有可执行代码和只读数据都合并进 flash 里的 `.text` 输出段. 通配符 `*(.text*)` 能匹配 `.text`, `.text.main`, `.text.GPIO_Config` 等等.

`KEEP(*(.ARM.attributes))` 保留 ARM 架构元数据, 工具可能会用到.

`.  = ALIGN(4)` 保证这个段从 4 字节边界开始, 从而让指令正确对齐.

### 栈符号

```ld
  __StackTop   = ORIGIN(RAM) + LENGTH(RAM);
  __StackLimit = __StackTop - __STACK_SIZE;
  __stack      = __StackTop;
```

这些链接器符号定义了栈的边界:

| 符号 | 值 | 说明 |
|--------|-------|-------------|
| `__StackTop` | `0x20080000` | SRAM 顶部 = 栈顶 |
| `__StackLimit` | `0x20078000` | 栈顶往下 32 KB |
| `__stack` | `0x20080000` | 栈顶的别名 |

注意: 我们的固件用的是 constants.s 里的 `.equ` 常量 (`STACK_TOP = 0x20082000`, `STACK_LIMIT = 0x2007a000`), 而不是这些链接器符号. 两种做法都可行.

### `.stack` 段

```ld
  .stack (NOLOAD) : { . = ALIGN(8); } > RAM

  PROVIDE(__Vectors = ADDR(.vectors));
```

`NOLOAD` 表示这个段在 RAM 里占用地址空间, 但在 flash 镜像里没有内容. 栈只在运行时存在 - 它不需要从 flash 初始化.

`PROVIDE(__Vectors = ADDR(.vectors))` 把向量表地址导出, 供可能需要它的代码使用.

## 最终的内存布局

```
Flash (0x10000000):
+-----------------------------+ 0x10000000
| .embedded_block (PICOBIN)   |
+-----------------------------+ ~0x10000014
| (padding to 128-byte align) |
+-----------------------------+ 0x10000080
| .vectors (SP, Reset_Handler)|
+-----------------------------+ 0x10000088
| .text (all code + rodata)   |
|                             |
+-----------------------------+ ~0x10000400

RAM (0x20000000):
+-----------------------------+ 0x20000000
| (available RAM)             |
+-----------------------------+
| .stack (32 KB)              |
+-----------------------------+ 0x20080000
```

## 小结

- `ENTRY(Reset_Handler)` 为工具链程序指明程序的入口点.
- `MEMORY` 定义 flash 在 `0x10000000` (32 MB), RAM 在 `0x20000000` (512 KB).
- `.embedded_block` 必须排在 flash 最前面, 引导 ROM 才能找到 PICOBIN 块.
- `.vectors` 对齐到 128 字节, 并且必须落在 flash 的前 4 KB 之内.
- `.text` 包含所有可执行代码和只读数据.
- 栈符号在 SRAM 顶部定义了一个 32 KB 的栈, 用 `NOLOAD` 表示不含 flash 内容.
- 链接脚本是汇编器相对地址与处理器绝对内存映射之间的桥梁.
