# Chapter 25: 用 cargo test 做主机测试

## 引言

本课程里的每个驱动都自带一套测试, 而每套测试都跑在桌面
电脑上 - 不是在芯片上. 靠的是 Cargo 配置里一个由两个文件
组成的小技巧, 我们在第 8, 18, 19 章都瞥见过它. 本章把它讲成
一个完整的故事: 主机测试为什么重要, `lib.rs` 如何让一个 crate 一物两用,
以及 `make test` 实际执行的是什么命令.

## 为什么要在主机上测试

硬件不是好的测试环境. 每跑一次测试都要烧录, 接线,
还要靠人眼观察, 结果要等几秒甚至几分钟才回来 - 或者干脆
变成一段看不懂的 LED 闪烁. 而状态机, 常量和转换函数,
则完全不需要硬件: 给它们输入, 断言输出,
再重复一遍.

比较一下这两个循环:

```
On the chip:                   On the host:
build -> flash -> wire         cargo test --lib --no-default-features
-> press button -> observe     -> 20 asserts in ~1 second
-> repeat for each change       -> repeat freely, zero wiring
```

配置里的笔误, `toggle` 转换的错误, 消抖的边界情况, 在笔记本上
几毫秒就能发现, 远远早于板子第一次上电. 测试套件
成了日常开发的一部分, 而不是事后才想起来的事.

## lib.rs 与 cfg_attr

库的根文件就是那个枢纽. 它那一行属性让这个 crate 在
`no_std` (构建固件时) 和 `std` (测试时) 之间切换:

```rust
//! FILE: lib.rs
//!
//! DESCRIPTION:
//! RP2350 闪烁驱动库模块导出.
//!
//! BRIEF:
//! 导出所有公开模块, 供测试与复用.
//! 在主机测试时按条件启用 std.
//!
//! AUTHOR: Kevin Thomas
//! CREATION DATE: November 28, 2025
//! UPDATE DATE: December 4, 2025

#![cfg_attr(not(test), no_std)]
pub mod config;
pub mod led;
```

把这一行魔法大声读出来: "只有当不是在为测试编译时, 才应用
`no_std`."

```
cargo build                    -> cfg(test) false -> #![no_std]   (bare metal)
cargo test                     -> cfg(test) true  -> #![no_std] skipped
                                 (std available for the test runner)
```

这个库始终是纯逻辑 - `config.rs`, `led.rs`, `button.rs`,
`uart.rs` 都没有导入任何嵌入式相关的东西 - 所以它在 `std` 下
也能一模一样地构建和运行. 那些硬件相关的 crate 根本不会进入测试构建.

## make test - no-default-features

Makefile 的 test 目标就是完整的仪式:

```make
test:
	cargo test --lib --target $(shell rustc --print host-tuple) --no-default-features
```

拿我们学过的东西来逐个解读这些标志:

- `--lib` - 只测试库目标. 二进制的 `main.rs` 是
  `test = false`, 根本不会被编译.
- `--target $(shell rustc --print host-tuple)` - 为*主机* CPU 编译,
  覆盖 `.cargo/config.toml` 里的嵌入式目标. 测试会作为本机
  桌面二进制运行.
- `--no-default-features` - 去掉 `Cargo.toml` 里的 `default` feature
  (第 8 章), 正是它引入了 `embassy-executor`, `embassy-time`,
  `embassy-rp`, `cortex-m`, `cortex-m-rt` 和 `panic-halt`. 这些没有一个能
  为桌面构建; 在这个构建里它们一个都不存在.

结果就是第二张并行的 crate 依赖图: 同样的纯模块, 零嵌入式
依赖, 一切都可以测试.

## 读测试输出

按钮驱动测试通过时的样子是这样的:

```
$ make test
running 20 tests
test tests::test_new_controller_not_pressed ... ok
test tests::test_default_equals_new          ... ok
test tests::test_pressed_after_threshold     ... ok
test tests::test_released_after_threshold    ... ok
test tests::test_debounce_resets_on_bounce   ... ok
test tests::test_rapid_bouncing_rejected     ... ok
...

test result: ok. 20 passed; 0 failed; 0 ignored; 0 measured
```

因为我们的类型派生了 `Debug` 和 `PartialEq` (第 5 章), 失败的
`assert_eq!` 会把实际值和期望值都打印出来 - 不需要任何调试器
就能看懂诊断信息:

```
thread 'tests::test_toggle_off_to_on' panicked at ...
assertion `left == right` failed
  left: Off
 right: On
```

## 测试驱动的文化

严格的文档注释标准和测试套件是同一个理念的两半:
代码应该能自我解释, 也应该能自我证明. 这个模式在每个
文件里都重复出现 -

```
item documented (# Details, # Arguments, # Returns)
       +
item tested (#[test] under a banner-ized module)
```

- 所以任何驱动里新加的常量或方法, 只有两者兼备才算完成.
贡献者和读者都能得到同样的两重保证: 名字说明了它做什么,
测试也认可这一点.

## 小结

- 硬件是糟糕的测试环境; 纯逻辑可以用毫秒级的速度测试.
- `#![cfg_attr(not(test), no_std)]` 让这个库在测试时是 `std`,
  为目标平台时是 `no_std`.
- `make test` = `--lib --target <host> --no-default-features`, 只为桌面
  编译那些纯模块.
- 派生出来的 `Debug`/`PartialEq` 让失败信息不言自明.
- 每一项都既有文档*又*有测试 - 这是本课程家规的两半.

第 V 部分结束. 最后一个驱动最有趣: UART, 中断
和 DMA 会在那里首次登场.