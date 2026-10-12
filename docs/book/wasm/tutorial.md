# 教程: 使用 Pulley 的 WebAssembly 组件模型 - 从零开始

## 许可证

SPDX-License-Identifier: MIT

Copyright (c) 2026 Kevin Thomas

---

## 这本书写给谁

你从没用过 WebAssembly. 你没听过 WIT, 组件模型和 Pulley. Rust 你可能懂, 也可能不懂. 本教程不预设任何前提, 把所有东西都讲清楚. 读完之后, 你会确切知道这个项目里每个文件, 每个结构体, 每个函数, 每一行代码在做什么, 以及它们对嵌入式系统为什么重要.

---

## 目录

1. [全局图景](#全局图景)
2. [什么是 WebAssembly (Wasm)](#什么是-webassembly-wasm)
3. [什么是 Wasm 运行时](#什么是-wasm-运行时)
4. [什么是 Wasmtime](#什么是-wasmtime)
5. [什么是 Pulley](#什么是-pulley)
6. [什么是 WIT](#什么是-wit)
7. [什么是组件模型](#什么是组件模型)
8. [什么是 no_std](#什么是-no_std)
9. [什么是 AOT 预编译](#什么是-aot-预编译)
10. [项目结构](#项目结构)
11. [WIT 文件逐行讲解](#wit-文件逐行讲解)
12. [Guest1 逐行讲解](#guest1-逐行讲解)
13. [Guest2 逐行讲解](#guest2-逐行讲解)
14. [构建脚本逐行讲解](#构建脚本逐行讲解)
15. [宿主逐行讲解](#宿主逐行讲解)
16. [深入 Engine](#深入-engine)
17. [深入 Linker](#深入-linker)
18. [深入 Store](#深入-store)
19. [深入 Component](#深入-component)
20. [深入 Instance](#深入-instance)
21. [它们如何串在一起](#它们如何串在一起)
22. [集成测试逐行讲解](#集成测试逐行讲解)
23. [如何构建和运行](#如何构建和运行)
24. [这对嵌入式系统为什么重要](#这对嵌入式系统为什么重要)
25. [术语表](#术语表)

---

## 全局图景

这个项目有两个客体程序和一个宿主程序. 两个客体用 Rust 以 `#![no_std]` (不带标准库) 编写, 编译成 WebAssembly, 再打包成 "组件". 构建时, 构建脚本 (`build.rs`) 编译每个客体, 把它编码成 WebAssembly 组件, 并 AOT 预编译成 Pulley 字节码. 宿主二进制程序把这些预编译产物嵌进去, 在运行时反序列化, 然后调用客体导出的函数. 客体通过组件模型的规范 ABI 返回字符串 - 不用 WASI, 不用 `println!`, 也不依赖任何操作系统.

整个执行流程长这样:

```
You type: cargo build

    build.rs runs:
        |
        v
    compile_guest_wasm("guest1") -> cargo build --target wasm32-unknown-unknown
        |
        v
    read_core_wasm() -> reads the guest1.wasm bytes
        |
        v
    encode_component() -> wraps core wasm as a Component Model component
        |
        v
    engine.precompile_component() -> AOT compiles to Pulley bytecode
        |
        v
    write guest1.cwasm to OUT_DIR (repeat for guest2)

You type: cargo run --bin hello

    main() starts in host.rs
        |
        v
    build_engine() creates a Wasmtime Engine configured for Pulley
        |
        v
    load_component() deserializes precompiled guest1 from include_bytes!
        |
        v
    run_guest1() creates Linker<()> + Store<()>, instantiates, calls run()
        |
        v
    Guest returns String "guest1 run() called" -> host prints it
        |
        v
    load_component() deserializes precompiled guest2 from include_bytes!
        |
        v
    run_guest2() calls run(Some(name)) and describe()
        |
        v
    Guest returns strings -> host prints them
```

---

## 什么是 WebAssembly (Wasm)

WebAssembly 是一种二进制指令格式. 你可以把它想成一种可移植的机器语言. 当你用 C, Rust, Go 或别的语言写代码时, 编译器通常生成的是针对某一款处理器的机器码 - Intel/AMD 上是 x86, 手机和树莓派上是 ARM, 等等. 那些机器码只能在那一种处理器上运行.

WebAssembly 不一样. 编译器生成的指令不是给真实处理器用的, 而是给一台虚拟机的. 也就是说, 同一份编译好的 WebAssembly 二进制文件, 在任何装了 WebAssembly 运行时的系统上都能跑, 不管那台系统的处理器是什么.

WebAssembly 的几个关键性质:

- **可移植**: 一份二进制文件, 凡是有运行时的地方都能运行.
- **沙箱化**: 除非宿主显式允许, WebAssembly 程序碰不到你的文件系统, 网络或内存. 这是一项安全特性.
- **快**: 比传统的解释器 (比如 Python 或 JavaScript 解释器) 快得多, 因为这种格式的设计目标就是贴近原生机器码.

---

## 什么是 Wasm 运行时

Wasm 运行时就是真正执行 WebAssembly 代码的那个程序. WebAssembly 二进制文件本身只是一堆字节, 它自己跑不起来. 它需要一个运行时来做这些事:

1. 读取并校验二进制文件.
2. 编译或解释其中的指令.
3. 提供客体代码需要的导入 (如果有的话).
4. 在被要求时执行客体导出的函数.

可以这样理解: 一个 `.mp3` 文件本身不会发出声音, 你需要一个播放器 (也就是运行时) 去读它, 把音频送到扬声器. 一个 `.wasm` 文件自己也不会执行, 你需要一个 Wasm 运行时去读它, 执行它的指令.

---

## 什么是 Wasmtime

Wasmtime 是其中一个具体的 Wasm 运行时, 由 Bytecode Alliance 打造. 它用 Rust 编写, 面向生产环境设计. 还有别的运行时 (Wasmer, WasmEdge 等等), 但这个项目用的是 Wasmtime.

Wasmtime 提供 Rust crate `wasmtime`, 其中给出了 `Engine`, `Store`, `Component`, `Linker` 这些类型. 你的宿主程序就是用这些积木块来加载和运行客体的 WebAssembly 代码的.

在本项目里, `host.rs` 中的宿主程序直接使用 `wasmtime` crate.

---

## 什么是 Pulley

Pulley 是内建于 Wasmtime 的软件解释器. 要理解它为什么存在, 你得先明白 Wasmtime 平时是怎么执行 WebAssembly 的.

**Wasmtime 的常规执行方式 (在你的笔记本或服务器上):**

Wasmtime 用一个叫 Cranelift 的编译器, 把 WebAssembly 指令翻译成你处理器上的原生机器码 (大多数笔记本上是 x86-64, Apple Silicon Mac 上是 AArch64). 这种方式很快, 因为结果是真正的机器码, 直接在你的 CPU 上跑.

**在嵌入式系统上遇到的问题:**

嵌入式微控制器 (比如树莓派 Pico 2 上的 RP2350) 用的处理器, Cranelift 并不支持. RP2350 用的是 Cortex-M33 (ARMv8-M) 处理器, Cranelift 没法为它生成原生代码. 所以 Wasmtime 的常规执行方式在这里行不通.

**Pulley 的解决办法:**

Pulley 是 Wasmtime 内部的一个可移植解释器. Wasmtime 不再把 WebAssembly 编译成原生机器码, 而是编译成 Pulley 字节码 - 一套简单的指令集, Pulley 解释器可以在任何处理器上执行它, 包括 Cranelift 不支持的那些.

代价是: Pulley 比原生编译慢, 因为 Pulley 解释器必须一条一条地读取并执行字节码指令, 而不是让 CPU 直接执行原生指令. 但它到处都能跑, 而对嵌入式来说这正是全部意义所在.

**在本项目中:**

我们在构建脚本和宿主里都设置了 `config.target("pulley64")`. 这是在告诉 Wasmtime: "不要编译成原生机器码, 改成编译成 Pulley 字节码." 我们用 `pulley64`, 因为运行在 64 位系统上 (你的 Mac). 如果目标像 RP2350 那样是 32 位嵌入式平台, 就要用 `pulley32`.

这个项目在你的笔记本上运行, 目的是把概念讲清楚. 而这套架构 - 宿主反序列化预编译的客体组件, 再通过 Pulley 执行 - 和 [embedded-wasm-uart-rp2350](https://github.com/mytechnotalent/embedded-wasm-uart-rp2350) 项目里跑在 RP2350 这类嵌入式微控制器上的架构完全一样.

---

## 什么是 WIT

WIT 是 WebAssembly Interface Types 的缩写. 它是一门纯文本语言, 用来定义跨越宿主与客体边界的函数签名.

**它为什么存在:**

当宿主想调用客体里的某个函数时, 两边必须对函数名, 参数, 返回值达成一致. WIT 就是把这些约定写下来的方式.

把 WIT 看成一纸契约. 客体说: "我保证导出一个叫 `run` 的函数, 它返回字符串." 宿主说: "我会去找一个叫 `run` 的函数, 它返回字符串." 两边都遵守契约, 一切正常. 如果对不上 (客体导出的 `run` 什么都不返回, 而宿主期待一个字符串), 实例化就会失败.

**一个 WIT 文件长什么样:**

```wit
package component:guest1;

world guest1-world {
    export run: func() -> string;
}
```

这段代码的意思是:

- `package component:guest1;` - 这个 WIT 文件属于一个叫 `component:guest1` 的包. 包名只是一个标识符.
- `world guest1-world` - "世界" (world) 是对一个组件导入和导出什么的完整描述. `guest1-world` 这个名字会被 `wit_bindgen::generate!` 宏用来找到正确的 world.
- `export run: func() -> string;` - 这个组件承诺导出一个叫 `run` 的函数, 它不接受参数, 返回一个字符串.

---

## 什么是组件模型

组件模型是架在 WebAssembly 之上的一套标准. 普通的 ("核心") WebAssembly 只认识数字 - 整数和浮点数. 它没有字符串, 列表, 记录这些高层类型的概念, 也没有除了数字参数裸函数签名之外的标准方式来描述导入导出.

组件模型补上了这些东西:

1. **丰富的类型**: 字符串, 列表, 记录, option, result, 枚举, 标志位等等. 当你的客体函数接受一个 `Option<String>` 时, 组件模型负责把这个 Rust 类型转换成客体能接收的字节.
2. **基于 WIT 的接口**: 组件不再使用裸的编号导入导出, 而是使用 WIT 文件里定义的具名接口.
3. **组合**: 多个组件可以互相连接, 一个组件的导出可以满足另一个组件的导入.

**说得直白些:**

没有组件模型时, 宿主和客体之间只能传数字. 有了组件模型, 你可以跨越这条边界传字符串, 结构体, option 以及其他复杂类型, 而运行时自动处理所有的内存布局和编码.

在本项目里, 我们在宿主中用 `config.wasm_component_model(true)` 启用组件模型, 并用 `Component::deserialize` (而不是 `Module`) 来加载客体产物. 一切都走组件模型.

---

## 什么是 no_std

在 Rust 里, `#![no_std]` 的意思是 "不要链接标准库". Rust 标准库 (`std`) 提供 `println!`, 文件 I/O, 网络, 线程以及其他操作系统相关的功能, 它需要操作系统的支持才能工作.

**客体为什么用 no_std:**

我们的客体组件目标是 `wasm32-unknown-unknown` - 一个没有操作系统的 WebAssembly 目标. 那里没有文件系统, 没有 stdout, 没有网络. 标准库里依赖操作系统的功能全都用不了. 用 `#![no_std]`, 我们是在告诉 Rust 编译器: "这段代码在没有操作系统的环境下运行, 不要试图链接操作系统相关的功能."

**客体仍然能用的东西:**

即使没有 `std`, 客体仍然可以使用 `core` (Rust 的基础类型, trait 和数学运算) 和 `alloc` (`String`, `Vec`, `format!` 这类堆分配类型). `alloc` crate 需要一个全局内存分配器. 由于没有操作系统来提供, 客体就用 `dlmalloc` - 一个简单, 可移植, 能在独立环境里工作的分配器.

**这和 WASI 客体有什么不同:**

有些 WebAssembly 项目目标是 `wasm32-wasip1` (WASI Preview 1) 或 `wasm32-wasip2` (WASI Preview 2). 这些目标通过 WASI 导入提供类操作系统的能力, 所以客体可以用 `println!` 和其他 `std` 功能. 本项目刻意避开 WASI, 以匹配嵌入式架构 - 那里根本不存在操作系统. 客体改为通过 WIT 导出返回字符串, 由宿主决定拿它们做什么 (打印到终端, 通过 UART 发出去等等).

---

## 什么是 AOT 预编译

AOT 是 Ahead-Of-Time (提前) 的缩写. 它指的是在需要之前就把代码编译好, 而不是等到运行时再编译.

**本项目里的编译流水线:**

1. **Rust 源代码** (`guest1/src/lib.rs`) 由 `rustc` 编译成一个**核心 WebAssembly 模块** (`guest1.wasm`). 目标三元组是 `wasm32-unknown-unknown`.
2. 核心模块被 `ComponentEncoder` 包装成一个 **WebAssembly 组件** (补上组件模型的类型元数据和规范 ABI 层).
3. 组件由 `engine.precompile_component()` 预编译成 **Pulley 字节码** (`guest1.cwasm`). 这一步就是 AOT.
4. 预编译得到的字节码通过 `include_bytes!` 嵌进宿主二进制文件.

**AOT 为什么重要:**

如果没有 AOT, 宿主每次启动都得把 WebAssembly 组件编译成 Pulley 字节码. 这个编译过程既花时间, 又要求二进制文件里带着完整的 Wasmtime 编译器. 有了 AOT, 编译只在构建时 (在你的笔记本上) 发生一次, 结果是一块 Pulley 字节码, 宿主只要反序列化就行. 运行时不再需要编译器.

这对嵌入式系统至关重要: RP2350 微控制器没有足够的内存和算力去跑 Wasmtime 编译器, 它只能反序列化预编译好的 Pulley 字节码. 把 AOT 编译放在构建阶段完成, 嵌入式宿主才能又小又快.

**在本项目中:**

`build.rs` 脚本负责执行 AOT 编译. 宿主用 `unsafe { Component::deserialize(engine, bytes) }` 加载预编译字节码. 这里需要 `unsafe`, 是因为 Wasmtime 相信这些字节是合法的预编译产物 (而不是任意数据). 这份信任由构建脚本背书, 因为那些字节正是它用 Wasmtime 自己生成的.

---

## 项目结构

```
0x01_hello-world/
    Cargo.toml              # Host package manifest (wasmtime dependency + build-deps)
    build.rs                # AOT pipeline: compile guests, encode, precompile to Pulley
    host.rs                 # Host program: deserializes and runs guest components
    tests/
        integration.rs      # Integration tests for both guest components
    guest1/
        Cargo.toml          # Guest1 package manifest (wit-bindgen + dlmalloc)
        wit/
            world.wit       # WIT contract: export run: func() -> string
        src/
            lib.rs          # Guest1 implementation: #![no_std], returns string
    guest2/
        Cargo.toml          # Guest2 package manifest (wit-bindgen + dlmalloc)
        wit/
            world.wit       # WIT contract: export run(name), export describe
        src/
            lib.rs          # Guest2 implementation: #![no_std], greeting + describe
```

这里有三个彼此独立的 Rust 包:

1. **宿主** (`Cargo.toml` + `host.rs` + `build.rs`): 一个普通的 Rust 二进制程序, 依赖 `wasmtime`. 构建脚本负责编译客体并预编译它们, 二进制程序负责反序列化并运行它们.
2. **guest1** (`guest1/Cargo.toml` + `guest1/src/lib.rs`): 一个 `#![no_std]` 的 Rust 库, 编译到 `wasm32-unknown-unknown`. 使用 `wit-bindgen` 和 `dlmalloc`.
3. **guest2** (`guest2/Cargo.toml` + `guest2/src/lib.rs`): 思路一样, 只是 WIT 契约和实现不同.

---

## WIT 文件逐行讲解

### guest1/wit/world.wit

```wit
package component:guest1;
```

这一行声明了 WIT 包名. 格式是 `namespace:name`. 这里 `component` 是命名空间, `guest1` 是名字. 这个标识符供工具链把各个部分对应起来, 不影响运行时行为.

```wit
world guest1-world {
```

一个 `world` 定义了一个组件完整的导入和导出集合. `guest1-world` 这个名字就是 `wit_bindgen::generate!` 宏用来在 WIT 文件里找到正确 world 定义的依据.

```wit
    export run: func() -> string;
```

这一行的意思是: "任何以这个 world 为目标的组件都必须导出一个叫 `run` 的函数, 它不接受参数并返回一个字符串." 宿主会按名字去找这个函数, 并核对签名.

```wit
}
```

world 定义到此结束.

### guest2/wit/world.wit

```wit
package component:guest2;

world guest2-world {
    export run: func(name: option<string>) -> string;
    export describe: func() -> string;
}
```

它和 guest1 有两处不同:

1. `run` 带了一个参数: `name: option<string>`. 在 WIT 里, `option<string>` 表示这个值要么是字符串, 要么什么都没有 (null/None). 组件模型负责把它编码后跨过宿主-客体边界. 这个函数同样返回 `string`.
2. 多了一个导出: `describe: func() -> string`. 这个函数不接受任何东西, 返回一个字符串.

正是这两个 WIT 文件的差异, 让 guest1 和 guest2 的行为不同. WIT 文件是契约, Rust 代码实现这个契约.

---

## Guest1 逐行讲解

文件: `guest1/src/lib.rs`

```rust
#![no_std]
```

这个属性告诉 Rust 编译器: 不要链接标准库. 客体运行在 `wasm32-unknown-unknown` 上, 那里没有操作系统, 所以 `println!`, 文件 I/O, 线程这些 `std` 功能都用不了.

```rust
extern crate alloc;
```

这行引入了 `alloc` crate, 它提供堆分配类型 (`String`, `Vec`, `Box` 等等), 而且不依赖 `std`. `alloc` crate 可以搭配任何全局分配器使用 - 它不依赖操作系统.

```rust
use alloc::string::String;
```

从 `alloc` 导入 `String` 类型. 在带 `std` 的 Rust 里, `String` 来自标准库的 prelude. 而在 `no_std` 下, 你得显式地从 `alloc` 导入它.

```rust
#[global_allocator]
static ALLOC: dlmalloc::GlobalDlmalloc = dlmalloc::GlobalDlmalloc;
```

这行把 `dlmalloc` 设为全局内存分配器. `#[global_allocator]` 属性告诉 Rust: "所有堆分配都用这个分配器." `dlmalloc` 是一个简单, 可移植的分配器, 能在 WebAssembly 这样的独立环境中工作. 没有它, 客体就没法分配 `String` 或任何其他堆类型. 规范 ABI 的 `cabi_realloc` 函数也依赖它 - 组件模型正是用这个函数来分配内存, 以便在宿主-客体边界上传数据 (比如字符串).

```rust
wit_bindgen::generate!({
    world: "guest1-world",
    path: "wit",
});
```

这个宏读取 `guest1/wit/world.wit`, 找到 `guest1-world` 这个 world, 然后生成与 WIT 契约匹配的 Rust 代码 (trait, 类型和胶水代码). 它会生成带 `run()` 方法的 `Guest` trait, 以及下面要用到的 `export!` 宏. 这取代了过去 `cargo-component` + `bindings.rs` 的做法 - 一切都在编译期就地生成.

```rust
struct Component;
```

这是一个零大小结构体. 它存在的唯一目的, 就是给你一个类型来实现 `Guest` trait. 它不存放任何数据.

```rust
export!(Component);
```

这个宏调用把 `Component` 注册为实现体, 供组件模型运行时在宿主调用导出函数时使用. 没有这一行, 组件就没有实现来支撑 WIT 导出, 实例化会失败.

```rust
impl Guest for Component {
    fn run() -> String {
        String::from("guest1 run() called")
    }
}
```

这里实现了 `Guest` trait. 当宿主调用 `run` 导出时, 执行的就是这个函数. 它返回一个 `String`, 由规范 ABI 编码后传回宿主. 不用 `println!`, 不用 WASI - 只是一个返回值.

---

## Guest2 逐行讲解

文件: `guest2/src/lib.rs`

整体结构和 guest1 一样, 差别在下面这几处:

```rust
use alloc::format;
use alloc::string::String;
```

Guest2 还从 `alloc` 导入了 `format!`, 因为它的 `run()` 方法要用字符串格式化.

```rust
const DEFAULT_NAME: &str = "world";
```

一个常量字符串, 当宿主给 `name` 参数传 `None` 时作为兜底值.

```rust
impl Guest for Component {
    fn run(name: Option<String>) -> String {
        let name = name.as_deref().unwrap_or(DEFAULT_NAME);
        format!("guest2 run() called: hello, {name}!")
    }
```

`run` 方法的参数是 `name: Option<String>`, 因为 WIT 文件里声明的是 `run: func(name: option<string>) -> string`. 生成的 `Guest` trait 要求签名完全一致. `as_deref()` 把 `Option<String>` 转成 `Option<&str>`, `unwrap_or(DEFAULT_NAME)` 在值为 `None` 时提供 `"world"`. 这个函数返回格式化好的问候字符串.

```rust
    fn describe() -> String {
        String::from("guest2 has an extra `describe` export")
    }
}
```

第二个导出. 宿主按名字查找这个函数, 找到就调用它并打印返回的字符串. Guest1 没有它, 所以宿主不会对 guest1 调用它.

---

## 构建脚本逐行讲解

文件: `build.rs`

构建脚本在 `cargo build` 阶段运行, 早于编译 `host.rs`. 它编译两个客体 crate, 把它们编码成 WebAssembly 组件, AOT 预编译成 Pulley 字节码, 并把结果写到 `OUT_DIR`, 供宿主嵌入.

### 常量

```rust
const GUEST1_CORE_WASM_PATH: &str = "guest1/target/wasm32-unknown-unknown/release/guest1.wasm";
const GUEST2_CORE_WASM_PATH: &str = "guest2/target/wasm32-unknown-unknown/release/guest2.wasm";
```

这两个路径指向编译各客体 crate 后得到的核心 WebAssembly 模块.

```rust
const GUEST1_SERIALIZED_NAME: &str = "guest1.cwasm";
const GUEST2_SERIALIZED_NAME: &str = "guest2.cwasm";
```

AOT 预编译得到的 Pulley 字节码产物写入 `OUT_DIR` 时使用的文件名.

```rust
const GUEST1_COMPONENT_NAME: &str = "guest1.component.wasm";
const GUEST2_COMPONENT_NAME: &str = "guest2.component.wasm";
```

编码后的组件字节 (AOT 预编译之前) 使用的文件名, 同样写入 `OUT_DIR`. 集成测试会用它们 - 测试里用 `Component::new()` 加载组件, 而不是 `Component::deserialize()`.

### 编译流水线

```rust
fn compile_guest_wasm(guest_dir: &str) {
    let status = Command::new("cargo")
        .args(["build", "--release", "--target", "wasm32-unknown-unknown"])
        .current_dir(guest_dir)
        .env_remove("CARGO_ENCODED_RUSTFLAGS")
        .status()
        .expect("failed to build guest wasm crate");
    assert!(status.success(), "guest wasm build failed: {}", guest_dir);
}
```

在客体目录里运行 `cargo build`, 目标是 `wasm32-unknown-unknown`. `--release` 开关生成优化后的产物. `.env_remove("CARGO_ENCODED_RUSTFLAGS")` 防止宿主的 Rust 编译参数泄漏到客体构建里 (它们针对的是不同的架构).

```rust
fn pulley_engine() -> Engine {
    let mut config = Config::new();
    config.wasm_component_model(true);
    config.target("pulley64").expect("set pulley64 target");
    Engine::new(&config).expect("create pulley engine")
}
```

创建一个 Wasmtime Engine, 配置与 `host.rs` 里运行时的 Engine 完全相同. 这一点至关重要: 只有当运行时的 Engine 与构建时的 Engine 配置一致时, 预编译字节码才是有效的. 任何不一致 (目标不同, 特性开关不同) 都会让 `Component::deserialize` 失败.

```rust
fn encode_component(wasm_bytes: &[u8]) -> Vec<u8> {
    ComponentEncoder::default()
        .module(wasm_bytes)
        .expect("set core wasm module")
        .validate(true)
        .encode()
        .expect("encode component")
}
```

接收原始的核心 WebAssembly 字节, 把它们包装成一个组件模型组件. `ComponentEncoder` 读取核心模块里嵌入的 `wit-bindgen` 元数据, 补上规范 ABI 层, 生成一个合法的组件二进制. `.validate(true)` 会做校验, 尽早发现编码错误.

```rust
fn precompile_component(engine: &Engine, component_bytes: &[u8]) -> Vec<u8> {
    engine
        .precompile_component(component_bytes)
        .expect("precompile component for pulley64")
}
```

这就是 AOT 那一步. 接收编码后的组件字节, 把它们编译成 Pulley 字节码. 输出是一块序列化数据, 之后可以用 `Component::deserialize` 反序列化. 正是这一步让运行时启动变得很快 - 不需要任何编译.

```rust
fn compile_guest_to_pulley(...) {
    compile_guest_wasm(guest_dir);
    let core_wasm = read_core_wasm(core_wasm_path);
    let component = encode_component(&core_wasm);
    write_precompiled_component(out_dir, component_name, &component);
    let serialized = precompile_component(engine, &component);
    write_precompiled_component(out_dir, output_name, &serialized);
}
```

一个客体的完整流水线: 编译, 读取, 编码, 写出组件 (给测试用), 预编译, 写出序列化结果 (给宿主用). 每个客体都会调用一次这个函数.

### 重跑触发条件

```rust
fn print_rerun_triggers() {
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=guest1/wit/world.wit");
    println!("cargo:rerun-if-changed=guest1/src/lib.rs");
    // ...
}
```

告诉 Cargo 只有这些特定文件发生变化时才重新运行构建脚本. 没有这几行, 每次 `cargo build` 都会跑一遍构建脚本, 即使什么都没改也要重新编译两个客体.

---

## 宿主逐行讲解

文件: `host.rs`

这里是整个项目的核心. 下面逐行解释.

### 导入

```rust
use wasmtime::component::{Component, Linker};
```

- `Component`: 表示一个已编译或已反序列化的 WebAssembly 组件.
- `Linker`: 把组件的导入 (如果有) 与宿主提供的实现连接起来. 我们的 `#![no_std]` 客体没有任何导入, 所以 Linker 是空的.

```rust
use wasmtime::{Config, Engine, Result, Store};
```

- `Config`: Engine 的配置构建器. 你可以设置目标架构, 特性开关这类选项.
- `Engine`: 编译代码的缓存与配置的持有者. 反序列化要求 Engine 的配置与预编译时使用的一致.
- `Result`: Wasmtime 的结果类型 (`Result<T, wasmtime::Error>`).
- `Store`: 运行时状态容器. 存放你的宿主状态, WebAssembly 内存和实例数据.

### 常量

```rust
const GUEST1_PRECOMPILED: &[u8] = include_bytes!(concat!(env!("OUT_DIR"), "/guest1.cwasm"));
const GUEST2_PRECOMPILED: &[u8] = include_bytes!(concat!(env!("OUT_DIR"), "/guest2.cwasm"));
```

这两行在编译期把预编译的 Pulley 字节码直接嵌进宿主二进制文件. `include_bytes!` 读取 `build.rs` 写入 `OUT_DIR` 的文件, 把内容作为一个 `&[u8]` 字节切片包含进来. 运行时没有任何文件 I/O - 字节已经在内存里了.

```rust
const DEFAULT_GUEST_NAME: &str = "Pulley";
```

没有提供命令行参数时, 传给 guest2 的 `run` 的默认值.

### 函数

```rust
fn build_engine() -> Result<Engine> {
    let mut config = Config::new();
    config.wasm_component_model(true);
    config.target("pulley64")?;
    Engine::new(&config)
}
```

在运行时创建一个 Wasmtime Engine. 这里的配置**必须和** `build.rs` 预编译时使用的一致. 如果你只在这里改了目标, 却没改 `build.rs` (或者反过来), `Component::deserialize` 就会失败.

```rust
fn load_component(engine: &Engine, bytes: &[u8]) -> Result<Component> {
    unsafe { Component::deserialize(engine, bytes) }
}
```

把预编译的 Pulley 字节码反序列化成一个 `Component`. 这里需要 `unsafe`, 是因为 Wasmtime 相信这些字节是合法的预编译产物. 如果你传进去的是任意字节, Wasmtime 可能会表现出未定义行为. 这个不变量由 `build.rs` 保证 - 那些字节正是它用 Wasmtime 自己的 `precompile_component` 生成的.

这也是与旧架构的关键区别: 我们不再用 `Component::from_file()` (它读取 `.wasm` 文件并在运行时编译), 而是用 `Component::deserialize()` (加载已经编译好的字节码). 运行时不再发生任何编译.

```rust
fn run_guest1(engine: &Engine, component: &Component) -> Result<String> {
    let linker = Linker::<()>::new(engine);
    let mut store = Store::new(engine, ());
    let instance = linker.instantiate(&mut store, component)?;
    let run = instance.get_typed_func::<(), (String,)>(&mut store, "run")?;
    let (result,) = run.call(&mut store, ())?;
    Ok(result)
}
```

创建一个空的 Linker (我们的客体没有导入), 创建一个宿主状态为 `()` 的 Store (不需要 WASI 上下文), 实例化组件, 取出 `run` 导出, 调用它, 返回结果字符串.

注意类型参数 `(String,)` - 这是一个单元素元组. 组件模型用元组来返回多个值. `run` 函数返回一个 `string`, 所以 Rust 这边收到的是 `(String,)`.

```rust
fn run_guest2(engine: &Engine, component: &Component, name: &str) -> Result<(String, String)> {
    let linker = Linker::<()>::new(engine);
    let mut store = Store::new(engine, ());
    let instance = linker.instantiate(&mut store, component)?;
    let run = instance.get_typed_func::<(Option<String>,), (String,)>(&mut store, "run")?;
    let (run_result,) = run.call(&mut store, (Some(name.to_string()),))?;
    let describe = instance.get_typed_func::<(), (String,)>(&mut store, "describe")?;
    let (desc_result,) = describe.call(&mut store, ())?;
    Ok((run_result, desc_result))
}
```

模式相同, 只是针对有两个导出的 guest2. `run` 接收 `(Option<String>,)` 作为输入, 返回 `(String,)`. `describe` 不接受输入, 返回 `(String,)`.

```rust
fn parse_name() -> String {
    std::env::args().nth(1).unwrap_or_else(|| DEFAULT_GUEST_NAME.to_string())
}
```

读取第一个命令行参数. 如果没提供, 就用默认值 `"Pulley"`.

```rust
fn run() -> Result<()> {
    let name = parse_name();
    println!("Building Pulley component engine...");
    let engine = build_engine()?;
    // ... 反序列化客体, 调用导出, 打印结果
    Ok(())
}
```

主逻辑函数, 由 `main()` 调用.

```rust
fn main() -> Result<()> {
    run()
}
```

程序入口. 返回 `wasmtime::Result<()>`, 这样错误会被自动打印出来.

---

## 深入 Engine

`Engine` 是 Wasmtime 里最基础的对象. 它只创建一次, 之后加载每个组件都复用它.

### Engine 做什么

1. **持有配置**: Engine 保存 `Config` 的设置 (目标架构, 特性开关), 并在每次操作时强制执行它们.

2. **校验预编译代码**: 当你调用 `Component::deserialize` 时, Engine 会检查这些预编译字节是否由兼容的配置产生.

3. **缓存已编译代码**: 如果你用同一个 Engine 两次加载同一个组件, 编译结果可以被复用.

### 那几行配置

**`config.wasm_component_model(true)`** - 启用组件模型支持. 没有它, Wasmtime 只能加载核心 WebAssembly 模块 (那种旧的, 只有数字的类型). 启用之后, Wasmtime 才看得懂组件, WIT 类型和规范 ABI.

**`config.target("pulley64")?`** - 把目标设为 `pulley64`. 这告诉 Engine: 所有组件都是 (或者都应该是) 按 Pulley64 字节码格式编译的. 这必须和 `build.rs` 里用的一致.

**`Engine::new(&config)`** - 根据配置创建 Engine.

### 为什么构建时和运行时的 Engine 必须一致

`Component::deserialize` 不会重新编译任何东西. 它接收的是由 `engine.precompile_component()` 预编译出来的字节. 如果运行时的 Engine 配置与构建时的 Engine 不同, 这些预编译字节就是无效的. Wasmtime 会检查这一点并返回错误.

---

## 深入 Linker

```rust
let linker = Linker::<()>::new(engine);
```

`Linker` 负责把组件的导入连接到宿主侧的实现.

### 什么是导入

WebAssembly 组件被编译出来时, 可能带有导入声明. 这些是组件需要但自己并未实现的函数, 它指望宿主来提供.

### 我们的客体没有导入

因为我们的客体使用 `#![no_std]` 并以 `wasm32-unknown-unknown` 为目标, 它们没有任何 WASI 导入. 它们不调用 `println!`, 不访问文件, 也不需要任何宿主提供的函数. 它们只导出函数, 通过规范 ABI 返回值.

也就是说 Linker 是空的 - `Linker::<()>::new(engine)` 创建了一个什么都没注册的 Linker, 而这已经足够了. 类型参数 `()` 表示 Store 不持有宿主状态 (就是单元类型).

### 什么情况下需要非空的 Linker

如果你在客体的 `world.wit` 里加了 WIT 导入 (例如 `import log: func(msg: string);`), 那你就得在实例化之前把这个函数注册到 Linker 里. Linker 负责把导入名映射到实现它们的 Rust 闭包或函数.

---

## 深入 Store

```rust
let mut store = Store::new(engine, ());
```

`Store` 是运行时状态容器.

### Store 里装了什么

1. **你的宿主状态** (`()`): 也就是那个类型参数. 在本项目里它是单元类型, 因为我们没有 WASI 上下文要存.
2. **WebAssembly 线性内存**: 客体分配内存时 (通过 `dlmalloc`), 这些内存就活在 Store 里.
3. **全局变量**: WebAssembly 的全局值存在这里.
4. **函数句柄**: 从实例取出的带类型函数引用存放在 Store 里.
5. **实例数据**: 实例化之后, 正在运行的实例的状态就活在 Store 里.

### 为什么用 Store<()> 而不是自定义结构体

在更早那套基于 WASI 的架构里, Store 里放的是一个 `HostState` 结构体, 内含 `WasiCtx` 和 `ResourceTable`. 既然我们的客体不再使用 WASI, 宿主就没有什么需要提供的了. 单元类型 `()` 是最简单的状态 - 它不存放任何数据.

### 每个组件一个全新的 Store

每个客体组件都有自己全新的 Store. 这意味着每个组件拥有彼此隔离的内存空间. 一个客体无法干扰另一个客体的内存或状态.

---

## 深入 Component

```rust
unsafe { Component::deserialize(engine, bytes) }
```

`Component` 表示一个已编译的 WebAssembly 组件. 它包含编译好的 Pulley 字节码和类型元数据 (它导入和导出什么), 随时可以实例化.

### Component::deserialize, Component::new 与 Component::from_file 的区别

创建 Component 有几种方式:

- **`Component::from_file(engine, path)`** - 从磁盘读取 `.wasm` 文件并在运行时编译. 集成测试里用的是它 (测试用 `Component::new` 从内嵌字节编译组件). 宿主二进制程序不用它.
- **`Component::new(engine, bytes)`** - 接收原始的组件字节并在运行时编译. 集成测试里用它.
- **`Component::deserialize(engine, bytes)`** - 接收预编译的 Pulley 字节码, 不做任何编译直接加载. 宿主二进制程序用它. 这是最快的方式, 也是唯一适合嵌入式目标的方式.

### 为什么 deserialize 是 unsafe 的

`Component::deserialize` 相信这些字节是合法的 Wasmtime 预编译产物. 如果你传进去的是随机字节或恶意字节, Wasmtime 可能会执行非法代码, 导致未定义行为. `unsafe` 标注把这份信任显式化. 在本项目里, 这份信任是有依据的: `build.rs` 用 `engine.precompile_component()` 生成了这些字节, 而且它们通过 `include_bytes!` 被嵌进了二进制文件.

---

## 深入 Instance

```rust
let instance = linker.instantiate(&mut store, &component)?;
```

`Instance` 是一个正在运行的组件. 实例化把编译好的 Component 与一个 Store 和一个 Linker 连接起来, 并解析所有导入.

### 实例化做了哪些事

1. **解析导入**: 如果组件有导入, 由 Linker 提供. 我们的客体没有导入, 所以这一步什么都不做.
2. **分配内存**: 组件的线性内存在 Store 内部完成分配.
3. **运行启动函数**: 如果组件有初始化代码, 现在运行.
4. **返回 Instance**: 你可以用这个对象来查找并调用导出函数.

### 调用导出

实例化之后, 你通过 Instance 调用导出:

```rust
let run = instance.get_typed_func::<(), (String,)>(&mut store, "run")?;
let (result,) = run.call(&mut store, ())?;
```

**`get_typed_func::<(), (String,)>(&mut store, "run")`** - 查找一个名为 `"run"` 的导出函数, 并核对它不接受参数 (`()`), 返回一个字符串 (`(String,)`). 类型参数就在这一步被检查. 如果函数的真实签名对不上, 这个调用会返回错误.

**`run.call(&mut store, ())`** - 执行这个函数. 需要 `&mut store`, 因为函数可能会改动内存或触发陷阱. 结果是 `(String,)` - 一个单元素元组, 装着返回的字符串.

对 guest2 来说, 签名不一样:

```rust
let run = instance.get_typed_func::<(Option<String>,), (String,)>(&mut store, "run")?;
let (result,) = run.call(&mut store, (Some(name.to_string()),))?;
```

`(Option<String>,)` 是输入用的单元素元组. 组件模型的规范 ABI 负责把 Rust 的 `Option<String>` 编码成客体期待的 WebAssembly 线性内存格式. 返回类型 `(String,)` 会被自动解码. 你写的是普通的 Rust 类型, 转换由运行时处理.

---

## 它们如何串在一起

下面是从上到下的依赖链条:

**构建时 (build.rs):**

```
Guest Rust source (lib.rs)
  |
  v
cargo build --target wasm32-unknown-unknown -> core .wasm module
  |
  v
ComponentEncoder -> component .wasm (with WIT metadata)
  |
  v
Engine (pulley64) -> engine.precompile_component() -> .cwasm (Pulley bytecode)
  |
  v
include_bytes! embeds .cwasm into host binary
```

**运行时 (host.rs):**

```
Config
  |
  v
Engine (holds configuration, validates precompiled code)
  |
  +---> Component::deserialize(engine, bytes) -> Component
  |
  +---> Linker<()>::new(engine) -> empty Linker (no imports needed)
  |
  +---> Store::new(engine, ()) -> Store with unit state
          |
          +---> linker.instantiate(&mut store, &component) -> Instance
                  |
                  +---> instance.get_typed_func("run") -> TypedFunc
                          |
                          +---> run.call(&mut store, args) -> String
                                  (Pulley interprets guest bytecode)
```

Engine 是一切的本源. 没有它, 你连 Store, Linker 或 Component 都创建不了. Engine 的配置在构建时与运行时必须一致.

---

## 集成测试逐行讲解

文件: `tests/integration.rs`

集成测试用来验证客体组件工作正常, 而不必运行整个宿主二进制程序. 它们使用与 `host.rs` 相同的 Wasmtime API, 但通过 `Component::new()` (运行时编译) 加载组件, 而不是 `Component::deserialize()` (AOT 预编译).

### 测试基础设施

测试里定义了这些辅助函数:

- **`create_engine()`** - 创建一个默认配置的 Engine (不带 Pulley 目标, 因为测试是在运行时编译的).
- **`compile_component(engine, wasm)`** - 通过 `Component::new` 把原始组件字节编译成 Component.
- **`call_run_no_args(engine, component)`** - 实例化并调用 `run()`, 返回 String.
- **`call_run_with_name(engine, component, name)`** - 实例化并调用 `run(Option<String>)`.
- **`call_describe(engine, component)`** - 实例化并调用 `describe()`.

### 组件字节

```rust
const GUEST1_WASM: &[u8] = include_bytes!(concat!(env!("OUT_DIR"), "/guest1.component.wasm"));
const GUEST2_WASM: &[u8] = include_bytes!(concat!(env!("OUT_DIR"), "/guest2.component.wasm"));
```

测试用的是编码后的组件字节 (不是 AOT 预编译出来的 `.cwasm` 文件). 这些字节与 `build.rs` 在预编译那一步之前写出的一致. `Component::new()` 在测试时用默认的 Engine 配置 (原生代码, 不是 Pulley) 编译它们, 在你的笔记本上测试这样完全够用.

### 每个测试验证什么

| 测试                                           | 检查内容                                                             |
| ---------------------------------------------- | -------------------------------------------------------------------- |
| `test_guest1_component_loads`                  | guest1 组件字节是否合法                                              |
| `test_guest2_component_loads`                  | guest2 组件字节是否合法                                              |
| `test_guest1_exports_run_function`             | guest1 是否导出签名为 `() -> (String,)` 的 `run`                     |
| `test_guest2_exports_run_function`             | guest2 是否导出签名为 `(Option<String>,) -> (String,)` 的 `run`      |
| `test_guest2_exports_describe_function`        | guest2 是否导出签名为 `() -> (String,)` 的 `describe`                |
| `test_guest1_does_not_export_describe`         | guest1 没有 `describe` 导出                                          |
| `test_guest1_run_returns_expected_string`      | `run()` 返回的字符串包含 "guest1"                                    |
| `test_guest2_run_returns_expected_string`      | `run(Some("Pulley"))` 返回的字符串包含 "guest2"                      |
| `test_guest2_describe_returns_expected_string` | `describe()` 返回的字符串与预期完全一致                              |
| `test_guest1_has_no_wasi_imports`              | guest1 没有与 WASI 相关的导入                                        |
| `test_guest2_has_no_wasi_imports`              | guest2 没有与 WASI 相关的导入                                        |
| `test_guest2_run_default_name`                 | `run(None)` 返回的字符串包含 "world"                                 |
| `test_guest2_run_custom_name`                  | `run(Some("Pulley"))` 返回的字符串包含 "Pulley"                      |
| `test_guest1_run_exact_message`                | `run()` 返回的正好是 "guest1 run() called"                           |
| `test_guest2_run_exact_greeting`               | `run(Some("Pulley"))` 返回的正好是预期的问候语                       |

### 测试为什么用 Component::new 而不是 Component::deserialize

AOT 预编译出来的 `.cwasm` 文件目标是 `pulley64`. 测试代码在你的笔记本上以原生方式运行 (x86-64 或 AArch64). 要在测试里原生执行客体代码, 你需要默认配置的 Engine (它编译成原生机器码), 而不是以 Pulley 为目标的 Engine. 编码后的组件字节 (`.component.wasm`) 与任何 Engine 配置都能配合, 因为 `Component::new()` 是在运行时编译它们的.

---

## 如何构建和运行

### 前置条件

安装 Rust 并加上 `wasm32-unknown-unknown` 目标:

```
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
rustup target add wasm32-unknown-unknown
```

### 构建全部

```
cargo build
```

这一条命令就完成了:

1. 运行 `build.rs`, 它编译两个客体 crate, 把它们编码成组件, 并 AOT 预编译成 Pulley 字节码.
2. 编译 `host.rs`, 其中通过 `include_bytes!` 嵌入了预编译的客体产物.

不需要单独构建客体, 不需要 `cargo-component`, 只要 `cargo build`.

### 运行宿主 (使用默认名字)

```
cargo run --bin hello
```

输出:

```
Building Pulley component engine...
Deserializing guest1 component...
guest1 run() called
Deserializing guest2 component...
guest2 run() called: hello, Pulley!
describe: guest2 has an extra `describe` export
Done.
```

### 用自定义名字运行宿主

```
cargo run --bin hello -- "Kevin"
```

输出:

```
Building Pulley component engine...
Deserializing guest1 component...
guest1 run() called
Deserializing guest2 component...
guest2 run() called: hello, Kevin!
describe: guest2 has an extra `describe` export
Done.
```

`--` 把 `cargo` 自己的参数和你程序的参数分开. `"Kevin"` 会成为 host.rs 里的 `args[1]`.

### 运行测试

```
cargo test
```

这会编译测试二进制程序, 并运行全部 15 个集成测试.

---

## 这对嵌入式系统为什么重要

### 问题所在

嵌入式微控制器 (RP2350, ESP32, STM32 等等) 跑的是裸机 - 没有操作系统, 没有进程隔离, 没有内存保护. 每一段固件都能完全访问所有硬件. 如果你加载了不受信任的代码, 它可以覆写内存, 弄坏外设, 甚至把设备变砖.

### WebAssembly 的解法

WebAssembly 运行在沙箱里. 一个客体组件:

- 除非宿主通过 WIT 接口显式暴露, 否则碰不到硬件寄存器.
- 读写不了自己线性内存之外的内存.
- 除非宿主通过 Linker 把它链接进来, 否则调用不了任何函数.
- 可以通过替换 `.wasm` 文件独立于宿主固件进行更新.

### Pulley 如何让它成为可能

RP2350 (Cortex-M33, ARMv8-M) 这类微控制器所用的处理器架构, 是 Cranelift 的原生代码生成器不支持的. Pulley 的解决办法是提供一个可移植的解释器, 它能在任何处理器上运行. 宿主固件里包含 Pulley 解释器, 而客体组件在构建时就被预编译成 Pulley 字节码.

### 嵌入式版本长什么样

[embedded-wasm-uart-rp2350](https://github.com/mytechnotalent/embedded-wasm-uart-rp2350) 项目用的架构与本教程完全一样:

| 本教程 (笔记本)                               | 嵌入式版本 (RP2350)                                         |
| --------------------------------------------- | ----------------------------------------------------------- |
| `host.rs` 运行在你的 Mac/Linux/Windows 上     | `src/main.rs` 在 RP2350 上以裸机方式运行                    |
| Config 的目标是 `pulley64`                    | Config 的目标是 `pulley32`                                  |
| `build.rs` 预编译成 Pulley 字节码             | `build.rs` 预编译成 Pulley 字节码                           |
| `Component::deserialize(include_bytes!(...))` | `Component::deserialize(include_bytes!(...))`               |
| 客体使用 `#![no_std]` + `dlmalloc`            | 客体使用 `#![no_std]` + `dlmalloc`                          |
| 客体通过 WIT 导出返回字符串                   | 客体调用宿主提供的 WIT 导入 (UART 的 `write_byte()`)        |
| `Linker<()>` - 空的, 没有导入                 | `Linker<Host>` - 注册 UART 硬件函数                         |
| `Store<()>` - 没有宿主状态                    | `Store<Host>` - 持有 UART 外设状态                          |

心智模型是完全一致的. 宿主创建 Engine, 反序列化预编译的 Component, 构建 Linker, 创建 Store, 实例化, 然后调用导出. 唯一的差别是目标 (`pulley32` 与 `pulley64`) 和导入 (UART 硬件与本教程里的什么都没有).

### 关键洞察

这个教程项目教的是架构. 一旦你在笔记本上弄懂了 Engine, Store, Linker, Component 和 Instance, 你也就确切知道了它们在嵌入式微控制器上是如何运作的. 概念完全相同, 唯一变化的是宿主通过 WIT 接口向客体提供什么硬件.

---

## 术语表

| 术语                         | 定义                                                                                                                              |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **WebAssembly (Wasm)**       | 一种可移植的二进制指令格式, 运行在沙箱化的虚拟机里.                                                                               |
| **Wasmtime**                 | 由 Bytecode Alliance 用 Rust 编写的生产级 WebAssembly 运行时.                                                                     |
| **Pulley**                   | Wasmtime 内部的可移植解释器, 能在任何 CPU 上执行 Pulley 字节码, 包括嵌入式微控制器.                                               |
| **WIT**                      | WebAssembly Interface Types. 一门用于定义宿主与客体之间函数签名的语言.                                                            |
| **Component Model**          | 架在 Wasm 之上的一套标准, 增加了丰富类型 (字符串, 记录, option) 和基于 WIT 的接口.                                                |
| **`#![no_std]`**             | 禁用标准库的 Rust 属性. 对没有操作系统支持的 `wasm32-unknown-unknown` 目标是必需的.                                               |
| **`dlmalloc`**               | 一个可移植的内存分配器, 在 `no_std` 客体中作为全局分配器使用. `String`, `Vec` 和规范 ABI 都需要它.                                |
| **`wit-bindgen`**            | 一个 Rust crate, 它的 `generate!` 宏在编译期从 WIT 定义生成 Rust trait 和类型.                                                    |
| **AOT**                      | Ahead-Of-Time 编译. 在构建时把 WebAssembly 编译成 Pulley 字节码, 这样运行时就不需要编译器了.                                      |
| **`ComponentEncoder`**       | `wit-component` 里的一个类型, 把核心 WebAssembly 模块包装成组件模型组件.                                                          |
| **Engine**                   | 持有配置并校验预编译代码的 Wasmtime 对象. 只创建一次, 所有组件复用.                                                               |
| **Config**                   | Engine 各项设置的构建器: 目标架构, 特性开关, 内存限制.                                                                            |
| **Store**                    | 运行时状态容器. 持有宿主状态, WebAssembly 内存, 全局变量和实例数据. 每个组件实例一个.                                             |
| **Linker**                   | 宿主提供函数的注册表. 把导入名映射到实现. 客体没有导入时它就是空的.                                                               |
| **Component**                | 一个已编译或已反序列化的 WebAssembly 组件. 包含代码和类型元数据, 但还没有运行.                                                    |
| **Instance**                 | 正在运行的组件. 由 `linker.instantiate()` 创建. 你通过 Instance 调用导出函数.                                                     |
| **`get_typed_func`**         | 按名字查找导出函数, 并在查找时核对其参数和返回类型.                                                                               |
| **`call`**                   | 执行一个带类型的函数. Pulley 解释器负责运行客体代码.                                                                              |
| **`include_bytes!`**         | Rust 宏, 在编译期把文件的字节嵌入二进制文件.                                                                                      |
| **`Component::deserialize`** | 加载预编译的 Pulley 字节码, 不做任何运行时编译. 加载组件最快的方式.                                                               |
| **Canonical ABI**            | 组件模型用来把高层类型 (字符串, option, 记录) 转换成线性内存中字节的编码格式.                                                     |
| **Linear memory**            | Store 内部一段连续的字节数组, 客体用它做堆分配. 与宿主内存隔离.                                                                   |
| **Cranelift**                | Wasmtime 的原生代码编译器. 为 x86-64, AArch64 等生成机器码. 不支持嵌入式 Cortex-M.                                                |
| **`cabi_realloc`**           | 规范要求客体导出的内存分配函数, 规范 ABI 需要它. 由 `dlmalloc` 提供.                                                              |
