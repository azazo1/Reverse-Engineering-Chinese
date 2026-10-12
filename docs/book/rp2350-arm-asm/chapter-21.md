# Chapter 21: image_def.s - PICOBIN 引导块

## 引言

RP2350 的引导 ROM 在 flash 中最先寻找的东西, 就是一个有效的 PICOBIN 块 - 一小段元数据结构, 用来证明这个镜像确实是合法的程序. 没有它, 引导 ROM 会把 flash 看成空白, 拒绝启动. image_def.s 定义了这块结构, 链接脚本把它放在 flash 的开头. 本章逐个字节地解读它.

## 完整源码

```asm
.section .picobin_block, "a"                     // 把 IMAGE_DEF 块放入 flash

.word  0xffffded3                                // PICOBIN_BLOCK_MARKER_START
.byte  0x42                                      // PICOBIN_BLOCK_ITEM_1BS_IMAGE_TYPE
.byte  0x1                                       // 该项大小为 1 个字
.hword 0b0001000000100001                        // SECURE 模式 (0x1021)
.byte  0xff                                      // PICOBIN_BLOCK_ITEM_2BS_LAST
.hword 0x0001                                    // 该项大小为 1 个字
.byte  0x0                                       // 填充
.word  0x0                                       // 指向下一块的相对指针 (0 = 指向自身)
.word  0xab123579                                // PICOBIN_BLOCK_MARKER_END
```

## 段的位置

```asm
.section .picobin_block, "a"                     // 把 IMAGE_DEF 块放入 flash
```

`"a"` 标志表示可分配 (allocatable), 也就是这个段会在最终的二进制里占位置. 链接脚本把它放在最前面:

```ld
.embedded_block :
{
  KEEP(*(.picobin_block))
} > FLASH :text
```

`KEEP` 能阻止链接器丢弃这个段, 尽管没有任何代码引用它. 引导 ROM 是按位置读取它的, 它就在 flash 的开头.

注意: 汇编里的段名是 `.picobin_block`, 而链接脚本的 `KEEP` 通过 `.embedded_block` 输出段里的 `*(.picobin_block)` 来匹配它.

## 块结构

PICOBIN 块是一个链表结构. 每个块以魔数标记开头和结尾, 中间包含一个或多个项:

```
+----------------------------+ Offset 0x00
| MARKER_START (0xffffded3)  | 4 bytes
+----------------------------+ Offset 0x04
| Item: IMAGE_TYPE           | 4 bytes
+----------------------------+ Offset 0x08
| Item: LAST                 | 4 bytes
+----------------------------+ Offset 0x0C
| Next block pointer (0)     | 4 bytes
+----------------------------+ Offset 0x10
| MARKER_END (0xab123579)    | 4 bytes
+----------------------------+ Offset 0x14
```

总大小: 20 字节 (5 个字).

## 逐字节分析

### 起始标记

```asm
.word  0xffffded3                                // PICOBIN_BLOCK_MARKER_START
```

引导 ROM 会在 flash 里扫描这个 32 位模式. 它标志着 PICOBIN 块的开始.

### IMAGE_TYPE 项

```asm
.byte  0x42                                      // PICOBIN_BLOCK_ITEM_1BS_IMAGE_TYPE
.byte  0x1                                       // 该项大小为 1 个字
.hword 0b0001000000100001                        // SECURE 模式 (0x1021)
```

这个 4 字节的项可以拆成:

| 字段 | 值 | 含义 |
|-------|-------|---------|
| 项类型 | `0x42` | IMAGE_TYPE (1 字节大小的变体) |
| 大小 | `0x01` | 1 个字 (含这些头部字节共 4 字节) |
| 数据 | `0x1021` | 镜像类型标志 |

数据字 `0x1021` (`0b0001000000100001`) 编码了:

| Bits | Value | Meaning |
|------|-------|---------|
| 0 | 1 | 镜像可执行 |
| 5 | 1 | ARM 架构 (Cortex-M33) |
| 12 | 1 | 安全模式: 安全 (secure) |

### LAST 项

```asm
.byte  0xff                                      // PICOBIN_BLOCK_ITEM_2BS_LAST
.hword 0x0001                                    // 该项大小为 1 个字
.byte  0x0                                       // 填充
```

| 字段 | 值 | 含义 |
|-------|-------|---------|
| 项类型 | `0xFF` | LAST 项 (结束项列表) |
| 大小 | `0x0001` | 1 个字 |
| 填充 | `0x00` | 对齐填充 |

LAST 项表示这个块内部项列表的结束.

### 下一块指针

```asm
.word  0x0                                       // 指向下一块的相对指针 (0 = 指向自身)
```

值为 0 表示这是唯一的块 - 它会指回自己. 在更复杂的镜像里, 多个块可以串成链表.

### 结束标记

```asm
.word  0xab123579                                // PICOBIN_BLOCK_MARKER_END
```

结束标记用于校验块的完整性. 引导 ROM 在接受这个块之前, 会同时检查两个标记.

## 为什么这很重要

没有有效的 PICOBIN 块会发生什么:

1. 引导 ROM 扫描 flash, 找不到可识别的镜像
2. 芯片退回 USB 引导模式 (BOOTSEL)
3. 我们的代码永远不会执行

PICOBIN 块是固件与引导 ROM 之间的握手 - 它在说 "这是一个合法的 ARM 可执行镜像, 请运行它."

## 小结

- image_def.s 定义了一个 20 字节的 PICOBIN 块, 放在 flash 的开头.
- 这个块包含起止标记, 一个 IMAGE_TYPE 项 (ARM, 可执行, 安全) 和一个 LAST 项.
- 链接脚本用 `KEEP` 保证这个段永远不会被丢弃.
- RP2350 的引导 ROM 会扫描这个块, 在执行之前校验固件镜像.
