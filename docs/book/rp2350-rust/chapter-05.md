# Chapter 5: Struct, Enum 与模式匹配

## 引言

三个驱动只用到了少量自定义类型: 用 `struct` 表示控制器,
用 `enum` 表示状态, 并大量使用 `match` 把状态变成硬件动作.
本章就来打造这些工具. 学完之后, 你就能认出 `led.rs`, `button.rs`
和 `uart.rs` 里出现的每一个类型和每一条 `match` 分支.

## Struct

`struct` 把具名字段组合成一个值. 我们的
`LedController` 就是一个带两个字段的 struct:

```rust
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[allow(dead_code)]
pub struct LedController {
    state: LedState,
    delay_ms: u64,
}
```

创建 struct 值时必须给每个字段命名:

```rust
let ctrl = LedController {
    state: LedState::Off,
    delay_ms: BLINK_DELAY_MS,
};
```

访问字段用点号: `ctrl.delay_ms`.
字段默认是私有的 - 其它模块碰不到它们,
所以这个 struct 通过方法来掌控自己的不变式.

## 方法与 impl 块

挂在类型上的行为住在 `impl` 块里. 第一个参数是
`self` 或 `&self` 的方法可以作用在值上调用;
带 `&mut self` 的方法可以改变这个值:

```rust
impl LedController {
    pub fn new() -> Self {
        Self {
            state: LedState::Off,
            delay_ms: BLINK_DELAY_MS,
        }
    }

    pub fn toggle(&mut self) -> LedState {
        self.state = match self.state {
            LedState::On => LedState::Off,
            LedState::Off => LedState::On,
        };
        self.state
    }
}
```

注意两点. 第一, `toggle` 需要 `&mut self`, 因为它要写
`self.state` - 借用检查器盯着我们做了这件事. 第二,
`match self.state` 就是 Rust 给状态迁移建模的方式:
把从旧状态到新状态的映射显式写成一张表, 一个边界情况都不会漏.

## Enum

`enum` 是一种类型, 它的取值是固定且穷尽的一组变体.
我们的 `LedState` 是最简单的那种 - 一组具名取值:

```rust
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[allow(dead_code)]
pub enum LedState {
    On,
    Off,
}
```

和 C 不同, Rust 的 enum 是穷尽的: 任何处理
`LedState` 的代码都必须同时处理 `On` 和 `Off`,
否则编译器拒绝构建. 这里不存在 "不可能出现" 的野整数值,
而在用寄存器标志位做映射时, 那种值恰恰是真实的 bug 来源.

## Option 与 Result

有两个 enum 承担了太多工作, 以至于它们被内置进了语言:

- **`Option<T>`** - `Some(value)`
  或 `None`. 表示一个可能缺席的值.
- **`Result<T, E>`** - `Ok(value)` 或 `Err(error)`.
  表示一个可能失败的操作, 并携带失败原因.

UART 驱动的 `read` 是 async 的, 返回一个
`Result`. 主循环在写回任何东西之前会先检查它:

```rust
if uart.read(&mut buf).await.is_ok() {
    let echo_bytes = controller.process_char(buf[0]);
    let _ = uart.write(echo_bytes).await;
}
```

`.is_ok()` 把成功转换成布尔值,
但模式匹配还能把载荷也取出来, 我们在代码里一直这么做.

## 模式匹配

`match` 是 Rust 的主力工具. 它处理每个 enum 变体,
绑定值, 还能加守卫条件 - 而且编译器会证明它是穷尽的:

```rust
match ch {
    b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' => {
        // 字母和数字: 在这张 62 项的表里查找这个字节.
        let idx = CHARS.iter().position(|&c| c == ch).unwrap();
        &CHARS[idx..idx + 1]
    }
    b' ' => b" ",
    b'!' => b"!",
    b'\n' => b"\n",
    _ => b"",
}
```

这就是 UART 驱动 `process_char` 的真正核心. 逐个研究这些部件:

- **区间模式** - `b'A'..=b'Z'` 匹配区间内的任意字节, 包含端点.
- **或模式** - `|` 把多个备选分支合在一起.
- **绑定** - `|&c| c == ch` 是一个闭包; `.position()` 返回 `Option`.
- **`unwrap()`** - 我们知道这个字节一定在表里,
  所以匹配不上属于编程错误; 只有当不变式有保证时, `unwrap` 才是安全的.
- **`_` 通配** - 兜住其它所有情况;
  没有它这段 match 就编译不过.

`matches!` 宏让单变体判断变得简洁 -
`led_state_to_level` 正是如此:

```rust
pub fn led_state_to_level(state: LedState) -> bool {
    matches!(state, LedState::On)
}
```

## 派生 trait

`#[derive(...)]` 请求编译器自动为一个类型生成标准
trait 的实现. 我们的驱动类型都派生了同样的四个 trait:

```rust
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
```

| Trait        | 提供的能力                           | 为什么需要它                        |
|--------------|---------------------------------------|------------------------------------|
| `Clone`      | 一个 `clone()` 方法                   | 在测试里复制值                      |
| `Copy`       | 赋值时按位复制                        | 按值传递之后还能继续用              |
| `Debug`      | `{:?}` 格式化                         | 测试失败时的输出                    |
| `PartialEq`  | `==` 和 `!=`                          | 测试里的 `assert_eq!`               |
| `Eq`         | 完全等价 (不含 `NaN`)                 | 比 `==` 更强的保证                  |

因为这些实现都是派生出来的, 我们的 struct 免费获得了比较,
复制和打印的能力. 每个驱动的测试套件都依赖
`PartialEq` 加 `Debug` 来产生可读的失败信息.

## 小结

- struct 把字段聚在一起; impl 块挂上方法,
  其中包括能迁移状态的 `&mut self` 方法.
- enum 是穷尽的, 它消灭了整整一类非法值 bug.
- `Option` 和 `Result` 把缺席与失败表达在类型系统里.
- `match` 是穷尽的模式匹配 - 我们状态机的核心.
- `derive` 生成 `Clone`, `Copy`, `Debug`,
  `PartialEq` 和 `Eq` 的实现, 测试都依赖它们.

接下来是进入裸机之前的最后一根语言支柱: trait 与泛型.