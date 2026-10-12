# Chapter 21: 引导元数据 - `image_def.s`

## 简介

在 RP2350 执行任何代码之前, boot ROM 必须先在前 4 KB flash 里找到一个合法的 IMAGE_DEF 块. 这个块告诉引导程序它正在加载什么类型的镜像 - CPU 架构, 入口点, 以及初始栈指针. 没有它, 芯片看到的只是空白或者无法识别的 flash, 于是拒绝启动. 本章我们逐字节走一遍 `image_def.s`.

## 完整源码

```asm
.include "constants.s"

.section .picobin_block, "a"                     # 把 IMAGE_DEF 块放在 flash 中
.align  2
embedded_block:
.word  0xffffded3                                # PICOBIN_BLOCK_MARKER_START
.byte  0x42                                      # PICOBIN_BLOCK_ITEM_1BS_IMAGE_TYPE
.byte  0x1                                       # 条目大小为 1 个字
.hword 0x1101                                    # EXE + RISCV + RP2350

.byte  0x44                                      # PICOBIN_BLOCK_ITEM_1BS_ENTRY_POINT
.byte  0x3                                       # 到下一个条目还有 3 个字
.byte  0x0                                       # 填充
.byte  0x0                                       # 填充
.word  Reset_Handler                             # RISC-V 复位入口点
.word  STACK_TOP                                 # 初始栈指针的值

.byte  0xff                                      # PICOBIN_BLOCK_ITEM_2BS_LAST
.hword (embedded_block_end - embedded_block - 16) / 4
.byte  0x0                                       # 填充
.word  0x0                                       # 指向下一个块的相对指针 (0 = 回到自身)
.word  0xab123579                                # PICOBIN_BLOCK_MARKER_END
embedded_block_end:
```

## 段的位置

```asm
.section .picobin_block, "a"                     # 把 IMAGE_DEF 块放在 flash 中
.align  2
```

`.section .picobin_block, "a"` 指令创建了一个带可分配标志 (`"a"`) 的具名段. 链接脚本把这个段放在 flash 的最前面:

```ld
.embedded_block :
{
  KEEP(*(.embedded_block))
  KEEP(*(.picobin_block))
} > FLASH :text
```

`KEEP` 保证链接器永远不会丢弃这个段, 即使没有任何代码引用它 - boot ROM 是直接扫描 flash 的原始字节来读取它的.

`.align 2` 会填充到 4 字节边界, 保证后面跟着的 `.word` 指令自然对齐.

## 起始标记

```asm
embedded_block:
.word  0xffffded3                                # PICOBIN_BLOCK_MARKER_START
```

boot ROM 会在 flash 的前 4 KB 里扫描这个魔数. 一旦找到 `0xffffded3`, 它就开始解析这个块. 标号 `embedded_block` 记录了起始地址, 供后面的大小计算使用.

## 镜像类型条目

```asm
.byte  0x42                                      # PICOBIN_BLOCK_ITEM_1BS_IMAGE_TYPE
.byte  0x1                                       # 条目大小为 1 个字
.hword 0x1101                                    # EXE + RISCV + RP2350
```

### 条目标签: `0x42`

PICOBIN 条目用一个标签字节来标识自己的类型. `0x42` 表示 "镜像类型, 单字节大小".

### 大小: `0x01`

大小字节表示 "后面跟着 1 个字的负载". 这个字就是 `.hword 0x1101` (填充之后才符合条目结构).

### 镜像类型字: `0x1101`

这个半字编码了三个标志位:

| 位域 | 值 | 含义 |
|-----------|-------|---------|
| EXE | `0x0001` | 这是一个可执行镜像 |
| CPU | `0x0100` | 目标 CPU 是 RISC-V |
| Chip | `0x1000` | 目标芯片是 RP2350 |

合并起来就是: `0x1000 | 0x0100 | 0x0001 = 0x1101`.

ARM 版本用的是 `0x1001` - 对 ARM 来说 CPU 字段是 `0x0000`. 正是这一个半字, 让引导程序启动 Hazard3 RISC-V 核心, 而不是 Cortex-M33.

## 入口点条目

```asm
.byte  0x44                                      # PICOBIN_BLOCK_ITEM_1BS_ENTRY_POINT
.byte  0x3                                       # 到下一个条目还有 3 个字
.byte  0x0                                       # 填充
.byte  0x0                                       # 填充
.word  Reset_Handler                             # RISC-V 复位入口点
.word  STACK_TOP                                 # 初始栈指针的值
```

### 条目标签: `0x44`

`0x44` 标识入口点条目.

### 大小: `0x03`

后面跟着三个字的负载 (包括补足第一个字的两个填充字节).

### 填充字节

这两个 `0x0` 字节填满第一个字在标签字节和大小字节之后的剩余部分. PICOBIN 条目按字对齐, 所以每个条目的负载都从 4 字节边界开始.

### `Reset_Handler`

```asm
.word  Reset_Handler                             # RISC-V 复位入口点
```

汇编器会为 `Reset_Handler` 符号生成一个重定位项. 链接器把它解析成 `Reset_Handler` 在 flash 里的绝对地址. 复位时, 引导程序把这个地址装入程序计数器.

### `STACK_TOP`

```asm
.word  STACK_TOP                                 # 初始栈指针的值
```

`STACK_TOP` 在 `constants.s` 里定义为 `0x20082000`. 引导程序在跳转到入口点之前, 把栈指针设成这个值. 这样我们就有了 32 KB 的栈空间 (一直延伸到 `0x2007a000`).

## 最后条目标记

```asm
.byte  0xff                                      # PICOBIN_BLOCK_ITEM_2BS_LAST
.hword (embedded_block_end - embedded_block - 16) / 4
.byte  0x0                                       # 填充
.word  0x0                                       # 指向下一个块的相对指针 (0 = 回到自身)
.word  0xab123579                                # PICOBIN_BLOCK_MARKER_END
embedded_block_end:
```

### 标签: `0xff`

"最后条目" 标签表示这个块内部的条目列表到此结束.

### 块大小

```asm
.hword (embedded_block_end - embedded_block - 16) / 4
```

汇编器在汇编阶段就把它算出来. 它测量这个块的总大小 (减去 16 字节的头部和尾部开销), 再折算成字. boot ROM 用它来校验块的完整性.

### 下一个块的指针

```asm
.word  0x0                                       # 指向下一个块的相对指针 (0 = 回到自身)
```

值为零表示 "这是唯一的块" - 没有指向另一个 IMAGE_DEF 的链.

### 结束标记

```asm
.word  0xab123579                                # PICOBIN_BLOCK_MARKER_END
```

boot ROM 会校验这个结束标记是否紧跟在最后一个条目之后. 如果 `0xab123579` 不在预期的位置, 这个块就会被判为损坏并拒绝.

## 内存布局

链接完成之后, IMAGE_DEF 块占据 flash 最开头的那些字节:

```
0x10000000  PICOBIN_BLOCK_MARKER_START  (0xffffded3)
0x10000004  Image-type item             (0x42, 0x01, 0x1101)
0x10000008  Entry-point item            (0x44, 0x03, pad, pad)
0x1000000c  Reset_Handler address
0x10000010  STACK_TOP value
0x10000014  Last-item + size + pad
0x10000018  Next-block pointer          (0x00000000)
0x1000001c  PICOBIN_BLOCK_MARKER_END    (0xab123579)
```

`.vectors` 段跟在下一个 128 字节对齐的地址上.

## ARM 与 RISC-V 的对比

| 字段 | ARM | RISC-V |
|-------|-----|--------|
| 镜像类型 | `0x1001` | `0x1101` |
| CPU 标志 | `0x0000` (ARM) | `0x0100` (RISC-V) |
| 入口点 | ARM `Reset_Handler` | RISC-V `Reset_Handler` |
| 栈 | 相同 (`STACK_TOP`) | 相同 (`STACK_TOP`) |
| 块结构 | 完全相同 | 完全相同 |

ARM 和 RISC-V 启动过程中唯一不同的字节, 就是镜像类型半字里的 CPU 标志.

## 小结

- `image_def.s` 提供了 RP2350 boot ROM 必需的 PICOBIN 元数据.
- 起始标记 `0xffffded3` 触发 flash 扫描阶段的块解析.
- `0x1101` 选择 RISC-V + RP2350 + 可执行镜像.
- 入口点和栈指针告诉引导程序从哪里开始执行.
- 结束标记 `0xab123579` 用于校验块的完整性.
- 链接脚本用 `KEEP` 把这个块放在 flash 的最开头.
