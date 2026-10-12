# Chapter 28: 中断与 DMA - 中断驱动的 UART

## 引言

UART 的 `read(...).await` 看起来像魔法: 字节落下来, future 就完成了,
没有浪费任何输入 - 因为硬件根本没有打扰 CPU. 让这一切成为可能的
是 RP2350 的两套机制: 中断, 它把 "来了一个字节" 送进
执行器; 以及 DMA, 它自己搬运字节. 本章把
`bind_interrupts!`, `InterruptHandler` 和 `main.rs` 里的两个 DMA 通道,
与驱动发出的那些 `await` 调用对应起来.

## CPU 会把整个循环浪费掉

**轮询**式的接收端会忙等, 不断采样状态位等一个字节到来,
把 CPU 百分之百地烧掉:

```
CPU:        [read status] [no] [read status] [no] [read status] [no] ...
UART RX:    ..... ......... came! ............................. (missed or
                                                              polled late)
```

这个驱动从不这么干. 它接好 UART 外设自己的信号, 这样只有当
确实有活干的时候, CPU 才会*被硬件*打断:

```
CPU:        [await]  ... [wakeup] echo [await] ... [wakeup] echo
UART RX:    ...... byte!   ...................  byte!  .........
```

中断让 CPU 可以在字节之间睡觉 (或者去跑别的任务); 这就是本设计中
中断驱动的那一半.

## bind_interrupts!

驱动只在一处告诉 Embassy, 哪个外设拥有哪条 IRQ 线:

```rust
use embassy_rp::{bind_interrupts, peripherals::UART0, uart::InterruptHandler};

bind_interrupts!(struct Irqs {
    UART0_IRQ => InterruptHandler<UART0>;
});
```

把这个宏块读出来: "RP2350 的 `UART0_IRQ` 向量会触发 `InterruptHandler`,
并把 `UART0` 外设令牌交给它." 这个宏会生成一个结构体 `Irqs`,
它把处理函数静态注册到向量表里, 并一直持有到
`embassy_rp::init` 为止. 当 FIFO 表示收到一个字节, 或者一次发送完成时,
`InterruptHandler` 会唤醒执行器里的 `Uart` future -
那正是这个 future 的就绪状态从 pending 翻到 ready 的确切时刻.

因为绑定是在宏那一行完成的 (不是运行时), 而且 `Irqs` 会被
`Uart::new` 消费掉, 这种连接关系在编译期就会被检查: IRQ 名字写错一个字母,
直接就无法构建.

## 两个 DMA 通道

`Uart::new` 在引脚之后还要两个外设:

```rust
let mut uart = Uart::new(
    p.UART0, p.PIN_0, p.PIN_1, Irqs, p.DMA_CH0, p.DMA_CH1, config,
);
```

`p.DMA_CH0` 和 `p.DMA_CH1` 是 RP2350 的两个 DMA 控制器. Embassy
把其中一个分给接收, 另一个分给发送, 一旦配置完成, DMA
引擎就自己驱动数据总线:

```
                in / out                           CPU: off doing math
Host <-> UART FIFO <--DMA0--< RAM (buf)   or   RAM (echo_bytes) -->DMA1--> UART FIFO
```

结果就是一个 **DMA UART**: 外设把字节交给内存缓冲区,
CPU 从头到尾都没复制过它们. 这就是本设计中 DMA 的那一半.

## 中断 + DMA + 异步 = 完整的故事

两半都落在同一个 `await` 里:

```rust
if uart.read(&mut buf).await.is_ok() { ... }
```

一步一步看:

1. Embassy 配置 `DMA_CH0`, 让它把下一个 RX 字节搬进 `buf[0]`, 然后
   走 "等待" 分支 - future 登记了自己的关注点.
2. DMA 引擎在没有 CPU 帮忙的情况下填好 `buf[0]` (在只请求
   一个字节的时候).
3. UART 触发 `UART0_IRQ`; 已注册的 `InterruptHandler` 把
   等待者标记为就绪.
4. 执行器恢复这个 future; `.await` 返回 `Ok`.

`write` 是对称的另一面: Embassy 配置 `DMA_CH1`, 让它把 `echo_bytes` 搬到
UART FIFO, DMA 把它抽干, 期间 CPU 一个寄存器都不用看, 而当 FIFO
排空时写 future 就完成了.

没有阻塞, 没有轮询, 没有手工复制 - 而这一整套安排
都是用看起来普普通通的 async 代码表达出来的.

## 错误路径

`read` 返回 `Result`, 而驱动不会悄悄丢弃任何东西:

```rust
if uart.read(&mut buf).await.is_ok() {
    let echo_bytes = controller.process_char(buf[0]);
    let _ = uart.write(echo_bytes).await;
}
```

读出错时这个字节就被跳过 - 这比回显一堆垃圾要安全. 写操作里的
`let _ = ...` 是在承认: 如果线被拔了, 我们并不做恢复. 将来的
驱动可以把这个错误记下来. Embassy 的错误类型 (溢出, break, 帧错误或
校验错误) 随时可用, 只要代码决定去关心它.

## 小结

- 用轮询的方式等 UART 会浪费 CPU; 中断只在某个字节
  真正重要时才唤醒它.
- `bind_interrupts!` 静态地把 `UART0_IRQ` 路由到
  `InterruptHandler<UART0>`, 并且有编译期检查.
- `DMA_CH0`/`DMA_CH1` 在 RAM 和 FIFO 之间搬运字节, 不需要 CPU 复制.
- 异步的 `read`/`write` 是这一切的融合: await, DMA 填充, IRQ 唤醒,
  future 完成.
- 返回 Result 的读操作, 让失控的错误不会变成无声的垃圾.

UART 驱动的收尾, 就是把这些全部接进 `main.rs`.