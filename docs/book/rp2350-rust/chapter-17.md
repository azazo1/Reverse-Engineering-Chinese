# Chapter 17: 用 embassy-rp 操作 GPIO

## 引言

我们的三个驱动里有两个是 GPIO 程序. 闪灯驱动持有一根 **输出**
引脚并翻转它. 按键驱动持有一根 **输入** 引脚, 读它, 再翻转
同一种输出. 本章讲解 `embassy_rp::gpio` - 也就是那四块
积木 (`Level`, `Output`, `Input`, `Pull`) 以及每个驱动都会做的调用.

## Level

`Level` 就是我们在 `led.rs` 里转成布尔值的那份电气真相:

```rust
pub enum Level {
    High,
    Low,
}
```

两行代码, 引脚上的两种电压状态:

```
+-----+        +-- HIGH (~3.3 V)
|     |       |
+-----+       |      +-- LOW (~0 V)
      |       |     |
      +-------+-----+
      Time        -->
```

构造时要给出初始状态: `Output::new(p.PIN_16, Level::Low)` 会让引脚
从低电平开始. 我们的 `led_state_to_level` 把 `LedState` 映射成 0/1 (第 5 章);
GPIO 在调用 `set_high`/`set_low` 时, 再把这个布尔值映射回一个类似
`Level` 的决定.

## 输出引脚

一根输出引脚只创建一次, 一次配置到位, 然后
一辈子都在用它:

```rust
let mut led = Output::new(p.PIN_16, Level::Low);
```

- `Output::new(pin, level)` - 认领这根引脚, 配置 pad (第 11 章),
  并设置初始电平.
- `led.set_high()` - 把引脚拉高.
- `led.set_low()` - 把引脚拉低.
- `led.toggle()` - 翻转当前状态 (由 `ToggleableOutputPin`
  trait 提供).

`mut` 是必需的, 因为这些方法接收 `&mut self` - 引脚的状态
会变. 闪灯循环正好依赖两个调用:

```rust
if led_state_to_level(state) {
    led.set_high();
} else {
    led.set_low();
}
```

泛型 `Output<'d, T>` 记得自己拥有哪根引脚 (`'d` 是这根引脚的
生命周期), 所以编译器会检查你绝不会把 GPIO16 和 GPIO17 搞混.

## 输入引脚与 Pull

读一根引脚需要电气上 *相反* 的配置: pad 必须悬空或者被
拉住, 然后芯片采样电平. 悬空这个问题正是 `Pull`
出场的地方:

```rust
pub enum Pull {
    None,
    Up,     // 没有东西驱动时把线拉高
    Down,   // 没有东西驱动时把线拉低
}
```

按键驱动这样配置它的输入:

```rust
let button = Input::new(p.PIN_15, Pull::Up);
```

有了 `Pull::Up`, 按键断开时引脚读到的就是高电平. 按下按键
会把它接地, 于是引脚读到低电平 - 这就是第 22 章的 **低电平有效** 接法.
没有上拉, 悬空的输入会读到随机噪声, 整套去抖
设计就崩了.

## 读与写

`Input` 上可用的两个读调用:

- **`is_high()`** - 输入电平为高时返回 `true`.
- **`is_low()`** - 正好相反.

按键循环用 `is_high` 采样:

```rust
controller.update(button.is_high());
```

从 `Timer` 醒来之后, 循环问这根引脚 "高还是低?", 再把
答案以 "松开还是按下?" 的形式喂进去抖滤波器. 布尔值就是
接口 - 位, 寄存器, pad 知识统统不会出现在应用
代码里.

## 我们驱动里的 GPIO

把这两块拼在一起, 看这两个循环:

```
Blink:                          Button:
+-------------+                 +---------------+
| Output::new |                 | Input::new    |
| PIN_16, Low |                 | PIN_15, Up    |
+-------------+                 +---------------+
      |                               |
      v                               v
+-------------+                 +---------------+
| toggle state|                 | update(sample)|
+-------------+                 +---------------+
      |                               |
      v                               v
+-------------+                 +---------------+
| set_high/   |                 | set_high/     |
| set_low     |                 | set_low       |
+-------------+                 +---------------+
```

每个驱动都在同样的三个时刻碰 GPIO: 创建一次引脚,
在循环里读或写它, 然后从此让 Embassy 永远持有寄存器.

## 小结

- `Level::High/Low` 是一根引脚的电气状态.
- `Output::new(pin, level)` 配置并认领一根输出引脚; 方法有
  `set_high`, `set_low` 和 `toggle`.
- `Input::new(pin, pull)` 配置一根输入引脚; `is_high`/`is_low` 采样它.
- `Pull::Up` 在没有东西驱动时把线拉高 - 这是
  按键驱动的基础.
- 精确到过分的类型 (`Output<'d, T>`) 让编译器在构建时就能抓到引脚
  误用.

第三部分到此结束: 现在你已经能读懂任何 Embassy GPIO 程序. 第四部分
在它之上搭建第一个完整的驱动 - 闪灯驱动, 一个文件一个文件地讲.