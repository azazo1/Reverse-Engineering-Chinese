# Chapter 29: 应用程序入口点 - `main.s`

## 简介

`main.s` 是所有初始化工作开花结果的地方. 它把 GPIO16 配置成输出, 然后进入一个死循环, 让 LED 闪烁 - 亮 500 ms, 灭 500 ms, 永不停歇. 本章逐条走一遍每条指令, 展示这些函数调用如何连接到前面几章搭好的模块, 并解释段布局.

## 完整源码

```asm
.include "constants.s"

.section .text                                   # 代码段
.align 2                                         # 对齐到 4 字节边界

.global main                                     # 导出 main
.type main, @function                            # 标记为函数
main:
.GPIO16_Config:
  li    a0, PADS_BANK0_GPIO16_OFFSET             # 装入 PADS_BANK0_GPIO16_OFFSET
  li    a1, IO_BANK0_GPIO16_CTRL_OFFSET          # 装入 IO_BANK0_GPIO16_CTRL_OFFSET
  li    a2, 16                                   # 装入 GPIO 编号
  call  GPIO_Config                              # 调用 GPIO_Config
.Loop:
  li    a0, 16                                   # 装入 GPIO 编号
  call  GPIO_Set                                 # 调用 GPIO_Set
  li    a0, 500                                  # 500 毫秒
  call  Delay_MS                                 # 调用 Delay_MS
  li    a0, 16                                   # 装入 GPIO 编号
  call  GPIO_Clear                               # 调用 GPIO_Clear
  li    a0, 500                                  # 500 毫秒
  call  Delay_MS                                 # 调用 Delay_MS
  j     .Loop                                    # 永远循环下去
  ret                                            # 返回调用者

.section .rodata                                 # 只读数据段

.section .data                                   # 数据段

.section .bss                                    # BSS 段
```

## 函数声明

```asm
.global main                                     # 导出 main
.type main, @function                            # 标记为函数
```

`.global main` 把符号导出, 这样链接器才能解析 `reset_handler.s` 里的 `j main`. `.type main, @function` 则是给调试器和链接器看的标记.

## GPIO16 的配置

```asm
.GPIO16_Config:
  li    a0, PADS_BANK0_GPIO16_OFFSET             # 装入 PADS_BANK0_GPIO16_OFFSET
  li    a1, IO_BANK0_GPIO16_CTRL_OFFSET          # 装入 IO_BANK0_GPIO16_CTRL_OFFSET
  li    a2, 16                                   # 装入 GPIO 编号
  call  GPIO_Config                              # 调用 GPIO_Config
```

这段在启动时执行一次, 在闪烁循环开始之前.

### 参数准备

| 寄存器 | 值 | 常量 | 含义 |
|----------|-------|----------|---------|
| `a0` | `0x44` | `PADS_BANK0_GPIO16_OFFSET` | GPIO16 的 pad 寄存器偏移 |
| `a1` | `0x84` | `IO_BANK0_GPIO16_CTRL_OFFSET` | GPIO16 的 CTRL 寄存器偏移 |
| `a2` | `16` | (字面量) | GPIO 引脚编号 |

RISC-V 调用约定用 `a0` - `a7` 传递前八个参数. `GPIO_Config` 期望 pad 偏移放在 `a0`, CTRL 偏移放在 `a1`, GPIO 编号放在 `a2`.

### `call` 指令

```asm
  call  GPIO_Config                              # 调用 GPIO_Config
```

`call` 是一条伪指令, 它会展开成 `auipc ra, offset[31:12]` / `jalr ra, ra, offset[11:0]`. 它把返回地址存进 `ra`, 然后跳到 `GPIO_Config`. 等 `GPIO_Config` 执行 `ret` 时, 控制权就回到 `call` 之后的那条指令.

### GPIO_Config 做了什么

对 GPIO16 来说, `GPIO_Config`:
1. 配置 `PADS_BANK0_BASE + 0x44` 处的 pad: 清掉 OD 和 ISO, 置上 IE
2. 在 `IO_BANK0_BASE + 0x84` 处把 FUNCSEL 设为 5 (SIO)
3. 通过 `SIO_GPIO_OE_SET` 的第 16 位使能输出

这次调用之后, GPIO16 就是一个完整配置好的输出引脚了.

## 闪烁循环

```asm
.Loop:
  li    a0, 16                                   # 装入 GPIO 编号
  call  GPIO_Set                                 # 调用 GPIO_Set
  li    a0, 500                                  # 500 毫秒
  call  Delay_MS                                 # 调用 Delay_MS
  li    a0, 16                                   # 装入 GPIO 编号
  call  GPIO_Clear                               # 调用 GPIO_Clear
  li    a0, 500                                  # 500 毫秒
  call  Delay_MS                                 # 调用 Delay_MS
  j     .Loop                                    # 永远循环下去
```

### 第 1 步: 点亮 LED

```asm
  li    a0, 16                                   # 装入 GPIO 编号
  call  GPIO_Set                                 # 调用 GPIO_Set
```

把 `16` (GPIO 编号) 装入 `a0` 并调用 `GPIO_Set`, 后者把 `(1<<16)` 写进 `SIO_GPIO_OUT_SET`, 把 GPIO16 拉高. 电流经过 LED 和电阻流向地 - LED 亮起.

### 第 2 步: 等 500 毫秒

```asm
  li    a0, 500                                  # 500 毫秒
  call  Delay_MS                                 # 调用 Delay_MS
```

把 `500` (毫秒) 装入 `a0` 并调用 `Delay_MS`. 这个函数空转 `500 × 3600 = 1,800,000` 次循环迭代, 大约消耗 500 毫秒.

### 第 3 步: 熄灭 LED

```asm
  li    a0, 16                                   # 装入 GPIO 编号
  call  GPIO_Clear                               # 调用 GPIO_Clear
```

调用 `GPIO_Clear`, 它把 `(1<<16)` 写进 `SIO_GPIO_OUT_CLR`, 把 GPIO16 拉低. 没有电流流过 LED - 它熄灭了.

### 第 4 步: 再等 500 毫秒

```asm
  li    a0, 500                                  # 500 毫秒
  call  Delay_MS                                 # 调用 Delay_MS
```

LED 熄灭状态下再等 500 毫秒.

### 第 5 步: 重复

```asm
  j     .Loop                                    # 永远循环下去
```

`j .Loop` 是一条无条件跳转, 回到这个周期的开头. LED 以 1 Hz 闪烁 (亮 500 毫秒 + 灭 500 毫秒 = 周期 1000 毫秒).

### 执行不到的 `ret`

```asm
  ret                                            # 返回调用者
```

这条 `ret` 永远不会被执行 - 它上面的 `j .Loop` 总是跳回去. 它作为防御性写法存在, 满足 "每个函数都有 `ret`" 这个惯例.

## 为什么每次都重新装入 `a0`

每一次对 `GPIO_Set`, `Delay_MS` 或 `GPIO_Clear` 的 `call` 都允许覆盖 `a0` - 它是调用者保存的寄存器. 尽管 `GPIO_Set` 并没有修改 `a0`, 但调用约定并不保证这一点. 我们在每次调用前都显式地重新装入 `a0`, 以确保正确性.

## 闪烁时序图

```
     ┌────────┐        ┌────────┐        ┌────────
     │  HIGH  │        │  HIGH  │        │  HIGH
─────┘        └────────┘        └────────┘
     |←500ms→| |←500ms→|←500ms→| |←500ms→|
     |←── 1000ms ──→|←── 1000ms ──→|
```

LED 每 500 毫秒翻转一次, 产生 1 Hz, 占空比 50% 的闪烁.

## 段声明

```asm
.section .rodata                                 # 只读数据段
.section .data                                   # 数据段
.section .bss                                    # BSS 段
```

这几个空的段声明是占位用的. 它们确保链接器知道这些标准段确实存在, 尽管闪烁驱动并没有用到它们:

| 段 | 用途 | 内容 |
|---------|---------|----------|
| `.rodata` | 只读常量 | 空 (没有字符串或表) |
| `.data` | 已初始化的全局变量 | 空 (没有全局变量) |
| `.bss` | 未初始化的全局变量 | 空 (没有全局变量) |

在更复杂的程序里, 这些段会用来存放字符串, 查找表和全局状态.

## 调用图

```
main
  ├── GPIO_Config(0x44, 0x84, 16)  → gpio.s
  │     ├── PADS_BANK0 config
  │     ├── IO_BANK0 FUNCSEL
  │     └── SIO_GPIO_OE_SET
  │
  └── .Loop (infinite):
        ├── GPIO_Set(16)   → gpio.s → SIO_GPIO_OUT_SET
        ├── Delay_MS(500)  → delay.s → spin loop
        ├── GPIO_Clear(16) → gpio.s → SIO_GPIO_OUT_CLR
        ├── Delay_MS(500)  → delay.s → spin loop
        └── j .Loop
```

## 为什么 `main` 不保存 `ra`

`main` 是从 `Reset_Handler` 经 `j main` (而不是 `call main`) 到达的. `j` 指令写的是 `x0` (零寄存器), 返回地址被丢掉了. 根本不存在有效的返回地址可以保存. `main` 会一直运行下去 - 它永远不返回.

## 与 ARM 的对照

| 方面 | ARM | RISC-V |
|--------|-----|--------|
| GPIO 置位 | `GPIO_Set` (通过 `mcrr p0`) | `GPIO_Set` (通过 `sw` 写 SIO) |
| GPIO 清零 | `GPIO_Clear` (通过 `mcrr p0`) | `GPIO_Clear` (通过 `sw` 写 SIO) |
| 调用约定 | `bl GPIO_Set` | `call GPIO_Set` |
| 参数寄存器 | `r0` | `a0` |
| 死循环 | `b .Loop` | `j .Loop` |
| 寄存器重新装入 | 同样的套路 | 同样的套路 |

结构完全一样 - 不同的只有指令助记符和寄存器名字.

## 小结

- `main` 先把 GPIO16 配置一次, 然后进入死循环闪烁.
- 循环在 `GPIO_Set`(高) 和 `GPIO_Clear`(低) 之间交替, 中间各加 500 毫秒延时.
- 每次 `call` 之前都要重新装入 `a0`, 因为调用约定允许被调用者修改它.
- `j .Loop` 构成了死循环 - `main` 永远不返回.
- `.rodata`, `.data` 和 `.bss` 这几个段声明是标准段的占位.
- 1 Hz 的闪烁 (亮 500 毫秒, 灭 500 毫秒) 是十个源文件协同工作正确的直观确认.
