# 逆向工程: embedded-wasm-uart

## 目录

1. [二进制概览](#1-二进制概览)
2. [ELF 头](#2-elf-头)
3. [节布局](#3-节布局)
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
15. [Ghidra 分析流程](#15-ghidra-分析流程)

---

## 1. 二进制概览

| 属性       | 值                                       |
| ---------- | ---------------------------------------- |
| 文件       | `embedded-wasm-uart`                     |
| 磁盘大小   | 1,168,560 字节 (1.11 MiB)                |
| 格式       | ELF32 ARM 小端                           |
| ABI        | EABI5, 硬浮点                            |
| 目标       | ARMv8-M Mainline (Cortex-M33)            |
| MCU        | RP2350 (Raspberry Pi Pico 2)             |
| 是否去符号 | 否 (符号表与字符串表都在)                |
| 代码函数数 | 2,375                                    |

这是一个裸机 `no_std` 的 Rust 固件, 里面装着 Wasmtime 组件模型
运行时以及 Pulley 字节码解释器. 一个预编译的 Wasm 组件会从
UART0 读取字符, 再把它们回显出去, 并带有行编辑能力 (退格处理
与换行回显). 它唯一的 WIT 接口是 `embedded:platform/uart`,
提供 `read-byte` 和
`write-byte` - 完全不涉及 GPIO.

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
Section headers:                   16 (at offset 1,167,920)
```

**入口点**: `0x1000010d` - `.text` 里的 `Reset` 处理函数. 最低位被
置 1 (0x0D 而非 0x0C) 是为了标明 Thumb 模式, 这是 ARMv8-M 的要求.
真正的代码从 `0x1000010c` 开始.

---

## 3. 节布局

```
Nr  Name            Type        Addr        Size      Flags  Description
 1  .vector_table   PROGBITS    0x10000000  0x000f8   A      ARM exception + interrupt vectors
 2  .start_block    PROGBITS    0x100000f8  0x00014   AR     RP2350 IMAGE_DEF boot metadata
 3  .text           PROGBITS    0x1000010c  0x83a28   AX     All executable code (527 KiB)
 4  .bi_entries     PROGBITS    0x10083b34  0x00000   A      Binary info entries (empty)
 5  .rodata         PROGBITS    0x10083b38  0x1db38   AMSR   Read-only data (119 KiB)
 6  .data           PROGBITS    0x20000000  0x00028   WA     Initialized globals (40 bytes)
 7  .gnu.sgstubs    PROGBITS    0x100a1690  0x00000   A      Secure gateway stubs (empty)
 8  .bss            NOBITS      0x20000028  0x40094   WA     Zero-init data (256 KiB)
 9  .uninit         NOBITS      0x200400bc  0x00000   WA     Uninitialized memory (empty)
10  .end_block      PROGBITS    0x100a1690  0x00000   WA     Block end marker (empty)
13  .symtab         SYMTAB      file only   0x1d200          Symbol table (7,530 entries)
15  .strtab         STRTAB      file only   0x5fb3c          String table (385 KiB)
```

### 体积细分

| 区域           | 节              | 大小          | 占 4 MiB Flash 的比例 |
| -------------- | --------------- | ------------- | --------------------- |
| 代码           | `.text`         | 539,176 B     | 12.9%                 |
| 常量           | `.rodata`       | 121,656 B     | 2.9%                  |
| 向量           | `.vector_table` | 248 B         | <0.1%                 |
| 启动元数据     | `.start_block`  | 20 B          | <0.1%                 |
| 初始化数据     | `.data`         | 40 B          | <0.1%                 |
| **已用 Flash** |                 | **661,140 B** | **15.8%**             |
| **剩余 Flash** |                 | 3,533,164 B   | 84.2%                 |
| BSS (RAM)      | `.bss`          | 262,292 B     | 占 512 KiB RAM 的 51.2% |

这是四个 embedded-wasm 变体里最小的一个, 因为它没有 GPIO 模块 -
只有 UART 读写的宿主绑定.

### .data 节说明

UART 变体有 40 字节的 `.data` (blinky/button/c2 都是 36 字节).
多出来的 4 字节是因为 UART 外设句柄存放在 `.data` 里, 用的是
8 字节的表示 (Mutex 加 RefCell 的开销), 而不是一个更简单的
4 字节 BSS 槽位.

---

## 4. 内存映射与段

```
Segment  VirtAddr     PhysAddr     MemSiz   Flags  Contents
  0      0x10000000   0x10000000   0x0010c  R      .vector_table + .start_block
  1      0x1000010c   0x1000010c   0x83a28  R E    .text (executable code)
  2      0x10083b34   0x10083b34   0x1db3c  R      .rodata (constants + cwasm blob)
  3      0x20000000   0x100a1668   0x00028  RW     .data (LMA in flash, VMA in RAM)
  4      0x20000028   0x20000028   0x40094  RW     .bss (zero-filled at boot)
  5      0x00000000   0x00000000   0x00000  RW     GNU_STACK (zero-size)
```

### 物理地址空间

```
Flash (XIP):  0x10000000 - 0x100a168f  (661 KiB used of 4 MiB)
              +-- 0x10000000  Vector table (248 B)
              +-- 0x100000f8  IMAGE_DEF boot block (20 B)
              +-- 0x1000010c  .text starts (Reset handler)
              +-- 0x10083b38  .rodata starts
              +-- 0x10088578  Embedded cwasm (Pulley ELF, ~24 KiB)
              +-- 0x100a1668  .data initializers (40 B, copied to RAM)

RAM (SRAM):   0x20000000 - 0x200400bb  (256 KiB used of 512 KiB)
              +-- 0x20000000  .data (40 B: UART handle + TLS value)
              +-- 0x20000028  TLS_VALUE (4 B)
              +-- 0x2000002c  HEAP_MEM (262,144 B = 256 KiB)
              +-- 0x2004002c  HEAP allocator struct (32 B)

Stack:        0x20080000  Initial SP (top of 512 KiB SRAM, grows down)
```

---

## 5. 启动流程

### 5.1 RP2350 启动 ROM 到 IMAGE_DEF

RP2350 的启动 ROM 会扫描 Flash, 寻找合法的映像定义块. 我们在
`0x100000f8` 的 `.start_block` 节里放着:

```
d3deffff 42012110 ff010000 00000000 793512ab
```

这就是 `hal::block::ImageDef::secure_exe()` - 它告诉启动 ROM
这是一个安全的 ARM 可执行文件.

### 5.2 向量表到复位处理函数

```
Word 0: 0x20080000  <- Initial Stack Pointer
Word 1: 0x1000010d  <- Reset vector (Thumb-mode)
```

### 5.3 复位处理函数 (0x1000010c)

```armasm
Reset:
    bl      DefaultPreInit          ; 空操作
    ; --- 清零 .bss (0x20000028 -> 0x200400bc) ---
    ; --- 把 .data 从 flash (0x100a1668) 复制到 RAM (0x20000000) ---
    ; --- 启用 FPU ---
    bl      main
    udf     #0
```

### 5.4 `main()` (0x10008014)

```armasm
main:
    bl      __cortex_m_rt_main      ; 位于 0x1000736c
```

### 5.5 `__cortex_m_rt_main` (0x1000736c)

```
    ; Enable FPU
    bl      init_heap               ; Initialize 256 KiB heap
    bl      init_hardware           ; Clocks, UART0 (GPIO0 TX + GPIO1 RX)
    bl      run_wasm                ; Run the Wasm UART echo component (never returns)
```

注意: blinky/button 会启用 SIO 的 GPIO 输出, 而本变体
没有任何 GPIO 输出的设置 - 只配置了 UART0.

---

## 6. 向量表

位于 `0x10000000` 的向量表长 248 字节 (62 个表项):

```
Offset  Vector              Handler          Address
0x0000  Initial SP          -                0x20080000
0x0004  Reset               Reset            0x1000010d
0x0008  NMI                 DefaultHandler   0x1007b5a5
0x000c  HardFault           HardFault_       0x10083b2d
0x0040+ IRQ0-IRQ51          DefaultHandler   0x1007b5a5
```

除 HardFault (同样是死循环) 之外, 所有异常和 IRQ 向量都指向
`DefaultHandler` (死循环). 没有任何外设中断被用到.

---

## 7. 固件函数地图

### 7.1 应用函数

| 地址         | 大小  | 符号                            | 用途                                        |
| ------------ | ----- | ------------------------------- | ------------------------------------------- |
| `0x1000010c` | 0x3e  | `Reset`                         | 清零 BSS, 复制 .data, 启用 FPU, 调用 main   |
| `0x100071e8` | 0x184 | `init_hardware`                 | 时钟, UART0 (GPIO0 TX, GPIO1 RX)            |
| `0x1000736c` | 0x6c  | `__cortex_m_rt_main`            | FPU, init_heap, init_hardware, run_wasm     |
| `0x100073d8` | 0x742 | `run_wasm`                      | 创建引擎, 反序列化 cwasm, 运行客体          |
| `0x10007b1c` | 0x20  | `init_heap`                     | 初始化 256 KiB 的链表堆                     |
| `0x1000801c` | 0xbc  | `platform::uart::add_to_linker` | 注册 read-byte/write-byte 的 WIT 绑定       |
| `0x10008014` | 0x8   | `main`                          | 薄薄的 #[entry] 包装                        |
| `0x1007b5a4` | 0x6   | `DefaultHandler`                | 死循环 (未处理的异常)                       |
| `0x1007b5ac` | 0x6   | `DefaultPreInit`                | 空操作 (立即返回)                           |
| `0x10083b2c` | 0x6   | `HardFault`                     | 死循环 (硬件错误)                           |

### 7.2 UART 宿主绑定

UART 变体没有单独的 `led.rs` 或 `button.rs` 模块. 所有
宿主绑定都走 `platform::uart::add_to_linker`, 由它注册
两个 WIT 导入:

- **`read-byte`**: 调用 `uart::read_byte()` - 从 UART0
  RX FIFO 阻塞读取. 通过 `nb::block!` 作用在 HAL 的 `read_full` 方法上实现.

- **`write-byte`**: 调用 `uart::write_byte(byte)` - 阻塞写入
  UART0 TX FIFO. 通过 `nb::block!` 作用在 HAL 的 `write_full`
  方法上实现.

注意: `uart::read_byte`, `uart::write_byte` 和 `uart::store_global`
都被编译器内联进了 `run_wasm` 和 `init_hardware`. 它们在二进制里
不会作为独立符号出现.

### 7.3 Wasmtime 运行时 (按体积排序)

| 地址         | 大小     | 还原后的名称                       |
| ------------ | -------- | ---------------------------------- |
| `0x10031a50` | 16,464 B | `OperatorCost::deserialize`        |
| `0x10066fc8` | 16,456 B | `decode_one_extended`              |
| `0x10063cac` | 12,518 B | `Interpreter::run` (分发循环)      |
| `0x1002d1f4` | 8,696 B  | `Metadata::check_cost`             |
| `0x1000c570` | 2,304 B  | `InterpreterRef::call`             |

### 7.4 BSS 与数据布局

| 地址         | 大小      | 节      | 符号         | 用途                            |
| ------------ | --------- | ------- | ------------ | ------------------------------- |
| `0x20000000` | 8 B       | .data   | `uart::UART` | Mutex<RefCell<Option<Uart0>>>   |
| `0x20000028` | 4 B       | .bss    | `TLS_VALUE`  | Wasmtime 的 TLS 垫片 (platform.rs) |
| `0x2000002c` | 262,144 B | .bss    | `HEAP_MEM`   | 堆的原始后备内存                |
| `0x2004002c` | 32 B      | .bss    | `HEAP`       | 链表分配器状态                  |

注意: 这里没有 `led::PINS` 或 `button::PINS` - 这个变体没有 GPIO
模块.

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
| `0x40070000` | UART0      | 串口 I/O (TX 加 RX)     |
| `0xe000ed88` | CPACR      | FPU 访问控制            |

### 8.2 UART0 寄存器

UART0 是运行时唯一被真正使用的外设:

```
0x40070000  UARTDR    Data register (TX/RX)
0x40070018  UARTFR    Flag register
                       Bit 4: RXFE (RX FIFO Empty)
                       Bit 5: TXFF (TX FIFO Full)
0x40070024  UARTIBRD  Integer baud rate divisor
0x40070028  UARTFBRD  Fractional baud rate divisor
0x4007002c  UARTLCR_H Line control (8N1 config)
0x40070030  UARTCR    Control register (enable)
```

### 8.3 GPIO 的使用

只配置了两个 GPIO 引脚, 都是给 UART0 用的:

- **GPIO0**: UART0 TX (功能: UART)
- **GPIO1**: UART0 RX (功能: UART)

运行时没有用到任何 SIO 的 GPIO 输出/输入寄存器 (没有访问
`0xd0000014` 的 SET, 也没有访问 `0xd0000004` 的 IN). 这是唯一一个
运行时完全不碰 SIO GPIO 的 embedded-wasm 变体.

---

## 9. Pulley 解释器深入剖析

### 9.1 解释器入口 (`InterpreterRef::call`)

```
Location:  0x1000c570  (2,304 bytes)
```

调用序列:

```
run_wasm()
  -> UartEcho::instantiate()
    -> UartEcho::call_run()
      -> InterpreterRef::call()     <-- native-to-Pulley boundary
        -> Vm::call_start()         ; Set up Pulley register file
        -> Vm::call_run()           ; Enter interpreter loop
          -> Interpreter::run()     ; Main dispatch loop
```

### 9.2 主分发循环

```
Location:  0x10063cac  (12,518 bytes)
```

所有 embedded-wasm 仓库用的都是同一套两级分发方案: 主操作码
(0x00-0xDB) 由 `Interpreter::run` 里的一张跳转表处理, 扩展的
操作码 (0xDC 前缀加 2 字节操作码) 由
`decode_one_extended` 处理.

---

## 10. 内嵌的 cwasm 数据块

### 10.1 位置与格式

预编译的 Pulley 字节码嵌在 `.rodata` 里的
`0x10088578` 处. 它**长 24,456 字节** (0x5f88).

| 字段   | 值                             |
| ------ | ------------------------------ |
| Magic  | `\x7fELF`                      |
| Class  | ELF64 (偏移 4 处的字节为 `02`) |
| Data   | 小端                           |
| Target | `pulley32-unknown-unknown-elf` |

这是四个 embedded-wasm 变体里最小的 cwasm, 因为客体只有两个
宿主导入 (`read-byte`, `write-byte`), 逻辑是简单的顺序执行,
没有分支.

### 10.2 客体代码逻辑

```
fn run() {
    loop {
        let byte = call_import uart::read_byte()
        match byte {
            0x08 | 0x7f => {            // Backspace or DEL
                call_import uart::write_byte(0x08)  // BS
                call_import uart::write_byte(0x20)  // Space
                call_import uart::write_byte(0x08)  // BS
            }
            0x0d => {                   // Carriage Return
                call_import uart::write_byte(0x0d)  // CR
                call_import uart::write_byte(0x0a)  // LF
            }
            _ => {
                call_import uart::write_byte(byte)  // Echo
            }
        }
    }
}
```

客体实现的是一套简单的终端回显, 带破坏性退格 (用一个空格把字符
覆盖掉) 和 CR 到 CRLF 的转换.

---

## 11. 宿主-客体调用流程

### 11.1 字符回显

```
[Pulley VM]  Bytecode: call_indirect_host -> read_byte()
    |
    v
[ARM Native]  uart::read_byte (inlined into run_wasm)
    |
    v
[Hardware]  UART0 UARTDR @ 0x40070000 -> read byte from RX FIFO

[Pulley VM]  Return to guest with byte value in x0
    |
    v
[Pulley VM]  Match: regular character -> call_indirect_host -> write_byte(byte)
    |
    v
[ARM Native]  uart::write_byte (inlined into run_wasm)
    |
    v
[Hardware]  UART0 UARTDR @ 0x40070000 -> write byte to TX FIFO
```

### 11.2 退格的处理

```
[Pulley VM]  read_byte() returns 0x08 (BS) or 0x7f (DEL)
    |
    v
[Pulley VM]  Match: backspace -> three consecutive write_byte calls
    |
    +-- call_indirect_host -> write_byte(0x08)    ; Move cursor back
    +-- call_indirect_host -> write_byte(0x20)    ; Overwrite with space
    +-- call_indirect_host -> write_byte(0x08)    ; Move cursor back again
    |
    v
[Hardware]  Three UART TX writes: BS, SPACE, BS
```

---

## 12. 逆向观察

### 12.1 二进制构成

| 组成                      | 大致大小 | 占 .text 的比例 |
| ------------------------- | -------- | --------------- |
| Wasmtime 运行时           | 约 533 KiB | 98.9%         |
| Pulley 解释器 (run)       | 12.2 KiB | 2.3%            |
| Pulley 解码器 (扩展)      | 16.1 KiB | 3.0%            |
| 应用部分 (uart+main)      | 约 6 KiB | 1.1%            |

这是最精简的 embedded-wasm 变体. 应用代码极少, 因为
`uart::read_byte` 和 `uart::write_byte` 都被内联进了 `run_wasm`,
而且没有链接任何 GPIO 模块.

### 12.2 各变体的对比

| 方面            | Blinky      | Button      | UART      | C2          |
| --------------- | ----------- | ----------- | --------- | ----------- |
| .text 大小      | 544,880 B   | 548,680 B   | 539,176 B | 556,712 B   |
| .data 大小      | 36 B        | 36 B        | 40 B      | 36 B        |
| .bss 大小       | 262,308 B   | 262,324 B   | 262,292 B | 262,316 B   |
| cwasm 大小      | 24,680 B    | 25,384 B    | 24,456 B  | 24,704 B    |
| 函数数          | 2,375       | 2,392       | 2,375     | 2,501       |
| WIT 接口        | gpio,timing | gpio,btn,tm | uart      | gpio,timing |
| 使用的 GPIO 引脚 | 1 个输出   | 1 入 1 出   | 0 (UART)  | 27 个输出   |
| SIO GPIO 访问   | 有          | 有          | **无**    | 有          |

### 12.3 关键地址速查

| 地址         | 说明                                          |
| ------------ | --------------------------------------------- |
| `0x10000000` | 向量表 (初始 SP 加异常向量)                   |
| `0x100000f8` | RP2350 IMAGE_DEF 启动块                       |
| `0x1000010c` | 复位处理函数 (入口点)                         |
| `0x100071e8` | init_hardware                                 |
| `0x1000736c` | __cortex_m_rt_main                            |
| `0x100073d8` | run_wasm                                      |
| `0x10007b1c` | init_heap                                     |
| `0x1000801c` | platform::uart::add_to_linker                 |
| `0x10008014` | main (薄包装)                                 |
| `0x10063cac` | Pulley Interpreter::run (分发循环)            |
| `0x10066fc8` | Pulley decode_one_extended                    |
| `0x1000c570` | InterpreterRef::call (原生到 Pulley 的桥接)   |
| `0x10088578` | 内嵌的 cwasm 数据块 (Pulley ELF)              |
| `0x1007b5a4` | DefaultHandler (死循环)                       |
| `0x10083b2c` | HardFault (死循环)                            |
| `0x40070000` | UART0 基地址 (UARTDR 数据寄存器)              |
| `0x40070018` | UART0 UARTFR (标志寄存器)                     |
| `0x20000000` | uart::UART 句柄 (.data, 8 B)                  |
| `0x2000002c` | HEAP_MEM (256 KiB)                            |
| `0x20080000` | 初始栈指针                                    |

---

## 13. Pulley 指令集架构

### 13.1 概览

Pulley 是 Wasmtime 的可移植字节码解释器 (wasmtime 43.0.0,
`pulley-interpreter` crate v43.0.0). 它定义了一套基于寄存器的
ISA, 指令长度可变, 设计目标是高效解释, 而不是走原生执行
那条路.

### 13.2 编码格式

**主操作码**用一个字节的操作码加操作数表示:

```
[opcode:1] [operands:0-9]
```

一共有 **220 个主操作码** (0x00-0xDB). 操作码 `0xDC` 是
**ExtendedOp** 哨兵 - 解释器遇到它时, 会再读一个 2 字节的
扩展操作码:

```
[0xDC] [ext_opcode:2] [operands:0-N]
```

还有 **310 个扩展操作码** (0x0000-0x0135), 用于 SIMD, 浮点
转换以及复杂操作.

### 13.3 关键指令

完整的 Pulley ISA 参考见 [embedded-wasm-servo-rp2350 RE.md](https://github.com/mytechnotalent/embedded-wasm-servo-rp2350)
第 13 节. UART 客体使用的指令子集与基础版 blinky
相同, 只是为 `match` 语句额外增加了比较
和条件分支指令.

---

## 14. Pulley 字节码反汇编

### 14.1 Guest::run() - UART 回显循环

```
; function[N]: Guest::run()

push_frame_save <frame>, <callee-saved regs>

; Load VMContext and function pointers
xload32le_o32 x_heap, x0, 28          ; heap_base
xmov x_vmctx, x0                      ; save VMContext

; Load host function pointers
xload32le_o32 x_read_fn, x_vmctx, ...
xload32le_o32 x_write_fn, x_vmctx, ...

; Load constants for comparison
xconst8 x_bs, 0x08                    ; Backspace
xconst8 x_del, 0x7f                   ; DEL
xconst8 x_cr, 0x0d                    ; Carriage Return
xconst8 x_lf, 0x0a                    ; Line Feed
xconst8 x_space, 0x20                 ; Space

.loop:
    ; --- uart::read_byte() ---
    call_indirect x_read_fn            ; -> ARM: blocking UART RX
    xmov x_byte, x0                   ; Save received byte

    ; --- Check for backspace (0x08) ---
    br_if_xeq32 x_byte, x_bs, .backspace

    ; --- Check for DEL (0x7f) ---
    br_if_xeq32 x_byte, x_del, .backspace

    ; --- Check for CR (0x0d) ---
    br_if_xeq32 x_byte, x_cr, .newline

    ; --- Default: echo the character ---
    xmov x2, x_byte
    call_indirect x_write_fn
    jump .loop

.backspace:
    xmov x2, x_bs                     ; BS
    call_indirect x_write_fn
    xmov x2, x_space                  ; Space (overwrite)
    call_indirect x_write_fn
    xmov x2, x_bs                     ; BS (back again)
    call_indirect x_write_fn
    jump .loop

.newline:
    xmov x2, x_cr                     ; CR
    call_indirect x_write_fn
    xmov x2, x_lf                     ; LF
    call_indirect x_write_fn
    jump .loop
```

---

## 15. Ghidra 分析流程

### 15.1 导入与初始分析

1. **File -> Import File**: 选中那个 ELF. Ghidra 会自动识别出
   `ARM:LE:32:v8T` (ARMv8 Thumb). 接受默认选项即可.

2. **自动分析**: Ghidra 会从符号表里识别出 2,375
   个函数.

3. **分析耗时**: 处理这个 1.11 MiB 的二进制大约需要 30 秒.

### 15.2 符号树导航

```
Functions/ (2,375 total)
+-- Reset                              0x1000010c
+-- main                               0x10008014
+-- __cortex_m_rt_main                 0x1000736c
+-- embedded_wasm_uart::run_wasm       0x100073d8
+-- embedded_wasm_uart::init_hardware  0x100071e8
+-- platform::uart::add_to_linker      0x1000801c
+-- pulley_interpreter::interp::Interpreter::run  0x10063cac
+-- pulley_interpreter::decode::decode_one_extended  0x10066fc8
+-- InterpreterRef::call               0x1000c570
+-- ... (2,366 more)
```

### 15.3 找到并提取 cwasm 数据块

1. 在 Listing 视图里跳到 `0x10088578`
2. Ghidra 会显示 `7f 45 4c 46` (ELF 魔数) 那几个字节
3. 右键 -> **Select Bytes** -> 输入长度 24456 (0x5f88)
4. **File -> Export Selection** -> 选 Binary 格式 -> 存成 `uart-echo.cwasm`

### 15.4 Ghidra 加 G-Pulley: 全栈分析

装上 [G-Pulley](https://github.com/mytechnotalent/G-Pulley) 扩展
之后, Ghidra 可以同时分析 ARM 宿主固件和
Pulley 客体字节码:

| 方面         | ARM 宿主代码               | Pulley 客体代码 (G-Pulley)           |
| ------------ | -------------------------- | ------------------------------------ |
| 反汇编       | 完整 ARM Thumb-2           | 完整 Pulley ISA 助记符               |
| 函数识别     | 依据符号自动识别           | 自动识别 (cwasm 加载器加分析器)      |
| 交叉引用     | 完整的引用图               | 函数调用与分支                       |
| 控制流       | 带 switch 识别的 CFG       | 分支与跳转目标已解析                 |
| 宿主调用边界 | `InterpreterRef::call`     | `call_indirect_host` 指令            |

**G-Pulley 提供**:

- 自定义 ELF 加载器, 从固件中提取 `.cwasm` 数据块
- Pulley 32 位与 64 位 ISA 的 SLEIGH 处理器描述 (Wasmtime v43.0.0)
- 加载后分析器, 用于发现函数, 跳板代码和宿主调用
- 对全部 220 个主操作码加 310 个扩展 Pulley 操作码的完整解码

### 15.5 推荐的 Ghidra 工作流

1. **安装 G-Pulley**: 从
   [G-Pulley releases](https://github.com/mytechnotalent/G-Pulley/releases) 下载.
   在 Ghidra 里: **File -> Install Extensions -> + -> 选择 zip**. 重启.

2. **分析 ARM 固件**: 导入 ELF. 运行自动分析.
   顺着 Reset -> main -> `__cortex_m_rt_main` -> `run_wasm` 一路看下去.

3. **考察 UART 绑定**: 跳到 `platform::uart::add_to_linker`
   (0x1000801c), 看 `read-byte` 和 `write-byte` 是怎么注册的.
   真正的 UART I/O 被内联进了 `run_wasm` (0x100073d8).

4. **跟踪解释器**: 从 `InterpreterRef::call` (0x1000c570) 出发,
   跟进 `Interpreter::run` (0x10063cac), 看 Pulley 的分发
   循环.

5. **分析 Pulley 字节码**: 用 G-Pulley 的 cwasm 加载器再次导入
   固件 ELF (选择 "Pulley cwasm" 格式). G-Pulley
   会提取内嵌的 cwasm 数据块, 反汇编所有 Pulley 操作码,
   并识别出客体函数, 包括那个带回显循环, 以及
   退格和换行处理分支.
