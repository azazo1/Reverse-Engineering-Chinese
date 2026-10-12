# Chapter 16: 系统寄存器与协处理器接口

## 引言

除了十六个通用寄存器和 APSR 之外, Cortex-M33 还提供系统级的特殊寄存器和一套协处理器接口. 我们的闪烁驱动用 `msr` 配置栈指针, 用 `dsb`/`isb` 同步处理器状态, 用 `mcrr` 经由 RP2350 的 SIO 协处理器控制 GPIO. 本章讲解这些系统级指令, 以及它们暴露出来的硬件接口.

## 特殊功能寄存器

Cortex-M33 有几个特殊功能寄存器, 通过 `msr` (写) 和 `mrs` (读) 访问:

| 寄存器 | 用途 | 使用位置 |
|----------|---------|---------|
| MSP | 主栈指针 | stack.s |
| PSP | 进程栈指针 | stack.s |
| MSPLIM | 主栈指针上限 | stack.s |
| PSPLIM | 进程栈指针上限 | stack.s |
| PRIMASK | 中断屏蔽 | (未使用) |
| CONTROL | 执行模式 / 栈选择 | (未使用) |

### 栈指针初始化

stack.s 把所有栈相关的寄存器都配置了一遍:

```asm
Init_Stack:
  ldr   r0, =STACK_TOP                           // r0 = 0x20082000
  msr   PSP, r0                                  // 进程栈指针
  ldr   r0, =STACK_LIMIT                         // r0 = 0x2007a000
  msr   MSPLIM, r0                               // 主栈上限
  msr   PSPLIM, r0                               // 进程栈上限
  ldr   r0, =STACK_TOP                           // r0 = 0x20082000
  msr   MSP, r0                                  // 主栈指针
  bx    lr                                       // 返回
```

**MSP** 是复位之后生效的栈指针. **MSPLIM** 和 **PSPLIM** 是 ARMv8-M 的特性: 一旦栈指针掉到上限以下就触发 fault, 从而杜绝了悄无声息的栈溢出.

## 内存映射的系统寄存器

有些系统配置是通过内存映射寄存器完成的, 它们位于 `0xE000_0000` 处的私有外设总线 (PPB) 区域:

### CPACR - 协处理器访问控制寄存器

地址: `PPB_BASE + 0x0ED88` = `0xE000ED88`

CPACR 控制对协处理器的访问. 我们的固件使能了协处理器 0 (CP0), 它提供了通往 RP2350 SIO GPIO 接口的访问路径:

```asm
Enable_Coprocessor:
  ldr   r0, =CPACR                               // r0 = 0xE000ED88
  ldr   r1, [r0]                                 // 读取当前的 CPACR
  orr   r1, r1, #(1<<1)                          // 置 CP0 完全访问位 1
  orr   r1, r1, #(1<<0)                          // 置 CP0 完全访问位 0
  str   r1, [r0]                                 // 写回
  dsb                                            // 同步
  isb                                            // 冲刷流水线
  bx    lr                                       // 返回
```

CPACR 的 bits [1:0] 控制 CP0 的访问权限:

| Bits [1:0] | 访问级别 |
|------------|-------------|
| `00` | 禁止访问 (默认) |
| `01` | 仅特权模式可访问 |
| `11` | 完全访问 (我们的设置) |

## 屏障指令

### `dsb` - 数据同步屏障

```asm
  dsb                                            // 等待所有内存访问完成
```

`dsb` 保证前面所有的内存访问 (加载和存储) 都已完成, 之后才开始执行后续指令. 在修改 CPACR 之后这一点很关键, 因为处理器必须先看到新的协处理器配置, 才能执行协处理器指令.

### `isb` - 指令同步屏障

```asm
  isb                                            // 冲刷流水线
```

`isb` 冲刷处理器流水线, 保证后续指令都按当前系统状态重新取指和译码. 改过 CPACR 之后, 流水线里任何 `mcrr` 指令都必须按新的访问权限重新取指.

`dsb` + `isb` 这个组合是 ARM 规定的固定套路, 凡是修改系统控制寄存器之后都要照做:

```
str  → dsb → isb → (now safe to use CP0)
```

## 协处理器接口

### 什么是协处理器?

在 RP2350 上, 协处理器 0 (CP0) 提供对单周期 IO (SIO) 块的快速访问. SIO 里有 GPIO 的置位/清除/翻转寄存器, 它们绕过了常规的外设总线 - 因而 GPIO 控制更快.

### `mcrr` - 从两个寄存器移动到协处理器

`mcrr` 指令把两个 ARM 寄存器里的数据传送给协处理器:

```asm
  mcrr  p0, #4, r2, r4, c4                      // CP0: 为 GPIO 使能 OE
```

指令格式是:

```
mcrr  pN, #opc, Rt, Rt2, CRm
```

| 字段 | 含义 | 在我们的固件里 |
|-------|---------|-----------------|
| `pN` | 协处理器编号 | `p0` (SIO) |
| `#opc` | 操作码 | `#4` (GPIO 操作) |
| `Rt` | 第一个源寄存器 | GPIO 编号或数值 |
| `Rt2` | 第二个源寄存器 | 数值或掩码 |
| `CRm` | 协处理器寄存器 | 操作选择器 |

### 经由 CP0 的 GPIO 操作

固件用 `mcrr` 完成三种不同的 GPIO 操作:

**1. 使能输出 (gpio.s - GPIO_Config):**

```asm
  mov   r4, #1                                   // r4 = 1 (使能)
  mcrr  p0, #4, r2, r4, c4                      // 为 GPIO r2 使能 OE
```

它把指定 GPIO 引脚对应的输出使能位置起来.

**2. 把 GPIO 置高 (gpio.s - GPIO_Set):**

```asm
  mov   r4, #1                                   // r4 = 1 (置高)
  mcrr  p0, #4, r0, r4, c0                      // 把 GPIO r0 置高
```

它把 GPIO 引脚驱动到逻辑高电平 (3.3V), LED 点亮.

**3. 把 GPIO 拉低 (gpio.s - GPIO_Clear):**

```asm
  mov   r4, #0                                   // r4 = 0 (拉低)
  mcrr  p0, #4, r0, r4, c0                      // 把 GPIO r0 拉低
```

它把 GPIO 引脚驱动到逻辑低电平 (0V), LED 熄灭.

### 为什么 GPIO 要用协处理器?

直接通过外设总线写寄存器, 会因为总线仲裁而耗费多个时钟周期. 协处理器接口提供了一条通往 SIO 块的专用通路, 让 GPIO 操作能在单周期内完成. 对一个闪烁驱动来说这点性能差异可以忽略, 但对高速位翻转来说就很可观了.

## 完整的协处理器流程

任何 `mcrr` 指令能够执行之前, 必须先完成:

```
1. Enable_Coprocessor: CPACR |= 0x3 → dsb → isb
2. GPIO_Config: pad setup → ctrl setup → mcrr OE enable
3. Main loop: mcrr set → delay → mcrr clear → delay → repeat
```

如果漏掉第 1 步, 任何 `mcrr` 指令都会触发 UsageFault, 因为 CP0 的访问默认是被拒绝的.

## 小结

- `msr`/`mrs` 用于访问 MSP, PSP 及其上限之类的特殊功能寄存器.
- CPACR (内存映射在 0xE000ED88) 控制协处理器的访问权限.
- `dsb` 与 `isb` 在系统寄存器改动之后同步内存与流水线状态.
- `mcrr` 把数据传给协处理器 0, 从而快速访问 SIO 的 GPIO 接口.
- 三种 `mcrr` 操作控制 GPIO: 使能输出, 置高, 拉低.
- 使用任何 `mcrr` 指令之前都必须先使能协处理器访问, 否则会触发 fault.
