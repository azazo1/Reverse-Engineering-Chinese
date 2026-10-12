# Chapter 9: memory.x 与链接脚本

## 引言

微控制器不会把固件加载进一个空白的进程.
代码必须落在特定的地址上: bootrom 会在 flash
里寻找特定的头部, 向量表必须在 flash 基址上, 而在第一条
Rust 指令执行之前, 栈指针必须被初始化到 RAM 的顶部.
**链接脚本** 就是用来表达这些事实的. 在嵌入式 Rust
里, 这个文件叫 `memory.x`, 我们的三个驱动共用同一份.

## RP2350 的内存区域

链接脚本首先要给芯片的物理内存区域
和它们的大小命名:

```
0x10000000  FLASH  4096K   (XIP, firmware)
0x20000000  RAM    512K    (stack + data)
0x20080000  SRAM8   4K     (bootrom scratch)
0x20081000  SRAM9   4K     (bootrom scratch)
```

用链接脚本的语法写出来, 就变成了 `MEMORY` 块:

```
MEMORY {
    FLASH : ORIGIN = 0x10000000, LENGTH = 4096K
    RAM   : ORIGIN = 0x20000000, LENGTH = 512K
    SRAM8 : ORIGIN = 0x20080000, LENGTH = 4K
    SRAM9 : ORIGIN = 0x20081000, LENGTH = 4K
}
```

`SRAM8` 和 `SRAM9` 是 bootrom 私有的暂存区域. 它们出现在脚本里,
是因为 RP2350 的 bootrom 在那里实现了部分安全启动握手,
但我们的固件本身是从 `FLASH` 和 `RAM` 运行的.

## 完整的链接脚本

这是三个驱动共用的完整 `memory.x`:

```
MEMORY {
    FLASH : ORIGIN = 0x10000000, LENGTH = 4096K
    RAM   : ORIGIN = 0x20000000, LENGTH = 512K
    SRAM8 : ORIGIN = 0x20080000, LENGTH = 4K
    SRAM9 : ORIGIN = 0x20081000, LENGTH = 4K
}

_stack_start = ORIGIN(RAM) + LENGTH(RAM);

SECTIONS {
    .start_block : ALIGN(4)
    {
        __start_block_addr = .;
        KEEP(*(.start_block));
        KEEP(*(.boot_info));
    } > FLASH
} INSERT AFTER .vector_table;

_stext = ADDR(.start_block) + SIZEOF(.start_block);

SECTIONS {
    .bi_entries : ALIGN(4)
    {
        __bi_entries_start = .;
        KEEP(*(.bi_entries));
        . = ALIGN(4);
        __bi_entries_end = .;
    } > FLASH
} INSERT AFTER .text;

SECTIONS {
    .end_block : ALIGN(4)
    {
        __end_block_addr = .;
        KEEP(*(.end_block));
    } > FLASH
} INSERT AFTER .uninit;

PROVIDE(start_to_end = __end_block_addr - __start_block_addr);
PROVIDE(end_to_start = __start_block_addr - __end_block_addr);
```

## 起始块

RP2350 的 bootrom 不引导裸可执行文件. 它引导的是一个
**image definition** - 一段前导数据, 外加一组描述镜像类型,
入口点和签名的 "boot info" 条目. 当我们启用
`imagedef-secure-exe` 时 (第 8 章), Embassy
会为我们生成这段前导数据; 链接器必须在已知偏移处为它留出空间.

```
0x10000000 +---------------------+
           |  .vector_table      |   (cortex-m-rt)
           |                     |
           +---------------------+
           |  .start_block       |   INSERT AFTER .vector_table
           |   __start_block_addr|
           |   KEEP .start_block |
           |   KEEP .boot_info   |
           +---------------------+
           |  .text ...          |
           +---------------------+
```

`.start_block` 收集所有 `.start_block` 和 `.boot_info`
输入段, 并且即使链接器本来会把它们当作垃圾回收掉, 也会保留它们
(`KEEP`). `INSERT AFTER .vector_table` 把这个块紧挨着向量表放置,
而 RP2350 bootrom 正是期望镜像定义出现在那里.

## Boot info 条目

bootrom 还需要一个 boot-info 条目数组 -
也就是描述大小, 标志和镜像类型的标签列表. `.bi_entries`
段把它们收集起来, 并公布它们的边界, 好让固件能找到它们:

```
SECTIONS {
    .bi_entries : ALIGN(4)
    {
        __bi_entries_start = .;
        KEEP(*(.bi_entries));
        . = ALIGN(4);
        __bi_entries_end = .;
    } > FLASH
} INSERT AFTER .text;
```

`.` 符号是 **位置计数器** - 你可以把它读作 "当前的内存地址".
`__bi_entries_start` 是数组第一个字节的地址;
`__bi_entries_end` 是最后一个字节之后的位置, 向上对齐到 4
字节. 任何需要遍历 phrase 表的代码都用这两个符号来知道范围.

## 结束块

结束标记为整个镜像收尾:

```
SECTIONS {
    .end_block : ALIGN(4)
    {
        __end_block_addr = .;
        KEEP(*(.end_block));
    } > FLASH
} INSERT AFTER .uninit;
```

`INSERT AFTER .uninit` 把它放在镜像的最末尾,
也就是所有代码, 数据和未初始化段之后.
bootrom 会用这些块加上大小符号来校验镜像.

## 提供的符号

最后几条语句把算出来的地址暴露给固件:

```
PROVIDE(start_to_end = __end_block_addr - __start_block_addr);
PROVIDE(end_to_start = __start_block_addr - __end_block_addr);
```

`PROVIDE` **只在固件还没有定义该符号时** 才定义它.
`start_to_end` 是镜像的字节大小 (从起始块地址到结束块地址的距离);
`end_to_start` 是它的负值. Embassy 的 RP2350
支持代码会读这两个值, 来帮助 bootrom 校验镜像.

## 为什么这很重要

这里的每一个地址, 都是第 2 章那套语言里的一个*数字*:

```
0x10000000  firmware base (BOOT2 image start)
0x20000000  stack base; top of RAM is the first SP value
0x20080000  SRAM8 — secure-boot scratch
0x20081000  SRAM9 — secure-boot scratch
```

当你的板子烧录并启动时, 硬件真的就是在读这些区域:
先是向量表, 然后是镜像定义, 再然后是代码.
如果链接器把起始块放错了位置, bootrom
什么都不会说, 只有一片沉默. `memory.x`
就是我们用来兑现那个承诺的东西: 代码一定落在硬件期望的地方.

## 小结

- `MEMORY` 声明了位于 `0x10000000` 的 `FLASH`, 位于
  `0x20000000` 的 `RAM`, 以及 SRAM8/9 这两块暂存区域.
- `_stack_start` 是 RAM 的顶部 - 也就是初始栈指针.
- `.start_block` 加 `.boot_info`
  构成紧跟在向量表之后的 RP2350 镜像定义.
- `.bi_entries` 保存 boot-info 条目数组, 并公布它的边界.
- `.end_block` 为镜像收尾; `start_to_end`/`end_to_start` 把大小暴露出来.
- 副作用 (`imagedef-secure-exe`)
  和这份脚本合在一起, 才让 .uf2 可以启动.

接下来是 `build.rs`, Makefile, 以及如何把固件送进芯片.