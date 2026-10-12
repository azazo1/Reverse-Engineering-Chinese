# Chapter 6: Trait 与泛型

## 引言

Trait 是 Rust 对接口的回答, 泛型是它对
"一份代码适用于多种类型" 的回答. 两者合在一起,
构成了整个生态的连接组织 - 而 Embassy 正是建立在其上的.
GPIO 的 `Output`, UART 的 `Uart`, `Timer` 使用的 `Wait`
trait - 它们每一个都是用 trait 和泛型表达的类型或契约.

## 什么是 trait?

**trait** 定义了一份行为契约: 一组类型承诺要实现的方法.
只要有一个用到该 trait 的地方,
而对应类型没有真正实现它, Rust *就无法编译这个程序*.

在本课程里我们会遇到三类 trait:

1. **派生 trait** - `Clone`, `Copy`, `Debug`, `PartialEq`,
   `Eq` - 它们的实现来自 `#[derive(...)]` (第 5 章).
2. **我们自己写的 trait 实现** - 比如 `impl Default for LedController`.
3. **Embassy 使用的 trait 约束** -
   这些契约让一段代码能驱动任何受支持的硬件.

## 定义与实现 trait

我们在第 5 章见过一个手写的 `Default`
实现. 再写一次, 这次留意它的结构:

```rust
impl Default for LedController {
    /// 返回默认的 LedController 实例.
    ///
    /// # Details
    /// 委托给 new() 完成初始化.
    ///
    /// # Returns
    /// * `Self` - 带有默认值的新 LedController
    #[allow(dead_code)]
    fn default() -> Self {
        Self::new()
    }
}
```

`impl Default for LedController` 的意思是: "LedController
获得了 `Default` trait 要求的行为." `fn default()`
上方的文档注释是我们的严格标准 - 驱动里的每个 trait 方法都会写明
`# Details`, 有参数时写 `# Arguments`, 以及 `# Returns`.

定义自己的 trait 也是同样的做法:

```rust
pub trait HasPulse {
    fn pulse(&self) -> u32;
}

impl HasPulse for LedState {
    fn pulse(&self) -> u32 {
        match self {
            LedState::On => 65535,
            LedState::Off => 0,
        }
    }
}
```

## 泛型

**泛型** 函数或类型通过参数适用于多种类型.
最经典的例子 - 也是你会一直用到的 - 是 `Option<T>`:
这里的 `T` 表示 "任意类型", 所以 `Option<u8>`
和 `Option<&[u8]>` 是同一个定义的两个不同用法.

```rust
fn take_seat<T>(thing: Option<T>) -> T {
    match thing {
        Some(value) => value,   // 泛型 T 一路流转过来
        None => panic!("no value"),
    }
}
```

在微控制器上, 泛型不花任何代价:
每个具体类型都会得到自己的一份编译结果 (见下面的单态化).
Embassy 正是利用了这一点 - 一个 GPIO bank, 一个 UART 通道和一个
DMA 通道都用泛型描述, 但编译之后会变成完全正确的寄存器地址.

## Trait 约束

**trait 约束** 限定了泛型能使用哪些类型. `T:
Copy` 表示这个泛型只能用于实现了 `Copy` 的类型:

```rust
fn echo_value<T: Copy>(value: T) -> T { value }

echo_value(5u8);         // 没问题 - u8 是 Copy
// 错误 - String 不是 Copy
```

约束可以和 `where` 子句组合起来, 让代码更好读:

```rust
fn handle<T, E>(r: Result<T, E>)
where
    T: Copy,
    E: Debug,
{
    // T 可以被复制; E 可以被调试打印
}
```

你写的每个 Embassy 驱动读起来都是一串这样的约束.
它们就是编译器的保证清单:
"这段代码适用于任何提供这些行为的类型, 而且只适用于它们."

## 单态化

Rust 会把每个泛型实例编译成专用的, 特化的代码 -
没有虚函数分发, 没有隐藏的指针跳转. 这就是 **单态化**,
也是零运行时开销的原因: 针对 `u8` 的泛型生成的字节,
和手写的 `u8` 函数一模一样. 嵌入式 Rust 依赖这个特性,
它也是这里的 "抽象" 从不意味着 "开销" 的核心原因.

```
Generic source            Compiled target
fn get<T>(x: T) -> T        get_u8:  mov w0, w0; ret
{ x }                       get_u32: mov w0, w0; ret
```

## Embassy 里的 trait

三个驱动会接触到这些既泛型又由 trait 驱动的 Embassy 类型:

- **`Output<'d, T>`** - 一个 GPIO 输出引脚, 泛型参数是引脚类型.
- **`Input<'d, T>`** - 一个 GPIO 输入引脚, 泛型参数是引脚类型.
- **`Uart<'d, T, D>`** - 一个 UART 实例, 泛型参数是通道和 DMA.
- **`Timer`** - 一个 async 等待原语; 对它 `.await` 会睡眠而不是阻塞.

你很少需要自己写出这些泛型参数 - `embassy_rp`
会推断并特化它们. 但你现在知道 `<'d, T>`
这对尖括号是什么意思了: 一个设备存活期内的借用,
外加一个编译器已经证明有效的具体引脚或外设类型.

## 小结

- trait 定义行为契约; `derive` 免费生成常见的实现.
- 泛型参数 (`<T>`) 让一个定义服务于多种类型.
- trait 约束 (`T: Copy`) 把泛型必须满足的契约编码进去.
- 单态化让泛型没有运行时开销 -
  这在微控制器上至关重要.
- Embassy 的 `Output`, `Input` 和 `Uart` 类型是对引脚,
  通道和 DMA 的泛型; 编译器在构建时把它们特化.

基础部分到此结束. 接下来我们离开主机,
走向裸机: `no_std`, `no_main` 和构建系统.