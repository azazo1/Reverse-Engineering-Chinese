# Chapter 12: ARM 调用, 返回与栈帧

## 引言

结构化的软件由一个个函数组成, 函数又会调用别的函数. Cortex-M33 用 `bl` (带链接的分支) 实现调用, 用 `bx lr` (经由链接寄存器分支并交换) 实现返回. 当函数层层嵌套 - 调用方调用了被调用方, 被调用方又调用了另一个被调用方 - 链接寄存器就必须保存到栈上. 本章考察闪烁驱动里调用, 返回和栈帧是如何协同工作的.

## 链接寄存器

`bl` 执行时, 处理器把下一条指令的地址存进链接寄存器 (LR, 也叫 r14):

```
Before bl:
  PC = 0x10000100   (bl GPIO_Set instruction)
  LR = (previous)

After bl:
  PC = GPIO_Set     (target address)
  LR = 0x10000104   (return address, next instruction)
```

被调用方执行 `bx lr` 就返回了, 这条指令把 LR 装回 PC.

## 叶子函数与非叶子函数

**叶子函数**不调用任何其他函数. 它可以直接使用 LR, 不必保存:

```asm
Init_Stack:
  ldr   r0, =STACK_TOP                           // r0 = 栈顶
  msr   PSP, r0                                  // 设置进程栈指针
  ldr   r0, =STACK_LIMIT                         // r0 = 栈上限
  msr   MSPLIM, r0                               // 设置主栈上限
  msr   PSPLIM, r0                               // 设置进程栈上限
  ldr   r0, =STACK_TOP                           // r0 = 栈顶
  msr   MSP, r0                                  // 设置主栈指针
  bx    lr                                       // 返回 (LR 未被破坏)
```

**非叶子函数**会调用其他函数, 而调用会覆盖 LR. 所以它必须在入口保存 LR, 在出口恢复:

```asm
main:
  push  {r4-r12, lr}                             // 保存 LR (以及工作寄存器)
  ...
  bl    GPIO_Config                              // LR 被覆盖
  ...
  bl    GPIO_Set                                 // LR 再次被覆盖
  ...
  pop   {r4-r12, lr}                             // 恢复原来的 LR
  bx    lr                                       // 返回调用方
```

## 调用链

闪烁驱动的调用层次是这样的:

```
Reset_Handler
  +-- Init_Stack          (leaf)
  +-- Init_XOSC           (leaf)
  +-- Enable_XOSC_Peri_Clock  (leaf)
  +-- Init_Subsystem      (leaf)
  +-- Enable_Coprocessor  (leaf)
  +-- main                (non-leaf)
        +-- GPIO_Config   (leaf)
        +-- GPIO_Set      (leaf)
        +-- Delay_MS      (leaf)
        +-- GPIO_Clear    (leaf)
```

Reset_Handler 用 `bl` 调用每个初始化函数, 然后用 `b main` (普通分支, 不是带链接的分支) 跳过去, 因为 main 永远不会返回. 在 main 内部, 再用 `bl` 调用 GPIO 和延时函数.

## 栈帧

`push {r4-r12, lr}` 执行时, 栈指针减小, 寄存器被逐个保存:

```
High addresses (STACK_TOP = 0x20082000)
+------------------+
| lr               |  SP + 36
| r12              |  SP + 32
| r11              |  SP + 28
| r10              |  SP + 24
| r9               |  SP + 20
| r8               |  SP + 16
| r7               |  SP + 12
| r6               |  SP + 8
| r5               |  SP + 4
| r4               |  SP + 0   <-- SP after push
+------------------+
Low addresses
```

函数返回时, `pop {r4-r12, lr}` 恢复每一个寄存器, 并把 SP 加回去.

## 嵌套调用

当 `main` 调用 `GPIO_Set`, 而 GPIO_Set 又压入自己的寄存器时:

```
+------------------+
| main's lr        |  main's frame
| main's r12       |
| ...              |
| main's r4        |
+------------------+
| GPIO_Set's lr    |  GPIO_Set's frame
| GPIO_Set's r12   |
| ...              |
| GPIO_Set's r0    |
+------------------+  <-- SP
```

每个函数都有自己的栈帧. GPIO_Set 返回时, 它的栈帧就被撤掉. main 的循环再调用 GPIO_Clear 时, 会在同一位置建立新的栈帧.

## ARM 调用约定 (AAPCS)

我们的固件遵循 ARM 架构过程调用标准 (AAPCS):

| 寄存器 | 角色 | 调用方/被调用方保存 |
|----------|------|-------------------|
| r0-r3 | 参数与返回值 | 调用方保存 (临时) |
| r4-r11 | 通用 | 被调用方保存 (必须保持) |
| r12 | 过程内临时寄存器 | 调用方保存 |
| r13 (SP) | 栈指针 | 被调用方保存 |
| r14 (LR) | 链接寄存器 | 被调用方保存 (非叶子时) |
| r15 (PC) | 程序计数器 | - |

我们的函数正好体现了这套约定:

- `main` 在 r0 里传 GPIO 编号, 也在 r0 里传延时毫秒数
- `GPIO_Config` 接收 pad 偏移 (r0), ctrl 偏移 (r1), GPIO 编号 (r2)
- `GPIO_Set` 和 `GPIO_Clear` 在 r0 里接收 GPIO 编号
- `Delay_MS` 在 r0 里接收毫秒数

## 参数传递示例

main 调用 GPIO_Config 时:

```asm
  ldr   r0, =PADS_BANK0_GPIO16_OFFSET            // r0 = pad 偏移
  ldr   r1, =IO_BANK0_GPIO16_CTRL_OFFSET          // r1 = ctrl 偏移
  mov   r2, #16                                  // r2 = GPIO 编号
  bl    GPIO_Config                              // 调用
```

被调用方直接在 r0, r1, r2 里拿到这些值, 不需要任何额外机制.

main 调用 GPIO_Set 时:

```asm
  mov   r0, #16                                  // r0 = GPIO 编号
  bl    GPIO_Set                                 // 调用
```

## Reset_Handler: 一个特例

Reset_Handler 永远不返回. 它用 `bl` 调用各个初始化函数, 然后用 `b` (不是 `bl`) 跳到 main:

```asm
Reset_Handler:
  bl    Init_Stack                               // 经由 bx lr 返回
  bl    Init_XOSC                                // 经由 bx lr 返回
  bl    Enable_XOSC_Peri_Clock                   // 经由 bx lr 返回
  bl    Init_Subsystem                           // 经由 bx lr 返回
  bl    Enable_Coprocessor                       // 经由 bx lr 返回
  b     main                                     // 永不返回
```

用 `b` 而不是 `bl`, 意味着 main 里的 LR 值还是最后一次 `bl` 留下的返回地址 - 但 main 里是个无限循环, 所以这一点无关紧要. 系统永远不会从 main 返回.

## 小结

- `bl` 把返回地址保存到 LR, 然后跳转到目标函数.
- `bx lr` 把 LR 装回 PC, 从而返回调用方.
- 非叶子函数用 `push` 保存 LR, 用 `pop` 恢复 LR.
- 栈向低地址方向增长; 每个函数都为自己的被保存寄存器建立一帧.
- AAPCS 规定 r0-r3 是参数/返回寄存器, r4-r11 由被调用方保存.
- Reset_Handler 用 `b main` (不是 `bl`), 因为系统永远不会返回.
