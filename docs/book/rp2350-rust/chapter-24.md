# Chapter 24: main.rs - 按钮轮询循环

## 引言

按钮驱动的 `main.rs` 只比闪烁版长了十一行,
其中九行是在接一个新的输入引脚. 它以 5 ms 的节奏采样按钮,
把每个采样喂给消抖滤波器, 再用滤波器的判决去驱动 LED.
本章要讲完第二个驱动的
最后一个文件.

## 完整源代码

下面是按钮驱动的 `src/main.rs` 的完整内容:

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
//! RP2350 嵌入式 Rust Embassy 按钮驱动应用.
//!
//! BRIEF:
//! 使用 Embassy 的 RP2350 GPIO 按钮驱动主程序入口.
//! 在 GPIO 15 上实现按钮输入, 控制 GPIO 16 上的 LED.
//! 按钮低电平有效 (按下时接到 GND).
//!
//! AUTHOR: Kevin Thomas
//! CREATION DATE: November 28, 2025
//! UPDATE DATE: December 5, 2025

#![no_std]
#![no_main]

mod button;
mod config;
mod led;

use button::ButtonController;
use config::DEBOUNCE_DELAY_MS;
use embassy_executor::Spawner;
use embassy_rp::gpio::{Input, Level, Output, Pull};
use embassy_time::Timer;
use led::{led_state_to_level, LedState};
use panic_halt as _;

/// 主程序入口.
///
/// # Details
/// 初始化 Embassy 运行时, 并运行主按钮轮询循环.
/// 用带消抖的 ButtonController 管理状态.
/// GPIO15 上的按钮 (低电平有效) 控制 GPIO16 上的 LED.
///
/// # Arguments
/// * `_spawner` - Embassy 任务 spawner (为将来的异步任务预留).
///
/// # Returns
/// * `()` - 永不返回 (无限循环).
#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let p = embassy_rp::init(Default::default());
    let button = Input::new(p.PIN_15, Pull::Up);
    let mut led = Output::new(p.PIN_16, Level::Low);
    let mut controller = ButtonController::new();
    loop {
        controller.update(button.is_high());
        let state = if controller.is_pressed() {
            LedState::On
        } else {
            LedState::Off
        };
        if led_state_to_level(state) {
            led.set_high();
        } else {
            led.set_low();
        }
        Timer::after_millis(DEBOUNCE_DELAY_MS).await;
    }
}
```

整体结构就是闪烁版 main 的那套, 只是加了一个输入, 并且换掉了
控制器. 所有新东西都体现在循环如何使用 `button` 上.

## 配置的就近放置

三个模块, 一个约定:

```rust
mod button;
mod config;
mod led;
```

这次是直接从 `config` 导入的 - 它的 `DEBOUNCE_DELAY_MS` 就出现在
循环里. 低电平有效的注释在 `button.rs` 的文档和 `main` 的 BRIEF 里都
出现了: 只要这个约定管着某处行为, 它就会在那里重复一遍.

## 配置输入引脚

```rust
let button = Input::new(p.PIN_15, Pull::Up);
```

这一行就把 GPIO15 配置成带内部上拉的输入 (第 17 章
和第 22 章). 初始状态是: 这条线被上拉电阻拉高, 所以 `is_high()`
返回 `true` - 正是消抖滤波器对 "已松开" 的期望.
不用写焊盘层的代码, 也不用做功能选择的周旋; HAL 把这一切都
收进了 `Input::new`.

输出引脚的创建方式和闪烁驱动里完全一样:

```rust
let mut led = Output::new(p.PIN_16, Level::Low);
```

而滤波器则从全新状态开始:

```rust
let mut controller = ButtonController::new();
```

## 带消抖的采样

循环的第一件事就是采样加滤波:

```rust
loop {
    controller.update(button.is_high());
```

`button.is_high()` 读取焊盘并返回一个 bool; `controller.update(...)`
则应用低电平有效的反相, 以及第 23 章的计数器逻辑.
采样节奏来自循环的末尾 - 也就是那次 `Timer` 等待 - 所以每一次
迭代就是一次采样, 间隔为 `DEBOUNCE_DELAY_MS`:

```
sample  update   is_pressed   set LED   sleep 5ms
   |       |         |            |          |
   +-------+---------+------------+----------+----> repeat
```

除了那 5 ms 的睡眠, 整个循环只在微秒级的时间里跑完, 于是滤波器
以稳定的约 200 Hz 采样. 执行器的空闲就是它最大的价值.

## 驱动 LED

判决结果通过这个共享的辅助函数来转换:

```rust
let state = if controller.is_pressed() {
    LedState::On
} else {
    LedState::Off
};
if led_state_to_level(state) {
    led.set_high();
} else {
    led.set_low();
}
```

两个判断点, 读起来一目了然:

1. 滤波器的判决 → `LedState` (按下就点亮 LED, 也就是 `LedState::On`).
2. `LedState` → GPIO 电平, 通过闪烁驱动里那个可复用的 `led_state_to_level`
   完成 (现在它是这个二进制 `mod led` 的一部分).

一直按住按钮会让 `pressed == true` 保持成立, 于是 LED 一直亮着; 松开
则完全对称地反过来. 这里没有边沿触发的锁存 - 状态直接
跟随滤波器的输出.

## 一眼看完整套程序

这个驱动就是传感器 → 滤波器 → 判断 → 执行器, 首尾相连:

```
+--------+      +------------------+      +---------------+
| GPIO15 | --→  | ButtonController | --→  | LedState      |
| is_high|      | (debounce)       |      | (on/off)      |
+--------+      +------------------+      +---------------+
                                                |
                                                v
+--------+      +------------------+      +---------------+
| Timer  | ←--  | 5 ms cadence     |      | GPIO16 output |
+--------+      +------------------+      +---------------+
```

闪烁驱动证明了状态机可以按定时驱动输出. 按钮驱动证明了
输入也能经过滤波器去驱动同一个状态机. 为课程收尾的 UART
驱动, 形状完全一样.

## 小结

- `Input::new(p.PIN_15, Pull::Up)` 一行就配置好了按钮输入.
- 循环每 `DEBOUNCE_DELAY_MS` (5 ms) 采样一次, 通过
  `controller.update(button.is_high())` 喂给滤波器.
- 滤波器的判决选出 `LedState::On/Off`, 再由共享的
  `led_state_to_level` 去驱动 GPIO16.
- 整个驱动 = 传感器 → 消抖 → 判断 → 执行器 → 定时器.

现在我们退后一步, 看看那个让这些文件都能在笔记本上测试的
技巧: 主机测试框架.