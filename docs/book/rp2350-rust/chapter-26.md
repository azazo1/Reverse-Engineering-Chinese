# Chapter 26: UART 基础与回显协议

## 引言

UART (Universal Asynchronous Receiver/Transmitter, 通用异步收发器) 是在两个系统之间
搬运字节最古老, 最简单, 也最通用的方式. RP2350 天生带有
UART0 和 UART1; UART 驱动使用 UART0, 接在 GPIO0 (TX) 和 GPIO1 (RX) 上,
构建一个**回显终端**: 你输入的每个字符都会回显给你, 而
退格键会擦掉前一个字符. 本章先把协议,
接线和设计讲清楚, 然后再看代码.

## 协议

UART 在一对没有时钟的共享线上, 一次一位地发送字节.
"异步" 意味着没有时钟线: 两端必须提前就速度和
帧格式达成一致.

一个数据帧长这样:

```
| START |  D0  |  D1  |  D2  |  D3  |  D4  |  D5  |  D6  |  D7  | STOP |
|   0   | lsb  |  .   |  .   |  .   |  .   |  .   |  .   | msb  |  1   |
```

- 空闲时线路为高电平.
- START 把它拉低一个位时间 - 这就是给接收端的触发信号.
- 接着是八个数据位, 最低位在前.
- STOP 把线路恢复成高电平.

RP2350 带有两个 UART; 驱动用的是 UART0. 它的引脚是:

```
+-------------------------------+
|         RP2350 Pico 2         |
|                               |
|  GPIO0  -------- UART0_TX     |----> to USB-serial (TX -> RX)
|  GPIO1  -------- UART0_RX     |<---- from host (RX -> TX)
|                               |
+-------------------------------+
  Host terminal @ 115200 8N1
```

因为 Pico 上的 Linux 终端是通过 USB-UART 桥接芯片访问的,
所以引脚要交叉: 芯片的 **TX** 接到桥接芯片的 **RX**, 而它的 **RX** 接
桥接芯片的 **TX**. 因此驱动按 `(TX, RX)` 的顺序声明引脚:

```rust
Uart::new(p.UART0, p.PIN_0, p.PIN_1, Irqs, p.DMA_CH0, p.DMA_CH1, config);
```

## 波特率与 8N1

唯一的握手就是时序. 两端必须就位时钟 - 也就是
**波特率** - 和帧格式达成一致. 协议简写 **8N1** 读作 "八个
数据位, 无校验, 一个停止位", 在 115200 波特下, 一个位持续约 8.7 µs.

这个速率在 `config.rs` 里是一个带文档的常量, 这样终端和
固件就不会因为疏忽而不一致:

```rust
/// 默认 UART 波特率.
///
/// # Details
/// 配置 UART 的通信速度.
/// 串口通信的标准波特率.
///
/// # Value
/// 115200 波特
#[allow(dead_code)]
pub const UART_BAUD_RATE: u32 = 115200;
```

在主机这一侧, 对应的命令是 `stty -F /dev/ttyACM0 115200 raw -echo`. 固件需要的
每一个运行时旋钮 - 波特率, 退格的表示方式, 擦除用的
字节序列 - 都放在 `config.rs` 里, 所以调节 UART 从来不需要改动逻辑.

## 回显协议

终端就是一根不会思考的线加上一块屏幕: 它把每次按键作为一个字节发出去,
然后指望对面把它回显回来, 这样用户就能看到自己打了什么. 这个
驱动的协议是一份很小的 ASCII 契约:

```
Host sends            Firmware echoes
---------------       ---------------
'A'                   'A'
backspace (0x08)      backspace + space + backspace   (erase)
delete    (0x7F)      backspace + space + backspace   (erase)
'n' etc.              itself
unknown (0x01)        nothing
```

为什么擦除要用三个字节? 终端的光标停在已打印字符的右边.
要删掉它, 固件必须先把光标左移 (退格), 打印一个空格盖住
这个字母, 然后为了让下次擦除还能生效再左移一次.
`config.rs` 把这个序列打包定义了一次:

```rust
/// 退格擦除序列: 退格, 空格, 退格.
///
/// # Details
/// 回显到终端时, 这个序列会擦掉前一个字符.
///
/// # Value
/// [0x08, b' ', 0x08]
#[allow(dead_code)]
pub const BACKSPACE_SEQ: [u8; 3] = [0x08, b' ', 0x08];
```

ASCII 匹配需要考虑退格键的两种写法 (`BACKSPACE = 0x08` 和
`DELETE = 0x7F`), 因为不同终端对于退格键产生哪个字节
并不一致. 固件把两者都当作擦除 - 而这个 `match` 依然是
穷尽的, 因为 `process_char` 对别的一切都回退到 `b""`.

## 异步接收与发送

UART 驱动的 `main` 用 async 的 `await` 一次读一个字节:

```rust
if uart.read(&mut buf).await.is_ok() {
    let echo_bytes = controller.process_char(buf[0]);
    let _ = uart.write(echo_bytes).await;
}
```

等待期间, `.await` 会让出给执行器 - CPU 是空闲的. 而在
幕后, 硬件几乎包办了一切:

- **中断** - 有新数据时, UART 外设会触发 `UART0_IRQ`;
  `InterruptHandler<UART0>` 把它转成执行器的唤醒事件.
- **DMA** - `p.DMA_CH0` 和 `p.DMA_CH1` 让两个 DMA 控制器在内存和
  UART FIFO 之间搬运字节, 完全不需要 CPU 参与.

这两者的配合是第 28 章的主题. 就协议而言, 重要的是那层
干净的异步表面: `read` 一直睡到有字节落下, `write` 一直睡到
字节冲刷完毕.

## 控制器的角色

和每个驱动一样, 一个纯粹的, 可测试的控制器承载逻辑, 并在主机上
接受测试. `UartController` 只保留一个计数器 - `echo_count` - 并把
每个输入字节映射成必须回显的字节:

```
+------------+     +-----------------+     +-----------------+
| UART rx    | --> | UartController  | --> | bytes to       |
| byte       |     | process_char    |     | echo back (TX) |
+------------+     +-----------------+     +-----------------+
```

任何关于 RPC 设备或 FIFO 的东西都没有渗进这个控制器; 它就是一个
从 `u8` 到 `&'static [u8]` 的函数, 外加一个累计总数. 正是这种纯粹性
让一套二十个测试成为可能.

## 小结

- UART 是一种两线, 无时钟, 逐字节的协议; RP2350 提供
  UART0/UART1, 而驱动使用接在 GPIO0 (TX) 和 GPIO1 (RX) 上的 UART0.
- 两端通过 `UART_BAUD_RATE` 就帧格式 - 115200 8N1 - 达成一致.
- 回显协议把按键映射成响应: 原样回显, 对两种退格写法都用三字节
  擦除, 对未知字节则保持沉默.
- 异步的 `read`/`write` 暂停的是执行器而不是 CPU, 与此同时由中断和
  DMA 完成物理层面的工作.
- 可测试的核心是 `process_char`, 一个从字节到响应的纯函数.

接下来是状态机本身 - `uart.rs`.