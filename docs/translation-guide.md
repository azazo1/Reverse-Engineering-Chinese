# 翻译规范

本文件面向执行翻译工作的 agent 与协作者. 上游英文原文见 [upstream/README.md](upstream/README.md).

## 工作范围

上游内容结构:

- 26 个课程系列, 491 节 Lesson, 全部集中在 `docs/upstream/README.md` 这一个文件里.
- 每节 Lesson 的形式固定, 通常只有两行: 标题行加一句简介, 再附一个指向外部 ebook 的链接.

大多数 Lesson 的正文并不在本仓库内, 而是链接到外部站点. 因此翻译工作的主体是把这些标题与简介转成中文, 并保持原有链接不变.

## 文件组织

推荐把翻译结果按课程系列拆分, 每个系列一个文件:

```
docs/zh/
├── 00-index.md              中文总目录
├── 01-x86.md                x86 Course
├── 02-arm32-1.md            ARM-32 Course 1
├── ...
└── 26-data.md               Reverse Engineering Data Course
```

拆分的好处是单文件体积可控, 便于并行翻译与 review. 上游那个 2717 行的单文件不适合直接对应翻译.

`docs/upstream/README.md` 是只读对照基准, 任何情况下都不要改动它.

## 标点与格式

- 正文统一使用半角标点, 不使用全角标点.
- 中英文之间, 中文与数字之间保留一个空格.
- 每行以半角句号 `.` 结束, 不使用全角句号.
- 代码, 命令, 路径, 文件名一律不翻译, 原样保留.
- 链接地址不翻译, 链接文字翻译.
- 行尾使用 LF, 不带多余尾部空格.

## 术语对照

首次出现某个术语时, 采用 `中文 (English)` 的形式, 之后只用中文.

| 英文 | 中文 | 备注 |
| --- | --- | --- |
| Reverse Engineering | 逆向工程 | |
| Lesson | Lesson | 保留原文, 不译作"课" |
| Course | Course | 保留原文, 不译作"课程" |
| Chapter | Chapter | 保留原文 |
| Assembly Language | 汇编语言 | |
| Assembler | 汇编器 | |
| Disassembler | 反汇编器 | |
| Register | 寄存器 | |
| Stack | 栈 | |
| Heap | 堆 | |
| Instruction | 指令 | |
| Opcode | 操作码 | |
| Calling Convention | 调用约定 | |
| Breakpoint | 断点 | |
| Debugger | 调试器 | |
| Patch | 补丁 | 动词可译作"打补丁" |
| Payload | 载荷 | 安全语境下不译作"负载" |
| Shellcode | Shellcode | 保留原文 |
| Exploit | 利用代码 | |
| Firmware | 固件 | |
| Flashing | 烧录 | |
| Bare Metal | 裸机 | |
| Toolchain | 工具链 | |
| Cross Compile | 交叉编译 | |
| Bootloader | 引导程序 | |
| Datasheet | 数据手册 | |
| Peripheral | 外设 | |
| Interrupt | 中断 | |
| GPIO | GPIO | 保留原文 |

## 注意事项

- 课程标题里的系列名保留英文, 例如 `Lesson 1: x86 Course (Part 1: Goals)` 译作 `Lesson 1: x86 Course (Part 1: 目标)`.
- 上游把 `Chapter` 与 `Part` 混用指代同一层级, 翻译时保持与原文一致, 不要统一.
- 上游存在编号重复与跳号, 翻译时照抄, 不要修正.
- 涉及人名, 项目名, 工具名的部分保持原文, 例如 `Ghidra`, `IDA`, `Pico 2`, `RP2350`.
- 翻译存疑时, 保留英文原文并就近标注, 好过臆测.
