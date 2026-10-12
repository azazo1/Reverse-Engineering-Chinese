# Chapter 21: main.rs - 异步闪烁循环

## 引言

`main.rs` 是唯一直接接触 RP2350 的文件. 它初始化 HAL, 配置一个 GPIO 输出,
然后跑一个无限 async 循环: 切换 `LedController` 的状态, 并把结果写到引脚上.
第 III 部分的每个概念 - 执行器, `Timer`, GPIO, 外设 - 都在这里落地,
一共 80 行.

## 完整源代码

下面是 `src/main.rs` 的完整内容:

```rust
/*
 * @file main.rs
 * @brief Microcontroller entry point
 * @author Kevin Thomas
 * @date 2025
 *
 * MIT License
 *
 * Copyright (c) 2025 Kevin Thomas
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

//! FILE: main.rs
//!
//! DESCRIPTION:
//! RP2350 嵌入式 Rust Embassy 闪烁应用.
//!
//! BRIEF:
//! 使用 Embassy 的 RP2350 GPIO 闪烁驱动主程序入口.
//! 在 GPIO 16 上实现异步 LED 闪烁.
//!
//! AUTHOR: Kevin Thomas
//! CREATION DATE: November 28, 2025
//! UPDATE DATE: December 4, 2025

#![no_std]
#![no_main]

mod config;
mod led;

use embassy_executor::Spawner;
use embassy_rp::gpio::{Level, Output};
use embassy_time::Timer;
use led::{led_state_to_level, LedController};
use panic_halt as _;

/// 主程序入口.
///
/// # Details
/// 初始化 Embassy 运行时, 并运行主闪烁循环.
/// 用 BlinkController 管理状态.
///
/// # Arguments
/// * `_spawner` - Embassy 任务 spawner (为将来的异步任务预留).
///
/// # Returns
/// * `()` - 永不返回 (无限循环).
#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let p = embassy_rp::init(Default::default());
    let mut led = Output::new(p.PIN_16, Level::Low);
    let mut controller = LedController::new();
    loop {
        let state = controller.toggle();
        if led_state_to_level(state) {
            led.set_high();
        } else {
            led.set_low();
        }
        Timer::after_millis(controller.delay_ms()).await;
    }
}
```

每一行都有它存在的理由. 我们从上到下逐行讲解.

## crate 属性

```rust
#![no_std]
#![no_main]
```

两行就是第 7 章的内容. 这个二进制跑在裸机上, 没有标准的 main.
`embassy-rp`, `cortex-m-rt`, `panic-halt` 这些只用于嵌入式的依赖之所以存在,
正是因为这两个属性要求如此.

## 模块声明与导入

```rust
mod config;
mod led;
```

`mod` 把这两个库文件拉进当前二进制的模块树. `config` 是间接使用的
(它的常量通过 `LedController::new()` 流进来); `led` 则提供了
`LedController`, `led_state_to_level` 以及它们的同伴.

```rust
use embassy_executor::Spawner;
use embassy_rp::gpio::{Level, Output};
use embassy_time::Timer;
use led::{led_state_to_level, LedController};
use panic_halt as _;
```

每个依赖只导入一项, 正好是这个二进制需要的表面:

- `Spawner` - 传给 `main` 的执行器句柄 (目前还没用到).
- `Level` 和 `Output` - GPIO 输出配置.
- `Timer` - 异步等待.
- `led` 导出的两项 - 状态机.
- `panic_halt as _` - 只为副作用而导入的 panic 处理器.

没有多余的东西被编译进来; 这个小二进制正好对应它小小的用途.

## 异步入口点

```rust
/// 主程序入口.
///
/// # Details
/// 初始化 Embassy 运行时, 并运行主闪烁循环.
/// 用 BlinkController 管理状态.
///
/// # Arguments
/// * `_spawner` - Embassy 任务 spawner (为将来的异步任务预留).
///
/// # Returns
/// * `()` - 永不返回 (无限循环).
#[embassy_executor::main]
async fn main(_spawner: Spawner) {
```

即使是 `main`, 文档注释也严格遵守标准: `# Details`,
`# Arguments` 和 `# Returns` (这里是 "永不返回"). 这个属性是第
14 章的具体化: 它启动执行器, 并把当前 async 函数 spawn 出去.
`_spawner` 参数留给将来的任务 - 前导下划线是在告诉
编译器, 我们知道它没被用到.

## 初始化外设

```rust
let p = embassy_rp::init(Default::default());
let mut led = Output::new(p.PIN_16, Level::Low);
let mut controller = LedController::new();
```

三行代码, 三个层次的准备工作:

- `embassy_rp::init(Default::default())` - 配置时钟, 释放复位,
  返回 `Peripherals` 令牌 (第 16 章).
- `Output::new(p.PIN_16, Level::Low)` - 把 GPIO16 占为输出, 并让它输出
  低电平 (第 17 章). 令牌 `p.PIN_16` 被移动到引脚里; GPIO16 从此永远
  归我们所有.
- `LedController::new()` - 让状态机从 Off 开始, 延时 500 ms (第 20 章).

## 闪烁循环

```rust
loop {
    let state = controller.toggle();
    if led_state_to_level(state) {
        led.set_high();
    } else {
        led.set_low();
    }
    Timer::after_millis(controller.delay_ms()).await;
}
```

每次迭代走四步:

1. `controller.toggle()` - 推进状态机, 并记住结果.
2. `if led_state_to_level(state)` - 把 LedState 转换成硬件层面的
   决定.
3. `led.set_high()` / `set_low()` - 真正驱动引脚.
4. `Timer::after_millis(controller.delay_ms()).await` - 用协作的方式
   睡眠, 让执行器空转, 或者去跑其他任务.

这个循环是程序的心脏: 每轮 500 ms, LED 每半秒翻转一次 - 这就是
闪烁.

## 小结

- `main.rs` 是唯一的嵌入式文件; 它把执行器, GPIO 和控制器接在一起.
- `#![no_std]` 加 `#![no_main]` 让它成为裸机程序; `panic_halt as _` 负责
  处理 panic 时的停机.
- `#[embassy_executor::main]` 在 RP2350 上启动执行器.
- 初始化只做一次: HAL 初始化, 输出引脚, 控制器.
- 循环在协作式的 `Timer` 等待两侧, 轮流推进状态机和写 GPIO.
- 三行初始化, 四步循环, 一个状态机 - 闪烁驱动到此为止.

闪烁驱动到这里就完整, 也可以测试了. 第 V 部分讲第二个驱动 -
按钮 - 从那个让它变得有趣的硬件现实讲起:
也就是消抖.