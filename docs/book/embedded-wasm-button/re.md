# 逆向工程: embedded-wasm-button-rp2350

## 目录

1. [二进制概览](#1-二进制概览)
2. [ELF 头](#2-elf-头)
3. [段布局](#3-段布局)
4. [内存映射与段](#4-内存映射与段)
5. [启动流程](#5-启动流程)
6. [向量表](#6-向量表)
7. [固件函数地图](#7-固件函数地图)
8. [硬件寄存器访问](#8-硬件寄存器访问)
9. [Pulley 解释器深入剖析](#9-pulley-解释器深入剖析)
10. [内嵌的 cwasm 数据块](#10-内嵌的-cwasm-数据块)
11. [宿主-客体调用流程](#11-宿主-客体调用流程)
12. [逆向观察](#12-逆向观察)
13. [Pulley 指令集架构](#13-pulley-指令集架构)
14. [Pulley 字节码反汇编](#14-pulley-字节码反汇编)
15. [Ghidra 分析走查](#15-ghidra-分析走查)

---

## 1. 二进制概览

| 属性           | 取值                                     |
| -------------- | ---------------------------------------- |
| 文件           | `embedded-wasm-button-rp2350`            |
| 磁盘大小       | 1,184,720 字节 (1.13 MiB)                |
| 格式           | ELF32 ARM 小端                           |
| ABI            | EABI5, hard-float                        |
| 目标           | ARMv8-M Mainline (Cortex-M33)            |
| MCU            | RP2350 (Raspberry Pi Pico 2)             |
| 是否 strip     | 否 (符号表与字符串表都在)                |
| 代码段函数数   | 2,392                                    |

这个二进制是一份裸机 `no_std` Rust 固件, 它承载着一个 Wasmtime
组件模型运行时, 并带有 Pulley 字节码解释器. 一个预编译好的
Wasm 组件每 10 ms 读一次 GPIO15 (按键), 并据此驱动 GPIO25
(LED) - 按住按键期间 LED 一直亮着. 宿主绑定暴露了 `gpio`,
`button` 和 `timing` 这三个 WIT 接口.

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
Section headers:                   16 (at offset 1,184,080)
```

**入口点**: `0x1000010d` - `.text` 里的 `Reset` 处理函数. 最低位
被置 1 (0x0D 而不是 0x0C) 表示 Thumb 模式, 这是 ARMv8-M 的硬性
要求. 真正的代码从 `0x1000010c` 开始.

---

## 3. 段布局

```
Nr  Name            Type        Addr        Size      Flags  Description
 1  .vector_table   PROGBITS    0x10000000  0x000f8   A      ARM exception + interrupt vectors
 2  .start_block    PROGBITS    0x100000f8  0x00014   AR     RP2350 IMAGE_DEF boot metadata
 3  .text           PROGBITS    0x1000010c  0x85f48   AX     All executable code (548 KiB)
 4  .bi_entries     PROGBITS    0x10086054  0x00000   A      Binary info entries (empty)
 5  .rodata         PROGBITS    0x10086058  0x1e050   AMSR   Read-only data (120 KiB)
 6  .data           PROGBITS    0x20000000  0x00024   WA     Initialized globals (36 bytes)
 7  .gnu.sgstubs    PROGBITS    0x100a40d0  0x00000   A      Secure gateway stubs (empty)
 8  .bss            NOBITS      0x20000028  0x400b4   WA     Zero-init data (256 KiB)
 9  .uninit         NOBITS      0x200400dc  0x00000   WA     Uninitialized memory (empty)
10  .end_block      PROGBITS    0x100a40d0  0x00000   WA     Block end marker (empty)
13  .symtab         SYMTAB      file only   0x1db40          Symbol table (7,580 entries)
15  .strtab         STRTAB      file only   0x60c0e          String table (389 KiB)
```

### 体积细分

| 区域           | 段              | 大小          | 占 4 MiB Flash 的比例 |
| -------------- | --------------- | ------------- | -------------------- |
| 代码           | `.text`         | 548,680 B     | 13.1%                |
| 常量           | `.rodata`       | 122,960 B     | 2.9%                 |
| 向量           | `.vector_table` | 248 B         | <0.1%                |
| 引导元数据     | `.start_block`  | 20 B          | <0.1%                |
| 初始化数据     | `.data`         | 36 B          | <0.1%                |
| **Flash 已用** |                 | **671,944 B** | **16.0%**            |
| **Flash 空闲** |                 | 3,522,360 B   | 84.0%                |
| BSS (RAM)      | `.bss`          | 262,324 B     | 占 512 KiB RAM 的 51.2% |

按键版比基础的 blinky 版大出约 4 KiB, 多出来的部分是
`button` 模块 (`is_pressed` 加 `store_pin`) 和一个额外的 WIT
接口.

---

## 4. 内存映射与段

```
Segment  VirtAddr     PhysAddr     MemSiz   Flags  Contents
  0      0x10000000   0x10000000   0x0010c  R      .vector_table + .start_block
  1      0x1000010c   0x1000010c   0x85f48  R E    .text (executable code)
  2      0x10086054   0x10086054   0x1e054  R      .rodata (constants + cwasm blob)
  3      0x20000000   0x100a40a8   0x00024  RW     .data (LMA in flash, VMA in RAM)
  4      0x20000028   0x20000028   0x400b4  RW     .bss (zero-filled at boot)
  5      0x00000000   0x00000000   0x00000  RW     GNU_STACK (zero-size)
```

### 物理地址空间

```
Flash (XIP):  0x10000000 - 0x100a40cb  (672 KiB used of 4 MiB)
              +-- 0x10000000  Vector table (248 B)
              +-- 0x100000f8  IMAGE_DEF boot block (20 B)
              +-- 0x1000010c  .text starts (Reset handler)
              +-- 0x10086058  .rodata starts
              +-- 0x1008a809  Embedded cwasm (Pulley ELF, ~25 KiB)
              +-- 0x100a40a8  .data initializers (36 B, copied to RAM)

RAM (SRAM):   0x20000000 - 0x200400db  (256 KiB used of 512 KiB)
              +-- 0x20000000  .data (36 B: UART state, TLS value)
              +-- 0x20000028  HEAP_MEM (262,144 B = 256 KiB)
              +-- 0x20040048  TLS_VALUE (4 B)
              +-- 0x2004004c  led::PINS (16 B)
              +-- 0x20040060  button::PINS (16 B)
              +-- 0x20040070  HEAP allocator struct (32 B)

Stack:        0x20080000  Initial SP (top of 512 KiB SRAM, grows down)
```

---

## 5. 启动流程

### 5.1 RP2350 Boot ROM -> IMAGE_DEF

RP2350 的 Boot ROM 会扫描 flash, 寻找一个合法的镜像定义块. 我们的
`.start_block` 段位于 `0x100000f8`, 内容是:

```
d3deffff 42012110 ff010000 00000000 793512ab
```

这就是 `hal::block::ImageDef::secure_exe()` - 它告诉 Boot ROM
这是一个安全的 ARM 可执行文件.

### 5.2 向量表 -> 复位处理函数

```
Word 0: 0x20080000  <- Initial Stack Pointer
Word 1: 0x1000010d  <- Reset vector (Thumb-mode)
```

### 5.3 复位处理函数 (0x1000010c)

```armasm
Reset:
    bl      DefaultPreInit          ; 空操作
    ; --- 清零 .bss (0x20000028 -> 0x200400dc) ---
    ; --- 把 .data 从 flash (0x100a40a8) 复制到 RAM (0x20000000) ---
    ; --- 使能 FPU ---
    bl      main
    udf     #0
```

### 5.4 `main()` (0x10007b78)

```armasm
main:
    bl      __cortex_m_rt_main      ; 位于 0x10006c50
```

### 5.5 `__cortex_m_rt_main` (0x10006c50)

```
    ; Enable SIO GPIO outputs for GPIO15 (button) and GPIO25 (LED)
    ; Enable FPU
    bl      init_heap               ; Initialize 256 KiB heap
    bl      init_hardware           ; Clocks, UART, GPIO15, GPIO25, SysTick
    bl      run_wasm                ; Run the Wasm button component (never returns)
```

---

## 6. 向量表

`0x10000000` 处的向量表长 248 字节 (62 个表项):

```
Offset  Vector              Handler          Address
0x0000  Initial SP          —                0x20080000
0x0004  Reset               Reset            0x1000010d
0x0008  NMI                 DefaultHandler   0x1007dac5
0x000c  HardFault           HardFault_       0x1008604d
0x0040+ IRQ0-IRQ51          DefaultHandler   0x1007dac5
```

除了 HardFault (同样是无限循环) 之外, 所有异常和 IRQ 向量都指向
`DefaultHandler` (无限循环). 固件没有使用任何外设中断.

---

## 7. 固件函数地图

### 7.1 应用函数

| 地址         | 大小  | 符号                 | 作用                                                |
| ------------ | ----- | -------------------- | --------------------------------------------------- |
| `0x1000010c` | 0x3e  | `Reset`              | BSS 清零, 复制 .data, 使能 FPU, 调用 main           |
| `0x10006b38` | 0x118 | `init_hardware`      | 时钟, UART0, GPIO15, GPIO25, SysTick                |
| `0x10006c50` | 0x6c  | `__cortex_m_rt_main` | 使能 SIO, FPU, init_heap, init_hardware, run_wasm   |
| `0x10006cbc` | 0x842 | `run_wasm`           | 创建 engine, 反序列化 cwasm, 运行客体               |
| `0x10007500` | 0x20  | `init_heap`          | 初始化 256 KiB 的链表式堆                           |
| `0x10009d88` | 0xc2  | `led::set_high`      | 通过 SIO 置位 GPIO, 并记 UART 日志                  |
| `0x10009cc4` | 0xc2  | `led::set_low`       | 通过 SIO 清零 GPIO, 并记 UART 日志                  |
| `0x10009e4c` | 0x108 | `led::store_pin`     | 为 LED 模块存放 GPIO 引脚句柄                       |
| `0x1000ac60` | 0xc6  | `button::is_pressed` | 通过 SIO 读取 GPIO 输入电平                         |
| `0x1000ad28` | 0x108 | `button::store_pin`  | 为按键模块存放 GPIO 引脚句柄                        |
| `0x1000abb4` | 0xac  | `uart::write_msg`    | 阻塞式 UART 发送                                    |
| `0x1000aaa8` | 0x10c | `uart::init`         | UART0 外设初始化 (115200 8N1)                       |
| `0x10007b78` | 0x8   | `main`               | 一层很薄的 #[entry] 包装                            |
| `0x1007dac4` | 0x6   | `DefaultHandler`     | 无限循环 (未处理的异常)                             |
| `0x1007dacc` | 0x6   | `DefaultPreInit`     | 空操作 (立即返回)                                   |
| `0x1008604c` | 0x6   | `HardFault`          | 无限循环 (硬故障)                                   |

### 7.2 按键模块的设计

按键模块照搬 `led.rs`, 换成 `store_pin` 加 `is_pressed` 这一对:

- `button::store_pin` (0x108 B): 把一个 GPIO 引脚句柄存进
  `0x20040060` 处的 `button::PINS`
- `button::is_pressed` (0xc6 B): 读取 `0xd0000004` 处的 SIO GPIO
  输入寄存器 `GPIO_IN`, 取出 GPIO15 对应的位, 如果该位为 1
  就返回 `true`

按键引脚 (GPIO15) 在 `init_hardware` 里被配成下拉输入,
而 LED 引脚 (GPIO25) 是推挽输出.

### 7.3 Wasmtime 运行时 (按体积排序)

| 地址         | 大小     | 还原后的名称                       |
| ------------ | -------- | ---------------------------------- |
| `0x10033f10` | 16,464 B | `OperatorCost::deserialize`        |
| `0x100694e8` | 16,456 B | `decode_one_extended`              |
| `0x100661cc` | 12,518 B | `Interpreter::run` (分派循环)      |
| `0x1002f6b0` | 8,696 B  | `Metadata::check_cost`             |
| `0x1000ea2c` | 2,304 B  | `InterpreterRef::call`             |

### 7.4 BSS 布局

| 地址         | 大小      | 符号           | 用途                            |
| ------------ | --------- | -------------- | ------------------------------- |
| `0x20000028` | 262,144 B | `HEAP_MEM`     | 堆的底层原始内存                |
| `0x20040048` | 4 B       | `TLS_VALUE`    | Wasmtime 的 TLS 桩 (platform.rs) |
| `0x2004004c` | 16 B      | `led::PINS`    | LED 用的 GPIO 引脚句柄          |
| `0x20040060` | 16 B      | `button::PINS` | 按键用的 GPIO 引脚句柄          |

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
| `0x40070000` | UART0      | 调试串口 (只用 TX)      |
| `0xd0000000` | SIO        | 单周期 IO (GPIO)        |
| `0xe000e010` | SysTick    | 系统定时器 (用于延时)   |
| `0xe000ed88` | CPACR      | FPU 访问控制            |

### 8.2 GPIO 控制

固件配置了两个 GPIO 引脚:

- **GPIO15 (按键)**: 下拉输入. 通过 `0xd0000004` 处的 `SIO GPIO_IN`
  读取. `button::is_pressed` 函数会取出第 15 位来判断
  按键状态.

- **GPIO25 (LED)**: 推挽输出. 通过 `0xd0000014` 处的
  `SIO GPIO_OUT_SET` 和 `0xd0000018` 处的 `SIO GPIO_OUT_CLR` 写入.

```
button::is_pressed (0x1000ac60):
    ; SIO base = 0xd0000000
    ; GPIO_IN @ 0xd0000004
    ldr     r0, =0xd0000004         ; GPIO_IN register
    ldr     r1, [r0]                ; Read all GPIO levels
    tst     r1, #(1 << 15)          ; Test bit 15 (button pin)
    ; Return true if bit is set, false otherwise

led::set_high / led::set_low:
    ; GPIO_OUT_SET @ 0xd0000014, GPIO_OUT_CLR @ 0xd0000018
    ; Same SIO register pattern as blinky
```

### 8.3 SysTick 定时器

用于按键轮询之间的 10 ms 延时. 机制和所有 embedded-wasm 仓库
一样: 在 150 MHz 系统时钟下, 按所需延时算出重装载值,
写进定时器.

---

## 9. Pulley 解释器深入剖析

### 9.1 解释器入口 (`InterpreterRef::call`)

```
Location:  0x1000ea2c  (2,304 bytes)
```

调用序列:

```
run_wasm()
  -> Button::instantiate()
    -> Button::call_run()
      -> InterpreterRef::call()     <-- native-to-Pulley boundary
        -> Vm::call_start()         ; Set up Pulley register file
        -> Vm::call_run()           ; Enter interpreter loop
          -> Interpreter::run()     ; Main dispatch loop
```

### 9.2 主分派循环

```
Location:  0x100661cc  (12,518 bytes)
```

两级分派方案和所有 embedded-wasm 仓库一样: 主操作码
(0x00-0xDB) 由 `Interpreter::run` 里的跳转表处理, 扩展操作码
(0xDC 前缀加 2 字节操作码) 则由
`decode_one_extended` 处理.

---

## 10. 内嵌的 cwasm 数据块

### 10.1 位置与格式

预编译好的 Pulley 字节码内嵌在 `.rodata` 中, 地址是
`0x1008a809`, 共 **25,384 字节** (0x6328).

| 字段   | 取值                           |
| ------ | ------------------------------ |
| Magic  | `\x7fELF`                      |
| Class  | ELF64 (偏移 4 处的字节是 `02`) |
| Data   | 小端                           |
| Target | `pulley32-unknown-unknown-elf` |

按键版的 cwasm 比基础 blinky 版大约 700 字节, 因为它多了一次
宿主导入调用 (`is_pressed`), 以及客体循环里的一个
条件分支.

### 10.2 客体代码逻辑

```
fn run() {
    let button_pin: u32 = 15;
    let led_pin: u32 = 25;
    loop {
        if call_import button::is_pressed(button_pin) {
            call_import gpio::set_high(led_pin)
        } else {
            call_import gpio::set_low(led_pin)
        }
        call_import timing::delay_ms(10)
    }
}
```

客体每 10 ms 轮询一次按键状态, 并把它镜像到 LED 上.

---

## 11. 宿主-客体调用流程

### 11.1 检测到按键按下

```
[Pulley VM]  Bytecode: call_indirect_host -> is_pressed(15)
    |
    v
[ARM Native]  button::is_pressed (0x1000ac60)
    |
    v
[Hardware]  SIO GPIO_IN @ 0xd0000004 -> bit 15 set = true

[Pulley VM]  Bytecode: br_if_xneq32 -> take set_high path
    |
    v
[Pulley VM]  Bytecode: call_indirect_host -> set_high(25)
    |
    v
[ARM Native]  led::set_high (0x10009d88)
    |
    v
[Hardware]  SIO GPIO_OUT_SET @ 0xd0000014 -> LED on

[Pulley VM]  Bytecode: call_indirect_host -> delay_ms(10)
    |
    v
[ARM Native]  SysTick countdown (10 ms)
```

### 11.2 按键未按下

```
[Pulley VM]  Bytecode: call_indirect_host -> is_pressed(15)
    |
    v
[ARM Native]  button::is_pressed (0x1000ac60)
    |
    v
[Hardware]  SIO GPIO_IN @ 0xd0000004 -> bit 15 clear = false

[Pulley VM]  Bytecode: br_if_xneq32 -> take set_low path
    |
    v
[Pulley VM]  Bytecode: call_indirect_host -> set_low(25)
    |
    v
[ARM Native]  led::set_low (0x10009cc4)
    |
    v
[Hardware]  SIO GPIO_OUT_CLR @ 0xd0000018 -> LED off
```

---

## 12. 逆向观察

### 12.1 二进制构成

| 组成                               | 大致大小    | 占 .text 比例 |
| ---------------------------------- | ----------- | ---------- |
| Wasmtime 运行时                    | 约 540 KiB  | 98.5%      |
| Pulley 解释器 (run)                | 12.2 KiB    | 2.2%       |
| Pulley 解码器 (extended)           | 16.1 KiB    | 2.9%       |
| 应用 (led+button+uart+main)        | 约 8 KiB    | 1.5%       |

### 12.2 按键版与 blinky 版的差异

| 方面           | Blinky         | Button                     |
| -------------- | -------------- | -------------------------- |
| GPIO 输出      | 只有 GPIO25    | GPIO25 (LED)               |
| GPIO 输入      | 无             | GPIO15 (按键, 下拉)        |
| WIT 接口       | gpio, timing   | gpio, button, timing       |
| 客体逻辑       | 翻转循环       | 轮询并镜像                 |
| cwasm 大小     | 24,680 B       | 25,384 B (+704 B)          |
| BSS 差异       | 只有 led::PINS | led::PINS + button::PINS   |

### 12.3 关键地址速查

| 地址         | 说明                                          |
| ------------ | --------------------------------------------- |
| `0x10000000` | 向量表 (初始 SP 加异常向量)                   |
| `0x100000f8` | RP2350 IMAGE_DEF 引导块                       |
| `0x1000010c` | 复位处理函数 (入口点)                       |
| `0x10006b38` | init_hardware                                 |
| `0x10006c50` | __cortex_m_rt_main                            |
| `0x10006cbc` | run_wasm                                      |
| `0x10007500` | init_heap                                     |
| `0x10009d88` | led::set_high (宿主绑定)                      |
| `0x10009cc4` | led::set_low (宿主绑定)                       |
| `0x1000ac60` | button::is_pressed (宿主绑定)                 |
| `0x1000abb4` | uart::write_msg                               |
| `0x1000aaa8` | uart::init                                    |
| `0x10007b78` | main (薄包装)                                 |
| `0x100661cc` | Pulley Interpreter::run (分派循环)            |
| `0x100694e8` | Pulley decode_one_extended                    |
| `0x1000ea2c` | InterpreterRef::call (本机到 Pulley 的桥)     |
| `0x1008a809` | 内嵌的 cwasm 数据块 (Pulley ELF)              |
| `0x1007dac4` | DefaultHandler (无限循环)                     |
| `0x1008604c` | HardFault (无限循环)                          |
| `0xd0000004` | SIO GPIO_IN 寄存器 (读按键)                   |
| `0xd0000014` | SIO GPIO_OUT_SET 寄存器                       |
| `0xd0000018` | SIO GPIO_OUT_CLR 寄存器                       |
| `0x20000028` | HEAP_MEM (256 KiB)                            |
| `0x2004004c` | led::PINS                                     |
| `0x20040060` | button::PINS                                  |
| `0x20080000` | 初始栈指针                                    |

---

## 13. Pulley 指令集架构

### 13.1 概览

Pulley 是 Wasmtime 的可移植字节码解释器 (wasmtime 43.0.0,
`pulley-interpreter` crate v43.0.0). 它定义了一套基于寄存器的
ISA, 指令长度可变, 设计目标是高效解释而不是本机
执行.

### 13.2 编码格式

**主操作码**用 1 字节操作码加操作数:

```
[opcode:1] [operands:0-9]
```

主操作码共有 **220 条** (0x00-0xDB). 操作码 `0xDC` 是
**ExtendedOp** 哨兵 - 解释器遇到它时, 会再读一个 2 字节的扩展
操作码:

```
[0xDC] [ext_opcode:2] [operands:0-N]
```

扩展操作码共有 **310 条** (0x0000-0x0135), 用于 SIMD, 浮点
转换以及复杂操作.

### 13.3 关键指令

完整的 Pulley ISA 参考见 [embedded-wasm-servo-rp2350 RE.md](https://github.com/mytechnotalent/embedded-wasm-servo-rp2350)
的 13 节. 按键客体用到的指令子集和基础 blinky 版一样,
只是多加了条件分支指令, 用来实现 `if is_pressed`
这个判断.

---

## 14. Pulley 字节码反汇编

### 14.1 Guest::run() - 按键轮询循环

```
; function[N]: Guest::run()

push_frame_save <frame>, <callee-saved regs>

; Load VMContext and function pointers
xload32le_o32 x_heap, x0, 28          ; heap_base
xmov x_vmctx, x0                      ; save VMContext

; Load constants
xconst8 x_button, 15                  ; BUTTON_PIN = 15
xconst8 x_led, 25                     ; LED_PIN = 25
xconst8 x_delay_val, 10               ; DELAY_MS = 10

; Load host function pointers
xload32le_o32 x_is_pressed, x_vmctx, ...
xload32le_o32 x_set_high, x_vmctx, ...
xload32le_o32 x_set_low, x_vmctx, ...
xload32le_o32 x_delay, x_vmctx, ...

.loop:
    ; --- button::is_pressed(15) ---
    xmov x2, x_button                 ; x2 = 15
    call_indirect x_is_pressed         ; -> ARM: button::is_pressed

    ; --- Branch on result ---
    br_if_xeq32 x0, x_zero, .not_pressed

    ; --- Pressed: gpio::set_high(25) ---
    xmov x2, x_led
    call_indirect x_set_high
    jump .delay

.not_pressed:
    ; --- Not pressed: gpio::set_low(25) ---
    xmov x2, x_led
    call_indirect x_set_low

.delay:
    ; --- timing::delay_ms(10) ---
    xmov x2, x_delay_val
    call_indirect x_delay

    jump .loop                         ; Infinite poll loop
```

---

## 15. Ghidra 分析走查

### 15.1 导入与初步分析

1. **File -> Import File**: 选中这个 ELF. Ghidra 会自动识别出
   `ARM:LE:32:v8T` (ARMv8 Thumb). 其余选项用默认值即可.

2. **自动分析**: Ghidra 从符号表里识别出 2,392 个
   函数.

3. **分析耗时**: 对这个 1.13 MiB 的二进制大约 30 秒.

### 15.2 符号树导航

```
Functions/ (2,392 total)
+-- Reset                              0x1000010c
+-- main                               0x10007b78
+-- __cortex_m_rt_main                 0x10006c50
+-- embedded_wasm_button_rp2350::run_wasm    0x10006cbc
+-- led::set_high                      0x10009d88
+-- led::set_low                       0x10009cc4
+-- button::is_pressed                 0x1000ac60
+-- button::store_pin                  0x1000ad28
+-- uart::init                         0x1000aaa8
+-- uart::write_msg                    0x1000abb4
+-- pulley_interpreter::interp::Interpreter::run  0x100661cc
+-- pulley_interpreter::decode::decode_one_extended  0x100694e8
+-- InterpreterRef::call               0x1000ea2c
+-- ... (2,379 more)
```

### 15.3 找到并导出 cwasm 数据块

1. 在 Listing 视图里跳到 `0x1008a809`
2. Ghidra 会显示 `7f 45 4c 46` (ELF magic) 这几个字节
3. 右键 -> **Select Bytes** -> 输入长度 25384 (0x6328)
4. **File -> Export Selection** -> 选 Binary 格式 -> 存为 `button.cwasm`

### 15.4 Ghidra + G-Pulley: 全栈分析

装上 [G-Pulley](https://github.com/mytechnotalent/G-Pulley) 扩展之后,
Ghidra 就能**同时**分析 ARM 宿主固件和 Pulley
客体字节码:

| 方面           | ARM 宿主代码              | Pulley 客体代码 (G-Pulley)          |
| ----------------------- | ------------------------- | ----------------------------------- |
| 反汇编         | 完整的 ARM Thumb-2        | 完整的 Pulley ISA 助记符            |
| 函数识别       | 从符号自动识别            | 自动 (cwasm 加载器加分析器)         |
| 交叉引用       | 完整 xref 图              | 函数调用与分支                      |
| 控制流         | 带 switch 识别的 CFG      | 分支与跳转目标均已解析              |
| 宿主调用边界   | `InterpreterRef::call`    | `call_indirect_host` 指令           |

**G-Pulley 提供**:

- 自定义 ELF 加载器, 能从固件里把 `.cwasm` 数据块抽出来
- Pulley 32 位与 64 位 ISA 的 SLEIGH 处理器描述 (Wasmtime v43.0.0)
- 加载后分析器, 能发现函数, 蹦床 (trampoline) 和宿主调用
- 覆盖全部 220 条主操作码加 310 条扩展 Pulley 操作码的完整解码

### 15.5 推荐的 Ghidra 工作流

1. **安装 G-Pulley**: 从
   [G-Pulley releases](https://github.com/mytechnotalent/G-Pulley/releases) 下载.
   在 Ghidra 里: **File -> Install Extensions -> + -> 选中 zip**. 然后重启.

2. **分析 ARM 固件**: 导入 ELF, 跑自动分析.
   顺着 Reset -> main -> `__cortex_m_rt_main` -> `run_wasm` 一路跟下去.

3. **看宿主绑定**: 跳到 `button::is_pressed`
   (0x1000ac60), 看 GPIO15 是怎么通过 SIO 读出来的. 再看 `led::set_high`
   和 `led::set_low`, 那是 GPIO25 的控制路径.

4. **跟踪解释器**: 从 `InterpreterRef::call` (0x1000ea2c) 开始,
   跟进 `Interpreter::run` (0x100661cc), 观察 Pulley 的分派
   循环.

5. **分析 Pulley 字节码**: 用 G-Pulley 的 cwasm 加载器再导入一次
   固件 ELF (格式选 "Pulley cwasm"). G-Pulley 会把内嵌的 cwasm
   数据块抽出来, 反汇编所有 Pulley 操作码,
   并识别出客体函数, 其中包括带条件分支的按键轮询
   循环.
