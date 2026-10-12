# Chapter 10: build.rs, Makefile 与烧录

## 引言

产出一个可启动的 `.uf2` 需要好几个阶段: 编译目标平台的
Rust 代码, 用我们的 `memory.x` 运行链接器,
生成启动镜像的元数据, 最后调用 `probe-rs` 把 RP2350 烧录好.
本章讲解每个驱动都会附带的那两个自动化文件: `build.rs` 和 `Makefile`.

## build.rs - 构建脚本

一个 Rust crate 可以在 crate 根目录放一个名为
`build.rs` 的特殊文件. Cargo 会在构建这个 crate
*之前* 编译并运行它, 而它打印出来的, 带 `cargo:`
前缀的任何内容都会变成构建指令. 我们的 `build.rs` 很短, 却很关键:

```rust
use std::env;
use std::fs::File;
use std::io::Write;
use std::path::PathBuf;

fn main() {
    let out = &PathBuf::from(env::var_os("OUT_DIR").unwrap());
    File::create(out.join("memory.x"))
        .unwrap()
        .write_all(include_bytes!("memory.x"))
        .unwrap();
    println!("cargo:rustc-link-search={}", out.display());
    println!("cargo:rerun-if-changed=memory.x");
}
```

逐行读一遍:

1. **`env::var_os("OUT_DIR")`** - Cargo
   会给构建脚本一个私有的输出目录. 链接脚本会被复制到那里.
2. **`include_bytes!("memory.x")`** -
   在编译期嵌入这个文件的字节, 并把它们写进 `OUT_DIR/memory.x`.
3. **`cargo:rustc-link-search=...`** - 告诉链接器去搜索那个目录,
   这样启动 crate 的 `-Tlink.x` 才能找到我们的 `memory.x`.
4. **`cargo:rerun-if-changed=memory.x`** - 如果
   `memory.x` 变了, 就重新构建, 而不是复用旧结果.

最终效果是: 链接器用的是*住在仓库里*的 `memory.x`,
而不是系统里某个隐藏的默认值. 只有一处事实来源.

## Makefile

`Makefile` 把常用操作包装成简短好记的目标.
完整文件里还带着 MIT 头部和
`@file`/`@brief`/`@author`/`@date` 文档注释块 -
这证明那套标准适用于每个文件, 连构建自动化也不例外:

```make
.PHONY: test build clean flash

test:
	cargo test --lib --target $(shell rustc --print host-tuple) --no-default-features

build:
	cargo build --release

flash: build
	probe-rs run --chip RP2350 target/thumbv8m.main-none-eabihf/release/rp2350-blink

clean:
	cargo clean
```

## make test - 主机测试

```
cargo test --lib --target $(shell rustc --print host-tuple) --no-default-features
```

- `--target $(shell rustc --print host-tuple)` -
  面向*主机*构建, 而不是 RP2350, 这样测试就能作为普通桌面程序运行.
- `--no-default-features` - 去掉 Embassy (`embassy-executor`,
  `embassy-rp`, `cortex-m`, `cortex-m-rt`, `panic-halt`).
  只编译那些纯粹的, 可测试的逻辑 - 这也正是为什么设计上要把逻辑留在库里
  (第 18 章), 以及为什么 `lib.rs` 只在*不*测试时才是 `no_std`.
- `--lib` - 测试库目标, 所有状态机都住在那里.

这条命令就是第 25 章的一行浓缩版. 它就是整个反馈循环:
写一个驱动, 在主机上运行状态机, 一秒钟内看到 20 多个测试通过.

## make build - 发布固件

`cargo build --release` 编译优化后的固件. `Cargo.toml`
里的 release profile 是针对微控制器调过的:

```toml
[profile.release]
debug = true
lto = true
opt-level = "z"
panic = "abort"
```

- `debug = true` - 保留调试信息, 这样 `probe-rs` 才能解析出符号名.
- `lto = true` - 跨 crate 的链接期优化; 能省下可观的体积.
- `opt-level = "z"` - 为体积优化. flash 是按 KB 来算的.
- `panic = "abort"` - 不生成栈展开元数据;
  panic 立刻停机 (与 `panic-halt` 对应).

## make flash - probe-rs

`probe-rs run` 既烧录音像, 又开一个片上调试会话:

```
probe-rs run --chip RP2350 target/thumbv8m.main-none-eabihf/release/rp2350-blink
```

从 Pico 1 到 Pico 2, 芯片名字变了: **`RP2040`** 变成了
**`RP2350`**. `probe-rs run` 需要一个调试探针 (刷了 "debugprobe"
固件的 Pico, 或者一片 Picoprobe) 插在一个 USB 口上, 目标 Pico
插在另一个口上. 这就是每个驱动 README 里描述的 "烧录并运行" 体验.

## 小结

- `build.rs` 把我们的 `memory.x`
  复制到构建输出目录, 并告诉链接器去哪里找它.
- `make test` 用 `--no-default-features`
  在主机上运行状态机测试.
- `make build` 产出经过体积优化的 release 镜像, 并启用 LTO.
- `make flash` 使用 `probe-rs` 和 `RP2350` 芯片配置来烧录并运行.
- `make clean` 删除构建产物.

现在我们来看看支撑这一切的想法: 内存映射
I/O, 以及固件到底是怎么碰到硬件的.