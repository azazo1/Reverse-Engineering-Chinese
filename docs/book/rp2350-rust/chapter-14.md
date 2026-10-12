# Chapter 14: Embassy 执行器

## 引言

future 只有在有人轮询它们时才会运行. 在单片机上, 这个 "有人" 就是
**执行器**: 一个极小的, 永不返回的循环, 它维护一个就绪 future 的
队列, 逐个轮询, 在没有就绪任务时睡觉. Embassy 的执行器
以 `embassy-executor` 的形式发布, 它在我们的代码里只露出一副面孔:
一个属性加一个参数 - `#[embassy_executor::main]` 和 `Spawner`. 本章
把这两者都拆开看看.

## #[embassy_executor::main]

每个驱动的入口点长得都一样:

```rust
/// 应用程序主入口点.
///
/// # Details
/// 初始化 Embassy 运行时并运行主闪灯循环.
/// 用 BlinkController 管理状态.
///
/// # Arguments
/// * `_spawner` - Embassy 任务 spawner (留给将来的 async 任务用).
///
/// # Returns
/// * `()` - 永不返回 (无限循环).
#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    ...
}
```

这个属性在启动时做三件事:

1. **初始化执行器的中断驱动时钟** (在 `arch-cortex-m` 上, 执行器由
   定时器中断来打拍子).
2. **构造一个 `Spawner`**, 并把它作为第一个参数传进来.
3. **把 `main` 本身作为第一个任务 spawn 出去**, 然后永远运行执行器.

先别管那段文档字符串 - 函数签名本身携带了真实信息.
参数是一个 `Spawner`; 在闪灯驱动里它没被用到 (`_spawner`), 因为
闪灯循环不需要额外任务. UART 驱动也没有 spawn 额外的
任务; 我们的三个驱动在设计上都是单任务的, 把 `Spawner` 传进来
只是为了将来扩展, 正如文档字符串所说.

## Spawner

`Spawner` 是一个 **指向执行器的句柄**. 有了它, 运行一个 async 任务就是
一次函数调用:

```rust
let spawner: Spawner = ...;          // 从 #[embassy_executor::main] 获得
spawner.spawn(my_task()).unwrap();   // 把 future 注册到执行器
```

用 `Spawner` 你能做这些事:

- **`spawn`** - 把一个任务 future 提交到执行器的队列.
- **克隆并共享** - `Spawner` 复制起来很便宜; 它可以被移进
  闭包和其它任务, 好让它们之后启动新任务.

在我们这些简单驱动里从未出现的那一点火花是任务池: 每个
`#[embassy_executor::task]` 都需要一个编译期确定大小的槽位, 所以 Embassy
静态分配任务, 而不是在堆上分配. 只有当池子满了 `spawn` 才会失败 -
那时会返回一个我们不得不处理的 `SpawnError`.

## 用 #[embassy_executor::task] 定义任务

一个可复用的 async 函数 (也就是 "任务") 用
`#[embassy_executor::task]` 标注. 这个属性会预留 future 需要的状态,
并把 future 接进执行器的机制里:

```rust
#[embassy_executor::task]
async fn blink(peripherals) {
    loop {
        ...
        Timer::after_millis(500).await;
    }
}

// 稍后, 在 main 里:
let _ = spawner.spawn(blink(peripherals));
```

这个语法和 `#[embassy_executor::main]` 如出一辙, 后者本身只是个
特殊任务, 只不过它拿到的是白送的 spawner. 我们的三个驱动都没有用
`#[task]` 变体 - 每个 `main` 只跑一个 `loop`, 不需要任何并发 -
但理解它能让 `main` 上的属性不再神秘, 也为你一旦出现第二个
并发任务时该写什么提供了模板.

## spawn 与 SpawnError

spawn 是会失败的, 类型系统也如实说明了这一点:

```rust
pub enum SpawnError {
    Busy,              // 这个任务已经被 spawn 了
    NoPoolMemory,      // 小容量池子用光了
    LargePoolMemory,
}

let result: Result<(), SpawnError> = spawner.spawn(my_task());
```

如果固件不能因为池子状况而 panic, 那就处理这个 `Result`. 在
单任务设计里根本不会失败, 所以我们的二进制文件保持代码
简单 - 但一旦你把工作拆成多个 Embassy 任务,
这个模式就重要了.

## 执行器在做什么

从概念上说, 执行器的整个程序就是一个循环:

```
+-------------+     +------------+     +-------------+
|  Wake event | --> |  Poll all  | --> |  Sleep (wfi)|
|  (IRQ)      |     |  ready tasks|    |  until next |
+-------------+     +------------+     +-------------+
```

- **唤醒事件** - 一个中断处理函数把受影响的 future 标记成 "就绪".
- **轮询就绪任务** - 执行器对每个就绪 future 调用 `poll`,
  把返回 `Ready` 的结果取走, 并把返回 `Pending` 的重新入队.
- **睡觉** - 没有任何就绪任务时, CPU 执行 `wfi` (等待中断),
  彻底停下来, 只烧几微安, 直到下一个事件.

这第三个状态是 async 送给我们的礼物: 一个还没到期的定时器不是一个
空转的循环, 而是一个停放的 future. 两个任务, 三个任务, 十个任务 -
只要没有谁就绪, 核就一分钱不花.

## 小结

- 执行器就是一个 "轮询然后睡觉" 的循环; future 只有在它
  轮询时才推进.
- `#[embassy_executor::main]` 初始化执行器, 构造一个 `Spawner`,
  spawn 出 `main`, 并且永不返回.
- `Spawner::spawn` 注册新任务; 它是 `Copy`, 在池子没有空位时
  返回一个 `Result`.
- `#[embassy_executor::task]` 把任意 `async fn` 变成可 spawn 的任务.
- 没有就绪任务 -> 核在 `wfi` 里睡觉, 几乎不耗电.

接下来: 时间. `Timer::after_millis` 到底做了什么.