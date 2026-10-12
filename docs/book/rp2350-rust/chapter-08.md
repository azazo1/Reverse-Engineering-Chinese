# Chapter 8: Cargo, 目标与工具链

## 引言

Cargo 是 Rust 的构建系统和包管理器. 它也是嵌入式
Rust 整套工具链的黏合剂: 一条 `cargo build`
就会调用正确的编译器, 链接正确的库, 并为我们这颗确切的
CPU 产出二进制. 本章带你装好所有东西, 并读懂一个驱动里的
`Cargo.toml`, `.cargo/config.toml` 和构建命令.

## 安装工具链

你需要两样东西:

1. 通过 [rustup](https://rustup.rs) 安装的 **Rust** - 工具链管理器.
2. **ARM GNU 工具链**, 用来提供链接器和其它主机工具 - 可从
   [arm.com](https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads)
   获取. 安装过程中请勾选 **Add path to environment variable**.

验证安装:

```bash
$ rustup --version
rustup 1.27.1

$ rustc --version
rustc 1.84.0 (9fc0cc514 2025-02-28)

$ arm-none-eabi-gcc --version
... (arm-none-eabi-gcc) 13.2.Rel1 ...
```

烧录和片上调试我们用 `probe-rs`:

```bash
$ cargo install probe-rs-tools
```

## 目标平台: thumbv8m.main-none-eabihf

Rust 不会编译成 "泛泛的 ARM". 它编译到一个
**目标三元组**, 由它指明确切的架构, ABI 和运行环境:

```
thumbv8m.main-none-eabihf
│       │     │       └── hard-float ABI
│       │     └────────── no standard library (bare metal)
│       └──────────────── mainline ARMv8-M (has the main features: security etc.)
└──────────────────────── Thumb instruction set
```

RP2350 的 M33 核属于 ARMv8-M mainline, 使用 Thumb 指令集,
所以 `thumbv8m.main-none-eabihf` 正好是我们的目标.
`none` 表示没有操作系统 - 这与 `no_std` 对应.

安装它:

```bash
$ rustup target add thumbv8m.main-none-eabihf
```

## .cargo/config.toml

驱动的 `.cargo/config.toml` 告诉 Cargo
在所有地方都使用这个目标, 并传入嵌入式运行时需要的链接器参数:

```toml
[build]
target = "thumbv8m.main-none-eabihf"

[target.thumbv8m.main-none-eabihf]
runner = "probe-rs run --chip RP2350"
rustflags = [
  "-C", "link-arg=--nmagic",
  "-C", "link-arg=-Tlink.x",
]
```

这里有两类标志:

- `--nmagic` - 不对数据段做页对齐;
  对 flash 来说二进制更小也更简单.
- `-Tlink.x` - 使用由 `cortex-m-rt` 根据我们自己的
  `memory.x` 生成的 `link.x` 链接脚本 (第 9 章).

在这里设好 `target` 之后, 直接 `cargo build` 就会面向 RP2350 构建, 而
`cargo run` 会通过 `probe-rs` 烧录 - 这正是每个驱动 README 里给出的表面 API.

## Cargo.toml

驱动的 `Cargo.toml` 有意拆成 **库** 和
**二进制** 两部分. 库装着所有可测试的逻辑;
二进制只是一层薄薄的 async 外壳:

```toml
[package]
name = "rp2350-blink"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "rp2350-blink"
test = false

[lib]
name = "rp2350_blink"
path = "src/lib.rs"
test = true
```

关键在于, **二进制不跑测试** (`test = false`),
而 **库跑测试** (`test = true`). 库里没有 main,
也没有中断机制, 所以 `cargo test --lib` 能在主机上运行它.

## 可选依赖与 feature

只有嵌入式二进制才需要的依赖 (Embassy, `cortex-m-rt`,
`panic-halt`) 都声明为 `optional`, 并藏在一个 feature 后面:

```toml
[dependencies]
embassy-executor = { git = "https://github.com/embassy-rs/embassy", features = [
    "arch-cortex-m",
    "executor-thread",
], optional = true }
embassy-time = { git = "https://github.com/embassy-rs/embassy", optional = true }
embassy-rp = { git = "https://github.com/embassy-rs/embassy", features = [
    "time-driver",
    "rp235xa",
    "critical-section-impl",
    "imagedef-secure-exe",
], optional = true }
cortex-m = { version = "0.7.7", optional = true }
cortex-m-rt = { version = "0.7.3", optional = true }
panic-halt = { version = "1.0.0", optional = true }

[features]
default = [
    "embassy-executor",
    "embassy-time",
    "embassy-rp",
    "cortex-m",
    "cortex-m-rt",
    "panic-halt",
]
```

`embassy-rp` 的这些 feature 就是硬件旋钮:

- `time-driver` - `embassy-time` 用来做延时的 RTC/定时器后端.
- `rp235xa` - 面向 RP2350 (RP235xA) 芯片.
- `critical-section-impl` - 提供临界区机制 (第 16 章).
- `imagedef-secure-exe` - 生成 RP2350 bootrom 所需的
  secure image definition (与第 9 章的 `memory.x` 配对).

`[features] default` 这一组就是普通 `cargo build` 会启用的东西.
跑主机测试时我们传 `--no-default-features`, 把所有嵌入式选项都去掉,
让 crate 用普通的 `core`/`std` 编译 (第 25 章).

## 小结

- rustup 安装 Rust; ARM GNU
  工具链提供链接器; probe-rs 负责烧录.
- `thumbv8m.main-none-eabihf`
  目标指明了我们确切的 CPU 和裸机 ABI.
- `.cargo/config.toml` 把 RP2350
  设为默认目标, 并提供 `--nmagic` 和 `link.x`.
- `Cargo.toml` 把一个可测试的库和一个不跑测试的二进制分开.
- 可选加 feature 门控的依赖, 让 no_std
  二进制和可在主机测试的库彼此隔离.

接下来是链接脚本, 它把我们的代码放到 flash 里正确的地址上.