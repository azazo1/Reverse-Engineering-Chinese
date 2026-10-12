# Chapter 7: no_std 与 no_main

## 引言

本课程里每个固件 crate 都以同样的两行开头:

```rust
#![no_std]
#![no_main]
```

这两个 crate 属性, 就是程序离开主机,
变成裸机程序的那一刻. 本章解释它们各自真正做了什么,
我们放弃了什么, 又换来了什么.

## no_main 是什么意思?

普通 Rust 程序的入口是一个叫 `main` 的函数,
它会在其它一切之前被命名并执行. 而在微控制器上,
没有操作系统来调用它, CPU 也根本不会直接引导进 Rust.

启动流程从 **汇编** 和一段 **启动例程**
开始 (由 `cortex-m-rt` 提供), 它负责:

```
+----------------+     +------------------+     +------------------+
|   Hardware     | --> |   Vector Table   | --> |   Reset Handler  |
|    reset       |     |  (first word SP, |     |  (sets up stack, |
|                |     |   second PC)     |     |   SVC, sections) |
+----------------+     +------------------+     +------------------+
                                                       |
                                                       v
                                              +------------------+
                                              |  Rust init code  |
                                              |  (embassy_rp)    |
                                              +------------------+
```

`#![no_main]` 告诉 Rust 编译器: "不要指望标准库里的
`main` 函数, 我们自己定义入口点." 配合
`cortex-m-rt` 的 `entry` 机制, 我们的
Rust 代码会在 CPU 进入已知状态之后被调用.

在 Embassy 里, 确切的入口点由执行器创造. 加在 `async
fn` 上的 `#[embassy_executor::main]` 属性替代了 `main`
(第 14 章). 那个函数永不返回 - 执行器会一直运行下去.

## no_std 是什么意思?

Rust 标准库 `std` 假设有一个操作系统: 它带来线程,
堆分配器, `println!`, 文件和网络 - 全都由内核提供.
微控制器没有内核, 所以我们用 `#![no_std]`
退出标准库, 于是我们能用的只剩下 **core** 库.

`core` 是标准库里不需要操作系统的那部分:

```
+----------------------+     +-----------------------------+
|  std  (needs OS)     |     |  core (no OS required)      |
+----------------------+     +-----------------------------+
|  Vec, String, Box    |     |  integer types, slices,     |
|  HashMap, threads    |     |  Option, Result, iterators, |
|  println!, files     |     |  traits (Copy, Debug, ...)  |
|  heap allocator      |     |  panic machinery (hook)     |
+----------------------+     +-----------------------------+
```

我们在第一部分用到的所有东西 - 所有权, 借用, struct,
enum, `match`, trait, 泛型 - 都住在 `core` 里, 在 `no_std`
下原样可用. 我们失去的东西并不需要: `Vec` 和 `String`
需要分配器和动态内存; 避开它们的固件拥有确定且可控的内存占用.

注意那个逃生舱口. 我们的 `lib.rs` 里写着:

```rust
#![cfg_attr(not(test), no_std)]
```

在 `test` 之下 - 也就是我们为主机编译并运行测试时 - 这个
crate 就是 `std`. 第 25 章的主机测试套件靠的就是这一招.

## Panic 处理

程序不得不放弃时会怎样? 在主机上, `panic!`
会展开栈. 在 `no_std` 里可能根本没有栈展开,
而且无论如何都没有控制台可以打印.

每个驱动都用一种取巧的 import 引入 panic 处理器:

```rust
use panic_halt as _;
```

`as _` 的意思是 "只为它的副作用引入这个 crate".
`panic-halt` 安装了一个 **panic 处理器**: 发生 panic
时, 它只是让 CPU 停下来 - 通常是永久等待 (`wfi`/`b`).
在我们的板子上, 效果就是 LED 不再闪烁, 芯片安静下来.
对裸机库来说这是正确的默认行为: 停机, 而不是继续破坏.

```rust
#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}
```

每个二进制文件只能有一个 panic 处理器, 这就是为什么由被引入的
crate 提供 `#[panic_handler]`, 而我们从不自己写.

## 输出的通道

没有 `println!`, 我们怎么看见东西? 固件有自己的通道:

```
+----------------+     +----------------+     +----------------+
|  GPIO + LED    |     |  UART (serial) |     |  SWD debugger |
|  blink patterns|     |  printf-style  |     |  probe-rs     |
+----------------+     +----------------+     +----------------+
```

闪灯驱动那套亮灭的节奏就是它的输出通道. UART 驱动通过
TX/RX 把真正的字节写进终端 - 这和桌面上的 `print`
用的是同一种通道, 只不过中间连着一根真实的串口线.

## 小结

- `#![no_main]` 交出了标准入口点; CPU
  通过向量表和复位处理器启动, 然后进入 Embassy 的执行器.
- `#![no_std]` 去掉了依赖操作系统的标准库,
  但保留了 `core`, 第一部分讲的内容都在里面.
- panic 默认会让 CPU 停机 (`panic-halt`), 这是裸机上的安全选择.
- 输出通过硬件发生 - LED, UART 和调试探针 - 而不是 stdout.

接下来我们安装工具链, 构建第一个固件目标.