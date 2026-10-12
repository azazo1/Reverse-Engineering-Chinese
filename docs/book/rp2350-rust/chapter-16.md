# Chapter 16: embassy-rp HAL

## 引言

每个驱动进入 `main` 之后都以同样的一行开始:

```rust
let p = embassy_rp::init(Default::default());
```

这个小小的调用解锁了后面的一切. 它初始化时钟和临界区
机制, 然后返回 **`Peripherals` 结构体** - 一组
独占的所有权令牌, 每个硬件模块一个. 本章回答
`init` 做了什么, 以及它的返回值为什么存在.

## Peripherals

一个 "外设" 就是一个硬件模块: UART0, GPIO bank 0, DMA0, 定时器等等.
每个都有自己的寄存器, 一条中断线和一个固定地址. Embassy
把每一个都建模成一个 **令牌类型** - 一个空结构体, 只有本程序才能持有它的
实例.

`init` 返回的那个打包体 `Peripherals`, 每个令牌占一个字段:

```rust
pub struct Peripherals {
    pub PIN_0: Pin<0>,        // GPIO 0 的令牌
    pub PIN_1: Pin<1>,
    pub PIN_15: Pin<15>,
    pub PIN_16: Pin<16>,
    pub UART0: UART0,         // UART 0 的令牌
    pub DMA_CH0: DmaChannel0,
    pub DMA_CH1: DmaChannel1,
    // ... 以及其它每一个引脚, 通道和模块
}
```

驱动就是通过字段访问来点名它想要的硬件的:

```rust
Output::new(p.PIN_16, Level::Low)           // PIN_16 的所有权移到这里
Input::new(p.PIN_15, Pull::Up)              // PIN_15 的所有权移到这里
Uart::new(p.UART0, p.PIN_0, p.PIN_1, ...)   // R, TX, RX 和 DMA 都移进来
```

## embassy_rp::init

`init` 做的是一次性的整芯片设置, 后面所有调用都以此为前提:

1. **时钟配置** - 建立可靠的时钟 (晶振, PLL, 参考
   时钟), 让定时器和外设以已知的频率运行.
2. **解除外设复位** - RP2350 启动时把大部分外设都保持在复位状态
   (汇编课程第 26 章讲的正是这段汇编里的舞蹈); `init`
   把它们释放到一个干净的状态.
3. **临界区机制** - 注册本平台的关中断
   临界区实现 (见下文), 这是安全共享数据的基础.
4. **返回 `Peripherals`** - 从此以后就一直消费着所有这些令牌.

在我们的驱动里, 签名始终是 `init(Default::default())`. 自定义的
`Config` 可以设置时钟频率, 也可以关掉不用的模块, 但三个驱动用的
就是默认值 - 也就是教程的规范形式.

## Peripherals 结构体

为什么这些令牌的 *所有权* 如此重要? 因为所有权等于
借用检查器对 **独占性** 的保证 (第 4 章). 两个并发任务
不可能同时拥有 `UART0`; 想在别人读的时候去写的那段代码
根本编译不过.

把 `p.PIN_16` 传进 `Output::new` 会 *移动* 这个令牌. 那一行之后, 字段
`p.PIN_16` 就不存在了 - 驱动不可能不小心配置 GPIO16
两次, 也没有别的东西能碰它. 这就是内存安全应用到硬件上:
编译器强制要求每个外设在程序的整个生命周期里最多只有
一个驱动.

## 临界区

有些操作绝不能被中断 - 比如, 在中断处理函数可能写入的情况下
读取一个共享计数器. Embassy 基于 `embedded-hal` 的 `critical_section`
crate 提供了机制: 进入一段关中断的区域, 干完你的
活, 退出. `embassy-rp` 的 `critical-section-impl` 特性 (第 8 章)
提供了真正的实现.

```
+----------------------+
|     normal code      |
|  enter critical sec. |  interrupts disabled
|  ... atomic work ... |
|  exit critical sec.  |  interrupts enabled
|     normal code      |
+----------------------+
```

执行器和 HAL 代码内部就使用临界区 - 比如原子地
认领一个中断. 应用代码很少手工进入临界区, 但了解
这个机制就能解释, 为什么中断和执行器能安全共存.

## rp235xa 芯片特性

`embassy-rp` 上的 `rp235xa` 特性用来选择 RP2350 这个变体.
Embassy 的 crate 覆盖 RP 系列里的好几款芯片; 这个特性把 HAL 指向
正确的内存映射, 正确的启动序列和正确的寄存器组. 没有
它, `init` 就会配置错误的硅片 - 正是这个特性门让
"RP2350" 而不是 "RP2040" 成立.

## 小结

- 外设就是硬件模块, 用独占的所有权令牌来表示.
- `embassy_rp::init(Default::default())` 配置时钟, 解除复位,
  装好临界区机制, 并交出 `Peripherals`.
- 把一个令牌 (`p.PIN_16`) 移动进 HAL 构造函数, 能让重复配置
  变成编译期错误.
- 临界区保证了相对中断的原子性; 执行器
  依赖它们.
- `rp235xa` 把 HAL 钉在 RP2350 这颗芯片上.

接下来: 所有 HAL 里最显眼的一个 - GPIO 输出和输入引脚.