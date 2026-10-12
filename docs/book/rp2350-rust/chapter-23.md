# Chapter 23: button.rs - 按钮控制器

## 引言

`button.rs` 把第 22 章的消抖理论变成可在主机上测试的
结构体. `ButtonController` 持有三个状态字段, 以及一个负责
全部滤波的方法. 和 `led.rs` 一样, 这个文件不碰任何硬件 -
它只接收布尔采样 - 所以第 22 章里的每个弹跳场景, 都能变成
在桌面上跑的 `#[test]`.

## 完整源代码

下面是 `src/button.rs` 的完整内容:

```rust
/*
 * @file button.rs
 * @brief Button input with debouncing
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

//! FILE: button.rs
//!
//! DESCRIPTION:
//! RP2350 带消抖的按钮输入.
//!
//! BRIEF:
//! 实现带消抖逻辑的按钮状态跟踪.
//! 按钮低电平有效 (按下时接到 GND).
//!
//! AUTHOR: Kevin Thomas
//! CREATION DATE: December 5, 2025
//! UPDATE DATE: December 5, 2025

use crate::config::DEBOUNCE_COUNT;

/// 带消抖的按钮控制器.
///
/// # Details
/// 用软件消抖维护按钮状态.
/// 采用基于采样的消抖, 以获得可靠的检测.
///
/// # Fields
/// * `pressed` - 当前经过消抖的按钮状态 (true = 已按下)
/// * `raw_pressed` - 当前原始 (未滤波) 状态
/// * `debounce_count` - 当前消抖计数器
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[allow(dead_code)]
pub struct ButtonController {
    pressed: bool,
    raw_pressed: bool,
    debounce_count: u32,
}

impl Default for ButtonController {
    /// 返回默认的 ButtonController 实例.
    ///
    /// # Details
    /// 把初始化工作委托给 new().
    ///
    /// # Returns
    /// * `Self` - 带默认值的新 ButtonController
    #[allow(dead_code)]
    fn default() -> Self {
        Self::new()
    }
}

impl ButtonController {
    /// 创建新的按钮控制器.
    ///
    /// # Details
    /// 以按钮松开的状态初始化控制器.
    ///
    /// # Returns
    /// * `Self` - 新的 ButtonController 实例
    #[allow(dead_code)]
    pub fn new() -> Self {
        Self {
            pressed: false,
            raw_pressed: false,
            debounce_count: 0,
        }
    }

    /// 用新的 GPIO 采样更新按钮状态.
    ///
    /// # Details
    /// 让原始 GPIO 输入经过消抖滤波器处理.
    /// 低电平有效: false (GPIO 为低) 表示已按下.
    ///
    /// # Arguments
    /// * `gpio_high` - GPIO 为高 (已松开) 时是 true, 为低 (已按下) 时是 false
    #[allow(dead_code)]
    pub fn update(&mut self, gpio_high: bool) {
        let new_raw = !gpio_high;
        if new_raw == self.raw_pressed {
            if self.debounce_count < DEBOUNCE_COUNT {
                self.debounce_count += 1;
            }
        } else {
            self.raw_pressed = new_raw;
            self.debounce_count = 0;
        }
        if self.debounce_count >= DEBOUNCE_COUNT {
            self.pressed = self.raw_pressed;
        }
    }

    /// 按钮被按下时返回 true.
    ///
    /// # Details
    /// 返回经过消抖的按钮状态.
    ///
    /// # Returns
    /// * `bool` - 按钮被按下时为 true
    #[allow(dead_code)]
    pub fn is_pressed(&self) -> bool {
        self.pressed
    }
}
```

接口只有三个方法 - `new`, `update`, `is_pressed` - 但它们编码的消抖行为,
比开头看起来的测试数量要丰富得多: 这个文件后面还跟着一整个测试模块,
我们会在讲完逻辑之后再仔细看.

## ButtonController 结构体

```rust
pub struct ButtonController {
    pressed: bool,
    raw_pressed: bool,
    debounce_count: u32,
}
```

三个字段, 三种角色 (第 22 章):

- **`pressed`** - 唯一会被别人读取的字段. 为 `true` 表示按钮
  经消抖后判定为已按下.
- **`raw_pressed`** - 最近一次未滤波的读数, 已做过低电平有效修正.
- **`debounce_count`** - 有多少个连续采样与
  `raw_pressed` 一致.

私有字段, 加上派生出来的 `Clone, Copy, Debug, PartialEq, Eq`, 与
`LedController` 完全对应 - 这几个驱动就是同一套模式配上不同的数据,
这正是共享架构的意义所在.

## update 方法

整个滤波器只有十一行:

```rust
pub fn update(&mut self, gpio_high: bool) {
    let new_raw = !gpio_high;                       // 低电平有效反相
    if new_raw == self.raw_pressed {
        if self.debounce_count < DEBOUNCE_COUNT {
            self.debounce_count += 1;               // 保持稳定, 继续累加
        }
    } else {
        self.raw_pressed = new_raw;
        self.debounce_count = 0;                    // 检测到变化: 清零
    }
    if self.debounce_count >= DEBOUNCE_COUNT {
        self.pressed = self.raw_pressed;            // 达到阈值
    }
}
```

逐条分支走一遍:

1. `new_raw = !gpio_high` - 应用低电平有效的约定: 低电平的线
   (`gpio_high == false`) 就是一次按下 (`new_raw == true`).
2. **与上次读数相同** - 按钮处于一段稳定的状态. 把计数器加一,
   上限为 `DEBOUNCE_COUNT`. 设上限可以避免任何溢出噪声.
3. **与上次不同** - 要么是弹跳, 要么是真实变化. 采纳新读数,
   并把计数器清零, 于是一个变化必须*持续存在*才作数.
4. **计数器达到 `DEBOUNCE_COUNT`** - 提交 `pressed = raw_pressed`.

阈值判断用的是 `>=`, 而自增用的是 `< ... += 1`; 两者合起来
意味着计数器会正好到达 `DEBOUNCE_COUNT`, 然后就停在那里. 这个
微妙之处在测试里得到回报: 阈值前一个采样必须*不*触发按下
(`test_one_sample_before_threshold`), 正好达到时才触发.

## is_pressed 方法

```rust
pub fn is_pressed(&self) -> bool {
    self.pressed
}
```

一个一行的取值方法. `main` 每轮喂进一个采样之后, 就查它一次:

```rust
let state = if controller.is_pressed() {
    LedState::On
} else {
    LedState::Off
};
```

读取路径被刻意做得极其简单 - 所有巧妙之处都发生在
`update` 里, 也就是采样到达的地方.

## 测试

`#[cfg(test)]` 模块证明了第 22 章弹跳理论里的每个场景.
横幅式的分组让它们便于扫读; 名字本身就把用途
说得明明白白:

- **构造** - 新建的控制器报告未按下; `default()` 等于
  `new()`.
- **消抖逻辑** - GPIO 一直保持高电平时始终是松开; `DEBOUNCE_COUNT + 1`
  次按下才算按下; 松开也以同样的方式持续.
- **拒绝弹跳** - `test_rapid_bouncing_rejected` 反复调用 `update(false)`,
  `update(true)` 十次, 并断言控制器从不判定为按下. 这就是
  滤波器存在的全部意义, 浓缩在一条断言里.
- **边界情况** - `test_exactly_at_threshold` 验证了那个边界, 而
  `test_debounce_resets_on_bounce` 验证一个孤立的 `true` 采样会重置
  朝按下方向的进度.
- **trait 实现** - `Clone`, `PartialEq`, `Debug` 的行为与派生的一致.

这些测试在主机上只需微秒级的时间, 但正因为有它们, 板子几年
之后仍然会表现正确.

## 小结

- `ButtonController` 保留三个字段: 消抖后的 `pressed`, 原始状态, 以及一个
  连续采样计数器.
- `update` 对低电平有效的采样做反相, 维护计数器 (变化时清零,
  稳定时封顶), 并在达到阈值时提交状态.
- `is_pressed` 是唯一的, 也是最简单的读取路径.
- 测试套件证明了构造, 消抖阈值, 弹跳拒绝以及
  边界情况 - 全程不需要硬件.

接下来是按钮驱动的 `main.rs`, 采样循环在那里与滤波器会合.