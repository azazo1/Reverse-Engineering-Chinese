# 教程: 嵌入式 Wasm Blinky - 完整代码走读

本教程会逐行, 逐个函数地讲解 **embedded-wasm-blinky** 项目里的每一个 Rust 源文件. 读完以后, 你会明白一个 WebAssembly 组件是怎样被编译, 部署, 并在 RP2350 微控制器上执行, 从而让一个 LED 闪烁的 - 整个过程全是裸机 Rust, 没有操作系统.

整个走读按下面的顺序进行:

1. [WIT 接口定义](#1-wit-接口定义-witworldwit) - 客体与宿主之间的契约
2. [平台胶水层](#2-平台胶水层-srcplatformrs) - 给 Wasmtime 用的线程局部存储桩
3. [UART 驱动](#3-uart-驱动-srcuartrs) - 用于诊断的串口输出
4. [LED 驱动](#4-led-驱动-srcledrs) - GPIO 输出引脚管理
5. [固件入口点](#5-固件入口点-srcmainrs) - 硬件初始化, Wasm 运行时, panic 处理程序
6. [构建脚本](#6-构建脚本-buildrs) - AOT 编译流水线
7. [Wasm 客体应用](#7-wasm-客体应用-wasm-appsrclibrs) - blinky 组件本身

---

## 1. WIT 接口定义 (`wit/world.wit`)

在写任何 Rust 代码之前, 项目先定义了一个 **WIT (WebAssembly Interface Type)** 文件. WIT 是一种与语言无关的接口描述, WebAssembly 组件模型用它来对宿主 (固件) 与客体 (Wasm 模块) 之间的函数调用做类型检查.

```wit
package embedded:platform;
```

这一行声明了一个名为 `embedded:platform` 的 WIT 包. 包名采用 namespace:name 的约定. 这个包位于 `embedded` 命名空间下, 提供 `platform` 层面的硬件抽象.

```wit
interface gpio {
    set-high: func(pin: u32);
    set-low: func(pin: u32);
}
```

`gpio` 接口定义了两个函数. `set-high` 接收一个引脚编号, 把它打开. `set-low` 接收一个引脚编号, 把它关闭. 引脚编号用 `u32`, 因为 WIT 的类型系统能干净地映射到 Wasm 的 32 位整数类型. 这两个是 **import** - 客体调用它们, 宿主提供实现.

```wit
interface timing {
    delay-ms: func(ms: u32);
}
```

`timing` 接口只提供一个阻塞式延时函数. 客体用毫秒数调用 `delay-ms`, 宿主通过数 CPU 周期阻塞相应的时间.

```wit
world blinky {
    import gpio;
    import timing;
    export run: func();
}
```

一个 **world** 是一份完整的契约. `blinky` world 的意思是: "我需要宿主提供 `gpio` 和 `timing`, 我会提供一个 `run` 函数." 宿主实例化组件, 调用 `run`, 然后 Wasm 代码接管 - 在需要时回调 `gpio` 和 `timing`. 硬件与应用逻辑之间的全部接口就是这些.

---

## 2. 平台胶水层 (`src/platform.rs`)

Wasmtime 最初是为桌面操作系统构建的, 那些系统由 OS 提供线程局部存储 (TLS). 在裸机微控制器上没有 OS, 所以 TLS 得我们自己提供. 这个文件是项目里最简单的 - 两个函数加一个静态变量.

### 导入

```rust
use core::ptr;
use core::sync::atomic::{AtomicPtr, Ordering};
```

`ptr` 提供 `null_mut()`, 用来初始化 TLS 的值. `AtomicPtr` 是原子指针类型, 可以在任何上下文中读写而不会产生数据竞争. 在单核 Cortex-M33 上原子操作并非必需, 但它能满足 Rust 类型系统的要求, 让代码在构造上就是正确的.

### TLS 变量

```rust
static TLS_VALUE: AtomicPtr<u8> = AtomicPtr::new(ptr::null_mut());
```

TLS 的全部实现就是这些. Wasmtime 运行时为每个线程保存一个指针. RP2350 只跑一个线程, 所以一个全局原子指针就够了. 它初始为 null, 在组件执行期间由 Wasmtime 设置.

### `wasmtime_tls_get`

```rust
#[unsafe(no_mangle)]
pub extern "C" fn wasmtime_tls_get() -> *mut u8 {
    TLS_VALUE.load(Ordering::Relaxed)
}
```

Wasmtime 按名字调用这个符号, 取回当前线程的 TLS 指针. `#[unsafe(no_mangle)]` 属性 (Rust 2024 语法) 阻止编译器对函数名做名称修饰, 这样 Wasmtime 的链接器就能找到它. `extern "C"` 表示使用 C 调用约定. `Ordering::Relaxed` 就足够了, 因为只有一个线程 - 不需要对其他线程提供顺序保证.

### `wasmtime_tls_set`

```rust
#[unsafe(no_mangle)]
pub extern "C" fn wasmtime_tls_set(ptr: *mut u8) {
    TLS_VALUE.store(ptr, Ordering::Relaxed);
}
```

这是对应的 setter. Wasmtime 在执行 Wasm 代码前调用它保存自己的运行时上下文指针, 执行结束时清空它 (存入 null). 这两个函数合起来, 就是 Wasmtime 在裸机上运行所需的最小平台胶水层.

---

## 3. UART 驱动 (`src/uart.rs`)

UART 驱动通过 GPIO0 (TX) 和 GPIO1 (RX) 以 115200 波特率提供串口输出. 它存在的理由有两个: 正常运行期间的诊断日志, 以及固件崩溃时的 panic 信息. 这个模块被设计成 **共享的即插即用** 驱动 - 不改一行代码就能放进任何 RP2350 项目.

### 模块头

```rust
#![allow(dead_code)]
```

因为这个模块在多个项目之间共享, 并非每个项目都会用到每个函数. 例如 blinky 项目从不调用 `read_byte`. 这个属性会抑制未使用函数的警告.

### 导入

```rust
use core::cell::RefCell;
use critical_section::Mutex;
use fugit::HertzU32;
use hal::Clock;
use nb::block;
use rp235x_hal as hal;
```

`RefCell` 提供内部可变性 - 即使 UART 外设放在静态变量里, 也能在运行时可变借用它. `critical_section` crate 里的 `Mutex` 是裸机互斥锁, 通过关闭中断来防止数据竞争. `HertzU32` 是带类型的频率值, 可以避免单位混淆. `Clock` 是读取外设时钟频率的 trait. `use nb::block` 把 `block!` 宏引入作用域, 它通过自旋把非阻塞操作变成阻塞操作. `hal` 别名指向 RP2350 的硬件抽象层.

### 常量

```rust
const UART0_BASE: u32 = 0x4007_0000;
```

UART0 外设在 RP2350 内存映射中的基地址. 只有 panic 处理程序里那些直接访问寄存器的函数会用到它 - 基于 HAL 的常规函数不需要.

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

这个类型别名刻画了完全配置好的 UART 外设类型. HAL 用 Rust 的类型系统来编码外设状态: 它是 `Enabled` 的, 它是 `UART0` (不是 UART1), 它的 TX/RX 引脚是配置为 UART 功能, 且没有上下拉电阻的 GPIO0 和 GPIO1. 这种类型层面的编码可以避免运行时错误 - 你没法把一个未配置的 UART 误传给需要已配置 UART 的函数.

### UART 全局存储

```rust
static UART: Mutex<RefCell<Option<Uart0>>> = Mutex::new(RefCell::new(None));
```

UART 外设存放在全局静态变量里, 由临界区互斥锁保护. `Option` 初始为 `None`, 初始化时被设为 `Some(uart)`. 这个模式 - `Mutex<RefCell<Option<T>>>` - 是嵌入式 Rust 里全局保存外设的标准安全做法, 完全避开了 `unsafe` 和裸指针.

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

这个函数接收原始的 UART0 外设, resets 控制器, 时钟管理器, 以及 **只接收** 它需要的两个 GPIO 引脚. 这是有意为之的设计: 函数不接收整个 `Pins` 结构体. 调用方 (`main.rs`) 拥有所有引脚, 只把 GPIO0 和 GPIO1 交给 UART. 这意味着给项目新增一个 GPIO 引脚时, 永远不需要改动这个模块.

引脚进来时处于默认状态 (`FunctionNull`, `PullDown`), 在函数内部被重新配置:

```rust
    let uart_pins = (
        tx_pin.reconfigure::<hal::gpio::FunctionUart, hal::gpio::PullNone>(),
        rx_pin.reconfigure::<hal::gpio::FunctionUart, hal::gpio::PullNone>(),
    );
```

`reconfigure` 是零成本的类型层面状态转换. 它配置硬件寄存器, 并返回一个新类型, 用来证明这个引脚现在处于 UART 模式.

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

UART 外设被创建出来, 配置为 115200 波特率, 8N1 帧格式 (8 个数据位, 无校验, 1 个停止位), 然后使能. 如果配置失败, `.expect()` 会带着说明性的信息 panic - 只有硬件处于意料之外的状态时才会发生.

### `store_global`

```rust
pub fn store_global(uart: Uart0) {
    critical_section::with(|cs| {
        UART.borrow(cs).replace(Some(uart));
    });
}
```

`init` 返回配置好的 UART 之后, 调用方把它存进全局互斥锁, 这样任何代码 (包括 GPIO 状态日志) 都能往 UART0 写. `critical_section::with` 在闭包执行期间关闭中断, 获取互斥锁, 并调用 `replace(Some(uart))` 保存外设.

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

这个函数用 HAL 把一个字节切片写到 UART0. 它获取全局互斥锁, 借用 UART 外设, 然后逐字节写出. `\n` 到 `\r\n` 的转换保证串口终端上的换行正确, 这些终端期望每个换行前有一个回车.

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

这个函数会阻塞, 直到 UART RX 线上收到一个字节. `nb` crate 的 `block!` 宏对非阻塞的 `read_raw` 调用反复自旋, 直到它返回 `Ok`. blinky 项目没有用这个函数, 但因为模块是跨项目共享的所以保留着 - UART 回显项目会用到它.

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

往 UART0 写一个字节. 和 `read_byte` 一样, 它主要供共享模块家族里的其他项目使用.

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

这个函数用 **裸寄存器写** 从头重新初始化 UART0 - 不用 HAL. 为什么? 因为 panic 发生时 HAL 可能处于未知状态, UART 全局变量可能压根没初始化过, 分配器可能已经损坏. 唯一安全的做法就是直接和硬件对话.

每个常量都指向一个具体的硬件寄存器. `RESET_CLR` 解除外设复位. `RESET_DONE` 报告外设何时退出复位. `GPIO0_CTRL` 和 `GPIO1_CTRL` 选择引脚功能 (UART). `UART*` 系列寄存器配置波特率, 数据格式, 并使能外设.

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

执行顺序是: 先向 atomic-clear 寄存器写入, 解除 IO_BANK0 (bit 6) 和 UART0 (bit 26) 的复位. 然后自旋, 直到两个外设都报告已退出复位. 接着把 GPIO0 和 GPIO1 设为功能 2 (UART). 最后在默认的 150 MHz 外设时钟下把 UART 配置成 115200 波特率. 整数波特率除数 (81) 和小数除数 (24) 的算法是: `150_000_000 / (16 * 115200) = 81.380`, 小数部分 `0.380 * 64 = 24.3 ≈ 24`. 线路控制寄存器设置 8 个数据位并使能 FIFO. 控制寄存器使能 UART, 发送器和接收器.

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

写一个字节: 先自旋直到 TX FIFO 有空位 (标志寄存器 bit 5 是 "TX FIFO 满" 标志), 然后写数据寄存器. 这是 panic 处理程序里对应 `write_byte` 的版本, 用裸寄存器而不是 HAL.

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

遍历一个字节切片, 逐字节写出并做 `\n` 到 `\r\n` 的转换, 走的是裸寄存器路径. panic 处理程序就是调用它来输出 panic 信息的.

---

## 4. LED 驱动 (`src/led.rs`)

LED 驱动按硬件引脚编号管理 GPIO 输出引脚. 它是为组件模型架构设计的: Wasm 客体说 "把 25 号引脚拉高", 宿主固件就在这个模块里查到 25 号引脚并把它拉高.

### 导入与类型别名

```rust
extern crate alloc;

use alloc::boxed::Box;
use alloc::collections::BTreeMap;
use core::cell::RefCell;
use core::convert::Infallible;
use critical_section::Mutex;
use embedded_hal::digital::OutputPin;
```

这个模块用堆分配 (`Box`, `BTreeMap`) 把引脚存成 trait 对象. `OutputPin` 是所有 GPIO 输出引脚都会实现的 embedded-hal trait. `Infallible` 是不会失败的 GPIO 操作的错误类型 (RP2350 的 GPIO 总是成功).

```rust
type PinBox = Box<dyn OutputPin<Error = Infallible> + Send>;
```

这个类型别名定义了堆分配, 类型擦除的 GPIO 引脚. 把引脚装箱成 trait 对象之后, 模块就能把任意 GPIO 引脚 (GPIO0, GPIO25 等) 存进同一个集合, 而不需要知道具体类型. `Send` 约束是必需的, 因为这个静态变量会从中断安全的临界区里访问.

### 引脚全局存储

```rust
static PINS: Mutex<RefCell<BTreeMap<u8, PinBox>>> = Mutex::new(RefCell::new(BTreeMap::new()));
```

`BTreeMap` 把引脚编号 (例如 `25`) 映射到装箱后的 trait 对象. 这和 UART 模块用的是同一个 `Mutex<RefCell<...>>` 模式. 这里用 `BTreeMap` 而不是 `HashMap`, 因为 `HashMap` 需要随机数生成器, 而 `no_std` 里没有.

### `store_pin`

```rust
pub fn store_pin(gpio_num: u8, pin: impl OutputPin<Error = Infallible> + Send + 'static) {
    critical_section::with(|cs| {
        PINS.borrow(cs).borrow_mut().insert(gpio_num, Box::new(pin));
    });
}
```

按硬件编号注册一个 GPIO 引脚. `impl OutputPin` 参数接受任何具体引脚类型 - 调用方不需要手动装箱. 在临界区里, 引脚被装箱并插入映射表. `'static` 约束是必需的, 因为映射表活在静态变量里.

### `set_high`

```rust
pub fn set_high(gpio_num: u8) {
    critical_section::with(|cs| {
        let map = PINS.borrow(cs);
        let mut map = map.borrow_mut();
        let pin = map.get_mut(&gpio_num).expect("pin not registered");
        let _ = pin.set_high();
    });
}
```

按编号查找引脚, 在 trait 对象上调用 `set_high()`, 并忽略 `Result` (它是 `Infallible`, 不可能失败). 如果 Wasm 客体试图控制一个宿主从未注册过的引脚, `.expect("pin not registered")` 的 panic 信息会给出清晰的诊断.

### `set_low`

```rust
pub fn set_low(gpio_num: u8) {
    critical_section::with(|cs| {
        let map = PINS.borrow(cs);
        let mut map = map.borrow_mut();
        let pin = map.get_mut(&gpio_num).expect("pin not registered");
        let _ = pin.set_low();
    });
}
```

和 `set_high` 相同, 只是把引脚拉低. `set_high` 和 `set_low` 合起来就是 WIT `gpio` 接口在宿主侧的实现.

---

## 5. 固件入口点 (`src/main.rs`)

这是最大的文件, 也是固件的心脏. 它初始化硬件, 搭建 Wasm 运行时, 并把 WIT 接口桥接到真实硬件上.

### crate 属性与模块声明

```rust
#![no_std]
#![no_main]
```

`no_std` 表示不使用标准库 - 只有 `core` 和 `alloc`. `no_main` 表示没有标准的 `fn main()` - 入口点由 `cortex-m-rt` 通过 `#[hal::entry]` 属性提供.

```rust
extern crate alloc;
```

启用 `alloc` crate, 它提供 `Vec`, `Box`, `String` 等堆类型. 堆由 `init_heap` 里初始化的 `embedded-alloc` 分配器支撑.

```rust
mod led;
mod platform;
mod uart;
```

这些声明把三个模块引入作用域. 每个模块都在自己的文件里 (`src/led.rs`, `src/platform.rs`, `src/uart.rs`).

### 导入

```rust
use core::panic::PanicInfo;
use embedded_alloc::LlffHeap as Heap;
use rp235x_hal as hal;
use wasmtime::component::{Component, HasSelf};
use wasmtime::{Config, Engine, Store};
```

`PanicInfo` 是传给 panic 处理程序的类型. `LlffHeap` 是为嵌入式系统设计的链表首次适配堆分配器. `hal` 是 RP2350 的硬件抽象层. Wasmtime 的导入引入了组件模型的核心类型: `Component` (预编译好的 Wasm 模块), `Engine` (执行环境), `Store` (每个实例的状态), 以及 `HasSelf` (用于链接器注册的标记类型).

### 生成 WIT 绑定

```rust
wasmtime::component::bindgen!({
    world: "blinky",
    path: "wit",
});
```

这个宏在编译期读取 WIT 文件, 为 `blinky` world 生成 Rust 类型和 trait. 它会生成:
- 一个 `Blinky` 结构体, 带有实例化组件和调用导出函数的方法
- 固件必须实现的 `embedded::platform::gpio::Host` 和 `embedded::platform::timing::Host` trait
- 表示组件导出项的 `Guest` 接口

### 全局分配器

```rust
#[global_allocator]
static HEAP: Heap = Heap::empty();
```

把堆分配器声明为全局静态变量. 它初始为空, 由 `init_heap` 用一块 256 KiB 的内存区域初始化. Wasmtime 大量使用堆 - 用于 `Store`, `Component` 元数据以及 Wasm 线性内存.

### 常量

```rust
const XOSC_CRYSTAL_FREQ: u32 = 12_000_000;
const HEAP_SIZE: usize = 262_144;
const WASM_BINARY: &[u8] = include_bytes!(concat!(env!("OUT_DIR"), "/blinky.cwasm"));
```

`XOSC_CRYSTAL_FREQ` 是用于配置 PLL 的外部晶振频率 (12 MHz). `HEAP_SIZE` 是 256 KiB - RP2350 512 KiB RAM 的一半, 另一半留给栈和 Wasmtime 的内部结构. `WASM_BINARY` 用 `include_bytes!` 在编译期把预编译好的 Pulley 字节码直接嵌进固件二进制. `.cwasm` 文件由 `build.rs` 生成.

### 启动元数据

```rust
#[unsafe(link_section = ".start_block")]
#[used]
pub static IMAGE_DEF: hal::block::ImageDef = hal::block::ImageDef::secure_exe();
```

RP2350 的引导 ROM 会在一个特殊的 `.start_block` 段里找元数据, 用来决定怎么启动. `secure_exe()` 告诉引导 ROM 这是一个安全的 ARM 可执行文件. `#[used]` 属性阻止链接器丢掉这个符号, 尽管代码里没有任何地方引用它. `#[unsafe(link_section)]` 是 Rust 2024 里把数据放进指定链接器段的语法.

### 宿主状态与 WIT 实现

```rust
struct HostState;
```

宿主状态就是 Wasmtime 的 `Store` 携带的那个 Rust 类型. WIT 宿主 trait 的实现都定义在这个结构体上. 在这个项目里它没有任何字段, 因为所有硬件访问都走全局静态变量 (`led::PINS`, `uart::UART`).

```rust
impl embedded::platform::gpio::Host for HostState {
    fn set_high(&mut self, pin: u32) {
        led::set_high(pin as u8);
        write_gpio_msg(pin as u8, true);
    }

    fn set_low(&mut self, pin: u32) {
        led::set_low(pin as u8);
        write_gpio_msg(pin as u8, false);
    }
}
```

这些是 WIT `gpio` 接口在宿主侧的实现. 当 Wasm 客体调用 `gpio::set_high(25)` 时, Wasmtime 把调用路由到这里. 函数委托给 `led::set_high` 去驱动物理 GPIO 引脚, 然后调用 `write_gpio_msg` 把状态变化记录到 UART.

```rust
impl embedded::platform::timing::Host for HostState {
    fn delay_ms(&mut self, ms: u32) {
        cortex_m::asm::delay(ms * 150_000);
    }
}
```

WIT `timing` 接口的实现. `cortex_m::asm::delay` 是一个数 CPU 周期的紧凑循环. 在 150 MHz (RP2350 默认的 PLL 频率) 下, `150_000` 个周期等于 1 毫秒. 在裸机上它比基于定时器的延时更可靠, 因为它不依赖定时器外设的配置.

### panic 处理程序

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

当任何代码 panic 时 (通过 `.unwrap()`, `.expect()`, `panic!` 等), 这个处理程序就会运行. 它用裸寄存器写从头重新初始化 UART0 (HAL 可能处于未知状态), 然后输出 panic 的位置和信息. 最后它用 `wfe` (Wait For Event) 进入死循环, 让 CPU 进入低功耗状态. 这对调试至关重要 - 如果没有可见的 panic 输出, 嵌入式目标上的崩溃就是隐形的.

### `init_heap`

```rust
fn init_heap() {
    use core::mem::MaybeUninit;
    static mut HEAP_MEM: [MaybeUninit<u8>; HEAP_SIZE] = [MaybeUninit::uninit(); HEAP_SIZE];
    unsafe { HEAP.init(&raw mut HEAP_MEM as usize, HEAP_SIZE) }
}
```

分配一块 256 KiB 的未初始化内存并交给堆分配器. `MaybeUninit` 告诉编译器这块内存不需要清零 - 节省启动时间. `unsafe` 块是必需的, 因为 `HEAP.init` 接收裸指针; 这是项目里少数几个无法避免的 `unsafe` 之一.

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

初始化 RP2350 的时钟树. 外部 12 MHz 晶振驱动两个 PLL: 系统 PLL (为 CPU 配置成 150 MHz) 和 USB PLL (为 USB 外设提供 48 MHz, 不过这里没用到 USB). 函数返回一个 `ClocksManager`, 为其他外设提供时钟频率信息 (比如 UART 的波特率计算).

### `write_gpio_msg`

```rust
fn write_gpio_msg(pin: u8, high: bool) {
    uart::write_msg(b"GPIO");
    let mut buf = [0u8; 3];
    let len = fmt_u8(pin, &mut buf);
    uart::write_msg(&buf[..len]);
    if high {
        uart::write_msg(b" On\n");
    } else {
        uart::write_msg(b" Off\n");
    }
}
```

格式化并通过 UART 发送类似 `GPIO25 On\n` 的消息. 它由 WIT `gpio` 宿主实现调用, 这样每次 LED 状态变化都能在串口控制台上看到. 这个函数避开 `format!` 以及任何需要 `std` 的字符串格式化 - 它改用 `fmt_u8` 手动把引脚编号转成 ASCII 数字.

### `fmt_u8`

```rust
fn fmt_u8(mut n: u8, buf: &mut [u8; 3]) -> usize {
    if n == 0 {
        buf[0] = b'0';
        return 1;
    }
    let mut i = 0;
    let mut tmp = [0u8; 3];
    while n > 0 {
        tmp[i] = b'0' + (n % 10);
        n /= 10;
        i += 1;
    }
    for j in 0..i {
        buf[j] = tmp[i - 1 - j];
    }
    i
}
```

把 `u8` 转成十进制 ASCII 表示, 不使用任何分配器或格式化机制. 它用取模和除法从右到左提取数字, 存进临时缓冲区, 再反转写入输出缓冲区. 返回写入的数字个数. 对于引脚 25, 它写入 `b"25"` 并返回 `2`.

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
    led::store_pin(25, pins.gpio25.into_push_pull_output());
}
```

这个函数初始化所有硬件. `Peripherals::take()` 是单例 - 只能调用一次, 防止多个驱动访问同一份硬件. 函数创建看门狗 (时钟初始化需要它), 配置时钟, 初始化用于 GPIO 访问的 SIO (Single-cycle IO), 并创建引脚结构体.

引脚分配只在这里发生. GPIO0 和 GPIO1 交给 UART. GPIO25 配置成推挽输出, 并以 25 号引脚的名义注册到 LED 驱动. 如果你想在 GPIO16 上再加一个 LED, 只需加一行: `led::store_pin(16, pins.gpio16.into_push_pull_output())`. 不需要改其他文件.

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

创建 Wasmtime 执行引擎. 这里的每一项设置都很关键, 必须和 `build.rs` 里构建期引擎的设置完全一致:

- `target("pulley32")` - 目标是 Pulley 32 位软件解释器, 而不是本机代码生成. Pulley 是 Wasmtime 的可移植字节码解释器, 能在任何架构上运行.
- `signals_based_traps(false)` - 关闭用于陷阱的 OS 信号处理. 这里没有 OS 来发信号.
- `memory_init_cow(false)` - 关闭写时复制的内存初始化. 这里没有虚拟内存系统.
- `memory_reservation(0)` - 关闭虚拟内存预留. RP2350 只有物理内存.
- `memory_guard_size(0)` - 关闭保护页. 没有虚拟内存就没有保护页.
- `memory_reservation_for_growth(0)` - 不预留增长空间.
- `guard_before_linear_memory(false)` - 线性内存前面不放保护页.
- `max_wasm_stack(16384)` - 把 Wasm 栈限制在 16 KiB, 以便塞进紧张的 RAM.

### `create_component`

```rust
fn create_component(engine: &Engine) -> Component {
    unsafe { Component::deserialize(engine, WASM_BINARY) }.expect("valid Pulley component")
}
```

反序列化由 `include_bytes!` 嵌入的预编译 Pulley 字节码. 这里需要 `unsafe`, 因为 `Component::deserialize` 信任这些字节是合法的 Wasmtime 序列化组件 - 而这是有保证的, 因为这些字节由我们自己的 `build.rs` 生成.

### `build_linker`

```rust
fn build_linker(engine: &Engine) -> wasmtime::component::Linker<HostState> {
    let mut linker = wasmtime::component::Linker::new(engine);
    Blinky::add_to_linker::<HostState, HasSelf<HostState>>(&mut linker, |state: &mut HostState| {
        state
    })
    .expect("register WIT interfaces");
    linker
}
```

创建组件链接器并注册所有 WIT 接口实现. `Blinky::add_to_linker` 由 `bindgen!` 生成, 它把 `HostState` 上的 `gpio::Host` 和 `timing::Host` trait 实现接到链接器上. `HasSelf<HostState>` 类型参数是 Wasmtime 内部使用的幽灵类型 - 闭包只是原样返回 `state`.

### `execute_wasm`

```rust
fn execute_wasm(
    store: &mut Store<HostState>,
    linker: &wasmtime::component::Linker<HostState>,
    component: &Component,
) {
    let blinky =
        Blinky::instantiate(&mut *store, component, linker).expect("instantiate component");
    blinky.call_run(&mut *store).expect("execute run");
}
```

实例化 Wasm 组件并调用导出的 `run` 函数. `Blinky::instantiate` 创建一个活的组件实例, 所有导入都已解析. `call_run` 调用客体的 `run` 函数, 后者进入无限的闪烁循环. 只有当 Wasm 客体的 `run` 函数返回时这个函数才会返回 - 而在这个项目里它永远不会返回.

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

编排 Wasm 运行时的启动. 创建引擎, 反序列化组件, 用宿主状态创建 store, 构建链接器, 然后执行 Wasm 组件. 末尾的 `loop` 是安全网 - `execute_wasm` 本不该返回, 因为客体的 `run` 函数会永远循环.

### `main`

```rust
#[hal::entry]
fn main() -> ! {
    init_heap();
    init_hardware();
    run_wasm()
}
```

固件入口点. `#[hal::entry]` 是 RP2350 HAL 的入口点属性 (构建在 `cortex-m-rt` 之上). 它设置栈指针和中断向量表, 然后调用这个函数. 启动顺序是: 初始化堆分配器, 初始化所有硬件外设, 然后启动 Wasm 运行时. `-> !` 返回类型表示这个函数永不返回 - Wasm 客体的闪烁循环会一直跑下去.

---

## 6. 构建脚本 (`build.rs`)

构建脚本在 `cargo build` 期间运行于 **宿主机** (你的开发电脑). 它编译 Wasm 客体应用, 并把它 AOT 编译成 Pulley 字节码, 这样设备上就不需要 Wasm 编译器了.

### 导入

```rust
use std::fs::File;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::Command;
use wasmtime::{Config, Engine};
use wit_component::ComponentEncoder;
```

和固件代码不同, 构建脚本使用完整标准库 (`std`). 它需要文件 I/O, 启动子进程, 以及带 Cranelift 代码生成的宿主侧 Wasmtime.

### `setup_output_dir`

```rust
fn setup_output_dir() -> PathBuf {
    let out = PathBuf::from(std::env::var_os("OUT_DIR").unwrap());
    println!("cargo:rustc-link-search={}", out.display());
    out
}
```

从 `OUT_DIR` 环境变量 (由 cargo 设置) 取得构建输出目录, 并把它注册为链接器搜索路径. 链接脚本 (`memory.x`) 和编译好的 Pulley 字节码 (`blinky.cwasm`) 都会被放在这里.

### `write_linker_script`

```rust
fn write_linker_script(out: &Path) {
    let memory_x = include_bytes!("rp2350.x");
    let mut f = File::create(out.join("memory.x")).unwrap();
    f.write_all(memory_x).unwrap();
}
```

把 RP2350 内存布局的链接脚本 (`rp2350.x`) 复制到输出目录, 命名为 `memory.x`. 链接脚本定义了 Flash (2 MiB) 和 RAM (512 KiB) 区域, 告诉链接器把代码, 数据和栈放在哪里. `cortex-m-rt` crate 的 `link.x` 脚本会自动包含 `memory.x`.

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

启动一个子 `cargo build` 进程来编译 Wasm 客体应用. 关键细节:

- `--target wasm32-unknown-unknown` 编译成 WebAssembly, 而不是宿主机架构.
- `.current_dir("wasm-app")` 在 Wasm 子 crate 的目录里执行构建.
- `.env_remove("CARGO_ENCODED_RUSTFLAGS")` 很关键 - 没有它, 父构建的 RUSTFLAGS (包含 `--nmagic` 和 `-Tlink.x` 这类 ARM 链接器标志) 会渗进子构建, 导致 Wasm 链接错误.

输出是一个核心 Wasm 模块, 位于 `wasm-app/target/wasm32-unknown-unknown/release/wasm_app.wasm`.

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

创建一个用于 AOT 交叉编译的 Wasmtime 引擎. 每一项设置都 **必须和** `src/main.rs` 里的 `create_engine` **完全一致**. Wasmtime 序列化组件时, 会把所有配置值嵌进 `.cwasm` 头部. 设备反序列化时, 会把每个值和运行时引擎逐项比较. 任何不匹配都会让 `Component::deserialize` 以一个晦涩的错误失败.

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
    std::fs::write(out.join("blinky.cwasm"), &serialized).expect("write Pulley bytecode");
}
```

这是 AOT 编译流水线的核心, 也是构建脚本里最重要的函数. 它做三次变换:

1. **读取核心 Wasm 模块** - 上一步 `cargo build` 产出的原始 `.wasm` 文件.
2. **编码成组件** - `ComponentEncoder` 读取 `wit-bindgen` 嵌在核心模块里的类型元数据, 把它包装成一个带类型化导入导出的正规 Wasm 组件.
3. **AOT 编译成 Pulley 字节码** - `precompile_component` 运行以 `pulley32` 架构为目标的 Cranelift (一个代码生成器), 产出序列化字节码, Pulley 解释器无需在设备上做任何编译就能执行它.

结果写入 `blinky.cwasm`, 固件通过 `include_bytes!` 把它包含进来.

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

告诉 cargo 哪些文件变化时应该重新运行构建脚本. 没有这些, cargo 可能缓存构建脚本的输出, 从而错过 Wasm 客体代码或 WIT 定义的改动.

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

构建脚本的入口点. 顺序是: 设置输出目录, 写链接脚本, 把 Wasm 客体编译成核心模块, 变换并 AOT 编译成 Pulley 字节码, 最后注册文件变化触发条件.

---

## 7. Wasm 客体应用 (`wasm-app/src/lib.rs`)

这就是运行在 RP2350 上 Wasmtime 运行时 **内部** 的 WebAssembly 组件. 它访问不到硬件 - 只能用宿主提供的 WIT 接口.

### crate 属性

```rust
#![no_std]
```

Wasm 客体是 `no_std` 的, 因为 `wasm32-unknown-unknown` 目标没有操作系统. 它用 `core` 提供语言原语, 用 `alloc` 提供堆.

```rust
extern crate alloc;
```

启用堆分配. 规范 ABI (宿主与客体之间的调用约定) 需要一个 `cabi_realloc` 函数, 好让宿主在客体的线性内存里分配内存. `wit-bindgen` crate 会生成这个函数, 而它需要一个能用的分配器.

### 全局分配器

```rust
#[global_allocator]
static ALLOC: dlmalloc::GlobalDlmalloc = dlmalloc::GlobalDlmalloc;
```

`dlmalloc` 是 Doug Lea 的 malloc 到 Rust 的移植. 它是 `no_std` 下唯一能在 `wasm32-unknown-unknown` 上工作的分配器, 因为它通过增长 Wasm 线性内存自己实现了 `sbrk`. `global` feature 开关让它成为 `#[global_allocator]`.

### 导入与绑定

```rust
use embedded::platform::{gpio, timing};
```

这些导入来自 `wit_bindgen::generate!` 生成的绑定. 它们提供 `gpio::set_high`, `gpio::set_low` 和 `timing::delay_ms` - 这些函数在 `world.wit` 里定义, 由宿主固件实现.

```rust
wit_bindgen::generate!({
    world: "blinky",
    path: "../wit",
});
```

这个宏在编译期读取 `wit/world.wit` 并生成客体侧绑定. 它创建 `embedded::platform::gpio` 和 `embedded::platform::timing` 两个模块, 里面的函数会调用宿主, 还生成一个组件必须实现的 `Guest` trait.

### 客体实现

```rust
struct BlinkyApp;

export!(BlinkyApp);
```

`BlinkyApp` 是实现 `blinky` world 客体侧的结构体. `export!` 宏 (由 `wit_bindgen` 生成) 把它注册为组件的实现, 并接好导出的 `run` 函数.

```rust
impl Guest for BlinkyApp {
    fn run() {
        const LED_PIN: u32 = 25;
        loop {
            gpio::set_high(LED_PIN);
            timing::delay_ms(500);
            gpio::set_low(LED_PIN);
            timing::delay_ms(500);
        }
    }
}
```

这就是全部的应用逻辑. 它以 500ms 的间隔在 GPIO25 上让 LED 闪烁, 循环无限. 每次调用 `gpio::set_high` 都会跨越 Wasm 边界 - Pulley 解释器暂停, Wasmtime 把调用派发给 `HostState::set_high`, 后者调用 `led::set_high(25)` 驱动物理引脚, 然后把控制权交回解释器.

引脚编号 (`25`) 是 **客体侧的决定**. WIT 接口与硬件无关 - 客体选择要控制哪个引脚, 宿主把它映射到真实硬件. 换一个客体就能闪另一个引脚, 固件一行都不用改.

### panic 处理程序

```rust
#[panic_handler]
fn panic(_info: &PanicInfo) -> ! {
    loop {
        core::hint::spin_loop();
    }
}
```

Wasm 客体的 panic 处理程序. 和固件的 panic 处理程序不同, 它没法往 UART 写 - 它没有硬件访问权限. 它只是用 `spin_loop()` (提示 CPU 在自旋时降低功耗) 进入死循环. 实际上, Wasm 客体里的 panic 会让 Wasmtime 触发陷阱, 最终由固件的 panic 处理程序接住.

---

## 小结: 完整执行流程

1. RP2350 上电, 引导 ROM 从 `.start_block` 读取 `IMAGE_DEF`
2. `main()` 调用 `init_heap()` 建立 256 KiB 的堆
3. `init_hardware()` 配置时钟 (150 MHz), UART0 (115200 波特率) 和 GPIO25 (推挽输出)
4. `run_wasm()` 创建 Pulley 引擎并反序列化预编译好的 Wasm 组件
5. `execute_wasm()` 实例化组件并调用 `run`
6. 客体的 `run()` 进入无限循环: `set_high(25)` -> `delay_ms(500)` -> `set_low(25)` -> `delay_ms(500)`
7. 每次 `set_high`/`set_low` 调用都跨越 Wasm 边界进入宿主, 驱动 LED, 并记录到 UART
8. 每次 `delay_ms` 调用都跨越边界, 按指定的 CPU 周期数自旋
9. LED 闪起来了. 永远.

## 文档链接

下面的参考资料覆盖了本项目用到的每一个主要 crate 和规范:

- [rp235x-hal](https://docs.rs/rp235x-hal) - RP2350 硬件抽象层 (GPIO, UART, 时钟)
- [Wasmtime](https://docs.wasmtime.dev) - WebAssembly 运行时文档 ([API 文档](https://docs.rs/wasmtime))
- [WIT / Component Model](https://component-model.bytecodealliance.org) - 组件模型规范 ([wit-bindgen API 文档](https://docs.rs/wit-bindgen))
- [cortex-m](https://docs.rs/cortex-m) - 底层 Cortex-M 访问 (中断, 寄存器, 内建函数)
- [cortex-m-rt](https://docs.rs/cortex-m-rt) - Cortex-M 启动运行时 (复位向量, 内存初始化)
- [embedded-hal](https://docs.rs/embedded-hal) - 硬件抽象 trait (GPIO, UART, SPI, I2C)
- [embedded-alloc](https://docs.rs/embedded-alloc) - 用于 `no_std` 环境的堆分配器
- [Cranelift](https://cranelift.dev) - 用于 AOT Wasm 编译的编译器后端 ([API 文档](https://docs.rs/cranelift-codegen))
- [Pulley](https://docs.rs/pulley-interpreter) - Wasmtime 可移植解释器的字节码格式
- [fugit](https://docs.rs/fugit) - 嵌入式用的类型安全时间单位 (波特率, 时钟频率)
- [critical-section](https://docs.rs/critical-section) - 跨平台的中断安全互斥

## 许可证

MIT
