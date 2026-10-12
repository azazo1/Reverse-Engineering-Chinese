# Chapter 30: 完整集成

## 引言

本课程的每个驱动都是按同一张蓝图构建的: 一个纯粹的, 可测试的
控制器; 一个带文档的配置模块; 以及一层很小的异步外壳, 它读取
硬件, 喂给控制器, 再把结果写回硬件. 这最后一章
把三个驱动组装成一个集成的固件 - 而更重要的是,
展示如何*设计*这样一个系统. 它最后会给出完整的
架构, 以及那些将来写任何驱动都用得上的习惯.

## 共享的架构

把三个驱动并排放在一起, 这个模式就再明显不过了:

```
              BLINK            BUTTON             UART
logic file    led.rs           button.rs          uart.rs
hardware      main.rs          main.rs            main.rs
config        config.rs        config.rs          config.rs
sensor        timer            GPIO15 in          UART0_RX
actuator      GPIO16 out       GPIO16 out         UART0_TX
cadence       Timer 500 ms     Timer 5 ms         interrupt + DMA
```

每个驱动都是三个文件, 配四个习惯:

1. `config.rs` 以带文档的常量形式拥有所有可调参数.
2. 控制器文件以纯方法的形式拥有逻辑, 并承载测试套件.
3. `main.rs` 是唯一导入 Embassy 外设的文件.
4. 循环是读 → 控制器 → 写 → await.

因为控制器从不接触引脚, 整个逻辑层都能在主机上测试;
因为 `main` 很薄, 硬件层也就容易审查得多.

## 集成项目

一个实用的收尾之作: 一个固件, 其中按钮选择闪烁速度,
而 UART 报告状态. 它的骨架 - 把本课程教的每条规则都用上 -
大致长这样:

```
src/
  config.rs         delay + baud + debounce constants
  led.rs             LedController (unchanged)
  button.rs          ButtonController (unchanged)
  uart.rs            UartController (unchanged)
  main.rs            executor: button -> led, uart logs state
Cargo.toml / memory.x / build.rs   build system (unchanged)
Makefile            test/build/flash     host testing pipeline
```

这三个控制器从一开始就是为组合而设计的: 每个都是 `Clone + Copy`, 每个
都通过 `new()` 启动, 而且没有一个拥有硬件. 于是集成在 `main` 里
就只剩一个策略决定:

```rust
#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let p = embassy_rp::init(Default::default());
    let mut led = Output::new(p.PIN_16, Level::Low);
    let mut button = ButtonController::new();
    let mut controller = LedController::new();
    // ... uart setup (Ch 28/29) ...
    loop {
        button.update(true); // 每轮从 GPIO15 采样
        let interval = if button.is_pressed() { 100 } else { 500 };
        let state = controller.toggle();
        led.set_level(Level::from(!led_state_to_level(state)));
        // ... uart.write(state_log).await;
        Timer::after_millis(interval).await;
    }
}
```

这就是整个课程浓缩成的一个循环: 采样, 判断, 行动, 等待 - 而每个
判断要么是一个有名字的常量, 要么是一个经过测试的方法.

## 用异步任务拆分工作

共享单循环的版本很简单, 但 Embassy 更欣赏另一种
形态: 彼此独立, 协作运行的异步**任务**. 核心洞见在于,
可 spawn 的任务按职责来切分系统, 让执行器
在它们之间交错调度:

```
                    +---------------+
   Spawner -------> | executor      |
                    |               |
                    |  button_task  : samples GPIO15, flips speed via channel
                    |  blink_task   : toggles LED at selected speed
                    |  uart_task    : echoes bytes + logs state changes
                    +---------------+
```

从第 14 章起就一直预留着的 `_spawner`, 正是这里需要的:

```rust
#[embassy_executor::main]
async fn main(spawner: Spawner) {
    spawner.spawn(blink_task()).unwrap();
    spawner.spawn(button_task()).unwrap();
    spawner.spawn(uart_task()).unwrap();
}
```

每个任务都是一个循环, 和各个驱动里的循环一样, 而 Embassy 的时间与
信号原语负责协调它们. 调试属性 `#[embassy_executor::task]`
把每一个都变成运行时的实体; 编译器保证可 spawn 的任务是
`Send` 的, 并且大小正确. 这就是本课程一路走来的
目的地: 三个小循环, 一个执行器, 零轮询.

## 写下一个驱动的规则

在你接一个新外设之前, 先把本课程已经变成
本能的五个习惯用上:

1. **配置优先.** 每个可调参数都是 `config.rs` 里带文档的常量,
   并且配有测试.
2. **控制器要纯.** 逻辑层只接收基本类型, 返回回显
   结果 - 可在主机上测试, 不导入 HAL.
3. **文档按标准来.** C 风格块注释头, `//!` FILE 块, 以及
   每一项的 `/// # Details` / `# Arguments` / `# Returns`.
4. **按横幅分组写测试.** 构造, 行为, trait - 二十个测试不过是
   一个平常的上午.
5. **异步外壳放最后.** `main` 文件绑定外设, spawn 任务, 并
   循环; 它是唯一的嵌入式文件.

## 完整的图景

从第 1 章到这里的一切, 都归结为一个系统:

```
+----------------------------------------------------------------------+
|  RP2350 firmware (Rust + Embassy)                                    |
|                                                                      |
|  pure logic  ->  host-tested controllers (std)                       |
|  embedded    ->  thin main.rs shells (no_std)                        |
|  build       ->  config.toml / memory.x / build.rs / Makefile        |
|  async       ->  executor, tasks, Timer, interrupt + DMA UART        |
+----------------------------------------------------------------------+
```

三个驱动是证明, 测试是保证, 而架构是可复用的经验.
现在你手里握着的, 是一条完整的开发者路径:
从一颗裸芯片, 到一个集成的, 中断驱动的, 可在主机上测试的 Rust 系统.

## 小结

- 三个驱动共享同一张蓝图: 配置常量, 带测试套件的纯控制器,
  以及很薄的异步外壳.
- 集成就是把没改过的控制器组合起来; 只有 `main.rs` 定义策略.
- Embassy 任务在一个执行器之下按职责切分系统;
  一直被预留的 `_spawner` 终于名副其实了.
- 这五个习惯 - 配置优先, 控制器要纯, 标准文档, 按横幅
  分组测试, 异步外壳放最后 - 原样适用于你的下一个驱动.
- 整个课程的旅程可以压缩成: 采样, 判断, 行动, 等待 -
  协作地, 安全地, 可测试地完成.

恭喜. 你打下的这个基础, 会支撑你接下来写的
每一个驱动.