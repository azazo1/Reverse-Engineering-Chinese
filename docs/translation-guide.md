# 翻译规范

本文件记录本仓库的中译约定, 供后续增补或校订课程内容时参照.

## 工作范围

上游内容结构:

- 26 个课程系列, 491 节 Lesson, 全部集中在 `docs/courses.md` 这一个文件里.
- 每节 Lesson 的形式固定, 通常只有两行: 标题行加一句简介, 再附一个指向外部 ebook 的链接.

大多数 Lesson 的正文并不在本仓库内, 而是链接到外部站点. 因此翻译工作的主体是把这些标题与简介转成中文, 并保持原有链接不变.

## 文件组织

中文课程目录集中在 `docs/courses.md` 一个文件里, 与上游保持同构, 便于逐行对照.

翻译时曾按课程系列切成 23 个片段并行处理, 各片段行数与原文章节严格对应, 拼接后与上游逐行对齐. 上游那个 2717 行的单文件不适合直接整篇交给单个翻译者.

教材正文放在 `docs/book/` 下, 按课程分目录, 每章一个文件. 详见 [book/README.md](book/README.md).

## 书稿翻译约定

`docs/book/` 里的正文与索引的译法略有不同, 补充约定如下.

- 行数与原英文逐行对应, 便于批量校验与后续增补.
- 代码本身不翻译, 只翻译代码里的注释; 注释符与缩进保持原位.
- 行内代码 (反引号内容), 字符串字面量, 标识符, 寄存器名, 指令名, 芯片型号一律保留原文.
- ASCII 示意图与终端输出保持原样, 只翻译框外的讲解文字.
- 表格只翻译单元格里的说明文字, 分隔符结构不变.
- 带目录的文件, 标题翻译后锚点要按译文标题重新推导, 否则目录链接会失效.
- 复合词内部不加空格, 例如 `加载-存储` `读-改-写` `取指-译码-执行`;
  ` - ` (两侧带空格) 只用作分句的破折号.
- 第二人称用 "你", 不用 "您".

## 标点与格式

- 正文统一使用半角标点, 不使用全角标点.
- 中英文之间, 中文与数字之间保留一个空格.
- 每行以半角句号 `.` 结束, 不使用全角句号.
- 代码, 命令, 路径, 文件名一律不翻译, 原样保留.
- 链接地址不翻译, 链接文字翻译.
- 行尾使用 LF, 不带多余尾部空格.
- 标题里的分隔符统一用半角 `-`, 不沿用上游的 en dash 与 em dash.

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
| Memory | 内存 | 泛指时用内存; `Flash Program Memory` 这类硬件专名保留"程序存储器" |
| Endianness | 字节序 | |
| Hacking | 修改 | 指改二进制, 改代码 |
| Debugging | 调试 | |
| Dataset | 数据集 | |
| Primitive Datatype | 基本数据类型 | 类型名本身 (char, int, float) 保留原文 |

## 链接行固定译法

这几类链接行在上游重复出现几百次, 译法固定, 不要逐次发挥.

| 英文原文 | 中文 |
| --- | --- |
| `-> Click [HERE](URL) to read the FREE ebook.` | `-> 点[这里](URL) 阅读免费电子书.` |
| `-> Click [HERE](URL) to read the FREE pdf book.` | `-> 点[这里](URL) 阅读免费 PDF 书.` |
| `-> Click [HERE](URL) to read the lesson and see the code.` | `-> 点[这里](URL) 阅读本课并查看代码.` |
| `-> Click [HERE](URL) to read the project on GitHub.` | `-> 点[这里](URL) 在 GitHub 上阅读该项目.` |
| `-> Click [HERE](URL) to read the FREE tutorial on GitHub.` | `-> 点[这里](URL) 在 GitHub 上阅读免费教程.` |
| `## 名字 [HERE](#anchor)` | `## 名字 [这里](#anchor)` |

## 注意事项

- 课程标题里的系列名保留英文, 例如 `Lesson 1: x86 Course (Part 1: Goals)` 译作 `Lesson 1: x86 Course (Part 1: 目标)`.
- 上游把 `Chapter` 与 `Part` 混用指代同一层级, 翻译时保持与原文一致, 不要统一.
- 上游存在编号重复与跳号, 翻译时照抄, 不要修正.
- 上游本身存在标题与正文口径不一致的地方, 照抄, 不要修正.
- 涉及人名, 项目名, 工具名的部分保持原文, 例如 `Ghidra`, `IDA`, `Pico 2`, `RP2350`.
- 简介句在同一系列内要轮换句式, 避免通篇同一个开头.
- 翻译存疑时, 保留英文原文并就近标注, 好过臆测.
