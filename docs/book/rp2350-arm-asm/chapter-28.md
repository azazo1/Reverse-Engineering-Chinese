# Chapter 28: gpio.s 第 2 部分, delay.s 与 coprocessor.s - 输出控制与定时

## 引言

GPIO16 由 `GPIO_Config` 配置好之后, 还需要三个函数才能让闪烁程序的运行时完整运转: `GPIO_Set` 把引脚拉高, `GPIO_Clear` 把它拉低, `Delay_MS` 在两次变化之间制造一段定时停顿. 第四个函数 `Enable_Coprocessor` 则让所有基于协处理器的 GPIO 操作成为可能. 本章覆盖这四个函数.

## GPIO_Set - 把引脚拉高

```asm
.global GPIO_Set
.type GPIO_Set, %function
GPIO_Set:
.GPIO_Set_Push_Registers:
  push  {r4-r12, lr}                             // 把寄存器 r4-r12, lr 压入栈
.GPIO_Set_Execute:
  ldr   r4, =1                                   // 使能输出
  mcrr  p0, #4, r0, r4, c0                       // gpioc_bit_out_put(GPIO, 1)
.GPIO_Set_Pop_Registers:
  pop   {r4-r12, lr}                             // 把寄存器 r4-r12, lr 弹出栈
  bx    lr                                       // 返回
```

### 函数签名

```
GPIO_Set(r0 = GPIO_NUMBER)
```

### 它的工作方式

```asm
  ldr   r4, =1                                   // r4 = 1 (高电平)
  mcrr  p0, #4, r0, r4, c0                       // 把 GPIO 输出置为高电平
```

`mcrr` 指令各字段的含义:

| 字段 | 值 | 含义 |
|-------|-------|---------|
| `p0` | 协处理器 0 | SIO 模块 |
| `#4` | 操作码 | GPIO 位操作 |
| `r0` | GPIO 编号 | 16 |
| `r4` | 输出值 | 1 (高电平 = 3.3V) |
| `c0` | 寄存器 | 输出值控制 |

当 r4 = 1 时, GPIO 引脚被驱动到 3.3V. 电流经 LED 和电阻流向地 - LED 就亮了.

## GPIO_Clear - 把引脚拉低

```asm
.global GPIO_Clear
.type GPIO_Clear, %function
GPIO_Clear:
.GPIO_Clear_Push_Registers:
  push  {r4-r12, lr}                             // 把寄存器 r4-r12, lr 压入栈
.GPIO_Clear_Execute:
  ldr   r4, =0                                   // 禁用输出
  mcrr  p0, #4, r0, r4, c0                       // gpioc_bit_out_put(GPIO, 0)
.GPIO_Clear_Pop_Registers:
  pop   {r4-r12, lr}                             // 把寄存器 r4-r12, lr 弹出栈
  bx    lr                                       // 返回
```

### 与 GPIO_Set 的区别

唯一的区别在 r4:

| 函数 | r4 的值 | 引脚状态 | LED |
|----------|----------|-----------|-----|
| GPIO_Set | 1 | 高电平 (3.3V) | 亮 |
| GPIO_Clear | 0 | 低电平 (0V) | 灭 |

两者都用 `c0` (输出值寄存器), 而不是 GPIO_Config 里用的 `c4` (输出使能寄存器).

## Delay_MS - 毫秒级延时

```asm
.global Delay_MS
.type Delay_MS, %function
Delay_MS:
.Delay_MS_Push_Registers:
  push  {r4-r12, lr}                             // 把寄存器 r4-r12, lr 压入栈
.Delay_MS_Check:
  cmp   r0, #0                                   // 如果毫秒数无效就直接返回
  ble   .Delay_MS_Done                           // 小于等于 0 则跳转
.Delay_MS_Setup:
  ldr   r4, =3600                                // 基于 14.5MHz 时钟的每毫秒循环次数
  mul   r5, r0, r4                               // 毫秒数 * 3600
.Delay_MS_Loop:
  subs  r5, r5, #1                               // 计数器减一
  bne   .Delay_MS_Loop                           // 不为零则继续
.Delay_MS_Done:
  pop   {r4-r12, lr}                             // 把寄存器 r4-r12, lr 弹出栈
  bx    lr                                       // 返回
```

### 函数签名

```
Delay_MS(r0 = milliseconds)
```

### 输入检查

```asm
  cmp   r0, #0                                   // 把毫秒数与 0 比较
  ble   .Delay_MS_Done                           // 若 <= 0 则跳到返回
```

`cmp` 用 r0 减去 0 并设置标志位. 如果结果小于等于零 (Z=1 或 N!=V), `ble` 就跳转. 这能防止:

- 零延时: `mul` 会得到 0 次迭代, 但这个检查把意图表达得更明确
- 负值: 如果 r0 被当作有符号的负数, `mul` 可能算出一个巨大的无符号计数

### 计算总迭代次数

```asm
  ldr   r4, =3600                                // 每毫秒的循环次数
  mul   r5, r0, r4                               // 总迭代次数 = 毫秒数 * 3600
```

在约 14.5 MHz 下, `subs` + `bne` 每轮大约花 4 个周期:

```
iterations per ms = 14,500,000 / 4 ≈ 3,625 ≈ 3,600 (rounded)
```

对于 500 ms: `500 × 3600 = 1,800,000` 次迭代.

### 延时循环

```asm
.Delay_MS_Loop:
  subs  r5, r5, #1                               // r5 = r5 - 1, 并设置标志位
  bne   .Delay_MS_Loop                           // r5 != 0 则继续循环
```

这是 ARM 上能做到的最紧凑的循环: 两条指令, 在 500 ms 延时里大约执行 1,800,000 次. `subs` 末尾的 `s` 会在 r5 减到零时置上 Zero 标志. `bne` 在 Z=0 (非零) 时继续循环.

### 定时精度

这个延时是近似的, 原因有:

1. 环形振荡器的频率会随温度和电压变化
2. 流水线效应会给每次迭代带来细微差别
3. 循环的额外开销 (准备, push/pop) 会多花几微秒

对于闪烁一颗 LED 来说, 这个精度已经绰绰有余.

## Enable_Coprocessor - 访问 CP0

```asm
.global Enable_Coprocessor
.type Enable_Coprocessor , %function
Enable_Coprocessor:
  ldr   r0, =CPACR                               // 加载 CPACR 地址
  ldr   r1, [r0]                                 // 读取 CPACR 的值
  orr   r1, r1, #(1<<1)                          // 置 CP0: 允许访问特权协处理器 0 位
  orr   r1, r1, #(1<<0)                          // 置 CP0: 允许访问特权协处理器 0 位
  str   r1, [r0]                                 // 把值写入 CPACR
  dsb                                            // 数据同步屏障
  isb                                            // 指令同步屏障
  bx    lr                                       // 返回
```

### 修改 CPACR

```asm
  ldr   r0, =CPACR                               // r0 = 0xE000ED88
  ldr   r1, [r0]                                 // 读取当前值
  orr   r1, r1, #(1<<1)                          // 置 bit 1
  orr   r1, r1, #(1<<0)                          // 置 bit 0
  str   r1, [r0]                                 // 写回
```

把 bits [1:0] 设成 `0b11`, 就授予了对协处理器 0 的完全访问权 (特权级 + 非特权级). 没有这一步, 任何 `mcrr p0, ...` 指令都会触发 UsageFault.

### 屏障指令

```asm
  dsb                                            // 所有内存访问完成
  isb                                            // 冲刷指令流水线
```

`dsb` (数据同步屏障) 保证 CPACR 的写入已经到达寄存器, 然后才继续往下走. `isb` (指令同步屏障) 冲刷流水线, 这样后续的 `mcrr` 指令都是在更新后的访问权限下取指的.

ARM 架构参考手册要求, 任何对 CPACR 的修改之后都必须有这段序列.

### 叶子函数

`Enable_Coprocessor` 是一个叶子函数, 只使用临时寄存器 (r0, r1). 不需要 push/pop.

## 运行时流程

四个函数都定义好之后, 闪烁循环就运转起来了:

```
main:
  GPIO_Config(0x44, 0x84, 16)    ← configure GPIO16
  loop:
    GPIO_Set(16)                  ← pin high (LED on)
    Delay_MS(500)                 ← wait 500ms
    GPIO_Clear(16)                ← pin low (LED off)
    Delay_MS(500)                 ← wait 500ms
    goto loop
```

LED 以 1 Hz 的频率闪烁 (亮 500 ms, 灭 500 ms).

## 小结

- `GPIO_Set` 用 r4=1 的 `mcrr p0, #4, r0, r4, c0` 把引脚拉高.
- `GPIO_Clear` 用同样的指令, 但 r4=0, 把引脚拉低.
- `Delay_MS` 检查输入, 计算迭代次数 (毫秒数 × 3600), 然后用 `subs`/`bne` 倒数.
- `Enable_Coprocessor` 通过修改 CPACR 授予 CP0 访问权, 随后是必需的 `dsb`/`isb` 屏障.
- 每毫秒 3600 次循环的延时校准, 依据的是约 14.5 MHz 的环形振荡器时钟速度.
