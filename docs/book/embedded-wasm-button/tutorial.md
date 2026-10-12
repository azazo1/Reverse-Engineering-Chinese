# 教程: 嵌入式 Wasm 按键 - 完整代码讲解

本教程逐行, 逐函数地讲解 **embedded-wasm-button-rp2350** 项目里的每一个 Rust 源文件. 读完你就能明白, 一个 WebAssembly 组件是怎样被编译, 部署, 并在 RP2350 微控制器上执行, 从而读取按键并控制 LED 的 - 全程都是裸机 Rust, 没有操作系统.

讲解按下面的顺序展开:

1. [WIT 接口定义](#1-wit-接口定义-witworldwit) - 客体与宿主之间的契约
2. [平台胶水层](#2-平台胶水层-srcplatformrs) - 给 Wasmtime 用的线程局部存储桩
3. [UART 驱动](#3-uart-驱动-srcuartrs) - 用于诊断的串口输出
4. [LED 驱动](#4-led-驱动-srcledrs) - GPIO 输出引脚管理
5. [按键驱动](#5-按键驱动-srcbuttonrs) - GPIO 输入引脚读取
6. [固件入口](#6-固件入口-srcmainrs) - 硬件初始化, Wasm 运行时, panic 处理器
7. [构建脚本](#7-构建脚本-buildrs) - AOT 编译流水线
8. [Wasm 客体应用](#8-wasm-客体应用-wasm-appsrclibrs) - 按键组件本身

---

## 1. WIT 接口定义 (`wit/world.wit`)

在写任何 Rust 代码之前, 项目先定义一个 **WIT (WebAssembly Interface Type)** 文件. WIT 是一种与语言无关的接口描述, WebAssembly 组件模型用它来对宿主 (固件) 与客体 (Wasm 模块) 之间的函数调用做类型检查.

```wit
package embedded:platform;
```

这一行声明了一个名为 `embedded:platform` 的 WIT 包. 包名采用 namespace:name 的约定. 这个包位于 `embedded` 命名空间下, 提供 `platform` 这一层的硬件抽象.

```wit
interface gpio {
    set-high: func(pin: u32);
    set-low: func(pin: u32);
}
```

`gpio` 接口定义了两个函数. `set-high` 接收引脚编号并把它打开. `set-low` 接收引脚编号并把它关掉. 引脚编号是 `u32`, 因为 WIT 的类型系统能干净地映射到 Wasm 的 32 位整数类型. 这两个函数是**导入项** - 客体调用它们, 宿主提供实现.

```wit
interface button {
    is-pressed: func(pin: u32) -> bool;
}
```

`button` 接口只定义了一个函数, 用来读取数字输入引脚. 客体传入引脚编号 (例如 `15`), 宿主返回按键当前是否被按下. 返回类型就是简单的 `bool` - 低电平有效那套逻辑 (上拉电阻, 按下时接地) 完全由宿主一侧处理, 所以客体看到的是一个干净的 "按下还是没按下" 抽象.

```wit
interface timing {
    delay-ms: func(ms: u32);
}
```

`timing` 接口提供一个阻塞式延时函数. 客体用毫秒数调用 `delay-ms`, 宿主就用 CPU 周期计数阻塞那么久.

```wit
world button-led {
    import gpio;
    import button;
    import timing;
    export run: func();
}
```

**world** 是一份完整的契约. `button-led` 这个 world 的意思是: "我需要宿主提供 `gpio`, `button` 和 `timing`, 而我会提供一个 `run` 函数." 宿主实例化组件, 调用 `run`, 之后 Wasm 代码就接管了 - 需要时再回调这三个接口. 这个 world 之所以叫 `button-led` 而不是 `button`, 是因为当 world 与它导入的某个接口同名时, WIT 会产生命名冲突 - 如果 world 自己也叫 `button`, `wit-bindgen` 就无法解析 `embedded::platform::button`. 带连字符的名字 `button-led` 在生成的 Rust 绑定里会变成 `ButtonLed`.

---

## 2. 平台胶水层 (`src/platform.rs`)

Wasmtime 最初是为桌面操作系统构建的, 那些系统由 OS 提供线程局部存储 (TLS). 在裸机微控制器上没有 OS, 所以我们必须自己提供 TLS. 这个文件是项目里最简单的 - 两个函数加一个静态变量.

### 导入

```rust
use core::ptr;
use core::sync::atomic::{AtomicPtr, Ordering};
```

`ptr` 提供 `null_mut()`, 用来初始化 TLS 的值. `AtomicPtr` 是一种原子指针类型, 可以在任何上下文中读写而不会产生数据竞争. 在单核 Cortex-M33 上, 原子操作并不是严格必需的, 但它们能满足 Rust 的类型系统, 让代码在构造上就是正确的.

### TLS 变量

```rust
static TLS_VALUE: AtomicPtr<u8> = AtomicPtr::new(ptr::null_mut());
```

这就是 TLS 实现的全部. Wasmtime 的运行时为每个线程保存一个指针. 由于 RP2350 只跑一个线程, 一个全局原子指针就够了. 它初始为 null, 在组件执行期间由 Wasmtime 设置.

### `wasmtime_tls_get`

```rust
#[unsafe(no_mangle)]
pub extern "C" fn wasmtime_tls_get() -> *mut u8 {
    TLS_VALUE.load(Ordering::Relaxed)
}
```

Wasmtime 按名字调用这个符号, 以取回当前线程的 TLS 指针. `#[unsafe(no_mangle)]` 属性 (Rust 2024 语法) 阻止编译器改写函数名, 这样 Wasmtime 的链接器就能找到它. `extern "C"` 表示使用 C 调用约定. `Ordering::Relaxed` 就够了, 因为只有一个线程 - 不需要相对其他线程的顺序保证.

### `wasmtime_tls_set`

```rust
#[unsafe(no_mangle)]
pub extern "C" fn wasmtime_tls_set(ptr: *mut u8) {
    TLS_VALUE.store(ptr, Ordering::Relaxed);
}
```

这是对应的 setter. Wasmtime 在执行 Wasm 代码之前调用它, 存入自己的运行时上下文指针; 执行结束时再清空 (存 null). 这两个函数合起来, 就是 Wasmtime 在裸机上运行所需的最小平台胶水层.

---

## 3. UART 驱动 (`src/uart.rs`)

UART 驱动通过 GPIO0 (TX) 和 GPIO1 (RX) 以 115200 波特率提供串口输出. 它存在的理由有两个: 正常运行时打诊断日志, 以及固件崩溃时输出 panic 信息. 这个模块被设计成一个**可共享, 即插即用**的驱动 - 不做任何修改就能放进任何 RP2350 项目.

### 模块头部

```rust
#![allow(dead_code)]
```

因为这个模块要在多个项目之间共享, 并不是每个项目都会用到每个函数. 比如按键项目从来不调用 `read_byte`. 这个属性用来抑制未使用函数的警告.

### 导入

```rust
use core::cell::RefCell;
use critical_section::Mutex;
use fugit::HertzU32;
use hal::Clock;
use nb::block;
use rp235x_hal as hal;
```

`RefCell` 提供内部可变性 - 让 UART 外设虽然住在静态变量里, 却能在运行时被可变借用. `critical_section` crate 的 `Mutex` 是裸机互斥锁, 靠关中断来防止数据竞争. `HertzU32` 是带类型的频率值, 避免单位混淆. `Clock` 是用来读取外设时钟频率的 trait. 导入 `nb::block` 把 `block!` 宏引入作用域, 它通过自旋把非阻塞操作变成阻塞操作. `hal` 这个别名指向 RP2350 的硬件抽象层.

### 常量

```rust
const UART0_BASE: u32 = 0x4007_0000;
```

UART0 外设在 RP2350 内存映射中的基地址. 只有 panic 处理器的裸寄存器访问函数会用到它 - 正常的基于 HAL 的函数不需要.

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

这个类型别名完整刻画了配置好的 UART 外设类型. HAL 用 Rust 的类型系统把外设状态编码进去: 它是 `Enabled` 的, 它是 `UART0` (不是 UART1), 它的 TX/RX 引脚是配成 UART 功能且不带上下拉电阻的 GPIO0 和 GPIO1. 这种类型层面的编码能防住运行时错误 - 你不可能把一个没配置的 UART 误传给期望已配置 UART 的函数.

### UART 全局存储

```rust
static UART: Mutex<RefCell<Option<Uart0>>> = Mutex::new(RefCell::new(None));
```

UART 外设被存放在一个全局静态变量里, 外面套着 critical-section 互斥锁. `Option` 一开始是 `None`, 初始化时被设成 `Some(uart)`. 这个 `Mutex<RefCell<Option<T>>>` 模式是嵌入式 Rust 里全局存放外设的标准安全写法, 完全避开了 `unsafe` 和裸指针.

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

这个函数接收原始 UART0 外设, 复位控制器, 时钟管理器, 以及**只**是它需要的那两个 GPIO 引脚. 这是刻意的设计决定: 函数不接收整个 `Pins` 结构体. 调用方 (`main.rs`) 拥有所有引脚, 只把 GPIO0 和 GPIO1 交给 UART. 这意味着项目里新增一个 GPIO 引脚时, 永远不需要改动这个模块.

引脚进来时是默认状态 (`FunctionNull`, `PullDown`), 在函数内部被重新配置:

```rust
    let uart_pins = (
        tx_pin.reconfigure::<hal::gpio::FunctionUart, hal::gpio::PullNone>(),
        rx_pin.reconfigure::<hal::gpio::FunctionUart, hal::gpio::PullNone>(),
    );
```

`reconfigure` 是一次零成本的类型层面状态转换. 它配置硬件寄存器, 并返回一个新类型, 证明这个引脚现在处于 UART 模式.

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

UART 外设在这里被创建, 配置成 115200 波特率, 8N1 帧格式 (8 位数据位, 无校验, 1 位停止位), 然后使能. 如果配置失败, `.expect()` 会带着说明性信息 panic - 而这种失败只可能发生在硬件处于异常状态时.

### `store_global`

```rust
pub fn store_global(uart: Uart0) {
    critical_section::with(|cs| {
        UART.borrow(cs).replace(Some(uart));
    });
}
```

`init` 返回配置好的 UART 之后, 调用方把它存进全局互斥锁, 这样任何代码 (包括 GPIO 状态日志) 都能往 UART0 写数据. `critical_section::with` 在闭包执行期间关中断, 获取互斥锁, 然后调用 `replace(Some(uart))` 把外设存进去.

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

这个函数用 HAL 把一段字节切片写进 UART0. 它先获取全局互斥锁, 借用 UART 外设, 然后逐字节写出. 把 `\n` 转成 `\r\n` 是为了让串口终端上的换行正确 - 这类终端期望每个换行符之前都有一个回车符.

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

这个函数会一直阻塞, 直到 UART 的 RX 线上来一个字节. `nb` crate 的 `block!` 宏会在非阻塞的 `read_raw` 调用上自旋, 直到它返回 `Ok`. 按键项目里用不到这个函数, 但因为模块要在多个项目间共享, 所以还是保留着 - UART 回显项目会用到它.

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

往 UART0 写一个字节. 和 `read_byte` 一样, 它主要是给这个共享模块家族里的其他项目用的.

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

这个函数用**裸寄存器写**从头重新初始化 UART0 - 不走 HAL. 为什么? 因为在 panic 期间, HAL 可能处于未知状态. UART 全局变量可能压根没初始化过. 分配器可能已经损坏. 唯一安全的做法就是直接和硬件对话.

每个常量都是指向某个硬件寄存器的指针. `RESET_CLR` 用于解除外设复位. `RESET_DONE` 报告外设是否已脱离复位. `GPIO0_CTRL` 和 `GPIO1_CTRL` 用来选择引脚功能 (UART). `UART*` 系列寄存器配置波特率, 数据格式, 并使能外设.

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

执行顺序是: 先往 atomic-clear 寄存器写入, 解除 IO_BANK0 (第 6 位) 和 UART0 (第 26 位) 的复位. 然后自旋等待, 直到两个外设都报告已脱离复位. 接着把 GPIO0 和 GPIO1 设成功能 2 (UART). 最后在默认的 150 MHz 外设时钟下, 把 UART 配置成 115200 波特率. 整数波特率除数 (81) 和分数除数 (24) 由下式算出: `150_000_000 / (16 * 115200) = 81.380`, 小数部分 `0.380 * 64 = 24.3 ≈ 24`. 线路控制寄存器设置 8 位数据位并使能 FIFO. 控制寄存器使能 UART, 发送器和接收器.

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

写一个字节: 先自旋等到 TX FIFO 有空位 (标志寄存器第 5 位是 "TX FIFO 满" 标志), 然后写数据寄存器. 这是 panic 处理器版的 `write_byte`, 用裸寄存器代替 HAL.

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

遍历一段字节切片, 逐字节写出, 同时做 `\n` 到 `\r\n` 的转换, 走的是裸寄存器路径. panic 处理器就是调用它来输出 panic 信息.

---

## 4. LED 驱动 (`src/led.rs`)

LED 驱动按硬件引脚编号来管理 GPIO 输出引脚. 它是为组件模型架构设计的: Wasm 客体说 "把 25 号引脚拉高", 宿主固件就在这个模块里查出 25 号引脚并把它拉高.

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

这个模块用堆分配 (`Box`, `BTreeMap`) 把引脚存成 trait 对象. `OutputPin` 是所有 GPIO 输出引脚都实现的 embedded-hal trait. `Infallible` 是不会失败的 GPIO 操作的错误类型 (RP2350 的 GPIO 总是成功).

```rust
type PinBox = Box<dyn OutputPin<Error = Infallible> + Send>;
```

这个类型别名定义了一个堆分配的, 类型擦除的 GPIO 引脚. 把引脚装进 trait 对象之后, 模块就能在不知道具体类型的情况下, 把任意 GPIO 引脚 (GPIO0, GPIO25 等等) 存进同一个集合. `Send` 约束是必需的, 因为这个静态变量会从中断安全的 critical section 里访问.

### 全局引脚存储

```rust
static PINS: Mutex<RefCell<BTreeMap<u8, PinBox>>> = Mutex::new(RefCell::new(BTreeMap::new()));
```

`BTreeMap` 把引脚编号 (例如 `25`) 映射到装箱后的 trait 对象. 这和 UART 模块用的是同一个 `Mutex<RefCell<...>>` 模式. 这里用 `BTreeMap` 而不是 `HashMap`, 是因为 `HashMap` 需要一个随机数生成器, 而 `no_std` 里没有.

### `store_pin`

```rust
pub fn store_pin(gpio_num: u8, pin: impl OutputPin<Error = Infallible> + Send + 'static) {
    critical_section::with(|cs| {
        PINS.borrow(cs).borrow_mut().insert(gpio_num, Box::new(pin));
    });
}
```

按硬件编号注册一个 GPIO 引脚. `impl OutputPin` 参数接受任意具体引脚类型 - 调用方不需要手动装箱. 在 critical section 内部, 引脚被装箱并插入映射表. `'static` 约束是必需的, 因为这张表住在静态变量里.

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

按编号查出引脚, 在 trait 对象上调用 `set_high()`, 并忽略 `Result` (它是 `Infallible` - 不可能失败). 如果有 Wasm 客体试图控制一个宿主从未注册过的引脚, `.expect("pin not registered")` 的 panic 信息能给出清晰的诊断.

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

和 `set_high` 一样, 只是把引脚拉低. `set_high` 和 `set_low` 合起来, 就是 WIT `gpio` 接口在宿主一侧的实现.

---

## 5. 按键驱动 (`src/button.rs`)

按键驱动是 LED 驱动的输入侧对应物. 它按硬件引脚编号管理 GPIO 输入引脚, 用的是同一套类型擦除引脚映射表模式. Wasm 客体问 "15 号引脚被按下了吗?", 宿主固件就在这个模块里查出 15 号引脚并读取它的状态.

### 导入与类型别名

```rust
extern crate alloc;

use alloc::boxed::Box;
use alloc::collections::BTreeMap;
use core::cell::RefCell;
use core::convert::Infallible;
use critical_section::Mutex;
use embedded_hal::digital::InputPin;
```

这个模块用和 LED 驱动一样的堆支撑集合模式. 关键区别在于导入的 trait: 这里是 `InputPin` 而不是 `OutputPin`. `InputPin` 提供 `is_high()` 和 `is_low()` 方法, 用来读取引脚状态.

```rust
type PinBox = Box<dyn InputPin<Error = Infallible> + Send>;
```

和 LED 驱动一样的类型擦除模式, 只不过针对输入引脚. `InputPin` trait 提供的读取操作在这个平台上不会失败 (`Error = Infallible`).

### 全局引脚存储

```rust
static PINS: Mutex<RefCell<BTreeMap<u8, PinBox>>> = Mutex::new(RefCell::new(BTreeMap::new()));
```

这是一张与 `led.rs` 分开的引脚映射表 - 输入引脚和输出引脚存放在不同模块的不同表里. 这样可以防止误把 `set_high` 用在输入引脚上, 或者误把 `is_pressed` 用在输出引脚上.

### `store_pin`

```rust
pub fn store_pin(gpio_num: u8, pin: impl InputPin<Error = Infallible> + Send + 'static) {
    critical_section::with(|cs| {
        PINS.borrow(cs).borrow_mut().insert(gpio_num, Box::new(pin));
    });
}
```

按硬件编号注册一个 GPIO 输入引脚. 在本项目里, `main.rs` 调用 `button::store_pin(15, pins.gpio15.into_pull_up_input())`. `into_pull_up_input()` 会配置内部上拉电阻 - 按键没按下时引脚读到高电平; 按下时引脚接地, 读到低电平.

### `is_pressed`

```rust
pub fn is_pressed(gpio_num: u8) -> bool {
    critical_section::with(|cs| {
        let map = PINS.borrow(cs);
        let mut map = map.borrow_mut();
        let pin = map.get_mut(&gpio_num).expect("pin not registered");
        pin.is_low().unwrap_or(false)
    })
}
```

读取引脚状态并返回按键是否被按下. 函数调用的是 `is_low()` 而不是 `is_high()`, 因为按键配上拉电阻时是低电平有效 - 按下按键就是把引脚接到地. `unwrap_or(false)` 用来处理 `Result<bool, Infallible>` - `Err` 分支永远不会执行, 但 `unwrap_or` 既避免了显式 `unwrap()`, 也表达了 "安全默认值" 的意图.

---

## 6. 固件入口 (`src/main.rs`)

这是最大的一个文件, 也是固件的心脏. 它初始化硬件, 搭起 Wasm 运行时, 并把 WIT 接口接到真实硬件上.

### crate 属性与模块声明

```rust
#![no_std]
#![no_main]
```

`no_std` 表示不用标准库 - 只有 `core` 和 `alloc`. `no_main` 表示没有标准的 `fn main()` - 入口由 `cortex-m-rt` 通过 `#[hal::entry]` 属性提供.

```rust
extern crate alloc;
```

启用 `alloc` crate, 它提供 `Vec`, `Box`, `String` 等堆类型. 堆由 `init_heap` 里初始化的 `embedded-alloc` 分配器支撑.

```rust
mod button;
mod led;
mod platform;
mod uart;
```

这几行声明把四个模块引入作用域. 每个模块各占一个文件 (`src/button.rs`, `src/led.rs`, `src/platform.rs`, `src/uart.rs`).

### 导入

```rust
use core::panic::PanicInfo;
use embedded_alloc::LlffHeap as Heap;
use rp235x_hal as hal;
use wasmtime::component::{Component, HasSelf};
use wasmtime::{Config, Engine, Store};
```

`PanicInfo` 是传给 panic 处理器的类型. `LlffHeap` 是为嵌入式系统设计的链表式首次适配堆分配器. `hal` 是 RP2350 的硬件抽象层. Wasmtime 的导入带来组件模型的核心类型: `Component` (预编译好的 Wasm 模块), `Engine` (执行环境), `Store` (每个实例的状态), 以及 `HasSelf` (链接器注册用的标记类型).

### 生成 WIT 绑定

```rust
wasmtime::component::bindgen!({
    world: "button-led",
    path: "wit",
});
```

这个宏在编译期读取 WIT 文件, 为 `button-led` 这个 world 生成 Rust 类型和 trait. 它会产出:
- 一个 `ButtonLed` 结构体, 带有实例化组件和调用导出函数的方法
- `embedded::platform::gpio::Host`, `embedded::platform::button::Host` 和 `embedded::platform::timing::Host` 三个 trait, 固件必须实现它们
- 一个 `Guest` 接口, 表示组件导出的内容

world 名 `button-led` 会以 PascalCase 变成 `ButtonLed`. 如果 world 叫 `button`, 就会和 `button` 接口撞名 - 这是 WIT 的一个限制.

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
const WASM_BINARY: &[u8] = include_bytes!(concat!(env!("OUT_DIR"), "/button.cwasm"));
```

`XOSC_CRYSTAL_FREQ` 是外部晶振频率 (12 MHz), 用于配置 PLL. `HEAP_SIZE` 是 256 KiB - RP2350 那 512 KiB RAM 的一半, 另一半留给栈和 Wasmtime 的内部结构. `WASM_BINARY` 用 `include_bytes!` 在编译期把预编译好的 Pulley 字节码直接嵌进固件二进制. 那个 `.cwasm` 文件由 `build.rs` 生成.

### 引导元数据

```rust
#[unsafe(link_section = ".start_block")]
#[used]
pub static IMAGE_DEF: hal::block::ImageDef = hal::block::ImageDef::secure_exe();
```

RP2350 的 启动 ROM 会在一个特殊的 `.start_block` 段里找元数据, 以决定怎么启动. `secure_exe()` 告诉 启动 ROM 这是一个安全的 ARM 可执行文件. `#[used]` 属性阻止链接器丢弃这个符号, 即使代码里没有任何地方引用它. `#[unsafe(link_section)]` 是 Rust 2024 里把数据放进指定链接器段的语法.

### 宿主状态与 WIT 实现

```rust
struct HostState;
```

宿主状态就是 Wasmtime 的 `Store` 所携带的那个 Rust 类型. WIT 的宿主 trait 实现都定义在这个结构体上. 在本项目里它没有字段, 因为所有硬件访问都走全局静态变量 (`led::PINS`, `button::PINS`, `uart::UART`).

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

这是 WIT `gpio` 接口在宿主一侧的实现. 当 Wasm 客体调用 `gpio::set_high(25)` 时, Wasmtime 会把调用转到这里. 函数转交给 `led::set_high` 去驱动物理 GPIO 引脚, 然后调用 `write_gpio_msg` 把状态变化通过 UART 记下来.

```rust
impl embedded::platform::button::Host for HostState {
    fn is_pressed(&mut self, pin: u32) -> bool {
        button::is_pressed(pin as u8)
    }
}
```

这是 WIT `button` 接口在宿主一侧的实现. 当 Wasm 客体调用 `button::is_pressed(15)` 时, Wasmtime 会把调用转到这里. 函数转交给 `button::is_pressed`, 它读取 GPIO15, 如果被按下 (低电平有效) 就返回 `true`. 按键读取不做 UART 日志, 免得 10ms 的轮询间隔把输出刷爆.

```rust
impl embedded::platform::timing::Host for HostState {
    fn delay_ms(&mut self, ms: u32) {
        cortex_m::asm::delay(ms * 150_000);
    }
}
```

这是 WIT `timing` 接口的实现. `cortex_m::asm::delay` 是一个数 CPU 周期的紧循环. 在 150 MHz (RP2350 默认的 PLL 频率) 下, `150_000` 个周期正好是 1 毫秒. 在裸机上, 这比基于定时器的延时更可靠, 因为它不依赖定时器外设的配置.

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

当任何代码 panic 时 (通过 `.unwrap()`, `.expect()`, `panic!` 等等), 这个处理器就会运行. 它先用裸寄存器写从头重新初始化 UART0 (HAL 可能处于未知状态), 然后输出 panic 的位置和信息. 最后进入一个用 `wfe` (Wait For Event) 的无限循环, 让 CPU 进入低功耗状态. 这对调试至关重要 - 没有可见的 panic 输出, 嵌入式目标上的崩溃就是隐形的.

### `init_heap`

```rust
fn init_heap() {
    use core::mem::MaybeUninit;
    static mut HEAP_MEM: [MaybeUninit<u8>; HEAP_SIZE] = [MaybeUninit::uninit(); HEAP_SIZE];
    unsafe { HEAP.init(&raw mut HEAP_MEM as usize, HEAP_SIZE) }
}
```

分配一块 256 KiB 的未初始化内存区域, 交给堆分配器. `MaybeUninit` 告诉编译器这块内存不需要清零 - 省下启动时间. `unsafe` 块是必需的, 因为 `HEAP.init` 接收裸指针; 这是项目里少数几处无法避免的 `unsafe`.

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

初始化 RP2350 的时钟树. 外部 12 MHz 晶振驱动两个 PLL: 系统 PLL (给 CPU 配到 150 MHz) 和 USB PLL (给 USB 外设的 48 MHz, 不过这里没用到 USB). 函数返回一个 `ClocksManager`, 它向其他外设提供时钟频率信息 (比如 UART 的波特率计算就要用到).

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

拼出并发送类似 `GPIO25 On\n` 的消息. 它由 WIT `gpio` 的宿主实现调用, 这样每次 LED 状态变化都能在串口终端上看到. 函数刻意避开 `format!` 或任何需要 `std` 的字符串格式化 - 它改用 `fmt_u8` 手工把引脚编号转成 ASCII 数字.

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

把一个 `u8` 转成它的十进制 ASCII 表示, 不用任何分配器或格式化机制. 它用取模和除法从右往左取出各位数字, 存进临时缓冲区, 再倒序写进输出缓冲区. 返回写出的数字个数. 对引脚 25 来说, 它写入 `b"25"` 并返回 `2`.

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
    uart::store_global(uart::init(
        pac.UART0, &mut pac.RESETS, &clocks, pins.gpio0, pins.gpio1,
    ));
    button::store_pin(15, pins.gpio15.into_pull_up_input());
    led::store_pin(25, pins.gpio25.into_push_pull_output());
}
```

这个函数初始化所有硬件. `Peripherals::take()` 是单例 - 只能调用一次, 防止多个驱动同时访问同一份硬件. 函数创建看门狗 (时钟初始化需要它), 配置时钟, 初始化用于 GPIO 访问的 SIO (单周期 IO), 并创建引脚结构体.

引脚的分配只在这里发生. GPIO0 和 GPIO1 归 UART. GPIO15 被配成上拉输入并注册到按键驱动 - 内部上拉意味着按键没按下时引脚读高电平, 接到地时读低电平. GPIO25 被配成推挽输出并注册到 LED 驱动. 如果你想在 GPIO14 上再加一个按键, 只要加一行: `button::store_pin(14, pins.gpio14.into_pull_up_input())`. 不需要改别的文件.

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

创建 Wasmtime 执行引擎. 这里的每一项设置都很关键, 必须和 `build.rs` 里构建期的引擎完全一致:

- `target("pulley32")` - 目标是 Pulley 32 位软件解释器, 而不是生成本机代码. Pulley 是 Wasmtime 的可移植字节码解释器, 能在任何架构上运行.
- `signals_based_traps(false)` - 关闭基于 OS 信号的陷入处理. 没有 OS 来发信号.
- `memory_init_cow(false)` - 关闭写时复制的内存初始化. 这里没有虚拟内存系统.
- `memory_reservation(0)` - 关闭虚拟内存预留. RP2350 只有物理内存.
- `memory_guard_size(0)` - 关闭保护页. 没有虚拟内存就没有保护页.
- `memory_reservation_for_growth(0)` - 不预留增长空间.
- `guard_before_linear_memory(false)` - 线性内存之前不放保护页.
- `max_wasm_stack(16384)` - 把 Wasm 栈限制在 16 KiB, 以适应紧张的 RAM.

### `create_component`

```rust
fn create_component(engine: &Engine) -> Component {
    unsafe { Component::deserialize(engine, WASM_BINARY) }.expect("valid Pulley component")
}
```

反序列化由 `include_bytes!` 嵌入的预编译 Pulley 字节码. 这里需要 `unsafe`, 因为 `Component::deserialize` 信任这些字节是一份合法的 Wasmtime 序列化组件 - 这一点由我们的 `build.rs` 保证, 因为字节就是它生成的.

### `build_linker`

```rust
fn build_linker(engine: &Engine) -> wasmtime::component::Linker<HostState> {
    let mut linker = wasmtime::component::Linker::new(engine);
    ButtonLed::add_to_linker::<HostState, HasSelf<HostState>>(&mut linker, |state: &mut HostState| {
        state
    })
    .expect("register WIT interfaces");
    linker
}
```

创建组件链接器并注册所有 WIT 接口实现. `ButtonLed::add_to_linker` 由 `bindgen!` 生成, 它把 `HostState` 上的 `gpio::Host`, `button::Host` 和 `timing::Host` trait 实现接到链接器上. `HasSelf<HostState>` 类型参数是 Wasmtime 内部使用的幻影类型 - 那个闭包只是把 `state` 原样返回.

### `execute_wasm`

```rust
fn execute_wasm(
    store: &mut Store<HostState>,
    linker: &wasmtime::component::Linker<HostState>,
    component: &Component,
) {
    let instance =
        ButtonLed::instantiate(&mut *store, component, linker).expect("instantiate component");
    instance.call_run(&mut *store).expect("execute run");
}
```

实例化 Wasm 组件并调用导出的 `run` 函数. `ButtonLed::instantiate` 创建组件的一个活实例, 所有导入都已解析完毕. `call_run` 调用客体的 `run` 函数, 后者进入无限的按键轮询循环. 只有当 Wasm 客体的 `run` 函数返回时, 这个函数才会返回 - 而在本项目里它永远不会返回.

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

编排 Wasm 运行时的启动过程. 创建引擎, 反序列化组件, 用宿主状态创建 store, 构建链接器, 然后执行 Wasm 组件. 末尾那个 `loop` 是一道保险 - `execute_wasm` 本不该返回, 因为客体的 `run` 函数会永远循环下去.

### `main`

```rust
#[hal::entry]
fn main() -> ! {
    init_heap();
    init_hardware();
    run_wasm()
}
```

固件入口. `#[hal::entry]` 是 RP2350 HAL 的入口点属性 (构建在 `cortex-m-rt` 之上). 它负责设置栈指针和向量表, 然后调用这个函数. 启动顺序是: 初始化堆分配器, 初始化所有硬件外设, 然后启动 Wasm 运行时. `-> !` 返回类型表示这个函数永不返回 - Wasm 客体的按键轮询循环会一直跑下去.

---

## 7. 构建脚本 (`build.rs`)

构建脚本在 `cargo build` 期间运行于**宿主机器** (你的开发电脑) 上. 它编译 Wasm 客体应用, 并把它 AOT 编译成 Pulley 字节码, 这样设备端就不需要 Wasm 编译器了.

### 导入

```rust
use std::fs::File;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::Command;
use wasmtime::{Config, Engine};
use wit_component::ComponentEncoder;
```

和固件代码不同, 构建脚本使用完整的标准库 (`std`). 它需要文件 IO, 创建子进程, 以及带 Cranelift 代码生成的宿主侧 Wasmtime.

### `setup_output_dir`

```rust
fn setup_output_dir() -> PathBuf {
    let out = PathBuf::from(std::env::var_os("OUT_DIR").unwrap());
    println!("cargo:rustc-link-search={}", out.display());
    out
}
```

从 `OUT_DIR` 环境变量 (由 cargo 设置) 取出构建输出目录, 并把它注册为链接器搜索路径. 链接脚本 (`memory.x`) 和编译好的 Pulley 字节码 (`button.cwasm`) 都会放在这里.

### `write_linker_script`

```rust
fn write_linker_script(out: &Path) {
    let memory_x = include_bytes!("rp2350.x");
    let mut f = File::create(out.join("memory.x")).unwrap();
    f.write_all(memory_x).unwrap();
}
```

把描述 RP2350 内存布局的链接脚本 (`rp2350.x`) 复制到输出目录, 命名为 `memory.x`. 这个链接脚本定义 Flash (2 MiB) 和 RAM (512 KiB) 两个区域, 并告诉链接器把代码, 数据和栈放在哪里. `cortex-m-rt` crate 的 `link.x` 脚本会自动包含 `memory.x`.

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

派生一个子 `cargo build` 进程来编译 Wasm 客体应用. 几个关键点:

- `--target wasm32-unknown-unknown` 表示编译成 WebAssembly, 而不是宿主架构.
- `.current_dir("wasm-app")` 让构建在 Wasm 子 crate 的目录里进行.
- `.env_remove("CARGO_ENCODED_RUSTFLAGS")` 很关键 - 不这样做的话, 父构建的 RUSTFLAGS (里面有 `--nmagic` 和 `-Tlink.x` 这类 ARM 链接器参数) 会漏进子构建, 导致 Wasm 链接错误.

产物是一个核心 Wasm 模块, 位于 `wasm-app/target/wasm32-unknown-unknown/release/wasm_app.wasm`.

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

创建一个用于 AOT 交叉编译的 Wasmtime 引擎. 每一项设置都**必须和** `src/main.rs` 里的 `create_engine` **完全一致**. Wasmtime 序列化组件时, 会把所有配置值写进 `.cwasm` 的头部. 设备反序列化时, 会把每个值拿来和运行时的引擎比对. 只要有一处不匹配, `Component::deserialize` 就会以一个含义晦涩的错误失败.

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
    std::fs::write(out.join("button.cwasm"), &serialized).expect("write Pulley bytecode");
}
```

这是 AOT 编译流水线的核心, 也是构建脚本里最重要的函数. 它做三次转换:

1. **读取核心 Wasm 模块** - 上一步里 `cargo build` 产出的原始 `.wasm` 文件.
2. **编码成组件** - `ComponentEncoder` 读取 `wit-bindgen` 嵌在核心模块里的类型元数据, 把它包装成一个带类型化导入导出的正式 Wasm 组件.
3. **AOT 编译成 Pulley 字节码** - `precompile_component` 以 `pulley32` 架构为目标运行 Cranelift (一个代码生成器), 产出序列化字节码, 让 Pulley 解释器在设备上无需任何编译就能执行.

结果写到 `button.cwasm`, 固件再用 `include_bytes!` 把它包含进来.

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

告诉 cargo 哪些文件变化时应该重新运行构建脚本. 没有这几行, cargo 可能会缓存构建脚本的输出, 从而漏掉 Wasm 客体代码或 WIT 定义的改动.

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

构建脚本的入口. 顺序是: 准备好输出目录, 写入链接脚本, 把 Wasm 客体编译成核心模块, 再转换并 AOT 编译成 Pulley 字节码, 最后登记文件变化触发条件.

---

## 8. Wasm 客体应用 (`wasm-app/src/lib.rs`)

这就是跑在 RP2350 上 Wasmtime 运行时**内部**的那个 WebAssembly 组件. 它碰不到硬件 - 只能通过宿主提供的 WIT 接口间接访问.

### crate 属性

```rust
#![no_std]
```

Wasm 客体是 `no_std` 的, 因为 `wasm32-unknown-unknown` 目标没有操作系统. 它用 `core` 提供语言原语, 用 `alloc` 提供堆.

```rust
extern crate alloc;
```

启用堆分配. 规范 ABI (宿主与客体之间的调用约定) 要求有一个 `cabi_realloc` 函数, 好让宿主在客体的线性内存里分配内存. `wit-bindgen` crate 会生成这个函数, 而它需要有一个能用的分配器可调.

### 全局分配器

```rust
#[global_allocator]
static ALLOC: dlmalloc::GlobalDlmalloc = dlmalloc::GlobalDlmalloc;
```

`dlmalloc` 是 Doug Lea 的 malloc 到 Rust 的移植. 它是 `no_std` 下唯一能在 `wasm32-unknown-unknown` 上工作的分配器, 因为它通过扩展 Wasm 线性内存自己实现了 `sbrk`. `global` feature 标志让它能当 `#[global_allocator]`.

### 导入与绑定

```rust
use embedded::platform::{button, gpio, timing};
```

这些导入来自 `wit_bindgen::generate!` 生成的绑定. 它们提供 `button::is_pressed`, `gpio::set_high`, `gpio::set_low` 和 `timing::delay_ms` - 也就是 `world.wit` 里定义, 由宿主固件实现的那几个函数.

```rust
wit_bindgen::generate!({
    world: "button-led",
    path: "../wit",
});
```

这个宏在编译期读取 `wit/world.wit` 并生成客体侧的绑定. 它创建 `embedded::platform::gpio`, `embedded::platform::button` 和 `embedded::platform::timing` 三个模块, 里面的函数会调到宿主去; 同时还生成一个 `Guest` trait, 组件必须实现它.

### 客体实现

```rust
struct ButtonApp;

export!(ButtonApp);
```

`ButtonApp` 就是实现 `button-led` world 客体侧的那个结构体. `export!` 宏 (由 `wit_bindgen` 生成) 把它注册为组件的实现, 并把导出的 `run` 函数接好线.

```rust
impl Guest for ButtonApp {
    fn run() {
        const BUTTON_PIN: u32 = 15;
        const LED_PIN: u32 = 25;
        loop {
            if button::is_pressed(BUTTON_PIN) {
                gpio::set_high(LED_PIN);
            } else {
                gpio::set_low(LED_PIN);
            }
            timing::delay_ms(10);
        }
    }
}
```

这就是应用逻辑的全部. 它每 10ms 轮询一次 GPIO15 上的按键, 并把状态镜像到 GPIO25 上的 LED. 每一次 `button::is_pressed` 或 `gpio::set_high` 调用都要跨过 Wasm 边界 - Pulley 解释器暂停, Wasmtime 把调用分派给 `HostState` 上对应的方法, 方法读取或驱动物理引脚, 然后把控制权交回解释器.

引脚编号 (`15` 和 `25`) 是**客体侧的决定**. WIT 接口与硬件无关 - 客体自己选用哪些引脚, 宿主负责把它们映射到真实硬件. 换一个客体用别的引脚, 固件完全不用改. 10ms 的轮询间隔提供了基本的消抖 - 机械按键的抖动大约持续 5-20ms, 而 10ms 的轮询周期意味着抖动不太可能造成肉眼可见的闪烁.

### panic 处理器

```rust
#[panic_handler]
fn panic(_info: &PanicInfo) -> ! {
    loop {
        core::hint::spin_loop();
    }
}
```

Wasm 客体的 panic 处理器. 和固件的 panic 处理器不同, 它不能往 UART 写东西 - 它没有硬件访问权限. 它只是用一个 `spin_loop()` (提示 CPU 在自旋时降低功耗) 进入无限循环. 实际上, Wasm 客体里的 panic 会让 Wasmtime 陷入, 而这个陷入会被固件的 panic 处理器捕获.

---

## 小结: 完整的执行流程

1. RP2350 上电, 启动 ROM 从 `.start_block` 读取 `IMAGE_DEF`
2. `main()` 调用 `init_heap()` 建立 256 KiB 的堆
3. `init_hardware()` 配置时钟 (150 MHz), UART0 (115200 波特率), GPIO15 (上拉输入) 和 GPIO25 (推挽输出)
4. `run_wasm()` 创建 Pulley 引擎, 并反序列化预编译好的 Wasm 组件
5. `execute_wasm()` 实例化组件并调用 `run`
6. 客体的 `run()` 进入无限循环: `is_pressed(15)` -> `set_high(25)` 或 `set_low(25)` -> `delay_ms(10)`
7. 每次 `is_pressed` 调用都跨过 Wasm 边界进入宿主, 读取 GPIO15, 返回一个 `bool`
8. 每次 `set_high`/`set_low` 调用都跨过边界, 驱动 LED, 并往 UART 记一条日志
9. 每次 `delay_ms` 调用都跨过边界, 按指定的 CPU 周期数自旋
10. 按键控制 LED. 永远.

## 文档链接

下面这些参考资料覆盖了本项目用到的每一个主要 crate 和规范:

- [rp235x-hal](https://docs.rs/rp235x-hal) - RP2350 硬件抽象层 (GPIO, UART, 时钟)
- [Wasmtime](https://docs.wasmtime.dev) - WebAssembly 运行时文档 ([API 文档](https://docs.rs/wasmtime))
- [WIT / 组件模型](https://component-model.bytecodealliance.org) - 组件模型规范 ([wit-bindgen API 文档](https://docs.rs/wit-bindgen))
- [cortex-m](https://docs.rs/cortex-m) - 底层 Cortex-M 访问 (中断, 寄存器, 内建函数)
- [cortex-m-rt](https://docs.rs/cortex-m-rt) - Cortex-M 启动运行时 (复位向量, 内存初始化)
- [embedded-hal](https://docs.rs/embedded-hal) - 硬件抽象 trait (GPIO, UART, SPI, I2C)
- [embedded-alloc](https://docs.rs/embedded-alloc) - 面向 `no_std` 环境的堆分配器
- [Cranelift](https://cranelift.dev) - 用于 AOT Wasm 编译的编译器后端 ([API 文档](https://docs.rs/cranelift-codegen))
- [Pulley](https://docs.rs/pulley-interpreter) - Wasmtime 的可移植解释器字节码格式
- [fugit](https://docs.rs/fugit) - 面向嵌入式的类型安全时间单位 (波特率, 时钟频率)
- [critical-section](https://docs.rs/critical-section) - 跨平台的中断安全互斥

## 许可证

MIT
