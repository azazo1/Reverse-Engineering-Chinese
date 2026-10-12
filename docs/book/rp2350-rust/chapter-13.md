# Chapter 13: future 与 async/await

## 引言

`async` 和 `await` 看起来像魔法, 其实它们只由一个诚实的原语搭起来:
**future** - 一个代表 "还没做完的工作" 的值. 理解了 future, 就理解了
`.await` 在做什么, 也就理解了 Embassy 的核心. 本章把每个关键字
还原成真正执行的东西.

## future 是什么?

`Future` 是一个只有一个方法的 Rust trait:

```rust
pub trait Future {
    type Output;
    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output>;
}
```

有三件事对我们很重要:

- future 有一个 **Output** 类型 - 就是它最终产出的值
  (`Timer` 产出 `()`, read 产出一个 `Result`).
- 调用 `poll` 会让它向前推进. future 要么返回 `Ready(output)` -
  表示完成 - 要么返回 `Pending` - 表示在等某样东西, 待会再来.
- future 是一个 **状态机**, 不是线程. 它占一个固定大小的
  结构体, 除了 `.await` 的记账之外不存别的东西.

这就是 future 在单片机上很便宜的原因: 没有线程栈, 没有堆,
没有内核. 每个 `.await` 只是执行器持有的那个小结构体里的一个状态.

## 轮询

当 future 返回 `Pending` 时, 是什么让它再次运行? 必须有某个东西
在它的条件满足后再次调用 `poll`. 在 Embassy 里, 这个 "某个东西" 就是
执行器 (第 14 章), 由硬件中断唤醒. future 被轮询,
发现自己的条件现在为真, 于是返回 `Ready`.

```
poll #1  ->  Pending        (need the timer to tick)
               ...CPU sleeps, interrupt fires...
poll #2  ->  Ready(())      (500 ms elapsed, yield the result)
```

`Pending` 这次状态转换的代价是零硬件开销: future 只是
记下 "我在等", 然后返回. 机器在睡觉时一点东西都不烧.

## 状态机

编译器会把一个 `async fn` 变成一个结构体, 每个局部变量占一个字段,
每个 `.await` 点占一个内部状态:

```rust
async fn blink_once() {
    led.set_high();                     // 状态 S0
    Timer::after_millis(500).await;     // 状态 S1 (挂起在这里)
    led.set_low();                      // 状态 S2
}
```

概念上就是:

```
S0: set high, build the Timer future, poll it  -> enter S1
S1: Timer pending?  -> stay S1.  Timer ready?  -> S2
S2: set low, return Ready
```

定时器上的 `.await` 变成了 "轮询定时器; 如果 Pending, 就保存我的状态并
返回 Pending." 再次被轮询时, 执行会正好从那个 `.await` 处恢复,
而不是从函数顶部. 这种接续式的恢复就是 async 魔法的全部.

## async 与 await

- **`async fn`** - 声明一个返回 future 的函数; 函数体只有在
  这个 future 被轮询时才运行, 而不是在函数被调用时.
- **`.await`** - 把内层 future 一直轮询到完成, 如果内层处于 `Pending`,
  就把外层 future 挂起. `.await` 只能用在
  `async` 上下文 **内部**.

```rust
async fn routine() {
    set_led_high();
    Timer::after_millis(500).await;   // 在这里挂起 500 ms
    set_led_low();
}
```

`Timer::after_millis(500)` *返回一个 future*; 是 `.await` 在驱动它. 少了
`.await`, 这个 future 会被创建后又立刻丢弃, 计时永远不会开始,
结果什么也不会发生 - 这是个经典 bug, 修起来却很干净.

你不能从 `main` 里 `.await`, 除非 `main` 本身是 async, 而且有一个执行器
去轮询它. 这正是为什么每个驱动都写
`#[embassy_executor::main] async fn main(...)`: 这个属性挂上了一个
执行器, 好让这个 `async fn` 有东西可以跑在它上面.

## 阻塞与非阻塞

UART 驱动给了我们一个绝佳的对照. HAL 为同一个操作
同时提供了阻塞形式和 async 形式:

```
Blocking call:  uart.blocking_write(&buf)   // task spins until sent
Async call:     uart.write(&buf).await      // yields; others run
```

在回显循环里, 两个方向我们都用 async 形式:

```rust
loop {
    if uart.read(&mut buf).await.is_ok() {   // 等待, 核心空闲, 让其它任务跑
        let echo_bytes = controller.process_char(buf[0]);
        let _ = uart.write(echo_bytes).await; // 再次等待, 再次空闲
    }
}
```

当 `read(...).await` 处于 pending 时, 执行器会去跑闪灯任务 (如果它
就绪了), 或者让核睡觉. 这种共享空闲的行为, 正是
Embassy 固件能够看起来同时做很多事的原因 - 没有谁在忙等;
等待本身就是协作式的让出.

## 小结

- future 是一个可轮询的状态机: `poll` 返回 `Ready` 或 `Pending`.
- `Pending` 的意思是 "待会再来"; 硬件发出事件信号时,
  执行器会恢复我们.
- 编译器把每个 `.await` 编码成固定大小结构体里的一个状态.
- `async fn` 返回一个 future; `.await` 在 async 上下文里
  把它驱动到完成.
- async 的等待会把核让给别的任务 - 不忙等, 也不浪费
  周期.

接下来: 执行器本身, 以及启动一切的
`#[embassy_executor::main]` 属性.