# Chapter 27: gpio.s 第 1 部分 - GPIO_Config

## 引言

`GPIO_Config` 是固件里最复杂的函数. 它通过修改两套寄存器组 (pad 和 IO 控制) 把一个 GPIO 引脚配置成输出, 然后通过 SIO 协处理器打开输出驱动器. 本章逐条指令地走一遍, 说明物理引脚是如何接到内部逻辑上, 又是如何准备好驱动一颗 LED 的.

## 完整源码 - GPIO_Config

```asm
.global GPIO_Config
.type GPIO_Config, %function
GPIO_Config:
.GPIO_Config_Push_Registers:
  push  {r4-r12, lr}                             // 把寄存器 r4-r12, lr 压入栈
.GPIO_Config_Modify_Pad:
  ldr   r4, =PADS_BANK0_BASE                     // 加载 PADS_BANK0_BASE 地址
  add   r4, r4, r0                               // PADS_BANK0_BASE + PAD_OFFSET
  ldr   r5, [r4]                                 // 读取 PAD_OFFSET 的值
  bic   r5, r5, #(1<<7)                          // 清除 OD 位
  orr   r5, r5, #(1<<6)                          // 置 IE 位
  bic   r5, r5, #(1<<8)                          // 清除 ISO 位
  str   r5, [r4]                                 // 把值写入 PAD_OFFSET
.GPIO_Config_Modify_CTRL:
  ldr   r4, =IO_BANK0_BASE                       // 加载 IO_BANK0 基地址
  add   r4, r4, r1                               // IO_BANK0_BASE + CTRL_OFFSET
  ldr   r5, [r4]                                 // 读取 CTRL_OFFSET 的值
  bic   r5, r5, #0x1f                            // 清除 FUNCSEL
  orr   r5, r5, #0x05                            // 设置 FUNCSEL 0x05->SIO_0
  str   r5, [r4]                                 // 把值写入 CTRL_OFFSET
.GPIO_Config_Enable_OE:
  ldr   r4, =1                                   // 使能输出
  mcrr  p0, #4, r2, r4, c4                       // gpioc_bit_oe_put(GPIO, 1)
.GPIO_Config_Pop_Registers:
  pop   {r4-r12, lr}                             // 把寄存器 r4-r12, lr 弹出栈
  bx    lr                                       // 返回
```

## 函数签名

```
GPIO_Config(r0 = PAD_OFFSET, r1 = CTRL_OFFSET, r2 = GPIO_NUMBER)
```

调用者需要提供:

| 寄存器 | 值 | 示例 (GPIO16) |
|----------|-------|-----------------|
| r0 | pad 寄存器偏移 | `0x44` (PADS_BANK0_GPIO16_OFFSET) |
| r1 | 控制寄存器偏移 | `0x84` (IO_BANK0_GPIO16_CTRL_OFFSET) |
| r2 | GPIO 引脚编号 | `16` |

通过把偏移量作为参数传入, 这个函数可以配置任意 GPIO 引脚 - 而不只是 GPIO16.

## 寄存器的保存与恢复

```asm
  push  {r4-r12, lr}                             // 保存 10 个寄存器 (40 字节)
  ...
  pop   {r4-r12, lr}                             // 恢复
  bx    lr                                       // 返回
```

GPIO_Config 把 r4 和 r5 当作工作寄存器. 按 AAPCS 它们是被调用者保存的, 所以必须保护. 压入 r4-r12 和 lr, 就把所有被调用者保存的寄存器连同返回地址一起保存了下来.

## 阶段 1: pad 配置

pad 寄存器控制物理引脚的电气特性.

### 计算 pad 地址

```asm
  ldr   r4, =PADS_BANK0_BASE                     // r4 = 0x40038000
  add   r4, r4, r0                               // r4 = 0x40038000 + 0x44 = 0x40038044
```

对于 GPIO16, pad 寄存器位于 `0x40038044`.

### 读-改-写 pad 寄存器

```asm
  ldr   r5, [r4]                                 // 读取当前 pad 值
  bic   r5, r5, #(1<<7)                          // 清除 OD (输出禁用) -> 允许输出
  orr   r5, r5, #(1<<6)                          // 置 IE (输入使能) -> 打开输入
  bic   r5, r5, #(1<<8)                          // 清除 ISO (隔离) -> 接通 pad
  str   r5, [r4]                                 // 写回
```

一次读-改-写里做了三处位修改:

| 位 | 字段 | 之前 | 之后 | 效果 |
|-----|-------|--------|-------|--------|
| 8 | ISO | 1 | 0 | 解除 pad 隔离 (接到逻辑上) |
| 7 | OD | 1 | 0 | 允许输出驱动 |
| 6 | IE | 0 | 1 | 使能输入 (读回时需要) |

复位之后, pad 处于隔离状态 (ISO=1), 输出被禁用 (OD=1), 输入也被禁用 (IE=0). 要得到一个能正常输出的引脚, 这三处都必须改.

pad 寄存器的位布局:

```
Bit:  8    7    6    5    4    3    2    1    0
    +----+----+----+----+----+----+----+----+----+
    |ISO | OD | IE | DR1| DR0| PUE| PDE| SCH| SLW|
    +----+----+----+----+----+----+----+----+----+
      0    0    1    (unchanged)
```

## 阶段 2: 功能选择

IO 控制寄存器把引脚接到某个内部外设上.

### 计算控制寄存器地址

```asm
  ldr   r4, =IO_BANK0_BASE                       // r4 = 0x40028000
  add   r4, r4, r1                               // r4 = 0x40028000 + 0x84 = 0x40028084
```

对于 GPIO16, 控制寄存器位于 `0x40028084`.

### 把 FUNCSEL 设为 SIO

```asm
  ldr   r5, [r4]                                 // 读取当前控制值
  bic   r5, r5, #0x1f                            // 清除 FUNCSEL bits [4:0]
  orr   r5, r5, #0x05                            // 设置 FUNCSEL = 5 (SIO)
  str   r5, [r4]                                 // 写回
```

这是对一个 5 位字段先清后置的操作:

1. 用 `0x1f` (`0b11111`) 做 `bic`, 清除 bits [4:0]
2. 用 `0x05` 做 `orr`, 把该字段设成 5

FUNCSEL = 5 把引脚接到 SIO (Single-cycle IO) 模块:

| FUNCSEL | 功能 |
|---------|----------|
| 0 | SPI |
| 1 | UART |
| 2 | I2C |
| 3 | PWM |
| 5 | SIO |
| 31 | NULL (禁用) |

## 阶段 3: 通过协处理器使能输出

```asm
  ldr   r4, =1                                   // r4 = 1 (使能)
  mcrr  p0, #4, r2, r4, c4                       // OE 使能: 为 GPIO 置输出使能
```

`mcrr` 指令与协处理器 0 (SIO) 通信:

| 字段 | 值 | 含义 |
|-------|-------|---------|
| `p0` | 协处理器 0 | SIO 模块 |
| `#4` | 操作码 | GPIO 位操作 |
| `r2` | GPIO 编号 | 16 |
| `r4` | 值 | 1 (使能) |
| `c4` | 寄存器 | 输出使能控制 |

这条指令在 SIO 模块里为 GPIO16 置上输出使能位. 执行之后, 引脚的输出驱动器就处于工作状态, 可以驱动 LED 了.

## GPIO 配置的三个层次

```
Layer 1: Pad (electrical)     → ISO=0, OD=0, IE=1
Layer 2: IO Bank (routing)    → FUNCSEL=5 (SIO)
Layer 3: SIO (output enable)  → OE=1 for GPIO16
```

三个层次都必须配置正确, 引脚才能驱动输出. 任何一层配错都会出问题:

| 配置错误 | 结果 |
|-----------------|--------|
| ISO=1 | 引脚在电气上断开 |
| OD=1 | 输出驱动器被禁用 |
| FUNCSEL≠5 | 引脚被接到错误的外设 |
| OE=0 | SIO 的输出没有驱动 |

## main.s 如何调用 GPIO_Config

```asm
  ldr   r0, =PADS_BANK0_GPIO16_OFFSET            // r0 = 0x44
  ldr   r1, =IO_BANK0_GPIO16_CTRL_OFFSET         // r1 = 0x84
  ldr   r2, =16                                  // r2 = GPIO 编号
  bl    GPIO_Config                              // 配置 GPIO16
```

## 小结

- GPIO_Config 分三个阶段把 GPIO 引脚配置成输出: pad, 功能选择, 输出使能.
- pad 寄存器 (PADS_BANK0) 控制电气特性: 清除 ISO 和 OD, 置上 IE.
- 控制寄存器 (IO_BANK0) 通过 FUNCSEL = 5 把引脚接到 SIO.
- SIO 协处理器 (`mcrr p0, #4, r2, r4, c4`) 使能输出驱动器.
- 这个函数接受偏移量作为参数, 因此可以复用于任意 GPIO 引脚.
- 三层都必须配置正确, 输出才能正常工作.
