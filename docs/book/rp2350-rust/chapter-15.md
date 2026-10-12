# Chapter 15: embassy-time

## 引言

闪灯驱动的心跳是 `Timer::after_millis(controller.delay_ms())`,
而按键驱动则按 `Timer::after_millis(DEBOUNCE_DELAY_MS)` 采样. 这两个调用
都会让任务挂起一段可度量的时间, 同时不占用核. 本章
打开 `embassy-time`: 它底下的 time driver, 用来表达时间的 `Instant` 和
`Duration` 类型, 以及等待它们的 `Timer` future.

## time driver

`embassy-time` 本身不认识任何硬件. 它是一套可移植的 API, 背后靠着
一个 **time driver**, 在启用 `time-driver` 特性时 (第 8 章) 由 `embassy-rp`
提供. 这个驱动持有硬件定时器, 只回答一个问题:
*现在几点了?*

```
+------------------+      +--------------------+
|  embassy-time    |  --> |  embassy-rp driver |
|  generic API     |      |  (RTC + timer IRQ) |
+------------------+      +--------------------+
```

驱动的节拍单位是 **微秒**. 几微秒的时间分辨率对于我们 500 ms 的闪灯
周期来说远远够细了 - 但同一个驱动也能安排一个 100 us 的
字节超时, 或者一个 5 秒的看门狗, 而应用代码
一个字都不用改.

## Instant 与 Duration

两个类型承载了单位:

- **`Instant`** - 驱动时间轴上的一个时间点. 由
  `Instant::now()` 创建; 可以比较, 也可以相减.
- **`Duration`** - 一段时间跨度. 由具名构造函数创建:
  `Duration::from_micros`, `::from_millis`, `::from_secs` 等等.

`Instant` 减去 `Instant` 得到一个 `Duration` - 也就是过去的时间:

```rust
let start = Instant::now();
read_sensor();
let elapsed = start.elapsed();          // Duration
if elapsed < Duration::from_millis(10) {
    // 还在时间窗口之内
}
```

`Instant`/`Duration` 都是 `Copy`, 所以它们可以在我们的控制器
结构体里自由传递 - 你可以用这个模式给任何驱动加上超时.

## Timer

`Timer` 是等待原语. 它最常用的两种形式:

```rust
Timer::after_millis(500).await;           // 从现在起等待 500 ms
Timer::after(Duration::from_secs(1)).await; // 从现在起等待 1 秒
```

`Timer::after(...)` 和 `Timer::at(instant)` 会在这个滴答作响的
时钟上挂一个 future. 轮询这个 future 会一直返回 `Pending`, 直到截止时间
过去, 然后返回 `Ready(())`. 在它 `Pending` 期间, 执行器会去跑别的任务 - 这
正是第 12 章讲的那种协作行为:

```
Task:  set_led_high  ->  await Timer 500ms  ->  set_led_low  ...
                          |          |
                          v          v
Executor:              other work or wfi (idle)
```

## 我们驱动里的 after_millis

闪灯循环的时序直接来自它自己的状态 - `LedController` 的 `delay_ms`
字段:

```rust
loop {
    let state = controller.toggle();
    if led_state_to_level(state) {
        led.set_high();
    } else {
        led.set_low();
    }
    Timer::after_millis(controller.delay_ms()).await;
}
```

每一轮迭代都是: 翻转状态, 驱动引脚, 然后睡过配置好的
时间间隔. 因为延时是一个 *方法*, 时序策略就住在控制器
内部; `main` 只是把它读出来.

按键驱动按自己的间隔采样:

```rust
Timer::after_millis(DEBOUNCE_DELAY_MS).await;
```

每隔五毫秒, 这个循环就把新的引脚采样喂进去抖
滤波器 (第 22-23 章). 两个循环做的事其实一样: 在 `Timer` 上 `.await`
把 "等" 变成了 "让出", 而执行器则把省下来的
时间用在有用的工作上, 或者干脆什么都不做, 以此证明这一点.

## 小结

- `embassy-time` 是一套可移植 API, 背后是 RP2350 的 time driver
  (`time-driver` 特性).
- `Instant` 是一个时间点; `Duration` 是一段时间跨度; 两者都是 `Copy`.
- `Timer::after_*` 返回一个 future, 它在截止时间
  过去后变成 `Ready`.
- 在 `Timer` 上等待会把这个核让出去 - 这就是每个驱动的协作式心脏.
- 闪灯和按键两个循环的周期都来自运行时读取的
  配置常量.

接下来: HAL. `embassy_rp::init` 如何把整个处理器安全地交给我们.