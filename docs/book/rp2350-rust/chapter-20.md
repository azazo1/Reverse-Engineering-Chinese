# Chapter 20: led.rs - LED 状态机

## 引言

`led.rs` 是闪灯驱动的大脑: 一个两状态的状态机, 外加一个翻转它的
控制器. 这个文件是纯逻辑 - 没有 Embassy, 没有寄存器, 没有 `unsafe`.
这是刻意的: 它就是那个你可以放到桌面上跑, 并证明其正确的文件.
本章先完整走一遍源码, 再逐块拆解.

## 完整源代码

下面是 `src/led.rs` 的完整内容:

```rust
/*
 * @file led.rs
 * @brief LED state management
 * @brief LED 状态管理
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

//! FILE: led.rs
//!
//! DESCRIPTION:
//! RP2350 的 LED 状态管理.
//!
//! BRIEF:
//! 提供 LED 状态枚举和闪灯控制器.
//!
//! AUTHOR: Kevin Thomas
//! CREATION DATE: December 5, 2025
//! UPDATE DATE: December 6, 2025

use crate::config::BLINK_DELAY_MS;

/// LED 状态枚举.
///
/// # Details
/// 表示 LED 当前的状态.
/// 用于状态跟踪与状态切换.
///
/// # Variants
/// * `On` - LED 当前是亮的 (高电平)
/// * `Off` - LED 当前是灭的 (低电平)
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[allow(dead_code)]
pub enum LedState {
    On,
    Off,
}

/// 带状态跟踪的 LED 控制器.
///
/// # Details
/// 维护 LED 状态和闪灯时序配置.
/// 提供状态切换和查询的方法.
///
/// # Fields
/// * `state` - 当前 LED 状态
/// * `delay_ms` - 闪烁延时, 单位毫秒
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[allow(dead_code)]
pub struct LedController {
    state: LedState,
    delay_ms: u64,
}

impl Default for LedController {
    /// 返回默认的 LedController 实例.
    ///
    /// # Details
    /// 委托给 new() 完成初始化.
    ///
    /// # Returns
    /// * `Self` - 带默认值的新 LedController
    #[allow(dead_code)]
    fn default() -> Self {
        Self::new()
    }
}

impl LedController {
    /// 用默认设置创建新的 LED 控制器.
    ///
    /// # Details
    /// 把控制器初始化成 LED 熄灭状态.
    ///
    /// # Returns
    /// * `Self` - 新的 LedController 实例
    #[allow(dead_code)]
    pub fn new() -> Self {
        Self {
            state: LedState::Off,
            delay_ms: BLINK_DELAY_MS,
        }
    }

    /// 翻转 LED 状态并返回新状态.
    ///
    /// # Details
    /// 把 LED 从亮切到灭, 或者从灭切到亮.
    ///
    /// # Returns
    /// * `LedState` - 翻转之后的新 LED 状态
    #[allow(dead_code)]
    pub fn toggle(&mut self) -> LedState {
        self.state = match self.state {
            LedState::On => LedState::Off,
            LedState::Off => LedState::On,
        };
        self.state
    }

    /// 返回当前的闪烁延时.
    ///
    /// # Details
    /// 闪灯时序所用的延时, 单位毫秒.
    ///
    /// # Returns
    /// * `u64` - 延时, 单位毫秒
    #[allow(dead_code)]
    pub fn delay_ms(&self) -> u64 {
        self.delay_ms
    }
}

/// 把 LedState 转换成布尔值, 供 GPIO 控制使用.
///
/// # Details
/// 把 On 状态映射为 true (高电平), Off 状态映射为 false (低电平).
///
/// # Arguments
/// * `state` - 要转换的 LED 状态
///
/// # Returns
/// * `bool` - On 为 true, Off 为 false
#[allow(dead_code)]
pub fn led_state_to_level(state: LedState) -> bool {
    matches!(state, LedState::On)
}

#[cfg(test)]
mod tests {
    use super::*;

    // ==================== LedState 枚举测试 ====================

    #[test]
    fn test_led_state_equality() {
        assert_eq!(LedState::On, LedState::On);
        assert_eq!(LedState::Off, LedState::Off);
        assert_ne!(LedState::On, LedState::Off);
    }

    #[test]
    fn test_led_state_copy() {
        let state = LedState::On;
        let copy = state;
        assert_eq!(state, copy);
    }

    #[test]
    fn test_led_state_to_level_on() {
        assert!(led_state_to_level(LedState::On));
    }

    #[test]
    fn test_led_state_to_level_off() {
        assert!(!led_state_to_level(LedState::Off));
    }

    // ==================== LedController 测试 ====================

    #[test]
    fn test_new_controller() {
        let ctrl = LedController::new();
        assert_eq!(ctrl.delay_ms(), BLINK_DELAY_MS);
    }

    #[test]
    fn test_default_equals_new() {
        let default = LedController::default();
        let new = LedController::new();
        assert_eq!(default.delay_ms(), new.delay_ms());
    }

    #[test]
    fn test_toggle_off_to_on() {
        let mut ctrl = LedController::new();
        assert_eq!(ctrl.toggle(), LedState::On);
    }

    #[test]
    fn test_toggle_on_to_off() {
        let mut ctrl = LedController::new();
        ctrl.toggle();
        assert_eq!(ctrl.toggle(), LedState::Off);
    }

    #[test]
    fn test_multiple_toggles() {
        let mut ctrl = LedController::new();
        assert_eq!(ctrl.toggle(), LedState::On);
        assert_eq!(ctrl.toggle(), LedState::Off);
        assert_eq!(ctrl.toggle(), LedState::On);
        assert_eq!(ctrl.toggle(), LedState::Off);
    }

    #[test]
    fn test_initial_state_off() {
        let ctrl = LedController::new();
        let expected = LedController {
            state: LedState::Off,
            delay_ms: BLINK_DELAY_MS,
        };
        assert_eq!(ctrl, expected);
    }

    // ==================== trait 实现测试 ====================

    #[test]
    fn test_led_state_debug() {
        let state = LedState::On;
        let debug_str = format!("{:?}", state);
        assert!(debug_str.contains("On"));
    }

    #[test]
    fn test_led_controller_clone() {
        let ctrl1 = LedController::new();
        let ctrl2 = ctrl1;
        assert_eq!(ctrl1.delay_ms(), ctrl2.delay_ms());
    }

    #[test]
    fn test_led_controller_partial_eq() {
        let ctrl1 = LedController::new();
        let ctrl2 = LedController::new();
        assert_eq!(ctrl1, ctrl2);
    }

    #[test]
    fn test_led_controller_debug() {
        let ctrl = LedController::new();
        let debug_str = format!("{:?}", ctrl);
        assert!(debug_str.contains("LedController"));
    }
}
```

这就是驱动完整的大脑: 一个枚举, 一个结构体, 一个辅助函数, 以及一套
证明状态切换正确的测试. 闪灯驱动里其余的东西都只是
管道.

## LedState 枚举

闪灯的两种状态, 穷尽地定义出来:

```rust
pub enum LedState {
    On,
    Off,
}
```

因为这个枚举派生了 `PartialEq` 和 `Debug`, 测试套件才能写出
`assert_eq!(ctrl.toggle(), LedState::On)`, 并且出错时得到一份可读的失败信息.
因为它派生了 `Copy`, 按值传它 (`led_state_to_level(state)`)
不会消耗它. `# Variants` 文档字符串为每个变体开票 - On 是高电平,
Off 是低电平 - 所以到 GPIO 的映射永远不会让人意外.

## LedController 结构体

控制器把当前状态和时序策略捆在一起:

```rust
pub struct LedController {
    state: LedState,
    delay_ms: u64,
}
```

两个字段都是 **私有** 的, 而结构体构造函数 `new()` 是唯一的
入口. 因此外部无法破坏它的不变式: 一个 `LedController` 总是
以配置好的延时从 Off 开始, 而且只有 `toggle` 能改它的状态.

在一个只有两个 `Copy` 字段的结构体上派生 `Clone, Copy, Debug, PartialEq, Eq`
是免费的, 而这些派生也确实在干活: `test_led_controller_clone`
执行 `ctrl2 = ctrl1`, 之后两者都还能用.

## Default trait

```rust
impl Default for LedController {
    fn default() -> Self {
        Self::new()
    }
}
```

`Default` 就是 `LedController::default()` 背后那个 trait. 它只是委托给
`new()`, 从而只保留一个规范的初始化入口. 那为什么还要实现它? 因为
一个类型一旦实现了 `Default`, 它就能和整个生态组合起来 - 集合,
可选值, 以及那些要求 `T: Default` 的泛型代码. 它是我们的控制器
与第 6 章那个更广阔的 trait 世界之间的一座一行桥.

## toggle 与 delay_ms

`toggle` 就是整台状态机, 只不过穿上了表格的外衣:

```rust
pub fn toggle(&mut self) -> LedState {
    self.state = match self.state {
        LedState::On => LedState::Off,
        LedState::Off => LedState::On,
    };
    self.state
}
```

必需的几块:

- `&mut self` - 因为这个方法会重新赋值 `self.state`; 借用检查器
  放我们进来, 是因为我们申请的是独占访问.
- `match self.state` - 穷尽: 两个变体都处理了, 各自映射到一个
  变体. `}` 下面那条注释横幅什么都没记录, 因为代码
  本身已经不言自明; 上面的文档字符串宣告了契约: 在 On 和 Off 之间切换.
- 返回 *新* 状态 - `main` 用这个返回值在
  同一串表达式里驱动引脚.

`delay_ms` 是这套策略的读侧: `&self`, 一个普通 getter, 返回
`self.delay_ms`. `main` 每一轮都在 `Timer` 表达式里调用它, 所以
配置好的周期就是唯一的事实来源.

## led_state_to_level

从 `LedState` 到电子学之间那座小小的桥:

```rust
pub fn led_state_to_level(state: LedState) -> bool {
    matches!(state, LedState::On)
}
```

`LedState` 是 "我们想要什么" 的概念; GPIO 的 `Level` 是 "线上看到什么"
的概念. 这个辅助函数让 `main` 读起来像英语: `if led_state_to_level(state)
{ led.set_high() }`. 按键驱动照搬的正是同一个模块里的
`led_state_to_level`, 一个字都不用改 - 两个驱动共用
它.

## 测试

三个横幅下面一共二十个测试. 横幅按关注点分组:

- **`LedState Enum Tests`** - 相等性, 复制, 以及转换辅助函数.
- **`LedController Tests`** - 构造, 默认值, 以及每一种状态
  切换.
- **`Trait Implementation Tests`** - 派生的 trait 行为正常.

最有价值的是那些状态切换测试. `test_initial_state_off` 手工构造出
期望的结构体并比较 - 以此证明 `new()` 恰好设置了 `state:
Off, delay_ms: BLINK_DELAY_MS`. `test_multiple_toggles` 证明它是交替的:
On, Off, On, Off, 永远如此. 这些测试把闪灯节奏钉成数据, 而这套
测试在笔记本上不到一秒就跑完.

## 小结

- `LedState` 是一个穷尽的 On/Off 枚举; `LedController` 用私有的状态
  字段和时序字段把它包起来.
- `Default` 委托给 `new()`; `toggle` 是一张状态切换表;
  `delay_ms` 是一个纯 getter.
- `led_state_to_level` 把状态转成给 GPIO 用的布尔值, 闪灯和
  按键两个驱动共用它.
- 测试套件 - 按横幅分组 - 在宿主机上证明构造, 切换以及
  trait 行为.

接下来是闪灯驱动的最后一块: `main.rs`, 那个 async 外壳.