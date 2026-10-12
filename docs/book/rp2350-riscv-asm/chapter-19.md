# Chapter 19: 链接脚本 - 把代码放进内存

## 引言

链接脚本是一张蓝图, 它把一堆目标文件变成一个 RP2350 能执行的单一二进制. 它定义了代码放在 flash 的什么位置, 栈在 RAM 的什么位置, 以及各个段的排列顺序. 没有一份正确的链接脚本, boot ROM 就找不到 PICOBIN 块, 向量表可能对不齐, 处理器也就永远跑不到我们的代码. 本章逐行讲解我们的 linker.ld.

## 入口点

```ld
ENTRY(Reset_Handler)
```

这告诉链接器以及所有工具链工具 (调试器, 烧录工具), `Reset_Handler` 是程序的入口点. 在 RISC-V 上, boot ROM 是读 PICOBIN 块来找到入口点的, 而 `ENTRY` 提供的是给工具链用的元数据.

## 内存常量

```ld
__XIP_BASE   = 0x10000000;
__XIP_SIZE   = 32M;

__SRAM_BASE  = 0x20000000;
__SRAM_SIZE  = 512K;
__STACK_SIZE = 32K;
```

这些定义了 RP2350 的物理内存布局:

| 符号 | 值 | 说明 |
|--------|-------|-------------|
| `__XIP_BASE` | `0x10000000` | Flash 起始 (XIP = Execute In Place, 就地执行) |
| `__XIP_SIZE` | 32 MB | Flash 容量 |
| `__SRAM_BASE` | `0x20000000` | SRAM 起始 |
| `__SRAM_SIZE` | 512 KB | SRAM 容量 |
| `__STACK_SIZE` | 32 KB | 栈预留大小 |

## 内存区域

```ld
MEMORY
{
  RAM   (rwx) : ORIGIN = __SRAM_BASE, LENGTH = __SRAM_SIZE
  FLASH (rx)  : ORIGIN = __XIP_BASE,  LENGTH = __XIP_SIZE
}
```

`MEMORY` 块定义了两个区域:

- **FLASH**: 只可读可执行 - 存放所有代码和常量
- **RAM**: 可读可写可执行 - 存放栈和数据

链接器用它们来检查各个段是否放得进所属区域, 并据此算出绝对地址.

## 程序头

```ld
PHDRS
{
  text PT_LOAD FLAGS(5);                         /* RX */
}
```

程序头描述的是可加载的段, 供那些往 flash 里烧写的工具使用. `FLAGS(5)` 表示可读 (4) 加可执行 (1). 我们的固件只有一个可加载段, 里面装着 flash 的全部内容.

## 段的放置

### `.embedded_block` - PICOBIN 元数据

```ld
  . = ORIGIN(FLASH);

  .embedded_block :
  {
    KEEP(*(.embedded_block))
    KEEP(*(.picobin_block))
  } > FLASH :text
```

位置计数器 (`.`) 从 flash 起始处 (`0x10000000`) 开始. `.embedded_block` 段被放在最前面. `KEEP` 阻止链接器在垃圾回收时丢掉这个段 - 尽管没有任何代码直接引用它, 但 boot ROM 是按位置去读它的.

这个段里装着来自 image_def.s 的 PICOBIN 块, boot ROM 用它来:
1. 确认这个镜像是合法固件
2. 判断架构 (RISC-V, 来自 `0x1101`)
3. 找到入口点 (`Reset_Handler`)
4. 读出初始栈指针的值

### `.vectors` - 向量表

```ld
  .vectors ALIGN(128) :
  {
    KEEP(*(.vectors))
  } > FLASH :text

  ASSERT(((ADDR(.vectors) - ORIGIN(FLASH)) < 0x1000),
         "Vector table must be in first 4KB of flash")
```

`ALIGN(128)` 保证向量表从 128 字节边界开始. 在 RISC-V 上, `mtvec` 要求陷阱向量至少 4 字节对齐 (直接模式), 或者按 2 的幂对齐 (向量模式). 128 字节对齐能同时兼容这两种模式.

`ASSERT` 用来验证向量表落在 flash 的前 4 KB 之内 - 这是 boot ROM 的要求.

### `.text` - 代码与只读数据

```ld
  .text :
  {
    . = ALIGN(4);
    *(.text*)
    *(.rodata*)
  } > FLASH :text
```

所有可执行代码和只读数据都被合并进 flash 里的 `.text` 输出段. 通配符 `*(.text*)` 能匹配 `.text`, `.text.main`, `.text.GPIO_Config` 等等.

`. = ALIGN(4)` 保证这个段从 4 字节边界开始, 好让指令正确对齐.

### 栈符号

```ld
  __StackTop   = ORIGIN(RAM) + LENGTH(RAM);
  __StackLimit = __StackTop - __STACK_SIZE;
  __stack      = __StackTop;
```

这些链接器符号定义了栈的边界:

| 符号 | 值 | 说明 |
|--------|-------|-------------|
| `__StackTop` | `0x20080000` | SRAM 顶端 = 栈顶 |
| `__StackLimit` | `0x20078000` | 顶端往下 32 KB |
| `__stack` | `0x20080000` | 栈顶的别名 |

注意: 我们的固件用的是 constants.s 里的 `.equ` 常量 (`STACK_TOP = 0x20082000`, `STACK_LIMIT = 0x2007a000`), 而不是这些链接器符号. 两种做法都可行.

### `.stack` 段

```ld
  .stack (NOLOAD) : { . = ALIGN(8); } > RAM

  PROVIDE(__Vectors = ADDR(.vectors));
```

`NOLOAD` 表示这个段在 RAM 里占地址空间, 但在 flash 镜像里没有内容. 栈只存在于运行时 - 它不需要从 flash 初始化.

`PROVIDE(__Vectors = ADDR(.vectors))` 把向量表的地址导出, 供可能用到它的代码取用.

## 最终的内存布局

```
Flash (0x10000000):
+-----------------------------+ 0x10000000
| .embedded_block (PICOBIN)   |  ~24 bytes
+-----------------------------+
| (padding to 128-byte align) |
+-----------------------------+ 0x10000080
| .vectors (handler addresses)|  8 bytes (2 words)
+-----------------------------+ 0x10000088
| .text (all code + rodata)   |
|                             |  ~1 KB
+-----------------------------+

RAM (0x20000000):
+-----------------------------+ 0x20000000
| (available RAM)             |
+-----------------------------+
| .stack (32 KB)              |
+-----------------------------+ 0x20080000
```

## 每个段为什么重要

| 段 | 缺失会怎样 |
|---------|------------------------|
| `.embedded_block` | boot ROM 找不到 PICOBIN - 镜像被拒 |
| `.vectors` | 没有陷阱处理程序地址 - 一出错就死锁 |
| `.text` | 没有可执行代码 - 无事可做 |
| `.stack` | 没有栈空间 - 第一次函数调用就把内存搞坏 |

## 小结

- `ENTRY(Reset_Handler)` 为工具链工具标明程序入口点.
- `MEMORY` 把 flash 定在 `0x10000000` (32 MB), 把 RAM 定在 `0x20000000` (512 KB).
- `.embedded_block` 必须排在 flash 最前面, boot ROM 才能找到 PICOBIN 块.
- `.vectors` 按 128 字节对齐, 并且必须落在 flash 前 4 KB 之内.
- `.text` 装着所有可执行代码和只读数据.
- 栈符号在 SRAM 顶端定义了一个 32 KB 的栈, 用 `NOLOAD` 表示它不占 flash 内容.
- 链接脚本是汇编器的相对地址和处理器绝对内存映射之间的桥梁.
