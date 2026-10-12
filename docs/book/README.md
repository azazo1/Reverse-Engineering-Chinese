# 书稿目录

本目录是各课程教材正文的中文版. 上游 `docs/courses.md` 只提供课程索引与外部链接,
正文分散在十多个独立仓库里, 这里把它们取回并译成中文, 便于离线阅读与检索.

## 课程一览

### 经典教程系列

上游 GitBook 电子书 (见 <https://0xinfection.xyz/reversing/>) 的正文, 也是这套教程中最早的系列.

| 目录 | 课程 | 篇目 | 内容 |
| --- | --- | --- | --- |
| [x86-course/](x86-course/) | x86 Course | 40 篇 | 恶意软件逆向入门, 从数制讲到汇编的数据搬运与 CMOV |
| [arm32-course-1/](arm32-course-1/) | ARM-32 Course 1 | 25 篇 | 32 位 ARM 基础, 以及 ADD / ADDS / ADC / SUB 系列 |
| [arm32-course-2/](arm32-course-2/) | ARM-32 Course 2 | 49 篇 | 承接 Course 1, 复习基础后讲各类变量与运算符 |
| [x64-course/](x64-course/) | x64 Course | 43 篇 | 64 位 x86, 含引导扇区基础与 x64 汇编 |
| [arm64-course/](arm64-course/) | ARM-64 Course | 11 篇 | 64 位 ARM 开发环境, 基本 I/O 与字符类型 |

### 嵌入式系列

这些课的正文在 GitHub 上以 markdown 形式存在, 取自上游各自独立的仓库.

| 目录 | 课程 | 篇目 | 内容 |
| --- | --- | --- | --- |
| [rp2350-rust/](rp2350-rust/) | RP2350 Rust Course | 30 章 | 用 Embassy 异步框架在 RP2350 上写裸机 Rust 固件 |
| [rp2350-arm-asm/](rp2350-arm-asm/) | RP2350 ARM Assembler Course | 30 章 | ARM Cortex-M33 汇编, 从数制讲到完整工程 |
| [rp2350-riscv-asm/](rp2350-riscv-asm/) | RP2350 RISC-V Assembler Course | 30 章 | RISC-V (Hazard3) 汇编, 结构同上 |
| [avr-assembler/](avr-assembler/) | AVR Assembler Course | 24 课 | ATmega328P 纯汇编, 每课驱动一个外设 |
| [wasm/](wasm/) | Wasm Course | 2 篇 | WebAssembly 组件模型与 Pulley 解释器, 桌面宿主 |
| [embedded-wasm-uart/](embedded-wasm-uart/) | Embedded Wasm UART Echo Course | 2 篇 | 同一套 Wasm 组件跑在 RP2350 裸机上, 回显 UART |
| [embedded-wasm-blinky/](embedded-wasm-blinky/) | Embedded Wasm Blinky Course | 2 篇 | 同上, 用 GPIO 驱动 LED 闪烁 |
| [embedded-wasm-button/](embedded-wasm-button/) | Embedded Wasm Button Course | 2 篇 | 同上, 读按键控制 LED |
| [embedded-wasm-servo/](embedded-wasm-servo/) | Embedded Wasm Servo Course | 1 篇 | 同上, 用 PWM 控制舵机 |

## 文件组织

- 每章/每课一个 markdown 文件, 文件名保持上游的编号顺序.
- `chapter-NN.md` 对应上游的 `CHAPTER-NN.md`, `lesson-NNN.md` 对应 `lessons/NNN/lesson.md`.
- 每个 Wasm 系列里, `tutorial.md` 是逐行讲解的教程, `re.md` 是对编译产物的逆向分析.
  `embedded-wasm-servo` 没有 `re.md`, 上游仓库就没有这一篇.
- 经典教程系列沿用上游的 `part-NN-<英文标题>.md` 命名, 便于与原文逐行对照.
- [imgs/](imgs/) 是经典教程系列的配图. 上游把那些课的代码与调试结果做成了截图直接放进正文,
  没有可翻译的文本形态, 只能原样取回.
  上游这批图的扩展名不可靠: 265 个 `.jpg` 里装的其实是 PNG. 这里按内容重新归置过,
  扩展名与真实格式一致, 因此目录里 `.jpg` 与 `.png` 混用.
- `arm32-course-2` 的前 13 篇复用 `arm32-course-1` 的同一批文件, 这是上游的编排方式:
  Course 2 先用同一批课文复习基础, 再从 Part 14 起讲新内容. 两处内容完全相同,
  改其中一处要同步另一处.

## 翻译约定

术语与标点规范见 [translation-guide.md](../translation-guide.md), 书稿专有约定见同文件末尾.

要点:

- 代码本身不翻译, 只翻译代码里的注释.
- 行内代码 (反引号内容), 标识符, 寄存器名, 指令名, 芯片型号一律保留原文.
- ASCII 示意图与终端输出保持原样, 只翻译框外的讲解文字.
- 正文使用半角标点, 中英文与数字之间留空格.

## 来源

各课程正文版权归上游作者 Kevin Thomas (@mytechnotalent) 所有, 取自下列仓库:

| 目录 | 上游仓库 |
| --- | --- |
| x86-course, arm32-course-1, arm32-course-2, x64-course, arm64-course | <https://github.com/0xInfection/reversing> |
| rp2350-rust | <https://github.com/mytechnotalent/RP2350-Rust-Tutorial> |
| rp2350-arm-asm | <https://github.com/mytechnotalent/RP2350-ARM-ASM-Tutorial> |
| rp2350-riscv-asm | <https://github.com/mytechnotalent/RP2350-RISCV-ASM-Tutorial> |
| avr-assembler | <https://github.com/mytechnotalent/Assembler> |
| wasm | <https://github.com/mytechnotalent/Wasm> |
| embedded-wasm-uart | <https://github.com/mytechnotalent/embedded-wasm-uart-rp2350> |
| embedded-wasm-blinky | <https://github.com/mytechnotalent/embedded-wasm-blinky-rp2350> |
| embedded-wasm-button | <https://github.com/mytechnotalent/embedded-wasm-button-rp2350> |
| embedded-wasm-servo | <https://github.com/mytechnotalent/embedded-wasm-servo-rp2350> |
