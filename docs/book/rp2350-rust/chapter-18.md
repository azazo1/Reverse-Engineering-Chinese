# Chapter 18: 驱动架构

## 引言

在写闪灯驱动的第一个常量之前, 我们先立好本课程每个驱动都
共享的那副骨架 - 也是你今后写任何 RP2350 驱动都该照抄的模式.
这个设计只有一个目标: 把所有 *可判定* 的逻辑都放进一个
库, 让桌面上的测试运行器能跑它, 二进制里只留
嵌入式的壳.

## 模块划分

一个驱动项目包含五个源文件, 按角色分工:

```
src/
├── lib.rs      # library root: exports config and logic modules
├── config.rs   # constants, fully documented, all testable
├── led.rs      # the LED state machine (pure logic, testable)
└── main.rs     # the async entry point (embedded only)

(button drivers add button.rs; UART drivers add uart.rs)
```

经验法则是: 如果一段代码有输入, 输出, 而且它的行为可能
出错, 那它就属于 **库**, 因为在那里你可以用
`#[test]` 调用它. 如果一段代码要碰硬件 - 引脚, 定时器, 中断 - 那它
属于 **二进制**, 它不做测试 (`Cargo.toml` 里的 `test = false`,
第 8 章), 但体积很小.

```
+------------------+          +------------------+
|   lib.rs         |          |   main.rs        |
+------------------+          +------------------+
|  config.rs       |          |  init()          |
|  led.rs          |   test   |  Output::new     |
|  (pure logic)    |  ←────── |  loop { ... }    |
+------------------+          |  Timer.await     |
                              +------------------+
```

## config.rs

配置模块就是一堆带文档的常量:

```
pub const BLINK_DELAY_MS: u64 = 500;
pub const MIN_BLINK_DELAY_MS: u64 = 10;
pub const MAX_BLINK_DELAY_MS: u64 = 10000;
```

每个常量都在自己的文档字符串里回答四个问题: 它是什么, 它
为什么存在, 有效范围是多少, 以及具体值是多少. 第 19 章
会展示这个标准的最终确切形式.

## lib.rs

库根一共三行, 外加标准文件头:

```rust
#![cfg_attr(not(test), no_std)]
pub mod config;
pub mod led;
```

- 除非在测试, 否则就是 `no_std` - 这就是第 25 章的宿主机测试开关.
- 两个私有源模块变成了公开的库模块.

## main.rs

二进制的 main 是一层薄壳, 把纯逻辑变成硬件行为:

```rust
let p = embassy_rp::init(Default::default());
let mut led = Output::new(p.PIN_16, Level::Low);
let mut controller = LedController::new();
loop {
    let state = controller.toggle();
    ...
    Timer::after_millis(controller.delay_ms()).await;
}
```

注意 `main` *没有* 包含什么: 没有去抖算术, 没有时序策略, 没有
状态. 这些全都住在库里. `main` 只把三样东西接在一起 -
执行器, 引脚和控制器 - 然后让循环永远跑下去.

## 宿主机可测性

这种拆分带来的回报, 用一条命令就能看到:

```
cargo test --lib --target <host> --no-default-features
```

因为 `config.rs`, `led.rs` 以及它们的同类都是纯 Rust - 没有
`embassy-rp`, 没有 `cortex-m`, 没有 `panic-halt` - 它们在一个只有
`core`/`std` 的桌面上就能编译, 满满一终端的 `#[test]` 函数几毫秒内
就开始并结束. 硬件行为 (引脚翻转, 连线复位) *不* 做单元
测试; 真正被测试的是围绕它的那些 *决策*.

## 小结

- 把驱动拆成一个可测的库 (`lib.rs`, `config.rs`, `led.rs`)
  和一个薄薄的嵌入式二进制 (`main.rs`).
- `config.rs` 放带文档的常量; `lib.rs` 在
  `cfg_attr(not(test), no_std)` 之下把它们导出去.
- `main.rs` 把硬件和执行器接起来, 但几乎不承担逻辑.
- 这个库在宿主机上用 `--no-default-features` 就能编译和测试.

现在我们开始写真正的文件. 第 19 章从 `config.rs` 开始 -
标准文件头, 以及第一批带文档的常量.