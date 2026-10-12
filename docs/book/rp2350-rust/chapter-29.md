# Chapter 29: main.rs - UART 回显循环

## 引言

UART 驱动的 `main.rs` 把整个课程装进了一个文件: `no_std`
属性, 模块接线, 一个 `bind_interrupts!` 绑定, 用八个参数
构造出来的可配置 UART, 以及一个读字节, 变换字节,
再写出结果的异步循环. 它只有 87 行, 本章逐行
走一遍.

## 完整源代码

下面是 UART 驱动的 `src/main.rs` 的完整内容:

```rust
/*
 * @file main.rs
 * @brief Microcontroller entry point
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

//! FILE: main.rs
//!
//! DESCRIPTION:
//! RP2350 嵌入式 Rust Embassy UART 回显应用.
//!
//! BRIEF:
//! 使用 Embassy 的 RP2350 UART 回显驱动主程序入口.
//! 在 GPIO 0 (TX) 和 GPIO 1 (RX) 上实现异步 UART 字符回显.
//!
//! AUTHOR: Kevin Thomas
//! CREATION DATE: December 4, 2025
//! UPDATE DATE: December 5, 2025

#![no_std]
#![no_main]

mod config;
mod uart;

use config::UART_BAUD_RATE;
use embassy_executor::Spawner;
use embassy_rp::uart::{Config, Uart};
use embassy_rp::{bind_interrupts, peripherals::UART0, uart::InterruptHandler};
use panic_halt as _;
use uart::UartController;

bind_interrupts!(struct Irqs {
    UART0_IRQ => InterruptHandler<UART0>;
});

/// 主程序入口.
///
/// # Details
/// 初始化 Embassy 运行时, 并运行主 UART 回显循环.
/// 用 UartController 管理状态.
///
/// # Arguments
/// * `_spawner` - Embassy 任务 spawner (为将来的异步任务预留).
///
/// # Returns
/// * `()` - 永不返回 (无限循环).
#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let p = embassy_rp::init(Default::default());
    let mut config = Config::default();
    config.baudrate = UART_BAUD_RATE;
    let mut uart = Uart::new(
        p.UART0, p.PIN_0, p.PIN_1, Irqs, p.DMA_CH0, p.DMA_CH1, config,
    );
    let mut controller = UartController::new();
    let mut buf = [0u8; 1];
    loop {
        if uart.read(&mut buf).await.is_ok() {
            let echo_bytes = controller.process_char(buf[0]);
            let _ = uart.write(echo_bytes).await;
        }
    }
}
```

和前面几个驱动相比, 真正新鲜的东西有两处:
`bind_interrupts!` 块 (第 28 章) 以及 `Uart::new` 的参数列表.
循环本身比按钮驱动的还小.

## 导入与 IRQ 绑定

这些导入把 Embassy 的 UART 接口与控制器和配置配在一起:

```rust
use embassy_rp::uart::{Config, Uart};
use embassy_rp::{bind_interrupts, peripherals::UART0, uart::InterruptHandler};
```

接着是整个驱动所依赖的那一次宏调用:

```rust
bind_interrupts!(struct Irqs {
    UART0_IRQ => InterruptHandler<UART0>;
});
```

正如第 28 章演示的, 它创建了静态注册的 `Irqs`
绑定, 并把它交给 `Uart::new`. 它只写一次, 位置靠上, 在任何
执行发生之前 - 所以在这段连接关系上, 中断链在 `main` 开始之前就已经存在了.

## 构造 UART

八个参数, 四个概念分组:

```rust
let mut config = Config::default();
config.baudrate = UART_BAUD_RATE;
let mut uart = Uart::new(
    p.UART0,          // UART 外设令牌
    p.PIN_0,          // TX 引脚
    p.PIN_1,          // RX 引脚
    Irqs,             // 上面那个中断绑定
    p.DMA_CH0,        // DMA 控制器 0 (接收)
    p.DMA_CH1,        // DMA 控制器 1 (发送)
    config,           // 设置: 波特率 115200, 8N1
);
```

`Config::default()` 本身已经编码了一套合理的 UART 配置; 驱动只改了
一个字段 - `baudrate` - 而且取自配置模块. 引脚顺序 `(TX,
RX)` 与数据手册里的 `UART0_TX`/`UART0_RX` 命名一致 (第 26 章),
而两个 DMA 通道则补全了中断加 DMA 的故事. 九行之内
就完成了设置; 没有任何寄存器被手工碰过.

## 控制器与缓冲区

```rust
let mut controller = UartController::new();
let mut buf = [0u8; 1];
```

控制器跟踪回显统计. 缓冲区是栈上的一个字节 -
正好一个 RX 字节还在路上. Embassy 的 DMA 先写进它自己的
内部静态区, 再复制到这里, 所以一个大小为 1 的栈数组
就够这个应用用了.

## 回显循环

```rust
loop {
    if uart.read(&mut buf).await.is_ok() {
        let echo_bytes = controller.process_char(buf[0]);
        let _ = uart.write(echo_bytes).await;
    }
}
```

四步, 就是整个应用:

1. `uart.read(&mut buf).await` - 挂起直到有字节到来 (硬件
   中断加 DMA, 见第 28 章); `Ok` 表示 `buf` 里已经有一个字节.
2. `controller.process_char(buf[0])` - 把这个字节转换成要回显的字节, 并
   把计数加一 (第 27 章).
3. `uart.write(echo_bytes).await` - 发送, 并等待 FIFO 排空.
4. 循环 - 每一次暂停都被执行器吸收了; CPU 从未轮询过任何寄存器.

读操作的 `Result` 会被检查, 这样错误帧 (校验, 溢出, break) 就绝不会
进入回显 - 而写操作的结果则有意用 `let _` 丢弃掉,
以此说明在这一层无法从写满的线路中恢复.

在主机终端以 115200 运行这个驱动时, 每次按键都会立刻
返回, 退格键则会实实在在地擦掉前一个字符.

## 小结

- 导入加上一次 `bind_interrupts!`, 在任何东西跑起来之前就建立了
  UART 的 IRQ 链接.
- `Config` 加上带八个参数的 `Uart::new`, 用九行代码构造出整个 UART,
  相对默认值只改了波特率.
- 一个一字节的缓冲区和共享的控制器, 就是循环仅有的状态.
- 循环读, 变换, 写, 再重复 - 每次 `await` 都在睡觉.
- 读操作检查 `Ok`; 写操作则有意承认错误.

第 VI 部分结束. 最后一章把三个驱动组装成一个
完整的集成应用.