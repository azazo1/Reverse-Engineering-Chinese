# Reverse-Engineering Chinese

`mytechnotalent/Reverse-Engineering` 教程的中文版.

## 这是什么

上游仓库是一份免费的逆向工程综合教程, 覆盖 x86, x64, 32/64 位 ARM, 8 位 AVR 以及 32 位 RISC-V 架构. 全部内容按课程系列组织, 共 26 个系列, 491 节 Lesson.

本仓库做了两件事:

1. 把这些课程内容翻译成中文.
2. 剔除上游仓库中体积庞大且可以从源码重新生成的编译产物, 让仓库回到"只装源材料"的状态.

## 上游来源

| 项目 | 值 |
| --- | --- |
| 上游仓库 | <https://github.com/mytechnotalent/Reverse-Engineering> |
| 作者 | Kevin Thomas (@mytechnotalent) |
| 许可证 | Apache License 2.0 |
| 本仓库取材的上游提交 | `72e0e700547cb6927208ae41e4757054499b4c21` |
| 取材日期 | 2026-10-12 |

上游 491 节 Lesson 的中文版完整收录在 [docs/courses.md](docs/courses.md).

上游索引里的链接大多指向外部站点, 正文并不在上游仓库内. 其中 9 个课程的 markdown 正文
已取回并译成中文, 放在 [docs/book/](docs/book/), 共 124 篇, 可直接离线阅读.

## 课程系列

| 课程系列 | Lesson 数 |
| --- | --- |
| x86 Course | 40 |
| ARM-32 Course 1 | 25 |
| ARM-32 Course 2 | 49 |
| ARM-32 Project Course | 6 |
| x64 Course | 43 |
| ARM-64 Course | 20 |
| Pico Hacking Course | 20 |
| Hacking Windows Course | 30 |
| Go Hacking Course | 12 |
| Hacking Rust Course | 15 |
| Hacking Embedded Rust Course | 6 |
| Hacking Embedded Rust Course w/ microbit | 5 |
| Embedded Assembler Course | 11 |
| Embedded Hacking Course | 40 |
| Hacking Bits Course | 10 |
| Hacking RISC-V Course | 9 |
| Wasm Course | 1 |
| Embedded Wasm UART Echo Course | 1 |
| Embedded Wasm Blinky Course | 1 |
| Embedded Wasm Button Course | 1 |
| Embedded Wasm Servo Course | 1 |
| AVR Assembler Course | 24 |
| RP2350 ARM Assembler Course | 30 |
| RP2350 RISC-V Assembler Course | 30 |
| RP2350 Rust Course | 30 |
| Reverse Engineering Data Course | 30 |
| **合计** | **491** |

## 在线阅读与电子书

在线阅读站点: <https://azazo1.github.io/Reverse-Engineering-Chinese/>

左侧目录, 全文搜索, 章节间翻页, 深色主题都由 mdBook 提供. 推到 main 后
由 [.github/workflows/pages.yml](.github/workflows/pages.yml) 自动重建并部署.

电子书在预发布页滚动更新, 资产名固定:

<https://github.com/azazo1/Reverse-Engineering-Chinese/releases/tag/book-latest>

| 格式 | 适用 |
| --- | --- |
| PDF | 打印与屏幕阅读, 约 600 页 |
| EPUB | 绝大多数阅读器 |
| MOBI | 旧款 Kindle |

推送到 main 后由 [.github/workflows/book.yml](.github/workflows/book.yml) 重建.

本地构建:

```shell
just site          # 构建阅读站点到 site/
just site-serve    # 起本地服务预览, 改文档自动重建
just book          # 构建 PDF 与 EPUB 到 dist/
just book-all      # 连 MOBI 一起构建, 需装 Calibre
```

PDF 与 EPUB 需要 `pandoc` 与 `typst`; MOBI 需要 Calibre 的 `ebook-convert`;
阅读站点需要 `mdbook`. CI 里会自动装好, 本机则需自行准备.

## 目录结构

```
.
├── README.md                    本文件
├── LICENSE                      Apache License 2.0, 继承自上游
├── justfile                     常用任务
├── docs/
│   ├── courses.md               中文课程目录, 26 个系列 491 节 Lesson
│   ├── book/                    部分课程教材正文的中文版
│   ├── translation-guide.md     翻译规范与术语表
│   └── inventory.md             素材清单与保留策略
├── scripts/
│   ├── build_book.py            组装并生成 PDF / EPUB / MOBI
│   └── build_site.py            组装并生成 mdBook 阅读站点
├── .github/workflows/           电子书构建与站点部署
├── 0xNNNN-<名字>/               各示例工程的源码与 Visual Studio 工程文件
├── 0xNNNN-<名字>-x64 Debug/     IDA 分析工作目录 (x64)
├── 0xNNNN-<名字>-x86 Debug/     IDA 分析工作目录 (x86)
├── badges/                      徽章设计素材
└── *.png *.fzz                  电路图与示意图
```

## 示例工程

`0xNNNN-<名字>/` 是教程里用到的 C 语言示例工程, 每个工程都带有完整的 Visual Studio 解决方案.

以 `0x0006-directories` 为例:

| 文件 | 作用 |
| --- | --- |
| `0x0006-directories.sln` | 解决方案文件 |
| `0x0006-directories.vcxproj` | 工程定义 |
| `0x0006-directories.vcxproj.filters` | 工程内文件分组 |
| `0x0006-directories.vcxproj.user` | 用户级调试配置 |
| `main.c` | 源码 |

编译产物不在版本控制范围内, 需要时用 Visual Studio 打开 `.sln` 自行构建.

## IDA 分析工作目录

`0xNNNN-<名字>-x64 Debug/` 与 `0xNNNN-<名字>-x86 Debug/` 这两类目录保存了作者用 IDA 分析示例程序的结果.

| 扩展名 | 说明 |
| --- | --- |
| `.i64` | IDA 64 位数据库 |
| `.id0` `.id1` `.id2` | IDA 数据库分片 |
| `.nam` | 名称列表 |
| `.til` | 类型库 |
| `.exe` | 与该数据库配对的可执行文件 |

这类目录必须整体保留. 其中的数据库无法由源码重新生成, 且旁边的 `.exe` 与数据库是配对关系: 源码改动之后重新编译出来的可执行文件与数据库记录的并不一致.

## 素材保留策略

判断标准只有一条: **能否从仓库内的其他内容重新生成.**

| 处理 | 内容 | 原因 |
| --- | --- | --- |
| 保留 | 源码, 解决方案与工程文件 | 人工编写的源材料 |
| 保留 | IDA 数据库及其配对 `.exe` | 无法重新生成 |
| 保留 | `.fzz` 电路图源文件 | Fritzing 工程源文件 |
| 保留 | 徽章与示意图 `.png` | 无可再生的源文件 |
| 移除 | `.vs/` 目录 | IDE 自动生成的缓存 |
| 移除 | `Debug/` `x64/` `x86/` 构建目录 | 编译输出 |
| 移除 | `reversing-for-everyone.pdf` | 可从 <https://0xinfection.github.io/reversing/reversing-for-everyone.pdf> 重新下载 |
| 移除 | 电路图 `.png` | 可由同名 `.fzz` 重新导出 |

上游仓库中这些被移除的内容合计约 379 MiB, 其中仅 `.ipch` 预编译头与 `Browse.VC.db` 浏览数据库两项就占了 350 MiB.

## 翻译约定

课程内容的中译规范与术语对照见 [docs/translation-guide.md](docs/translation-guide.md). 素材清单与保留策略见 [docs/inventory.md](docs/inventory.md).

源码中的注释已译成中文, 代码本身, 字符串字面量, 标识符与工程文件保持原样. 仓库里的 IDA 数据库与配对的 `.exe` 是与特定二进制绑定的, 改动源码字符串会让两者对不上, 因此这部分不做翻译.

## 许可证

[Apache License 2.0](LICENSE), 继承自上游仓库. 上游作者为 Kevin Thomas (@mytechnotalent).
