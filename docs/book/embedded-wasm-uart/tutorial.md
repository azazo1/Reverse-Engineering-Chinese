# 教程: 嵌入式 Wasm UART 回显 - 完整代码走读

本教程逐行, 逐函数地讲解 **embedded-wasm-uart** 项目里的每一个 Rust 源文件. 读完之后, 你会明白一个 WebAssembly 组件是如何被编译, 部署, 并在 RP2350 微控制器上执行 UART 字符回显的 - 全程都是裸机 Rust, 没有操作系统.

走读按下面的顺序进行:

1. [WIT 接口定义](#1-wit-接口定义-witworldwit) - 客体与宿主之间的契约
2. [平台胶水代码](#2-平台胶水代码-srcplatformrs) - 给 Wasmtime 用的线程局部存储桩
3. [UART 驱动](#3-uart-驱动-srcuartrs) - 串口初始化与 I/O
4. [固件入口点](#4-固件入口点-srcmainrs) - 硬件初始化, Wasm 运行时, panic 处理器
5. [构建脚本](#5-构建脚本-buildrs) - AOT 编译流水线
6. [Wasm 客体应用](#6-wasm-客体应用-wasm-appsrclibrs) - UART 回显组件本身

---

## 1. WIT 接口定义 (`wit/world.wit`)

在任何 Rust 代码之前, 项目先定义了一个 **WIT (WebAssembly Interface Type)** 文件. WIT 是一门与语言无关的接口描述语言, WebAssembly 组件模型用它来对宿主 (固件) 与客体 (Wasm 模块) 之间的函数调用做类型检查.

```wit
package embedded:platform;
```

这行声明了一个名为 `embedded:platform` 的 WIT 包. 包名沿用 namespace:name 的约定. 这个包位于 `embedded` 命名空间下, 提供 `platform` 层面的硬件抽象.

```wit
interface uart {
    read-byte: func() -> u8;
    write-byte: func(byte: u8);
}
```

`uart` 接口定义了两个函数. `read-byte` 会阻塞, 直到 UART 接收线上有字节可读, 然后把它返回. `write-byte` 接收一个字节并通过 UART 发送出去. 这两个都是**导入** - 由客体调用, 宿主提供背后连着真实硬件的实现.

与 blinky 项目的 `gpio` 和 `timing` 接口不同, UART 接口是双向的 - 客体既能读也能写. 这让回显循环这样的交互式应用成为可能.

```wit
world uart-echo {
    import uart;
    export run: func();
}
```

**world** 就是一份完整的契约. `uart-echo` 这个 world 的意思是: "我需要宿主提供 `uart`, 同时我会提供一个 `run` 函数." 宿主实例化组件, 调用 `run`, 然后 Wasm 代码就接管了 - 它从 UART 读字符, 再通过宿主提供的 `uart` 接口把字符回显出去.

---

## 2. 平台胶水代码 (`src/platform.rs`)

Wasmtime 最初是为桌面操作系统打造的, 那些系统通过操作系统提供线程局部存储 (TLS). 在裸机微控制器上没有操作系统, 所以 TLS 得我们自己提供. 这个文件是项目里最简单的 - 两个函数加一个静态变量.

### 导入

```rust
use core::ptr;
use core::sync::atomic::{AtomicPtr, Ordering};
```

`ptr` 提供 `null_mut()` 用来初始化 TLS 值. `AtomicPtr` 是一种原子指针类型, 可以从任何上下文读写而不会产生数据竞争. 在单核的 Cortex-M33 上原子操作并非必需, 但它们能满足 Rust 的类型系统, 让代码从构造上就是正确的.

### TLS 变量

```rust
static TLS_VALUE: AtomicPtr<u8> = AtomicPtr::new(ptr::null_mut());
```

这就是 TLS 的全部实现. Wasmtime 的运行时每个线程存一个指针. 由于 RP2350 只跑一个线程, 一个全局原子指针就够用了. 它初始为 null, 之后在组件执行期间由 Wasmtime 设置.

### `wasmtime_tls_get`

```rust
#[unsafe(no_mangle)]
pub extern "C" fn wasmtime_tls_get() -> *mut u8 {
    TLS_VALUE.load(Ordering::Relaxed)
}
```

Wasmtime 按名字调用这个符号, 取出当前线程的 TLS 指针. `#[unsafe(no_mangle)]` 属性 (Rust 2024 语法) 阻止编译器对函数名做名字修饰, 这样 Wasmtime 的链接器才能找到它. `extern "C"` 表示使用 C 调用约定. `Ordering::Relaxed` 已经足够, 因为只有一个线程 - 不需要相对其他线程的次序保证.

### `wasmtime_tls_set`

```rust
#[unsafe(no_mangle)]
pub extern "C" fn wasmtime_tls_set(ptr: *mut u8) {
    TLS_VALUE.store(ptr, Ordering::Relaxed);
}
```

这是配套的 setter. Wasmtime 在执行 Wasm 代码之前调用它保存自己的运行时上下文指针, 执行结束时再清空它 (存入 null). 这两个函数合起来, 就是 Wasmtime 在裸机上运行所需的最小平台胶水.

---

## 3. UART 驱动 (`src/uart.rs`)

UART 驱动通过 GPIO0 (TX) 和 GPIO1 (RX) 提供 115200 波特率的串口 I/O. 在这个项目里, UART 是主要接口 - 不仅用于诊断, 更是应用本身的一部分. Wasm 客体通过这个模块读写字符. 它被设计成一个**可共享的即插即用**驱动 - 无需修改就能放进任何 RP2350 项目.

### 模块头部

```rust
#![allow(dead_code)]
```

因为这个模块在多个项目之间共享, 并非每个项目都会用到每个函数. 比如 blinky 项目从不调用 `read_byte`, 而本项目却频繁使用它. 这个属性用来抑制未使用函数的警告.

### 导入

```rust
use core::cell::RefCell;
use critical_section::Mutex;
use fugit::HertzU32;
use hal::Clock;
use nb::block;
use rp235x_hal as hal;
```

`RefCell` 提供内部可变性 - 即使 UART 外设存放在静态变量里, 也能在运行时可变地借用它. `critical_section` crate 的 `Mutex` 是裸机用的互斥锁, 它通过关闭中断来防止数据竞争. `HertzU32` 是带类型的频率值, 能避免单位混淆. `Clock` 是用于读取外设时钟频率的 trait. `nb::block` 这个导入把 `block!` 宏引入作用域, 它通过空转把非阻塞操作变成阻塞操作. `hal` 这个别名指向 RP2350 的硬件抽象层.

### 常量

```rust
const UART0_BASE: u32 = 0x4007_0000;
```

UART0 外设在 RP2350 内存映射中的基地址. 它只被 panic 处理器里的裸寄存器访问函数使用 - 那些基于 HAL 的常规函数不需要它.

### UART 类型别名

```rust
pub type Uart0 = hal::uart::UartPeripheral<
    hal::uart::Enabled,
    hal::pac::UART0,
    (
        hal::gpio::Pin<hal::gpio::bank0::Gpio0, hal::gpio::FunctionUart, hal::gpio::PullNone>,
        hal::gpio::Pin<hal::gpio::bank0::Gpio1, hal::gpio::FunctionUart, hal::gpio::PullNone>,
    ),
>;
```

这个类型别名把完全配置好的 UART 外设类型固化下来. HAL 用 Rust 的类型系统来编码外设的状态: 它处于 `Enabled` 状态, 它是 `UART0` (而不是 UART1), 它的 TX/RX 引脚是 GPIO0 和 GPIO1, 配置为 UART 功能且不带上下拉电阻. 这种类型层面的编码能防止运行时错误 - 你没法不小心把一个未配置的 UART 传给需要已配置 UART 的函数.

### 全局 UART 存储

```rust
static UART: Mutex<RefCell<Option<Uart0>>> = Mutex::new(RefCell::new(None));
```

UART 外设存放在一个全局静态变量里, 由临界区互斥锁保护. `Option` 初始为 `None`, 在初始化期间被设为 `Some(uart)`. 这种 `Mutex<RefCell<Option<T>>>` 的写法, 是嵌入式 Rust 里全局存放外设的标准安全做法, 完全避开了 `unsafe` 和裸指针.

### `init`

```rust
pub fn init(
    uart0: hal::pac::UART0,
    resets: &mut hal::pac::RESETS,
    clocks: &hal::clocks::ClocksManager,
    tx_pin: hal::gpio::Pin<hal::gpio::bank0::Gpio0, hal::gpio::FunctionNull, hal::gpio::PullDown>,
    rx_pin: hal::gpio::Pin<hal::gpio::bank0::Gpio1, hal::gpio::FunctionNull, hal::gpio::PullDown>,
) -> Uart0 {
```

这个函数接收原始的 UART0 外设, 复位控制器, 时钟管理器, 以及**只接收**它需要的那两个 GPIO 引脚. 这是刻意的设计决定: 函数不接受整个 `Pins` 结构体. 调用方 (`main.rs`) 拥有全部引脚, 只把 GPIO0 和 GPIO1 交给 UART. 这意味着往项目里新增一个 GPIO 引脚, 永远不需要改动这个模块.

引脚以默认状态 (`FunctionNull`, `PullDown`) 传入, 然后在函数内部被重新配置:

```rust
    let uart_pins = (
        tx_pin.reconfigure::<hal::gpio::FunctionUart, hal::gpio::PullNone>(),
        rx_pin.reconfigure::<hal::gpio::FunctionUart, hal::gpio::PullNone>(),
    );
```

`reconfigure` 是一次零成本的类型层面状态转换. 它配置硬件寄存器, 并返回一个证明该引脚现在处于 UART 模式的新类型.

```rust
    hal::uart::UartPeripheral::new(uart0, uart_pins, resets)
        .enable(
            hal::uart::UartConfig::new(
                HertzU32::from_raw(115_200),
                hal::uart::DataBits::Eight,
                None,
                hal::uart::StopBits::One,
            ),
            clocks.peripheral_clock.freq(),
        )
        .expect("configure UART0")
}
```

UART 外设被创建出来, 配置成 115200 波特率, 8N1 帧格式 (8 位数据位, 无校验, 1 位停止位), 然后启用. 如果配置失败, `.expect()` 会带着一句说明性的消息 panic - 而这种情况只有在硬件处于意外状态时才会发生.

### `store_global`

```rust
pub fn store_global(uart: Uart0) {
    critical_section::with(|cs| {
        UART.borrow(cs).replace(Some(uart));
    });
}
```

`init` 返回配置好的 UART 之后, 调用方把它存进全局互斥锁, 这样任何代码都能读写 UART0. `critical_section::with` 在闭包执行期间关闭中断, 获取互斥锁, 并调用 `replace(Some(uart))` 把外设存进去.

### `write_msg`

```rust
pub fn write_msg(msg: &[u8]) {
    critical_section::with(|cs| {
        let cell = UART.borrow(cs);
        let uart = cell.borrow();
        let uart = uart.as_ref().unwrap();
        for &b in msg {
            if b == b'\n' {
                uart.write_full_blocking(b"\r");
            }
            uart.write_full_blocking(&[b]);
        }
    });
}
```

这个函数用 HAL 把一段字节切片写到 UART0. 它先获取全局互斥锁, 借用 UART 外设, 然后逐字节写出. 那个把 `\n` 转成 `\r\n` 的处理是为了让串口终端上的换行正确 - 终端期待每个换行符前面先有一个回车符.

### `read_byte`

```rust
pub fn read_byte() -> u8 {
    critical_section::with(|cs| {
        let cell = UART.borrow(cs);
        let mut uart = cell.borrow_mut();
        let uart = uart.as_mut().unwrap();
        let mut buf = [0u8; 1];
        let _ = block!(uart.read_raw(&mut buf));
        buf[0]
    })
}
```

这个函数会一直阻塞, 直到 UART 接收线上来一个字节. `nb` crate 的 `block!` 宏在非阻塞的 `read_raw` 调用上反复空转, 直到它返回 `Ok`. 在本项目里, `read_byte` 是主要的输入机制 - Wasm 客体通过 WIT 的 `uart` 接口调用它, 从串口终端接收字符. 注意它用的是 `borrow_mut`, 因为 `read_raw` 需要 UART 外设的可变引用 (读取会改变 RX FIFO 的状态).

### `write_byte`

```rust
pub fn write_byte(byte: u8) {
    critical_section::with(|cs| {
        let cell = UART.borrow(cs);
        let uart = cell.borrow();
        uart.as_ref().unwrap().write_full_blocking(&[byte]);
    });
}
```

往 UART0 写一个字节. 这就是回显路径 - Wasm 客体用 `read_byte` 读到一个字符, 再用 `write_byte` 把它送回去. 和 `read_byte` 不同, 写入只需要不可变借用, 因为 `write_full_blocking` 不修改 UART 的内部状态.

### `panic_init`

```rust
pub fn panic_init() {
    const RESETS_BASE: u32 = 0x4002_0000;
    const RESET_CLR: *mut u32 = (RESETS_BASE + 0x3000) as *mut u32;
    const RESET_DONE: *const u32 = (RESETS_BASE + 0x0008) as *const u32;
    const IO_BANK0_BASE: u32 = 0x4002_8000;
    const GPIO0_CTRL: *mut u32 = (IO_BANK0_BASE + 0x004) as *mut u32;
    const GPIO1_CTRL: *mut u32 = (IO_BANK0_BASE + 0x00C) as *mut u32;
    const UARTIBRD: *mut u32 = (UART0_BASE + 0x024) as *mut u32;
    const UARTFBRD: *mut u32 = (UART0_BASE + 0x028) as *mut u32;
    const UARTLCR_H: *mut u32 = (UART0_BASE + 0x02C) as *mut u32;
    const UARTCR: *mut u32 = (UART0_BASE + 0x030) as *mut u32;
```

这个函数用**裸寄存器写入**从零开始重新初始化 UART0 - 不经过 HAL. 为什么? 因为 panic 发生时, HAL 可能处于未知状态. UART 全局变量也许压根没被初始化过. 分配器可能已经损坏. 唯一安全的做法就是直接跟硬件对话.

每个常量都是指向某个硬件寄存器的指针. `RESET_CLR` 用来撤销外设复位. `RESET_DONE` 报告外设何时脱离复位状态. `GPIO0_CTRL` 和 `GPIO1_CTRL` 用来选择引脚功能 (UART). `UART*` 那几个寄存器则用来配置波特率, 数据格式并启用外设.

```rust
    unsafe {
        core::ptr::write_volatile(RESET_CLR, (1 << 26) | (1 << 6));
        while core::ptr::read_volatile(RESET_DONE) & (1 << 26) == 0 {}
        while core::ptr::read_volatile(RESET_DONE) & (1 << 6) == 0 {}
        core::ptr::write_volatile(GPIO0_CTRL, 2);
        core::ptr::write_volatile(GPIO1_CTRL, 2);
        core::ptr::write_volatile(UARTIBRD, 81);
        core::ptr::write_volatile(UARTFBRD, 24);
        core::ptr::write_volatile(UARTLCR_H, (0b11 << 5) | (1 << 4));
        core::ptr::write_volatile(UARTCR, (1 << 0) | (1 << 8) | (1 << 9));
    }
```

整个顺序是: 先往原子清除寄存器写入, 撤销 IO_BANK0 (第 6 位) 和 UART0 (第 26 位) 的复位. 然后空转等待两个外设都报告自己脱离了复位. 接着把 GPIO0 和 GPIO1 设为功能 2 (UART). 最后按默认的 150 MHz 外设时钟把 UART 配成 115200 波特率. 整数波特率分频值 (81) 和小数分频值 (24) 是这样算出来的: `150_000_000 / (16 * 115200) = 81.380`, 小数部分 `0.380 * 64 = 24.3 ≈ 24`. 线路控制寄存器设置 8 位数据位并启用 FIFO. 控制寄存器则启用 UART 本体, 发送器和接收器.

### `panic_write_byte`

```rust
pub fn panic_write_byte(byte: u8) {
    const UARTDR: *mut u32 = UART0_BASE as *mut u32;
    const UARTFR: *const u32 = (UART0_BASE + 0x018) as *const u32;
    unsafe {
        while core::ptr::read_volatile(UARTFR) & (1 << 5) != 0 {}
        core::ptr::write_volatile(UARTDR, byte as u32);
    }
}
```

写单个字节: 先空转等到 TX FIFO 有空位 (标志寄存器第 5 位是 "TX FIFO 满" 标志), 然后写入数据寄存器. 这就是 panic 处理器版本的 `write_byte`, 只不过用裸寄存器代替了 HAL.

### `panic_write`

```rust
pub fn panic_write(msg: &[u8]) {
    for &b in msg {
        if b == b'\n' {
            panic_write_byte(b'\r');
        }
        panic_write_byte(b);
    }
}
```

遍历一段字节切片, 逐字节写出, 并做 `\n` 到 `\r\n` 的转换, 走的是裸寄存器那条路. panic 处理器就是调用它来输出 panic 消息的.

---

## 4. 固件入口点 (`src/main.rs`)

这是最大的一个文件, 也是固件的核心. 它初始化硬件, 搭起 Wasm 运行时, 并把 WIT 的 `uart` 接口接到真实硬件上. 与 blinky 项目不同, 这里没有 LED 驱动 - 本项目完全围绕 UART.

### crate 属性与模块声明

```rust
#![no_std]
#![no_main]
```

`no_std` 表示不用标准库 - 只用 `core` 和 `alloc`. `no_main` 表示没有标准的 `fn main()` - 入口点由 `cortex-m-rt` 通过 `#[hal::entry]` 属性提供.

```rust
extern crate alloc;
```

启用 `alloc` crate, 它提供 `Vec`, `Box`, `String` 以及其他堆类型. 堆由 `init_heap` 里初始化的 `embedded-alloc` 分配器支撑.

```rust
mod platform;
mod uart;
```

这两行把两个模块引入作用域. 注意这里没有 `led` 模块 - 本项目不控制任何 GPIO 输出引脚.

### 导入

```rust
use core::panic::PanicInfo;
use embedded_alloc::LlffHeap as Heap;
use rp235x_hal as hal;
use wasmtime::component::{Component, HasSelf};
use wasmtime::{Config, Engine, Store};
```

`PanicInfo` 是传给 panic 处理器的类型. `LlffHeap` 是面向嵌入式系统设计的链表首次适配堆分配器. `hal` 是 RP2350 的硬件抽象层. Wasmtime 的那几个导入带来组件模型的核心类型: `Component` (预编译的 Wasm 模块), `Engine` (执行环境), `Store` (每个实例的状态), 以及 `HasSelf` (用于链接器注册的标记类型).

### WIT 绑定生成

```rust
wasmtime::component::bindgen!({
    world: "uart-echo",
    path: "wit",
});
```

这个宏在编译期读取 WIT 文件, 为 `uart-echo` world 生成 Rust 类型和 trait. 它会产出:
- 一个 `UartEcho` 结构体, 带有实例化组件和调用导出的方法
- 一个 `embedded::platform::uart::Host` trait, 固件必须实现它
- 一个 `Guest` 接口, 表示组件导出的内容

### 全局分配器

```rust
#[global_allocator]
static HEAP: Heap = Heap::empty();
```

把堆分配器声明为全局静态变量. 它初始是空的, 由 `init_heap` 用一块 256 KiB 的内存区域初始化. Wasmtime 会大量使用堆 - 用于 `Store`, `Component` 元数据以及 Wasm 线性内存.

### 常量

```rust
const XOSC_CRYSTAL_FREQ: u32 = 12_000_000;
const HEAP_SIZE: usize = 262_144;
const WASM_BINARY: &[u8] = include_bytes!(concat!(env!("OUT_DIR"), "/uart_echo.cwasm"));
```

`XOSC_CRYSTAL_FREQ` 是外部晶振频率 (12 MHz), 用于配置 PLL. `HEAP_SIZE` 是 256 KiB - RP2350 总共 512 KiB RAM 的一半, 另一半留给栈和 Wasmtime 的内部结构. `WASM_BINARY` 用 `include_bytes!` 在编译期把预编译的 Pulley 字节码直接嵌进固件二进制. 那个 `.cwasm` 文件由 `build.rs` 生成, 命名为 `uart_echo.cwasm` 是为了与 blinky 的组件区分开.

### 启动元数据

```rust
#[unsafe(link_section = ".start_block")]
#[used]
pub static IMAGE_DEF: hal::block::ImageDef = hal::block::ImageDef::secure_exe();
```

RP2350 的启动 ROM 会在一个特殊的 `.start_block` 节里寻找元数据, 以决定如何启动. `secure_exe()` 告诉启动 ROM 这是一个安全的 ARM 可执行文件. `#[used]` 属性阻止链接器把这个符号删掉, 尽管代码里没有任何地方引用它. `#[unsafe(link_section)]` 是 Rust 2024 里把数据放进指定链接器节的语法.

### 宿主状态与 WIT 实现

```rust
struct HostState;
```

宿主状态就是 Wasmtime 的 `Store` 所携带的 Rust 类型. WIT 的宿主 trait 实现在这个结构体上. 它没有字段, 因为所有硬件访问都走全局的 UART 静态变量.

```rust
impl embedded::platform::uart::Host for HostState {
    fn read_byte(&mut self) -> u8 {
        uart::read_byte()
    }

    fn write_byte(&mut self, byte: u8) {
        uart::write_byte(byte);
    }
}
```

这是 WIT `uart` 接口在宿主侧的实现. 当 Wasm 客体调用 `uart::read_byte()` 时, Wasmtime 把调用路由到这里, 再委托给 UART 驱动的 `read_byte` 函数, 阻塞等待一个字符到来. 当客体调用 `uart::write_byte(b)` 时, Wasmtime 把它路由到 `uart::write_byte`, 由后者把字节通过串口线发出去. 每次宿主调用期间 Pulley 解释器都会暂停, 等调用返回后再继续.

### panic 处理器

```rust
#[panic_handler]
fn panic(info: &PanicInfo) -> ! {
    uart::panic_init();
    uart::panic_write(b"\n!!! PANIC !!!\n");
    if let Some(location) = info.location() {
        uart::panic_write(b"Location: ");
        uart::panic_write(location.file().as_bytes());
        uart::panic_write(b"\n");
    }
    if let Some(msg) = info.message().as_str() {
        uart::panic_write(b"Message: ");
        uart::panic_write(msg.as_bytes());
        uart::panic_write(b"\n");
    }
    loop {
        cortex_m::asm::wfe();
    }
}
```

当任何代码 panic 时 (通过 `.unwrap()`, `.expect()`, `panic!` 等等), 这个处理器就会运行. 它先用裸寄存器写入从零重新初始化 UART0 (HAL 可能处于未知状态), 然后输出 panic 的位置和消息. 最后进入一个用 `wfe` (Wait For Event) 的无限循环, 让 CPU 进入低功耗状态. 这对调试至关重要 - 如果看不到 panic 输出, 嵌入式目标上的崩溃就是隐形的.

### `init_heap`

```rust
fn init_heap() {
    use core::mem::MaybeUninit;
    static mut HEAP_MEM: [MaybeUninit<u8>; HEAP_SIZE] = [MaybeUninit::uninit(); HEAP_SIZE];
    unsafe { HEAP.init(&raw mut HEAP_MEM as usize, HEAP_SIZE) }
}
```

分配一块 256 KiB 的未初始化内存, 交给堆分配器. `MaybeUninit` 告诉编译器这块内存不需要清零 - 这能省下启动时间. `unsafe` 块是必需的, 因为 `HEAP.init` 接收裸指针; 这是本项目里少数几处无法避免的 `unsafe` 之一.

### `init_clocks`

```rust
fn init_clocks(
    xosc: hal::pac::XOSC,
    clocks: hal::pac::CLOCKS,
    pll_sys: hal::pac::PLL_SYS,
    pll_usb: hal::pac::PLL_USB,
    resets: &mut hal::pac::RESETS,
    watchdog: &mut hal::Watchdog,
) -> hal::clocks::ClocksManager {
    hal::clocks::init_clocks_and_plls(
        XOSC_CRYSTAL_FREQ, xosc, clocks, pll_sys, pll_usb, resets, watchdog,
    )
    .ok()
    .unwrap()
}
```

初始化 RP2350 的时钟树. 外部 12 MHz 晶振驱动两个 PLL: 系统 PLL (配置为 150 MHz 供 CPU 使用) 和 USB PLL (48 MHz 供 USB 外设使用, 不过这里用不到 USB). 这个函数返回一个 `ClocksManager`, 向其他外设提供时钟频率信息 - 关键是, UART 的波特率计算依赖于知道外设时钟频率.

### `init_hardware`

```rust
fn init_hardware() {
    let mut pac = hal::pac::Peripherals::take().unwrap();
    let mut watchdog = hal::Watchdog::new(pac.WATCHDOG);
    let clocks = init_clocks(
        pac.XOSC, pac.CLOCKS, pac.PLL_SYS, pac.PLL_USB,
        &mut pac.RESETS, &mut watchdog,
    );
    let sio = hal::Sio::new(pac.SIO);
    let pins = hal::gpio::Pins::new(
        pac.IO_BANK0, pac.PADS_BANK0, sio.gpio_bank0, &mut pac.RESETS,
    );
    let uart_dev = uart::init(pac.UART0, &mut pac.RESETS, &clocks, pins.gpio0, pins.gpio1);
    uart::store_global(uart_dev);
}
```

这个函数初始化所有硬件. `Peripherals::take()` 是个单例 - 它只能被调用一次, 从而防止多个驱动同时访问同一套硬件. 函数创建看门狗 (时钟初始化需要它), 配置时钟, 初始化 SIO (Single-cycle IO) 以便访问 GPIO, 并创建引脚结构体.

引脚分配只发生在这里, 也仅此一处. GPIO0 和 GPIO1 交给 UART - 这个项目需要的就这么多. 与 blinky 项目不同, 这里没有 `led::store_pin` 调用, 因为没有输出引脚需要登记. 如果你想在 GPIO25 上加一个 LED, 就在这儿加一句 `led::store_pin(25, pins.gpio25.into_push_pull_output())`, 并引入 `led` 模块.

### `create_engine`

```rust
fn create_engine() -> Engine {
    let mut config = Config::new();
    config.target("pulley32").expect("set pulley32 target");
    config.signals_based_traps(false);
    config.memory_init_cow(false);
    config.memory_reservation(0);
    config.memory_guard_size(0);
    config.memory_reservation_for_growth(0);
    config.guard_before_linear_memory(false);
    config.max_wasm_stack(16384);
    Engine::new(&config).expect("create Pulley engine")
}
```

创建 Wasmtime 执行引擎. 这里每一项设置都很关键, 必须与 `build.rs` 里构建时的引擎完全一致:

- `target("pulley32")` - 目标是 Pulley 32 位软件解释器, 而不是原生代码生成. Pulley 是 Wasmtime 的可移植字节码解释器, 在任何架构上都能运行.
- `signals_based_traps(false)` - 关闭基于操作系统信号的陷阱处理. 这里没有操作系统来发信号.
- `memory_init_cow(false)` - 关闭写时复制的内存初始化. 这里没有虚拟内存系统.
- `memory_reservation(0)` - 关闭虚拟内存预留. RP2350 只有物理内存.
- `memory_guard_size(0)` - 关闭保护页. 没有虚拟内存就没有保护页.
- `memory_reservation_for_growth(0)` - 不预留增长空间.
- `guard_before_linear_memory(false)` - 线性内存前面不放保护页.
- `max_wasm_stack(16384)` - 把 Wasm 栈限制在 16 KiB, 以适应紧张的内存.

### `create_component`

```rust
fn create_component(engine: &Engine) -> Component {
    unsafe { Component::deserialize(engine, WASM_BINARY) }.expect("valid Pulley component")
}
```

反序列化由 `include_bytes!` 嵌入的预编译 Pulley 字节码. 这里需要 `unsafe`, 因为 `Component::deserialize` 相信这些字节是合法的 Wasmtime 序列化组件 - 而这一点是有保证的, 因为它们是我们的 `build.rs` 生成的.

### `build_linker`

```rust
fn build_linker(engine: &Engine) -> wasmtime::component::Linker<HostState> {
    let mut linker = wasmtime::component::Linker::new(engine);
    UartEcho::add_to_linker::<HostState, HasSelf<HostState>>(
        &mut linker,
        |state: &mut HostState| state,
    )
    .expect("register WIT interfaces");
    linker
}
```

创建一个组件链接器, 并注册所有 WIT 接口的实现. `UartEcho::add_to_linker` 由 `bindgen!` 生成, 它把 `HostState` 上 `uart::Host` trait 的实现接到链接器上. `HasSelf<HostState>` 这个类型参数是 Wasmtime 内部使用的幽灵类型 - 那个闭包只是原样返回 `state`.

### `execute_wasm`

```rust
fn execute_wasm(
    store: &mut Store<HostState>,
    linker: &wasmtime::component::Linker<HostState>,
    component: &Component,
) {
    let uart_echo =
        UartEcho::instantiate(&mut *store, component, linker).expect("instantiate component");
    uart_echo.call_run(&mut *store).expect("execute run");
}
```

实例化 Wasm 组件并调用它导出的 `run` 函数. `UartEcho::instantiate` 创建一个活的组件实例, 所有导入都已解析完毕. `call_run` 调用客体的 `run` 函数, 后者进入无限回显循环. 只有当 Wasm 客体的 `run` 函数返回时, 这个函数才会返回 - 而在本项目里它永远不会返回.

### `run_wasm`

```rust
fn run_wasm() -> ! {
    let engine = create_engine();
    let component = create_component(&engine);
    let mut store = Store::new(&engine, HostState);
    let linker = build_linker(&engine);
    execute_wasm(&mut store, &linker, &component);
    loop {
        cortex_m::asm::wfe();
    }
}
```

编排 Wasm 运行时的启动. 创建引擎, 反序列化组件, 用宿主状态创建 store, 构建链接器, 然后执行 Wasm 组件. 末尾那个 `loop` 是一道保险 - `execute_wasm` 本不该返回, 因为客体的 `run` 函数会永远循环下去.

### `main`

```rust
#[hal::entry]
fn main() -> ! {
    init_heap();
    init_hardware();
    run_wasm()
}
```

固件入口点. `#[hal::entry]` 是 RP2350 HAL 的入口点属性 (构建在 `cortex-m-rt` 之上). 它设置栈指针和向量表, 然后调用这个函数. 启动顺序是: 初始化堆分配器, 初始化所有硬件外设, 然后启动 Wasm 运行时. 返回类型 `-> !` 表示这个函数永不返回 - Wasm 客体的回显循环会一直跑下去.

---

## 5. 构建脚本 (`build.rs`)

构建脚本在 `cargo build` 期间运行于**宿主机** (你的开发电脑) 上. 它编译 Wasm 客体应用, 并把它 AOT 编译成 Pulley 字节码, 这样设备上就不需要 Wasm 编译器了.

### 导入

```rust
use std::fs::File;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::Command;
use wasmtime::{Config, Engine};
use wit_component::ComponentEncoder;
```

与固件代码不同, 构建脚本使用完整的标准库 (`std`). 它需要文件 I/O, 进程启动, 以及带 Cranelift 代码生成的宿主侧 Wasmtime.

### `setup_output_dir`

```rust
fn setup_output_dir() -> PathBuf {
    let out = PathBuf::from(std::env::var_os("OUT_DIR").unwrap());
    println!("cargo:rustc-link-search={}", out.display());
    out
}
```

从 `OUT_DIR` 环境变量 (由 cargo 设置) 取出构建输出目录, 并把它注册为链接器搜索路径. 链接脚本 (`memory.x`) 和编译好的 Pulley 字节码 (`uart_echo.cwasm`) 都会放在这里.

### `write_linker_script`

```rust
fn write_linker_script(out: &Path) {
    let memory_x = include_bytes!("rp2350.x");
    let mut f = File::create(out.join("memory.x")).unwrap();
    f.write_all(memory_x).unwrap();
}
```

把描述 RP2350 内存布局的链接脚本 (`rp2350.x`) 复制到输出目录, 命名为 `memory.x`. 这个链接脚本定义了 Flash (2 MiB) 和 RAM (512 KiB) 区域, 并告诉链接器把代码, 数据和栈放在哪里. `cortex-m-rt` crate 的 `link.x` 脚本会自动包含 `memory.x`.

### `compile_wasm_app`

```rust
fn compile_wasm_app() {
    let status = Command::new("cargo")
        .args(["build", "--release", "--target", "wasm32-unknown-unknown"])
        .current_dir("wasm-app")
        .env_remove("CARGO_ENCODED_RUSTFLAGS")
        .status()
        .expect("failed to build Wasm app");
    assert!(status.success(), "Wasm app compilation failed");
}
```

启动一个子 `cargo build` 进程来编译 Wasm 客体应用. 几个关键细节:

- `--target wasm32-unknown-unknown` 编译成 WebAssembly, 而不是宿主架构.
- `.current_dir("wasm-app")` 让构建在 Wasm 子 crate 的目录里执行.
- `.env_remove("CARGO_ENCODED_RUSTFLAGS")` 至关重要 - 没有它, 父构建的 RUSTFLAGS (其中含有 `--nmagic` 和 `-Tlink.x` 这类 ARM 链接参数) 会泄漏到子构建里, 导致 Wasm 链接错误.

产物是位于 `wasm-app/target/wasm32-unknown-unknown/release/wasm_app.wasm` 的核心 Wasm 模块.

### `create_pulley_engine`

```rust
fn create_pulley_engine() -> Engine {
    let mut config = Config::new();
    config.target("pulley32").expect("set pulley32 target");
    config.signals_based_traps(false);
    config.memory_init_cow(false);
    config.memory_reservation(0);
    config.memory_guard_size(0);
    config.memory_reservation_for_growth(0);
    config.guard_before_linear_memory(false);
    config.max_wasm_stack(16384);
    Engine::new(&config).expect("create Pulley engine")
}
```

创建一个用于 AOT 交叉编译的 Wasmtime 引擎. 每一项设置都**必须与** `src/main.rs` 里的 `create_engine` 完全相同. Wasmtime 序列化组件时, 会把所有配置值写进 `.cwasm` 的头部. 设备反序列化时, 会逐项与运行时引擎比对. 任何不一致都会让 `Component::deserialize` 以一句晦涩的错误失败.

### `compile_wasm_to_pulley`

```rust
fn compile_wasm_to_pulley(out: &Path) {
    let wasm_path = "wasm-app/target/wasm32-unknown-unknown/release/wasm_app.wasm";
    let wasm_bytes = std::fs::read(wasm_path).expect("read Wasm binary");
    let component_bytes = ComponentEncoder::default()
        .module(&wasm_bytes)
        .expect("set core module")
        .validate(true)
        .encode()
        .expect("encode component");
    let engine = create_pulley_engine();
    let serialized = engine
        .precompile_component(&component_bytes)
        .expect("precompile component");
    std::fs::write(out.join("uart_echo.cwasm"), &serialized).expect("write Pulley bytecode");
}
```

这是 AOT 编译流水线的核心, 也是构建脚本里最重要的函数. 它做了三次转换:

1. **读取核心 Wasm 模块** - 也就是上一步 `cargo build` 产出的原始 `.wasm` 文件.
2. **编码成组件** - `ComponentEncoder` 读取 `wit-bindgen` 嵌入核心模块里的类型元数据, 把它包装成一个带类型化导入导出的正式 Wasm 组件.
3. **AOT 编译成 Pulley 字节码** - `precompile_component` 运行以 `pulley32` 架构为目标的 Cranelift (一个代码生成器), 产出序列化字节码, Pulley 解释器在设备上无需任何编译就能执行它.

结果写入 `uart_echo.cwasm`, 固件通过 `include_bytes!` 把它包含进来.

### `print_rerun_triggers`

```rust
fn print_rerun_triggers() {
    println!("cargo:rerun-if-changed=rp2350.x");
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=wasm-app/src/lib.rs");
    println!("cargo:rerun-if-changed=wasm-app/Cargo.toml");
    println!("cargo:rerun-if-changed=wit/world.wit");
}
```

告诉 cargo 哪些文件变化时应当触发构建脚本重跑. 没有这些, cargo 可能会缓存构建脚本的输出, 从而漏掉 Wasm 客体代码或 WIT 定义的改动.

### `main`

```rust
fn main() {
    let out = setup_output_dir();
    write_linker_script(&out);
    compile_wasm_app();
    compile_wasm_to_pulley(&out);
    print_rerun_triggers();
}
```

构建脚本入口点. 顺序是: 建立输出目录, 写出链接脚本, 把 Wasm 客体编译成核心模块, 转换并 AOT 编译成 Pulley 字节码, 最后登记文件变化触发条件.

---

## 6. Wasm 客体应用 (`wasm-app/src/lib.rs`)

这是运行在 RP2350 上 Wasmtime 运行时**内部**的 WebAssembly 组件. 它接触不到硬件 - 只能用宿主提供的 WIT `uart` 接口. 与 blinky 客体 (只是循环执行 set-high/delay/set-low) 不同, UART 回显客体执行的是带终端字符处理的交互式 I/O.

### crate 属性

```rust
#![no_std]
```

Wasm 客体是 `no_std` 的, 因为 `wasm32-unknown-unknown` 目标没有操作系统. 它用 `core` 提供语言原语, 用 `alloc` 提供堆.

```rust
extern crate alloc;
```

启用堆分配. 规范 ABI (宿主与客体之间的调用约定) 要求有一个 `cabi_realloc` 函数, 让宿主能在客体的线性内存里分配内存. `wit-bindgen` crate 会生成这个函数, 而它需要一个能用的分配器.

### 全局分配器

```rust
#[global_allocator]
static ALLOC: dlmalloc::GlobalDlmalloc = dlmalloc::GlobalDlmalloc;
```

`dlmalloc` 是把 Doug Lea 的 malloc 移植到 Rust 的产物. 在 `no_std` 下它是唯一能配合 `wasm32-unknown-unknown` 工作的分配器, 因为它通过增长 Wasm 线性内存自己实现了 `sbrk`. `global` 特性开关让它成为 `#[global_allocator]`.

### 导入与绑定

```rust
use embedded::platform::uart;
```

这个导入来自 `wit_bindgen::generate!` 生成的绑定. 它提供 `uart::read_byte` 和 `uart::write_byte` - 也就是 `world.wit` 里定义, 由宿主固件实现的那两个函数.

```rust
wit_bindgen::generate!({
    world: "uart-echo",
    path: "../wit",
});
```

这个宏在编译期读取 `wit/world.wit`, 生成客体侧的绑定. 它会创建 `embedded::platform::uart` 模块 (其中的函数会调用到宿主), 以及组件必须实现的 `Guest` trait.

### 客体实现

```rust
struct UartEchoApp;

export!(UartEchoApp);
```

`UartEchoApp` 就是实现 `uart-echo` world 客体侧的那个结构体. `export!` 宏 (由 `wit_bindgen` 生成) 把它注册为组件的实现, 并把导出的 `run` 函数接好.

```rust
impl Guest for UartEchoApp {
    fn run() {
        loop {
            echo_char(read_byte());
        }
    }
}
```

`run` 函数就是整个应用循环. 它从 UART 读一个字节, 交给 `echo_char` 处理, 然后永远重复下去. 每次调用 `read_byte` 都会跨过 Wasm 边界 - Pulley 解释器暂停, Wasmtime 把调用派发给 `HostState::read_byte`, 后者在 UART 驱动里阻塞等待字符到来, 然后才把控制权交还给解释器.

### `read_byte`

```rust
fn read_byte() -> u8 {
    uart::read_byte()
}
```

对 WIT 生成的 `uart::read_byte` 的一层薄封装. 它直接委托给宿主函数, 后者会阻塞直到 UART0 上有一个字节到来. 这层封装是为了让代码更好读, 并保持辅助函数写在调用者前面的惯例.

### `write_byte`

```rust
fn write_byte(b: u8) {
    uart::write_byte(b);
}
```

对 WIT 生成的 `uart::write_byte` 的一层薄封装. 它把一个字节跨过 Wasm 边界送到宿主, 由宿主通过 UART0 发出去.

### `handle_backspace`

```rust
fn handle_backspace() {
    write_byte(0x08);
    write_byte(b' ');
    write_byte(0x08);
}
```

用标准的终端退格序列来处理退格键和删除键: 光标左移 (`0x08` 即 BS), 用一个空格覆盖掉那个字符, 再把光标左移一次. 这样才能让前一个字符从终端显示上真正消失. 没有这三个字节的序列, 退格只会移动光标而不会擦掉字符.

### `handle_newline`

```rust
fn handle_newline() {
    write_byte(b'\r');
    write_byte(b'\n');
}
```

把任何换行输入 (CR 或 LF) 转成规范的 CR+LF 序列. 串口终端需要这两个字符才能正确换行 - CR 把光标移到第 0 列, LF 把光标下移一行. 只发其中一个, 结果要么是覆盖当前行, 要么是下移了却没有回到第 0 列.

### `echo_char`

```rust
fn echo_char(b: u8) {
    match b {
        0x08 | 0x7F => handle_backspace(),
        b'\r' | b'\n' => handle_newline(),
        _ => write_byte(b),
    }
}
```

字符派发函数. 它接收一个字节, 按值把它路由到相应的处理器. 退格 (`0x08`) 和删除 (`0x7F`) 触发擦除序列. 回车 (`\r`) 和换行 (`\n`) 触发换行序列. 其他字符原样回显. 这个 `match` 就是回显应用的核心 - 它把一个简单的字节进字节出循环变成了可用的终端体验.

### panic 处理器

```rust
#[panic_handler]
fn panic(_info: &PanicInfo) -> ! {
    loop {
        core::hint::spin_loop();
    }
}
```

Wasm 客体的 panic 处理器. 与固件的 panic 处理器不同, 它没法往 UART 写东西 - 它没有直接的硬件访问权. 它只是用一个 `spin_loop()` (提示 CPU 在空转时降低功耗) 进入无限循环. 实际上, Wasm 客体里发生 panic 会让 Wasmtime 触发陷阱, 随后被固件的 panic 处理器接住.

---

## 小结: 完整的执行流程

1. RP2350 上电, 启动 ROM 从 `.start_block` 读取 `IMAGE_DEF`
2. `main()` 调用 `init_heap()` 建立那 256 KiB 的堆
3. `init_hardware()` 配置时钟 (150 MHz) 和 UART0 (GPIO0/GPIO1 上的 115200 波特率)
4. `run_wasm()` 创建 Pulley 引擎并反序列化预编译的 Wasm 组件
5. `execute_wasm()` 实例化组件并调用 `run`
6. 客体的 `run()` 进入无限循环: `read_byte()` -> `echo_char()` -> 回到 `read_byte()`
7. 每次 `read_byte` 调用都跨过 Wasm 边界进入宿主, 宿主阻塞直到 UART0 上来一个字符
8. 每次 `write_byte` 调用都跨过边界, 通过 UART0 发送一个字节
9. 特殊字符 (退格, 换行) 由客体的派发逻辑处理
10. 字符就这样回显下去. 永远.

## 文档链接

下面这些参考覆盖了本项目用到的每一个主要 crate 和规范:

- [rp235x-hal](https://docs.rs/rp235x-hal) - RP2350 硬件抽象层 (GPIO, UART, 时钟)
- [Wasmtime](https://docs.wasmtime.dev) - WebAssembly 运行时文档 ([API 文档](https://docs.rs/wasmtime))
- [WIT / 组件模型](https://component-model.bytecodealliance.org) - 组件模型规范 ([wit-bindgen API 文档](https://docs.rs/wit-bindgen))
- [cortex-m](https://docs.rs/cortex-m) - Cortex-M 底层访问 (中断, 寄存器, 内建函数)
- [cortex-m-rt](https://docs.rs/cortex-m-rt) - Cortex-M 启动运行时 (复位向量, 内存初始化)
- [embedded-hal](https://docs.rs/embedded-hal) - 硬件抽象 trait (GPIO, UART, SPI, I2C)
- [embedded-alloc](https://docs.rs/embedded-alloc) - 面向 `no_std` 环境的堆分配器
- [Cranelift](https://cranelift.dev) - 用于 Wasm AOT 编译的编译器后端 ([API 文档](https://docs.rs/cranelift-codegen))
- [Pulley](https://docs.rs/pulley-interpreter) - Wasmtime 的可移植解释器字节码格式
- [fugit](https://docs.rs/fugit) - 嵌入式用的类型安全时间单位 (波特率, 时钟频率)
- [critical-section](https://docs.rs/critical-section) - 跨平台的关中断安全互斥

## 许可证

MIT
