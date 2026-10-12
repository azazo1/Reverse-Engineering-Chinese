# 逆向分析: embedded-wasm-blinky

## 目录

1. [二进制概览](#1-二进制概览)
2. [ELF 头](#2-elf-头)
3. [段布局](#3-段布局)
4. [内存映射与段](#4-内存映射与段)
5. [启动流程](#5-启动流程)
6. [中断向量表](#6-中断向量表)
7. [固件函数映射](#7-固件函数映射)
8. [硬件寄存器访问](#8-硬件寄存器访问)
9. [Pulley 解释器深入剖析](#9-pulley-解释器深入剖析)
10. [内嵌的 cwasm 数据块](#10-内嵌的-cwasm-数据块)
11. [宿主与客体调用流程](#11-宿主与客体调用流程)
12. [逆向观察](#12-逆向观察)
13. [Pulley 指令集架构](#13-pulley-指令集架构)
14. [Pulley 字节码反汇编](#14-pulley-字节码反汇编)
15. [Ghidra 分析实战](#15-ghidra-分析实战)

---

## 1. 二进制概览

| 属性              | 值                                       |
| ----------------- | ---------------------------------------- |
| 文件              | `embedded-wasm-blinky`                   |
| 磁盘大小          | 1,174,232 字节 (1.12 MiB)                |
| 格式              | ELF32 ARM 小端                           |
| ABI               | EABI5, 硬浮点                            |
| 目标              | ARMv8-M Mainline (Cortex-M33)            |
| MCU               | RP2350 (Raspberry Pi Pico 2)             |
| 是否 strip        | 否 (符号表 + 字符串表都在)               |
| 代码函数数        | 2,375                                    |
| 只读符号数        | 2,660                                    |

这个二进制是一份裸机 `no_std` Rust 固件, 内部承载着 Wasmtime 组件模型
运行时和 Pulley 字节码解释器. 它以 500 ms 的间隔让 GPIO25 上的板载
LED 闪烁, 而闪烁逻辑本身是作为一个 WebAssembly 客体
组件运行的.

---

## 2. ELF 头

```
Magic:   7f 45 4c 46 01 01 01 03 00 00 00 00 00 00 00 00
Class:                             ELF32
Data:                              2's complement, little endian
Version:                           1 (current)
OS/ABI:                            UNIX - GNU
Type:                              EXEC (Executable file)
Machine:                           ARM
Entry point address:               0x1000010d
Flags:                             0x5000400, Version5 EABI, hard-float ABI
Program headers:                   6 (at offset 52)
Section headers:                   16 (at offset 1,173,592)
```

**入口点**: `0x1000010d` - `.text` 里的 `Reset` 处理程序. 最低位被
置 1 (0x0D 而非 0x0C) 以表示 Thumb 模式, 这是 ARMv8-M 的要求. 真正的
代码从 `0x1000010c` 开始.

---

## 3. 段布局

```
Nr  Name            Type        Addr        Size      Flags  Description
 1  .vector_table   PROGBITS    0x10000000  0x000f8   A      ARM exception + interrupt vectors
 2  .start_block    PROGBITS    0x100000f8  0x00014   AR     RP2350 IMAGE_DEF boot metadata
 3  .text           PROGBITS    0x1000010c  0x84c70   AX     All executable code (532 KiB)
 4  .bi_entries     PROGBITS    0x10084d7c  0x00000   A      Binary info entries (empty)
 5  .rodata         PROGBITS    0x10084d80  0x1dbb0   AMSR   Read-only data (120 KiB)
 6  .data           PROGBITS    0x20000000  0x00024   WA     Initialized globals (36 bytes)
 7  .gnu.sgstubs    PROGBITS    0x100a2960  0x00000   A      Secure gateway stubs (empty)
 8  .bss            NOBITS      0x20000028  0x400a4   WA     Zero-init data (256 KiB)
 9  .uninit         NOBITS      0x200400cc  0x00000   WA     Uninitialized memory (empty)
10  .end_block      PROGBITS    0x100a2960  0x00000   WA     Block end marker (empty)
13  .symtab         SYMTAB      file only   0x1dea0          Symbol table (7,702 entries)
15  .strtab         STRTAB      file only   0x5dda0          String table (383 KiB)
```

### 大小分解

Pico 2 板子有 **4 MiB** (4,194,304 B) 的外部 QSPI flash.
链接脚本 (`rp2350.x`) 保守地只分配了 **2 MiB**
(2,097,152 B). 下面的百分比都是相对 4 MiB 物理
flash 而言的.

| 区域           | 段              | 大小          | 占 4 MiB Flash 的比例 |
| -------------- | --------------- | ------------- | -------------------- |
| 代码           | `.text`         | 544,880 B     | 13.0%                |
| 常量           | `.rodata`       | 122,800 B     | 2.9%                 |
| 向量表         | `.vector_table` | 248 B         | <0.1%                |
| 启动元数据     | `.start_block`  | 20 B          | <0.1%                |
| 初始化数据     | `.data`         | 36 B          | <0.1%                |
| **已用 Flash** |                 | **667,984 B** | **15.9%**            |
| **剩余 Flash** |                 | 3,526,320 B   | 84.1%                |
| BSS (RAM)      | `.bss`          | 262,308 B     | 占 512 KiB RAM 的 51.2% |

固件用了 4 MiB flash 里的 652 KiB (占链接器分配的 2 MiB
的 31.9%). `.text` 段 (532 KiB) 绝大部分是 Wasmtime 运行时:
Pulley 解释器的派发循环, 组件元数据的 serde
反序列化, BTree 容器, 类型注册表,
以及组件链接器代码. 真正属于 blinky 固件的函数只占
大约 2 KiB.

---

## 4. 内存映射与段

```
Segment  VirtAddr     PhysAddr     MemSiz   Flags  Contents
  0      0x10000000   0x10000000   0x0010c  R      .vector_table + .start_block
  1      0x1000010c   0x1000010c   0x84c70  R E    .text (executable code)
  2      0x10084d7c   0x10084d7c   0x1dbb4  R      .rodata (constants + cwasm blob)
  3      0x20000000   0x100a2930   0x00024  RW     .data (LMA in flash, VMA in RAM)
  4      0x20000028   0x20000028   0x400a4  RW     .bss (zero-filled at boot)
  5      0x00000000   0x00000000   0x00000  RW     GNU_STACK (zero-size)
```

### 物理地址空间

```
Flash (XIP):  0x10000000 - 0x100a2953  (668 KiB used of 4 MiB)
              +-- 0x10000000  Vector table (248 B)
              +-- 0x100000f8  IMAGE_DEF boot block (20 B)
              +-- 0x1000010c  .text starts (Reset handler)
              +-- 0x10084d80  .rodata starts
              +-- 0x1008a059  Embedded cwasm (Pulley ELF, ~24 KiB)
              +-- 0x100a2930  .data initializers (36 B, copied to RAM)

RAM (SRAM):   0x20000000 - 0x200400cb  (256 KiB used of 512 KiB)
              +-- 0x20000000  .data (36 B: UART state, TLS value)
              +-- 0x20000028  TLS_VALUE (4 B)
              +-- 0x2000002c  led::PINS (16 B)
              +-- 0x2000003c  HEAP_MEM (262,144 B = 256 KiB)
              +-- 0x2004003c  HEAP allocator struct (32 B)

Stack:        0x20080000  Initial SP (top of 512 KiB SRAM, grows down)
```

**段 3** 的加载地址是分离的: `PhysAddr = 0x100a2930` (flash),
而 `VirtAddr = 0x20000000` (RAM). Reset 处理程序在 `.data` 初始化
循环里把这 36 个字节从 flash 复制到 RAM.

---

## 5. 启动流程

### 5.1 RP2350 引导 ROM -> IMAGE_DEF

RP2350 引导 ROM 会在 flash 里扫描合法的镜像定义块. 我们位于
`0x100000f8` 的 `.start_block` 段内容是:

```
d3deffff 42012110 ff010000 00000000 793512ab
```

这就是 `hal::block::ImageDef::secure_exe()` - 它告诉引导 ROM
这是一个安全的 ARM 可执行文件, 于是 ROM 会配置好 XIP 并
把控制权交给向量表.

### 5.2 向量表 -> Reset 处理程序

处理器读取位于 `0x10000000` 的向量表:

```
Word 0: 0x20080000  <- Initial Stack Pointer (top of 512 KiB SRAM)
Word 1: 0x1000010d  <- Reset vector (Thumb-mode address of Reset handler)
```

上电复位之后, CPU 从 word 0 加载 SP, 然后跳转到
Reset 向量.

### 5.3 Reset 处理程序 (0x1000010c)

```armasm
Reset:
    bl      DefaultPreInit          ; 空操作 (空的预初始化钩子)

    ; --- 清零 .bss (0x20000028 -> 0x200400cc) ---
    ldr     r0, =0x20000028         ; BSS 起始
    ldr     r1, =0x200400cc         ; BSS 结束
    movs    r2, #0
.bss_loop:
    cmp     r1, r0
    beq     .bss_done
    stmia   r0!, {r2}              ; 写入零, 指针前进
    b       .bss_loop

    ; --- 把 .data 从 flash 复制到 RAM ---
.bss_done:
    ldr     r0, =0x20000000         ; RAM 目标 (.data VMA)
    ldr     r1, =0x20000024         ; RAM 结束
    ldr     r2, =0x100a2930         ; Flash 源 (.data LMA)
.data_loop:
    cmp     r1, r0
    beq     .data_done
    ldmia   r2!, {r3}
    stmia   r0!, {r3}
    b       .data_loop

    ; --- 使能 FPU ---
.data_done:
    ldr     r0, =0xe000ed88         ; CPACR (协处理器访问控制)
    ldr     r2, [r0]
    orr     r2, r2, #0xf00000      ; 完全放开 CP10 + CP11 (FPU)
    str     r2, [r0]
    dsb     sy
    isb     sy

    bl      main                    ; 进入 Rust main()
    udf     #0                      ; 若 main 返回则陷入 (不应该发生)
```

### 5.4 `main()` (0x10008410)

`#[hal::entry]` 宏生成一个很薄的包装函数, 它调用位于
`0x100075a8` 的 `__cortex_m_rt_main`:

```armasm
main:
    ; 使能全部 32 路 SIO GPIO 输出
    ldr     r0, =0xd0000100         ; SIO GPIO_OE 基址
    movs    r1, #1
    str     r1, [r0, #0]            ; 为每个 bank 设置 GPIO_OE_SET
    ...

    ; 使能 FPU (冗余, Reset 里也做过 - 双保险)
    ldr     r0, =0xe000ed88         ; CPACR
    ldr     r1, [r0]
    orr     r1, r1, #0x303          ; CP10 + CP11 完全放开
    str     r1, [r0]

    bl      init_heap               ; 初始化 256 KiB 堆分配器
    bl      init_hardware           ; 时钟配置, UART, GPIO
    bl      run_wasm                ; 创建 Wasmtime 引擎, 运行组件
```

---

## 6. 中断向量表

位于 `0x10000000` 的向量表有 248 字节 (62 项):

```
Offset  Vector              Handler          Address
0x0000  Initial SP          -                0x20080000
0x0004  Reset               Reset            0x1000010d
0x0008  NMI                 DefaultHandler   0x1007c7ed
0x000c  HardFault           HardFault_       0x10084d75
0x0010  MemManage           DefaultHandler   0x1007c7ed
0x0014  BusFault            DefaultHandler   0x1007c7ed
0x0018  UsageFault          DefaultHandler   0x1007c7ed
0x001c  SecureFault         DefaultHandler   0x1007c7ed
0x0020  Reserved            -                0x00000000
0x0024  Reserved            -                0x00000000
0x0028  Reserved            -                0x00000000
0x002c  SVCall              DefaultHandler   0x1007c7ed
0x0030  DebugMonitor        DefaultHandler   0x1007c7ed
0x0034  Reserved            -                0x00000000
0x0038  PendSV              DefaultHandler   0x1007c7ed
0x003c  SysTick             DefaultHandler   0x1007c7ed
0x0040+ IRQ0-IRQ51          DefaultHandler   0x1007c7ed
```

### DefaultHandler (0x1007c7ec)

```armasm
DefaultHandler_:
    push    {r7, lr}
    mov     r7, sp
    b.n     .                       ; 死循环 (未处理异常时挂起)
```

### HardFault (0x10084d74)

```armasm
HardFault_:
    push    {r7, lr}
    mov     r7, sp
    b.n     .                       ; 死循环 (硬错误时挂起)
```

两个处理程序都保存帧指针然后永远自旋. 这是 `cortex-m-rt`
的默认行为 - 不做恢复, 也不输出诊断信息.

固件不使用任何外设中断. 全部 52 个 IRQ 向量都指向
`DefaultHandler`. 整个固件完全是轮询式的:

- GPIO 写入是直接写 SIO 寄存器
- UART 发送是阻塞的 (轮询 TXFF 标志)
- 延时通过 `cortex_m::delay::Delay` 轮询 SysTick

---

## 7. 固件函数映射

### 7.1 应用函数

| 地址         | 大小  | 符号                 | 用途                                                                      |
| ------------ | ----- | -------------------- | ------------------------------------------------------------------------- |
| `0x1000010c` | 0x3e  | `Reset`              | BSS 清零, .data 复制, 使能 FPU, 调用 main                                 |
| `0x100073dc` | 0x1cc | `init_hardware`      | 时钟, UART0, GPIO25, SysTick                                              |
| `0x100075a8` | 0x6c  | `__cortex_m_rt_main` | 使能 SIO GPIO, FPU, init_heap, init_hardware, run_wasm                    |
| `0x10007760` | 0x856 | `run_wasm`           | Engine::new, Component::deserialize, Store::new, Linker, instantiate, run |
| `0x10007fb8` | 0x20  | `init_heap`          | 初始化 256 KiB 链表堆                                                     |
| `0x10006858` | 0xc2  | `led::set_low`       | 通过 SIO 清除 GPIO, UART 日志                                             |
| `0x1000691c` | 0xc2  | `led::set_high`      | 通过 SIO 置位 GPIO, UART 日志                                             |
| `0x100069e0` | 0x108 | `led::store_pin`     | 为 led 模块保存 GPIO 引脚句柄                                             |
| `0x10007614` | 0x14c | `uart::write_msg`    | 阻塞式 UART 发送                                                          |
| `0x10008410` | 0x8   | `main`               | 很薄的 #[entry] 包装                                                      |
| `0x1007c7ec` | 0x6   | `DefaultHandler`     | 死循环 (未处理异常)                                                       |
| `0x1007c7f4` | 0x6   | `DefaultPreInit`     | 空操作 (立即返回)                                                         |
| `0x10084d74` | 0x6   | `HardFault`          | 死循环 (硬错误)                                                           |

### 7.2 Wasmtime 运行时 (按大小排前 20)

| 地址         | 大小     | 还原后的名称                                                   |
| ------------ | -------- | -------------------------------------------------------------- |
| `0x10032c98` | 16,464 B | `wasmtime_environ::tunables::OperatorCost::deserialize`        |
| `0x10068210` | 16,456 B | `pulley_interpreter::decode::decode_one_extended`              |
| `0x10064ef4` | 12,518 B | `pulley_interpreter::interp::Interpreter::run` (派发循环)      |
| `0x1002e43c` | 8,696 B  | `wasmtime::engine::serialization::Metadata::check_cost`        |
| `0x1000d7b8` | 2,304 B  | `wasmtime::runtime::vm::interpreter::InterpreterRef::call`     |

### 7.3 BSS 布局

| 地址         | 大小      | 符号        | 用途                            |
| ------------ | --------- | ----------- | ------------------------------- |
| `0x20000028` | 4 B       | `TLS_VALUE` | Wasmtime TLS 垫片 (platform.rs) |
| `0x2000002c` | 16 B      | `led::PINS` | LED 模块的 GPIO 引脚句柄        |
| `0x2000003c` | 262,144 B | `HEAP_MEM`  | 堆的原始后备内存                |
| `0x2004003c` | 32 B      | `HEAP`      | 链表分配器状态                  |

### 7.4 .data 布局

| 地址         | 大小 | 符号            | 用途                         |
| ------------ | ---- | --------------- | ---------------------------- |
| `0x20000000` | 1 B  | `UART` (.1)     | UART 初始化标志              |
| `0x20000001` | 35 B | (填充/其他)     | 其余 .data 初始化数据        |

---

## 8. 硬件寄存器访问

### 8.1 外设基地址

| 基地址       | 外设       | 固件中的用途            |
| ------------ | ---------- | ----------------------- |
| `0x40020000` | RESETS     | 子系统复位控制          |
| `0x40028000` | IO_BANK0   | GPIO 功能选择           |
| `0x40030000` | PADS_BANK0 | 焊盘配置                |
| `0x40040000` | XOSC       | 晶体振荡器              |
| `0x40048000` | PLL_SYS    | 系统 PLL (150 MHz)      |
| `0x4004c000` | PLL_USB    | USB PLL (48 MHz)        |
| `0x40050000` | CLOCKS     | 时钟发生器              |
| `0x40070000` | UART0      | 调试串口输出            |
| `0xd0000000` | SIO        | 单周期 I/O (GPIO)       |
| `0xe000e010` | SysTick    | 系统定时器 (延时)       |
| `0xe000ed88` | CPACR      | FPU 访问控制            |

### 8.2 GPIO 控制 (LED 闪烁)

LED 模块直接写 SIO (Single-cycle I/O) 寄存器
来翻转 GPIO25:

```
led::set_high (0x1000691c):
    ; SIO GPIO output set register
    ldr     r0, =0xd0000014         ; SIO GPIO_OUT_SET
    movs    r1, #1
    lsls    r1, r1, #25             ; Bit 25 (GPIO25)
    str     r1, [r0]                ; Set GPIO25 high

led::set_low (0x10006858):
    ; SIO GPIO output clear register
    ldr     r0, =0xd0000018         ; SIO GPIO_OUT_CLR
    movs    r1, #1
    lsls    r1, r1, #25             ; Bit 25 (GPIO25)
    str     r1, [r0]                ; Set GPIO25 low
```

GPIO25 在 `init_hardware` 期间被配置为推挽 SIO 输出:

```
init_hardware (0x100073dc):
    ; Configure GPIO25 pad
    movw    r0, #0x806c
    movt    r0, #0x4003             ; 0x4003806c = PADS_BANK0 GPIO25
    ldr     r1, [r0]
    bfi     r1, r2, #6, #3         ; Output enable, drive strength
    str     r1, [r0]

    ; Set GPIO25 function to SIO (function 5)
    movw    r0, #0x80cc
    movt    r0, #0x4002             ; 0x400280cc = IO_BANK0 GPIO25_CTRL
    movs    r1, #5                  ; Function 5 = SIO
    str     r1, [r0]
```

### 8.3 SysTick 定时器 (延时)

```
init_hardware:
    ; Configure SysTick for processor clock
    movw    r1, #0xe010
    movt    r1, #0xe000             ; 0xe000e010 = SYST_CSR
    ldr     r0, [r1]
    orr     r2, r0, #4             ; Set CLKSOURCE (processor clock)
    str     r2, [r1]
```

### 8.4 UART0 配置

```
uart::init:
    ; GPIO0 -> UART0 TX (function 2)
    ; GPIO1 -> UART0 RX (function 2)
    ; Baud rate 115200 at 150 MHz:
    ;   IBRD = 81, FBRD = 24
    ; UART0 base = 0x40070000
```

---

## 9. Pulley 解释器深入剖析

### 9.1 架构

Pulley 是 Wasmtime 的可移植字节码解释器. 构建脚本不生成
本机 ARM 代码 (那需要 JIT 和 MMU), 而是在 `cargo build` 期间
把 Wasm 组件 AOT 编译成 Pulley 字节码.
运行时, ARM 固件逐条指令地解释这些
字节码.

### 9.2 解释器入口 (`InterpreterRef::call`)

```
Location:  0x1000d7b8  (2,304 bytes)
```

这个函数是本机 ARM 代码与 Pulley 虚拟机之间的桥梁.
调用顺序:

```
run_wasm()
  -> Blinky::instantiate()
    -> Blinky::call_run()
      -> InterpreterRef::call()     <-- native-to-Pulley boundary
        -> Vm::call_start()         ; Set up Pulley register file
        -> Vm::call_run()           ; Enter interpreter loop
          -> Interpreter::run()     ; Main dispatch loop
```

### 9.3 主派发循环 (`Interpreter::run`)

```
Location:  0x10064ef4  (12,518 bytes)
```

这是执行 Pulley 字节码的热点循环. 它采用两级
派发方案:

**第 1 级: 主操作码 (1 字节)**

```armasm
Interpreter::run (0x10064ef4):
    push    {r4-r7, lr}
    stmdb   sp!, {r8-r11}
    sub     sp, #12
    mov.w   r8, #0x80000000         ; 哨兵值

.fetch:
    mov     r0, r1                  ; r1 = 程序计数器 (PC)
    ldrb.w  r2, [r0], #1           ; 取 1 字节操作码, PC 前进
    str     r0, [sp, #8]            ; 保存更新后的 PC

    tbh     [pc, r2, lsl #1]        ; Table Branch Halfword - 256 项跳转表
```

`tbh` 指令是 Thumb-2 的表分支. 它从 `pc + r2*2` 读取一个半字,
然后跳转到 `pc + offset*2`. 这就实现了一个直接的
计算跳转, 通向 256 个可能的操作码处理程序.

**第 2 级: 扩展操作码 (2 字节前缀)**

当主操作码是 "扩展" 哨兵值 (0xDC) 时, 会再取一个
2 字节的操作码:

```
Location:  0x10068210  (16,456 bytes)
```

### 9.4 寄存器文件

Pulley 虚拟机使用一个虚拟寄存器文件, 存放在 `Vm` 结构体里:

- **x0-x30**: 64 位通用寄存器 (位于偏移 `+0x200`,
  每个 8 字节)
- **f0-f31**: 128 位浮点/向量寄存器
- **sp**: 栈指针 (位于相对 Vm 基址的偏移 `+0x40c`)
- **lr**: 返回地址寄存器

### 9.5 宿主调用机制

当 Pulley 字节码调用一个宿主导入的函数 (比如
`gpio::set_high` 或 `timing::delay_ms`) 时, 解释器会带着返回码 0
(`CallIndirectHost`) 返回. `InterpreterRef::call` 的循环会:

1. 从 Pulley 状态里读出宿主函数索引
2. 在陷阱处理程序的 TLS 里查找这个宿主函数
3. 直接调用本机 ARM 宿主函数
4. 把返回值写回 Pulley 寄存器
5. 重新进入 `Vm::call_run` 继续解释

---

## 10. 内嵌的 cwasm 数据块

### 10.1 位置与格式

预编译好的 Pulley 字节码内嵌在 `.rodata` 的
`0x1008a059` 处, 由 `WASM_BINARY` 常量引用. 它
有 **24,680 字节** (0x6068).

这个数据块本身就是一个 **ELF 文件** - Wasmtime 的序列化格式
把 Pulley 字节码包在标准的 ELF 容器里:

```
Hex dump at 0x1008a059:
7f 45 4c 46 02 01 01 c8 ... .ELF....
```

头部解析:

| 字段   | 值                             |
| ------ | ------------------------------ |
| Magic  | `\x7fELF`                      |
| Class  | ELF64 (偏移 4 处的字节 `02`)   |
| Data   | 小端                           |
| Target | `pulley32-unknown-unknown-elf` |

### 10.2 构建流水线

cwasm 由构建脚本 (`build.rs`) 生成:

```
wasm-app/src/lib.rs
    |
    v  (cargo build --target wasm32-unknown-unknown)
wasm_app.wasm  (core Wasm module with wit-bindgen metadata)
    |
    v  (ComponentEncoder::encode())
component.wasm  (Wasm Component Model binary)
    |
    v  (engine.precompile_component())
blinky.cwasm  (Pulley ELF container with pre-lowered bytecode)
    |
    v  (include_bytes! in firmware)
WASM_BINARY const in .rodata
```

运行时, `Component::deserialize()` 读取这个数据块, 校验
引擎配置是否匹配 (目标, tunables, 内存设置), 然后
为解释器映射 Pulley 字节码的各段.

### 10.3 客体代码逻辑

客体组件 (`wasm-app/src/lib.rs`) 编译成实现下面逻辑的 Pulley
字节码:

```
const LED_PIN: u32 = 25;
loop {
    call_import gpio::set_high(LED_PIN)    -> host ARM code
    call_import timing::delay_ms(500)      -> host ARM code
    call_import gpio::set_low(LED_PIN)     -> host ARM code
    call_import timing::delay_ms(500)      -> host ARM code
}
```

每次 `call_import` 都会触发 Pulley 解释器里的 `CallIndirectHost`
返回路径, 从字节码执行切换到本机 ARM
宿主函数.

---

## 11. 宿主与客体调用流程

### 11.1 `gpio::set_high(25)` 的完整调用链

```
[Pulley VM]  Bytecode: call_indirect_host #0, args=[25]
    |
    v  (Interpreter::run returns CallIndirectHost)
[ARM Native]  InterpreterRef::call (0x1000d7b8)
    |  reads host function index, dispatches
    v
[ARM Native]  <HostState as gpio::Host>::set_high
    |
    v
[ARM Native]  led::set_high (0x1000691c)
    |
    v
[Hardware]  SIO GPIO_OUT_SET @ 0xd0000014
            Bit 25 set = GPIO25 driven high (LED on)
```

### 11.2 `timing::delay_ms(500)` 的完整调用链

```
[Pulley VM]  Bytecode: call_indirect_host #2, args=[500]
    |
    v  (Interpreter::run returns CallIndirectHost)
[ARM Native]  InterpreterRef::call (0x1000d7b8)
    |
    v
[ARM Native]  <HostState as timing::Host>::delay_ms
    |
    v
[Hardware]  SysTick countdown for 500 ms (polling loop)
```

### 11.3 UART 诊断输出

置位或清除 GPIO 之后, 宿主函数会通过 UART0 写一条
诊断信息:

```
led::set_high:
    bl      uart::write_msg         ; Print "GPIO 25 High\n"

led::set_low:
    bl      uart::write_msg         ; Print "GPIO 25 Low\n"
```

---

## 12. 逆向观察

### 12.1 二进制构成

固件里约 99.6% 是 Wasmtime 运行时, 约 0.4% 是应用代码:

| 组成                        | 大致大小    | 占 .text 比例 |
| --------------------------- | ----------- | ---------- |
| Wasmtime 运行时             | ~542 KiB    | 99.4%      |
| Pulley 解释器 (run)         | 12.2 KiB    | 2.3%       |
| Pulley 解码器 (extended)    | 16.1 KiB    | 3.0%       |
| Serde 反序列化              | ~50 KiB     | 9.2%       |
| 应用代码 (led+uart+main)    | ~2.5 KiB    | 0.5%       |

### 12.2 逆向工程师在 Ghidra 里会看到什么

用 ARM Cortex 处理器模块在 Ghidra 里打开这个二进制:

1. **一眼就能认出**: 带符号的 ELF - Ghidra 会自动分析并命名
   约 7,700 个函数. Rust 的名称修饰结果很长, 但可读.

2. **中断向量表**: Ghidra 的 ARM 分析器会找到位于
   `0x10000000` 的向量表, 并识别出 Reset 处理程序.

3. **`tbh` 派发**: Pulley 解释器在 `0x10064f18` 处的 `tbh` (Table Branch
   Halfword) 构成一个 256 项的 switch 语句. Ghidra
   会把它识别成 switch/case 并生成带标签的分支, 但
   规模实在太大 (12 KiB 的处理程序), 手工分析很枯燥.

4. **没有混淆**: 二进制没有 strip, 没有加壳, 而且带
   完整的符号表. 所有函数边界都能恢复出来.

5. **cwasm 数据块**: 逆向工程师会在 `.rodata` 里发现 `\x7fELF` 魔数,
   认出这是一个内嵌的 ELF. 把它单独提取出来分析, 就会看到 Pulley
   字节码 - 一套陌生的 ISA, 要反汇编它得先弄懂
   Pulley 的操作码表.

6. **硬件识别**: 外设基地址
   (`0xd0000014` SIO, `0x40070000` UART0) 立刻就能确定这是
   RP2350/RP2040 系列的芯片.

### 12.3 安全性观察

- **没有代码签名**: ELF 以普通二进制方式加载, Wasmtime 层面不做
  签名校验 (RP2350 的安全启动是另一回事).

- **完整符号表**: 383 KiB 的调试字符串暴露了内部
  结构, 函数名和 crate 依赖. 生产构建
  应该 strip 符号 (`cargo build --release` + `strip`).

- **执行是确定性的**: 没有中断, 没有 DMA - 固件
  完全是顺序且可预测的, 这让逆向和
  时序分析都变简单了.

- **Wasmtime 沙箱**: Wasm 客体无法直接访问硬件;
  所有 I/O 都经过宿主的 `set_high`, `set_low` 和 `delay_ms`
  函数, 这就把客体的能力限制在 LED 控制和
  延时上.

### 12.4 关键地址速查

| 地址         | 说明                                          |
| ------------ | --------------------------------------------- |
| `0x10000000` | 向量表 (初始 SP + 异常向量)                   |
| `0x100000f8` | RP2350 IMAGE_DEF 启动块                       |
| `0x1000010c` | Reset 处理程序 (入口点)                       |
| `0x100073dc` | init_hardware                                 |
| `0x100075a8` | __cortex_m_rt_main                            |
| `0x10007760` | run_wasm                                      |
| `0x10007fb8` | init_heap                                     |
| `0x1000691c` | led::set_high (宿主绑定)                      |
| `0x10006858` | led::set_low (宿主绑定)                       |
| `0x10008410` | main (很薄的包装)                             |
| `0x10007614` | uart::write_msg                               |
| `0x10064ef4` | Pulley Interpreter::run (派发循环)            |
| `0x10068210` | Pulley decode_one_extended                    |
| `0x1000d7b8` | InterpreterRef::call (本机到 Pulley 的桥)     |
| `0x1008a059` | 内嵌的 cwasm 数据块 (Pulley ELF)              |
| `0x1007c7ec` | DefaultHandler (死循环)                       |
| `0x10084d74` | HardFault (死循环)                            |
| `0xd0000014` | SIO GPIO_OUT_SET 寄存器                       |
| `0xd0000018` | SIO GPIO_OUT_CLR 寄存器                       |
| `0x40070000` | UART0 基址                                    |
| `0x2000003c` | HEAP_MEM (256 KiB)                            |
| `0x20080000` | 初始栈指针                                    |

---

## 13. Pulley 指令集架构

### 13.1 概览

Pulley 是 Wasmtime 的可移植字节码解释器 (wasmtime 43.0.0,
`pulley-interpreter` crate v43.0.0). 它定义了一套基于寄存器的
ISA, 指令长度可变, 为高效解释而不是本机执行
而设计.

### 13.2 编码格式

**主操作码** 用 1 字节操作码加上操作数:

```
[opcode:1] [operands:0-9]
```

一共有 **220 个主操作码** (0x00-0xDB). 操作码 `0xDC` 是
**ExtendedOp** 哨兵值 - 解释器遇到它时, 会再读一个
2 字节的扩展操作码:

```
[0xDC] [ext_opcode:2] [operands:0-N]
```

一共有 **310 个扩展操作码** (0x0000-0x0135), 用于 SIMD, 浮点
转换以及复杂运算.

### 13.3 寄存器文件

Pulley 有 32 个 64 位通用寄存器:

| 寄存器      | 编号  | 用途                                     |
| ----------- | ----- | ---------------------------------------- |
| `x0`-`x15`  | 0-15  | 参数, 返回值, 临时值                     |
| `x16`-`x25` | 16-25 | 被调用者保存 (由 push_frame_save 压栈)   |
| `x26`-`x29` | 26-29 | 被调用者保存                             |
| `sp`        | 30    | 栈指针                                   |
| `spilltmp0` | 31    | 溢出临时寄存器 (编译器内部用)            |

此外还有 32 个浮点/向量寄存器 (`f0`-`f31`, 每个 128 位),
以及一个专门用于返回地址的链接寄存器 (`lr`).

### 13.4 本二进制用到的关键指令

| 操作码 | 助记符              | 操作数             | 说明                                     |
| ------ | ------------------- | ------------------ | ---------------------------------------- |
| `0x00` | `nop`               | (无)               | 空操作                                   |
| `0x01` | `ret`               | (无)               | 返回调用者 (弹出 lr, 跳转)               |
| `0x02` | `call`              | `i32 offset`       | 相对调用, 保存 lr                        |
| `0x07` | `call_indirect`     | `r`                | 通过寄存器调用 (函数指针)                |
| `0x08` | `jump`              | `i32 offset`       | 无条件相对跳转                           |
| `0x0a` | `br_if32`           | `r, i32 offset`    | 寄存器 != 0 时分支 (32 位判断)           |
| `0x41` | `xmov`              | `r_dst, r_src`     | 复制 64 位寄存器                         |
| `0x42` | `xzero`             | `r`                | 把寄存器置 0                             |
| `0x44` | `xconst8`           | `r, i8`            | 加载符号扩展的 8 位立即数                |
| `0x45` | `xconst16`          | `r, i16`           | 加载符号扩展的 16 位立即数               |
| `0x48` | `xadd32`            | `r, r, r`          | 32 位加法                                |
| `0x84` | `xload32le_o32`     | `r, r, i32`        | 从 base + offset 加载 32 位小端          |
| `0x88` | `xstore32le_o32`    | `r, i32, r`        | 把 32 位小端存入 base + offset           |
| `0xa8` | `push_frame`        | (无)               | 保存 lr, 分配栈帧                        |
| `0xa9` | `pop_frame`         | (无)               | 恢复 lr, 释放栈帧                        |
| `0xaa` | `push_frame_save`   | `u16 amt, bitmask` | 保存 lr 和被调用者保存寄存器, 分配栈帧   |
| `0xab` | `pop_frame_restore` | `u16 amt, bitmask` | 恢复被调用者保存寄存器和 lr, 释放栈帧    |
| `0xdc` | *(扩展前缀)*        | `u16 ext_op, ...`  | 扩展操作码哨兵值                         |

#### 扩展操作码

| 扩展码   | 助记符               | 操作数   | 说明                        |
| -------- | -------------------- | -------- | --------------------------- |
| `0x0001` | `call_indirect_host` | `u8`     | 按索引调用宿主函数          |
| `0x0002` | `xpcadd`             | `r, i32` | PC 相对地址计算             |
| `0x0003` | `xmov_fp`            | `r`      | 把帧指针移到寄存器          |

`call_indirect_host` 是客体到宿主切换的关键指令. 操作数字节
指明了要调用哪个宿主导入.

---

## 14. Pulley 字节码反汇编

### 14.1 Guest::run() - 闪烁循环

客体组件的 `run()` 函数编译成实现 LED 闪烁循环的
Pulley 字节码. 结构如下:

```
; function[N]: Guest::run()
; Source: impl Guest for BlinkyApp { fn run() { ... } }

push_frame_save <frame>, <callee-saved regs>

; Load VMContext and function pointers
xload32le_o32 x_heap, x0, 28          ; heap_base
xmov x_vmctx, x0                      ; save VMContext
xload32le_o32 x_set_high_fn, x_vmctx, ...  ; set_high fn ptr
xload32le_o32 x_set_low_fn, x_vmctx, ...   ; set_low fn ptr
xload32le_o32 x_delay_fn, x_vmctx, ...     ; delay_ms fn ptr

.loop:
    ; --- gpio::set_high(25) ---
    xconst8 x2, 25                    ; x2 = pin = 25 (GPIO25)
    xmov x0, x_callee_vmctx
    xmov x1, x_vmctx
    call_indirect x_set_high_fn        ; set_high(25)

    ; --- timing::delay_ms(500) ---
    xconst16 x2, 500                   ; x2 = 500 ms
    xmov x0, x_callee_vmctx
    xmov x1, x_vmctx
    call_indirect x_delay_fn           ; delay_ms(500)

    ; --- gpio::set_low(25) ---
    xconst8 x2, 25                    ; x2 = pin = 25
    xmov x0, x_callee_vmctx
    xmov x1, x_vmctx
    call_indirect x_set_low_fn         ; set_low(25)

    ; --- timing::delay_ms(500) ---
    xconst16 x2, 500                   ; x2 = 500 ms
    xmov x0, x_callee_vmctx
    xmov x1, x_vmctx
    call_indirect x_delay_fn           ; delay_ms(500)

    jump .loop                         ; Infinite loop - never returns
```

**关键观察:**

- 引脚 25 是编译期常量 (`xconst8 x2, 25`), 每次迭代都重新
  加载 - 编译器没有把它提到循环外面
- 500 ms 的延时每次迭代也重新加载 (`xconst16 x2, 500`)
- `call_indirect` 通过函数指针寄存器调用 - 这些指针
  从 VMContext 的组件表里加载
- 函数从不返回 - `jump` 构成一个死循环

### 14.2 panic() - 死循环

```
push_frame
jump 0x0                              ; jump to self (infinite spin)
```

这与 `fn panic(_: &PanicInfo) -> ! { loop { spin_loop() } }` 对应.

---

## 15. Ghidra 分析实战

### 15.1 导入与初步分析

1. **File -> Import File**: 选中那个 ELF. Ghidra 会自动识别出
   `ARM:LE:32:v8T` (ARMv8 Thumb). 保持默认选项.

2. **自动分析**: 弹出提示时点 "Yes". Ghidra 会:
   - 从符号表里识别出 2,375 个函数
   - 还原 Rust 的名称修饰
   - 检测出位于 `0x10000000` 的 ARM 向量表
   - 找出函数之间的交叉引用
   - 识别出 Pulley 解释器里的 `tbh` 派发表

3. **分析耗时**: 这个 1.12 MiB 的二进制大约 30 秒.

### 15.2 符号树导航

```
Functions/ (2,375 total)
+-- Reset                              0x1000010c
+-- main                               0x10008410
+-- __cortex_m_rt_main                 0x100075a8
+-- embedded_wasm_blinky::run_wasm     0x10007760
+-- led::set_high                      0x1000691c
+-- led::set_low                       0x10006858
+-- uart::write_msg                    0x10007614
+-- pulley_interpreter::interp::Interpreter::run  0x10064ef4
+-- pulley_interpreter::decode::decode_one_extended  0x10068210
+-- wasmtime::runtime::vm::interpreter::InterpreterRef::call  0x1000d7b8
+-- ... (2,362 more)
```

### 15.3 找到并提取 cwasm 数据块

1. 在 Listing 视图里跳转到 `0x1008a059`
2. Ghidra 会显示 `7f 45 4c 46` (ELF 魔数) 这些字节
3. 右键 -> **Select Bytes** -> 输入长度 24680 (0x6068)
4. **File -> Export Selection** -> Binary 格式 -> 保存为 `blinky.cwasm`

提取出来的文件是一个合法的 ELF64, 目标平台为 `pulley32-unknown-unknown-elf`.
要分析这个数据块里的 Pulley 字节码, 可以使用
[G-Pulley](https://github.com/mytechnotalent/G-Pulley) 这个 Ghidra 扩展.

### 15.4 Ghidra + G-Pulley: 全栈分析

装好 [G-Pulley](https://github.com/mytechnotalent/G-Pulley) 扩展之后,
Ghidra 就能同时分析 ARM 宿主固件和
Pulley 客体字节码:

| 方面           | ARM 宿主代码              | Pulley 客体代码 (G-Pulley)          |
| -------------- | ------------------------- | ----------------------------------- |
| 反汇编         | 完整的 ARM Thumb-2        | 完整的 Pulley ISA 助记符            |
| 函数识别       | 从符号表自动识别          | 自动 (cwasm 加载器 + 分析器)        |
| 交叉引用       | 完整的 xref 图            | 函数调用与分支                      |
| 控制流         | 带 switch 识别的 CFG      | 已解析的分支与跳转目标              |
| 宿主调用边界   | `InterpreterRef::call`    | `call_indirect_host` 指令           |

**G-Pulley 提供**:

- 自定义 ELF 加载器, 能从固件里提取 `.cwasm` 数据块,
  并把 Pulley 字节码加载进 Ghidra 的 Listing 视图
- Pulley 32 位与 64 位 ISA (Wasmtime v43.0.0) 的 SLEIGH 处理器描述
- 加载后分析器, 用于发现函数, 蹦床和宿主调用
- 对全部 220 个主操作码和 310 个扩展 Pulley 操作码的完整解码

### 15.5 推荐的 Ghidra 工作流

1. **安装 G-Pulley**: 从
   [G-Pulley releases](https://github.com/mytechnotalent/G-Pulley/releases) 下载.
   在 Ghidra 里: **File -> Install Extensions -> + -> 选中 zip**. 重启.

2. **分析 ARM 固件**: 导入 ELF. Ghidra 会自动识别出
   `ARM:LE:32:v8T`. 运行自动分析. 沿着 Reset -> main ->
   `__cortex_m_rt_main` -> `run_wasm` 追启动流程.

3. **查看宿主绑定**: 跳到 `led::set_high` 和
   `led::set_low`, 看 SIO GPIO 的寄存器写入. 跳到
   `uart::write_msg` 看 UART 诊断输出的路径.

4. **追踪解释器**: 从 `InterpreterRef::call` 开始, 跟到
   `Interpreter::run` 里, 研究 `tbh` 跳转表, 弄清
   每一类操作码是怎么处理的.

5. **分析 Pulley 字节码**: 用 G-Pulley 的 cwasm 加载器再导入一次
   固件 ELF (选择 "Pulley cwasm" 格式). G-Pulley 会
   提取内嵌的 cwasm 数据块, 反汇编所有 Pulley 操作码,
   并识别出客体函数, 蹦床和宿主调用.
