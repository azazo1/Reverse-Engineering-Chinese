# 素材清单

本文件记录仓库内的素材构成, 以及相对上游仓库所做的取舍. 数据取自 2026-10-12.

## 总量对照

| 项目 | 上游仓库 | 本仓库 |
| --- | --- | --- |
| 版本控制内文件数 | 395 | 114 |
| 工作区体积 | 440.7 MiB | 36.4 MiB |
| `.git` 体积 | 133.2 MiB | 首次提交后生成 |

上游仓库那 440.7 MiB 里有 379 MiB 是可以从源码重新生成的编译产物与 IDE 缓存, 这部分在本仓库中全部剔除.

## 保留内容

### 示例工程 (12 个)

每个工程都带完整的 Visual Studio 解决方案, 单个体积在 10 KiB 上下.

| 目录 | 文件数 | 体积 |
| --- | --- | --- |
| `0x0001-hello_world-x64` | 5 | 10.2 KiB |
| `0x0001-hello_world-x86` | 5 | 10.2 KiB |
| `0x0006-directories` | 5 | 9.9 KiB |
| `0x0007-copyfile` | 5 | 9.7 KiB |
| `0x0010-movefile` | 5 | 9.6 KiB |
| `0x0011-createfile` | 10 | 19.7 KiB |
| `0x0012-writefile` | 10 | 20.6 KiB |
| `0x0013-readfile` | 10 | 21.3 KiB |

`0x0011` 到 `0x0013` 这三个工程的目录里多嵌套了一层同名子目录, 因此文件数翻倍. 这是上游就有的结构, 保持原样.

### IDA 分析工作目录 (13 个)

| 目录 | 文件数 | 体积 |
| --- | --- | --- |
| `0x0001-hello_world-x64 Debug` | 2 | 125.4 KiB |
| `0x0001-hello_world-x86 Debug` | 2 | 221.3 KiB |
| `0x0006-directories-x64 Debug` | 6 | 1270.6 KiB |
| `0x0006-directories-x86 Debug` | 2 | 1246.3 KiB |
| `0x0007-copyfile-x64 Debug` | 2 | 1254.8 KiB |
| `0x0007-copyfile-x86 Debug` | 2 | 1229.8 KiB |
| `0x0010-movefile-x64 Debug` | 2 | 1254.4 KiB |
| `0x0010-movefile-x86 Debug` | 2 | 1286.0 KiB |
| `0x0011-createfile-x64 Debug` | 2 | 1285.2 KiB |
| `0x0011-createfile-x86 Debug` | 2 | 1309.3 KiB |
| `0x0012-writefile-x64 Debug` | 4 | 1582.9 KiB |
| `0x0012-writefile-x86 Debug` | 2 | 1320.8 KiB |
| `0x0013-readfile-x86 Debug` | 2 | 1377.0 KiB |

合计约 13.8 MiB. 这类目录必须整体保留, 详见下方"为何保留配对的可执行文件".

### 图片素材

| 路径 | 文件数 | 体积 |
| --- | --- | --- |
| `badges/ouroboros-badge/` | 14 | 18.5 MiB |
| `K Background.png` | 1 | 1315.0 KiB |
| `Reverse Engineering.png` | 1 | 1070.1 KiB |
| `DC540 Angels Of Death.png` | 1 | 779.1 KiB |
| `REDAH.png` | 1 | 39.8 KiB |

### 电路图源文件

| 路径 | 体积 |
| --- | --- |
| `oled and button schematic.fzz` | 43.7 KiB |
| `dynamic RE schematic.fzz` | 34.4 KiB |
| `static RE schematic.fzz` | 28.9 KiB |

`.fzz` 是 Fritzing 工程文件, 内部打包了 `.fz` 工程描述与若干 `.svg` 图形. 同名 `.png` 是它的导出结果, 已移除, 需要时用 Fritzing 打开 `.fzz` 重新导出即可.

## 移除内容

| 类别 | 文件数 | 体积 | 移除理由 |
| --- | --- | --- | --- |
| `.vs/` 目录 | 12 | 350.1 MiB | IDE 缓存, 含 `.ipch` 预编译头与 `Browse.VC.db` 浏览数据库 |
| `Debug/` 构建目录 | 266 | 29.1 MiB | 编译输出, 含 `.pdb` `.obj` `.ilk` `.tlog` 等 |
| `reversing-for-everyone.pdf` | 1 | 23.9 MiB | 可从上游站点重新下载 |
| 电路图 `.png` | 3 | 0.8 MiB | 可由同名 `.fzz` 重新导出 |
| `Ouroboros_How_It_Works.pdf` | 1 | 0.3 MiB | 说明文档, 可另行获取 |

上游仓库中有 6 个 `.ipch` 文件合计 253.4 MiB, 3 个 `Browse.VC.db` 合计 96.7 MiB. 这两项就占了整个仓库体积的 79%.

## 为何保留配对的可执行文件

IDA 工作目录里的 `.exe` 看起来像是编译产物, 似乎可以删掉让读者自行编译. 实际情况并非如此.

以 `0x0006-directories` 为例, 对比 IDA 目录里的可执行文件与源码当前编译结果:

| 位置 | 大小 | 二进制差异 |
| --- | --- | --- |
| `0x0006-directories-x64 Debug/0x0006-directories.exe` | 62464 B | 5 字节 |
| `0x0006-directories/x64/Debug/0x0006-directories.exe` | 62464 B | 基准 |

差异集中在偏移 36911 到 36919 这 5 个字节, 内容是硬编码的路径常量:

```
IDA 目录中的版本:  C:\hacky
构建目录中的版本:  C:\mydir
```

当前源码 [0x0006-directories/main.c](../0x0006-directories/main.c) 用的是 `C:\mydir`. 也就是说, IDA 目录里那个可执行文件是作者早期用另一份源码编译出来的, 与当前源码并不对应.

结论: `.i64` 数据库记录的是那个旧版本二进制的分析结果. 如果删掉配对的 `.exe`, 读者重新编译得到的是另一个程序, 数据库里的函数地址与偏移将全部对不上, 整个分析结果作废.

因此这两者必须成对保留.
