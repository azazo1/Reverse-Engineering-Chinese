# 逆向工程: Wasm (桌面 Pulley 宿主)

## 目录

1. [二进制概览](#1-二进制概览)
2. [Mach-O 头](#2-mach-o-头)
3. [段布局](#3-段布局)
4. [内存映射](#4-内存映射)
5. [应用架构](#5-应用架构)
6. [Cranelift 编译器集成](#6-cranelift-编译器集成)
7. [函数地图](#7-函数地图)
8. [运行时环境](#8-运行时环境)
9. [Pulley 解释器深入剖析](#9-pulley-解释器深入剖析)
10. [内嵌的 cwasm 数据块](#10-内嵌的-cwasm-数据块)
11. [宿主-客体调用流程](#11-宿主-客体调用流程)
12. [逆向观察](#12-逆向观察)
13. [Pulley 指令集架构](#13-pulley-指令集架构)
14. [Pulley 字节码反汇编](#14-pulley-字节码反汇编)
15. [Ghidra 分析流程](#15-ghidra-分析流程)

---

## 1. 二进制概览

| 属性       | 值                          |
| ---------- | --------------------------- |
| 文件       | `hello`                     |
| crate 名称 | `hello-world`               |
| 磁盘大小   | 12,284,112 字节 (11.7 MiB)  |
| 格式       | Mach-O 64 位可执行文件      |
| 架构       | arm64 (Apple Silicon)       |
| 目标系统   | macOS                       |
| 是否去符号 | 否 (27,450 个符号)          |

这是一个**桌面端**的 Wasmtime 组件模型宿主, 它从内嵌字节中加载两个
预编译的 Pulley 客体组件 (`guest1.cwasm`, `guest2.cwasm`), 并
通过 **Pulley 64 位**解释器 (`pulley64` 目标) 执行它们导出的函数.
与那些跑在裸机 Cortex-M33 上的嵌入式版本不同, 这个二进制程序运行在
macOS 上, 拥有完整的 `std` 支持. 下面把它的结构和运行机制逐项拆开
来看.

与 embedded-wasm 系列版本的关键差异:

| 方面           | 嵌入式 (RP2350)       | 桌面 (macOS)                  |
| -------------- | --------------------- | ----------------------------- |
| 二进制格式     | ELF32 ARM             | Mach-O 64 位 arm64            |
| Pulley 目标    | `pulley32`            | `pulley64`                    |
| 客体数量       | 1                     | 2 (guest1 + guest2)           |
| WIT 接口       | 硬件 (GPIO, UART)     | 纯计算 (无导入)               |
| 二进制大小     | 约 1.1-1.2 MiB        | 11.7 MiB                      |
| 是否链接 Cranelift | 否                | 是 (二进制内含 AOT 编译器)    |
| 硬件访问       | 直接寄存器 I/O        | 无 (用户态进程)               |

---

## 2. Mach-O 头

```
Mach header
      magic  cputype cpusubtype  caps    filetype ncmds sizeofcmds      flags
 0xfeedfacf 16777228          0  0x00           2    18       2160 0x00a18085
```

| 字段       | 值                                     |
| ---------- | -------------------------------------- |
| Magic      | `0xfeedfacf` (MH_MAGIC_64)             |
| CPU 类型   | `0x0100000c` (ARM64)                   |
| 文件类型   | `2` (MH_EXECUTE)                       |
| 加载命令数 | 18                                     |
| 标志       | `0x00a18085` (PIE, TWOLEVEL, DYLDLINK) |

这个二进制是位置无关可执行文件 (PIE), 带有两级命名空间绑定
和动态链接器支持.

---

## 3. 段布局

```
Segment        VMAddr           VMSize       FileOff    FileSize     Prot   Description
__PAGEZERO     0x000000000      4 GiB        0          0            ---    Guard page
__TEXT         0x100000000      8.56 MiB     0          8,978,432    r-x    Code + constants
__DATA_CONST   0x100890000      384 KiB      8,978,432  393,216      rw-    Const data
__DATA         0x1008f0000      16 KiB       9,371,648  16,384       rw-    Mutable data
__LINKEDIT     0x1008f4000      2.77 MiB     9,388,032  2,896,080    r--    Symbol tables
```

### __TEXT 各节细分

| 节                 | 大小     | 说明                         |
| ------------------ | -------- | ---------------------------- |
| `__text`           | 6.89 MiB | 全部可执行代码               |
| `__const`          | 703 KiB  | 只读数据 + cwasm 数据块      |
| `__gcc_except_tab` | 263 KiB  | 异常处理表                   |
| `__unwind_info`    | 142 KiB  | 栈展开元数据                 |
| `__cstring`        | 85 KiB   | C 字符串字面量               |
| `__stubs`          | 1.2 KiB  | 惰性符号桩                   |
| `__stub_helper`    | 1.2 KiB  | 桩辅助代码                   |

### 体积分析

这个二进制比嵌入式版本**大 10 倍**, 原因在于:

1. **Cranelift 编译器** (约 5 MiB): 完整的 AOT 编译器被链接了进来,
   供 `Engine::new()` 使用, 尽管我们在运行时只反序列化预编译的
   组件.

2. **异常处理** (405 KiB): `__gcc_except_tab` 加上 `__unwind_info`,
   用于支持 Rust panic 的栈展开 (`no_std` 里没有这套东西).

3. **两个 cwasm 数据块**: `guest1.cwasm` 和 `guest2.cwasm` 都
   内嵌在 `__const` 里.

4. **标准库**: 链接了完整的 `std` (线程, I/O, 分配器).

---

## 4. 内存映射

```
Virtual Address Space (arm64 macOS):

0x000000000 - 0x0FFFFFFFF   __PAGEZERO (4 GiB guard)
0x100000000 - 0x10088FFFF   __TEXT (code + constants)
    +-- 0x1000008c0          __text starts (executable code)
    +-- 0x10068e934          __stubs (dyld lazy binding)
    +-- 0x1006cfce0          __const (cwasm blobs embedded here)
    +-- 0x10077b8c8          __cstring (string literals)
0x100890000 - 0x1008EFFFF   __DATA_CONST (vtables, type metadata)
0x1008f0000 - 0x1008F3FFF   __DATA (mutable globals, TLS)
0x1008f4000 - 0x100BB7FFF   __LINKEDIT (symbols, string table)

Heap:   Managed by system allocator (malloc/free)
Stack:  Thread stack managed by macOS (default 8 MiB)
```

---

## 5. 应用架构

### 5.1 入口点

macOS 的动态链接器 (`dyld`) 调用 `_main`, 后者再转发到
Rust 运行时的入口. 应用入口是位于
`0x10002096c` 的 `hello::main`.

### 5.2 执行流程

```
_main (dyld entry)
  -> std::rt::lang_start
    -> hello::main (0x10002096c)
      -> hello::run()                [inlined]
        -> parse_name()              [inlined] - read argv[1] or "Pulley"
        -> build_engine()            [inlined] - Config + pulley64 target
        -> load_component(guest1)    [inlined] - deserialize guest1.cwasm
        -> run_guest1()              [inlined] - instantiate + call run()
        -> load_component(guest2)    [inlined] - deserialize guest2.cwasm
        -> run_guest2(name)          [inlined] - instantiate + call run(name) + describe()
```

所有应用函数 (`build_engine`, `load_component`,
`run_guest1`, `run_guest2`, `parse_name`, `run`) 都被
release 模式的优化器内联进了 `hello::main`.

### 5.3 Engine 配置

```rust
let mut config = Config::new();
config.wasm_component_model(true);
config.target("pulley64")?;
Engine::new(&config)
```

嵌入式版本会关掉那些依赖操作系统的特性
(`signals_based_traps(false)`, `memory_init_cow(false)` 等等),
桌面版这边则不同, 用的是默认设置. `pulley64` 目标选中的是
64 位 Pulley ISA 变体, 指针宽度为 64 位.

---

## 6. Cranelift 编译器集成

桌面版二进制里包含了完整的 **Cranelift** 代码生成器 -
就代码体积而言, 它是其中最大的一块. 它之所以被链接进来, 是因为
`Engine::new()` 会牵出整条 AOT 流水线, 尽管我们的用法只
调用 `Component::deserialize()` 来处理预编译好的 cwasm 字节.

### 6.1 体积最大的 Cranelift 函数

| 地址          | 大小      | 还原后的名称                                     |
| ------------- | --------- | ------------------------------------------------ |
| `0x1003da46c` | 168,192 B | `constructor_simplify` (egraph 优化)             |
| `0x100390cac` | 56,696 B  | `pulley_shared::inst::print` (指令打印)          |
| `0x1004e94a0` | 56,264 B  | `aarch64::constructor_lower` (ARM64 指令下降)    |
| `0x1002b9fe4` | 36,884 B  | `pulley_shared::constructor_lower` (Pulley)      |
| `0x1002b0fd0` | 36,884 B  | `pulley_shared::constructor_lower` (Pulley #2)   |
| `0x100232aec` | 32,284 B  | `translate_operator` (Wasm 到 CLIF)              |
| `0x1004dfbe8` | 28,776 B  | `aarch64::MInst::print_with_state`               |

### 6.2 Cranelift 的架构

这个二进制同时包含了宿主 (aarch64)
和 Pulley 目标**两者**的指令下降后端:

- `cranelift_codegen::isa::aarch64` - ARM64 原生代码生成
- `cranelift_codegen::isa::pulley_shared` - Pulley 字节码发出

两者都在 `build.rs` 的 AOT 编译阶段被用到. 到了运行时,
只有 Pulley 解释器那条路径是活跃的.

---

## 7. 函数地图

### 7.1 应用函数

| 地址          | 符号          | 用途                         |
| ------------- | ------------- | ---------------------------- |
| `0x10002096c` | `hello::main` | 入口点 (所有辅助函数已内联)  |

其余应用函数 (`build_engine`, `load_component`,
`run_guest1`, `run_guest2`, `parse_name`, `run`) 都被内联进了
`hello::main`, 这是 release 模式优化器的功劳.

### 7.2 Wasmtime 运行时 (关键符号)

| 地址          | 还原后的名称                              |
| ------------- | ----------------------------------------- |
| `0x10009ab08` | `OperatorCost::deserialize`               |
| `0x10050a75c` | `decode_one_extended`                     |
| `0x100510158` | `Interpreter::run` (Pulley 分发循环)      |
| `0x10053b3d4` | `OperatorCost::cost`                      |
| `0x10053d488` | `OperatorCostStrategy::cost`              |
| `0x1000c356c` | `Metadata::check_cost`                    |
| `0x100045078` | `InterpreterRef::call`                    |
| `0x100513708` | `Vm::call_start`                          |
| `0x100513998` | `Vm::call_run`                            |

### 7.3 符号统计

| 类别                   | 数量     | 占 27,450 的比例 |
| ---------------------- | -------- | ---------------- |
| Cranelift 代码生成     | 约 8,000 | 29%              |
| Wasmtime 运行时        | 约 6,000 | 22%              |
| Pulley 解释器          | 约 2,000 | 7%               |
| 标准库                 | 约 5,000 | 18%              |
| 组件模型 / WIT         | 约 3,000 | 11%              |
| 其他 (alloc, serde)    | 约 3,450 | 13%              |

---

## 8. 运行时环境

### 8.1 动态库

这个二进制链接了 macOS 的系统库:

```
/usr/lib/libSystem.B.dylib       - POSIX syscalls, malloc, pthreads
/usr/lib/libc++.1.dylib          - C++ standard library (for exception handling)
```

### 8.2 内存管理

- **堆**: 系统分配器 (`malloc`/`free`) - 没有自定义分配器
- **栈**: macOS 默认线程栈 (8 MiB)
- **Wasm 线性内存**: 由 Wasmtime 的 `MemoryCreator` 使用
  带保护页的 `mmap` 分配

### 8.3 不与硬件交互

嵌入式版本会直接访问 SIO, UART 和
SysTick 寄存器, 而这个二进制**完全不碰硬件寄存器**. 所有
I/O 都走标准库函数 (`println!`, `std::env::args`).

---

## 9. Pulley 解释器深入剖析

### 9.1 解释器入口 (`InterpreterRef::call`)

```
Location:  0x100045078
```

调用序列 (针对 guest1):

```
hello::main()
  -> Engine::new(&config)           ; pulley64 target
  -> Component::deserialize(guest1.cwasm)
  -> Linker::instantiate()
  -> get_typed_func("run")
  -> run.call()
    -> InterpreterRef::call()       <-- native-to-Pulley boundary
      -> Vm::call_start()           ; Set up Pulley register file
      -> Vm::call_run()             ; Enter interpreter loop
        -> Interpreter::run()       ; Main dispatch loop
```

### 9.2 主分发循环

```
Location:  0x100510158
```

和嵌入式版本用的是同一套两级分发方案. 64 位变体在
Pulley 寄存器文件里使用 64 位的寄存器和指针, 但分发机制
完全一致.

### 9.3 Pulley 64 位与 32 位对比

| 方面               | pulley32 (嵌入式)    | pulley64 (桌面)      |
| ------------------ | -------------------- | -------------------- |
| 寄存器宽度         | 32 位                | 64 位                |
| 指针大小           | 4 字节               | 8 字节               |
| 线性内存地址       | 32 位偏移            | 64 位偏移            |
| 加载/存储操作      | `xload32le_*`        | `xload64le_*`        |
| cwasm 的 ELF 目标  | pulley32-unknown-elf | pulley64-unknown-elf |

---

## 10. 内嵌的 cwasm 数据块

### 10.1 两个客体组件

这个二进制通过 `include_bytes!` 内嵌了两份预编译的 cwasm 数据块:

```rust
const GUEST1_PRECOMPILED: &[u8] = include_bytes!(concat!(env!("OUT_DIR"), "/guest1.cwasm"));
const GUEST2_PRECOMPILED: &[u8] = include_bytes!(concat!(env!("OUT_DIR"), "/guest2.cwasm"));
```

两者都位于 `__TEXT` 段中 `__const` 节的
`0x1006cfce0` 处.

### 10.2 Guest1 - 简单的导出

**WIT 契约** (`guest1/wit/world.wit`):

```wit
package component:guest1;
world guest1-world {
    export run: func() -> string;
}
```

**客体代码**:

```rust
fn run() -> String {
    String::from("guest1 run() called")
}
```

没有宿主导入 - 这个客体就是一个返回字符串的纯函数.

### 10.3 Guest2 - 带参数的导出加 describe

**WIT 契约** (`guest2/wit/world.wit`):

```wit
package component:guest2;
world guest2-world {
    export run: func(name: option<string>) -> string;
    export describe: func() -> string;
}
```

**客体代码**:

```rust
fn run(name: Option<String>) -> String {
    let name = name.as_deref().unwrap_or("world");
    format!("guest2 run() called: hello, {name}!")
}

fn describe() -> String {
    String::from("guest2 has an extra `describe` export")
}
```

Guest2 有两个导出, 并且接受一个可选的字符串参数.
`format!` 宏生成的 Pulley 字节码会通过客体的 `dlmalloc` 分配器
完成字符串拼接.

---

## 11. 宿主-客体调用流程

### 11.1 Guest1 的执行

```
[arm64 Native]  hello::main
    |  Engine::new(pulley64)
    |  Component::deserialize(GUEST1_PRECOMPILED)
    |  Linker::instantiate()
    v
[arm64 Native]  get_typed_func::<(), (String,)>("run")
    |  run.call(())
    v
[arm64 Native]  InterpreterRef::call (0x100045078)
    |  Set up Pulley64 register file
    v
[Pulley64 VM]   Guest1::run()
    |  Allocate string "guest1 run() called" via dlmalloc
    |  Return string through component model canonical ABI
    v
[arm64 Native]  Receive String result
    |  println!("{result}")
```

### 11.2 Guest2 的执行

```
[arm64 Native]  hello::main
    |  Component::deserialize(GUEST2_PRECOMPILED)
    |  Linker::instantiate()
    v
[arm64 Native]  get_typed_func::<(Option<String>,), (String,)>("run")
    |  run.call((Some("Pulley"),))
    v
[Pulley64 VM]   Guest2::run(Some("Pulley"))
    |  Unwrap option -> "Pulley"
    |  format!("guest2 run() called: hello, Pulley!")
    |  Return formatted string
    v
[arm64 Native]  println!("{run_result}")
    |
    v
[arm64 Native]  get_typed_func::<(), (String,)>("describe")
    |  describe.call(())
    v
[Pulley64 VM]   Guest2::describe()
    |  Return "guest2 has an extra `describe` export"
    v
[arm64 Native]  println!("describe: {desc_result}")
```

### 11.3 没有宿主导入

嵌入式版本里客体会回调宿主代码来访问硬件 (GPIO, UART, SysTick),
而这两个桌面客体**没有任何导入**. WIT 声明全都是导出. Pulley
解释器会把客体代码一直跑到结束, 中途不需要任何宿主回调, 也
不用等宿主的介入.

---

## 12. 逆向观察

### 12.1 二进制构成

| 组成                      | 大致大小 | 占 __text 的比例 |
| ------------------------- | -------- | ---------------- |
| Cranelift 代码生成        | 约 3.5 MiB | 50.8%          |
| Wasmtime 运行时           | 约 1.5 MiB | 21.8%          |
| Pulley 解释器             | 约 0.5 MiB | 7.3%           |
| 组件模型 / WIT            | 约 0.5 MiB | 7.3%           |
| 标准库                    | 约 0.6 MiB | 8.7%           |
| 应用代码                  | <1 KiB     | <0.1%          |
| 异常处理                  | 约 263 KiB | 3.7%           |
| 其他 (serde, alloc 等)    | 约 0.3 MiB | 4.4%           |

### 12.2 死代码: Cranelift

Cranelift 编译器占了整个二进制约 50% 的体积, 但**运行时根本
用不到**. 应用只调用 `Component::deserialize()`, 加载的是预编译好的
Pulley 字节码. Cranelift 之所以被链接进来, 是因为
`Engine::new()` 会把整条编译流水线拉进来. 后续的优化可以
更精细地使用 `wasmtime` 的 `cranelift`
特性开关.

### 12.3 桌面版与嵌入式版对比

| 指标               | 桌面版 (`hello`)  | 嵌入式版 (blinky)   |
| ------------------ | ----------------- | ------------------- |
| 二进制大小         | 11.7 MiB          | 1.12 MiB            |
| 代码大小 (__text)  | 6.89 MiB          | 533 KiB             |
| 函数数量           | 27,450            | 2,375               |
| 应用代码           | <1 KiB            | 约 6 KiB            |
| 是否链接 Cranelift | 是 (约 3.5 MiB)   | 否 (0 B)            |
| Pulley 字长        | 64 位             | 32 位               |
| WIT 导入           | 0                 | 2-4 (gpio 等)       |
| 客体组件           | 2                 | 1                   |
| 硬件访问           | 无                | 直接寄存器 I/O      |
| 操作系统支持       | 完整 std          | no_std 裸机         |
| 堆分配器           | 系统 malloc       | embedded-alloc LLFF |

### 12.4 关键地址速查

| 地址          | 说明                                          |
| ------------- | --------------------------------------------- |
| `0x1000008c0` | __text 节起始                                 |
| `0x10002096c` | hello::main (应用入口)                        |
| `0x100045078` | InterpreterRef::call (原生到 Pulley 的桥接)   |
| `0x100510158` | Pulley Interpreter::run (分发循环)            |
| `0x10050a75c` | Pulley decode_one_extended                    |
| `0x100513708` | Vm::call_start                                |
| `0x100513998` | Vm::call_run                                  |
| `0x10009ab08` | OperatorCost::deserialize                     |
| `0x1006cfce0` | __const 节 (cwasm 数据块就嵌在这里)           |
| `0x1003da46c` | Cranelift constructor_simplify (168 KiB)      |
| `0x100390cac` | Cranelift pulley inst::print (57 KiB)         |
| `0x1004e94a0` | Cranelift aarch64 constructor_lower (56 KiB)  |

---

## 13. Pulley 指令集架构

### 13.1 概览

Pulley 是 Wasmtime 的可移植字节码解释器 (wasmtime 43.0.0,
`pulley-interpreter` crate v43.0.0). 它定义了一套基于寄存器的
ISA, 指令长度可变, 设计目标是高效解释, 而不是走
原生执行那条路.

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

### 13.3 64 位变体

`pulley64` 目标使用与 `pulley32` 相同的操作码编码, 但
通用寄存器是 64 位的, 运算按指针宽度进行.
`xload64le_*` 这类加载/存储指令以及地址计算都使用
完整的 64 位值.

完整的 Pulley ISA 参考见 [embedded-wasm-servo-rp2350 RE.md](https://github.com/mytechnotalent/embedded-wasm-servo-rp2350)
第 13 节.

---

## 14. Pulley 字节码反汇编

### 14.1 Guest1::run() - 返回字符串

```
; function: Guest1::run() -> string

push_frame_save <frame>, <callee-saved regs>

; Load VMContext
xload64le_o32 x_heap, x0, ...        ; heap_base (64-bit pointer)
xmov x_vmctx, x0

; Allocate string via dlmalloc
; "guest1 run() called" (20 bytes)
xconst8 x_len, 20                    ; string length
call <cabi_realloc>                   ; allocate 20 bytes on guest heap

; Copy string data to allocated buffer
; ... memcpy of "guest1 run() called" ...

; Return (ptr, len) through canonical ABI
xmov x_ret_ptr, x_alloc
xmov x_ret_len, x_len
pop_frame_restore <frame>, <callee-saved regs>
ret
```

### 14.2 Guest2::run(name) - 字符串格式化

```
; function: Guest2::run(name: option<string>) -> string

push_frame_save <frame>, <callee-saved regs>

; Load parameters via canonical ABI
; x2 = discriminant (0 = None, 1 = Some)
; x3, x4 = string ptr, len (if Some)

; Check if name is Some
br_if_xeq32 x2, x_zero, .use_default

; Some case: use provided name
xmov x_name_ptr, x3
xmov x_name_len, x4
jump .format

.use_default:
; None case: use "world"
xconst8 x_name_len, 5
; load address of "world" literal
; ...

.format:
; Concatenate: "guest2 run() called: hello, " + name + "!"
; Multiple cabi_realloc calls for string building
; ...

pop_frame_restore <frame>, <callee-saved regs>
ret
```

---

## 15. Ghidra 分析流程

### 15.1 导入与初始分析

1. **File -> Import File**: 选中 `hello` 二进制. Ghidra
   会自动识别出 `AARCH64:LE:64:AppleSilicon`. 接受默认选项即可.

2. **自动分析**: Ghidra 会从 Mach-O 符号表里识别出大约 27,450
   个函数.

3. **分析耗时**: 处理这个 11.7 MiB 的二进制大约需要 2-3 分钟.

### 15.2 符号树导航

```
Functions/ (27,450 total)
+-- _main                                          (dyld entry)
+-- hello::main                                    0x10002096c
+-- pulley_interpreter::interp::Interpreter::run   0x100510158
+-- pulley_interpreter::decode::decode_one_extended 0x10050a75c
+-- InterpreterRef::call                           0x100045078
+-- Vm::call_start                                 0x100513708
+-- Vm::call_run                                   0x100513998
+-- cranelift_codegen::opts::constructor_simplify   0x1003da46c
+-- cranelift_codegen::isa::pulley_shared::lower    0x1002b9fe4
+-- ... (27,441 more)
```

### 15.3 找到 cwasm 数据块

1. 在 `__const` 节里搜索 `\x7fELF` (该节从
   `0x1006cfce0` 开始)
2. `guest1.cwasm` 和 `guest2.cwasm` 都在这里
3. 每个都以 ELF64 魔数开头, 目标是 `pulley64-unknown-unknown-elf`
4. 右键 -> **Select Bytes** -> 把每个数据块单独导出

### 15.4 Ghidra 加 G-Pulley: 全栈分析

装上 [G-Pulley](https://github.com/mytechnotalent/G-Pulley) 扩展
之后, Ghidra 可以同时分析 arm64 宿主二进制和
Pulley 客体字节码:

| 方面         | arm64 宿主代码             | Pulley 客体代码 (G-Pulley)           |
| ------------ | -------------------------- | ------------------------------------ |
| 反汇编       | 完整 AArch64               | 完整 Pulley ISA 助记符               |
| 函数识别     | 依据符号自动识别           | 自动识别 (cwasm 加载器加分析器)      |
| 交叉引用     | 完整的引用图               | 函数调用与分支                       |
| 控制流       | 带 switch 识别的 CFG       | 分支与跳转目标已解析                 |

**G-Pulley 提供**:

- 自定义 ELF 加载器, 从宿主二进制中提取 `.cwasm` 数据块
- Pulley 32 位与 64 位 ISA 的 SLEIGH 处理器描述 (Wasmtime v43.0.0)
- 加载后分析器, 用于发现函数, 跳板代码和宿主调用
- 对全部 220 个主操作码加 310 个扩展 Pulley 操作码的完整解码

### 15.5 推荐的 Ghidra 工作流

1. **安装 G-Pulley**: 从
   [G-Pulley releases](https://github.com/mytechnotalent/G-Pulley/releases) 下载.
   在 Ghidra 里: **File -> Install Extensions -> + -> 选择 zip**. 重启.

2. **分析 arm64 宿主**: 导入 Mach-O 二进制. 运行
   自动分析. 跳到 `hello::main` (0x10002096c), 看那段
   被内联的应用逻辑 - 创建 Engine, 反序列化组件,
   调用客体.

3. **跟踪解释器**: 从 `InterpreterRef::call`
   (0x100045078) 出发, 跟进 `Vm::call_start` -> `Vm::call_run` ->
   `Interpreter::run` (0x100510158), 看 Pulley 的分发循环.

4. **考察 Cranelift**: 跳到那些体积庞大的 Cranelift 函数
   (`constructor_simplify` 位于 0x1003da46c), 理解 AOT
   编译流水线, 不过它们在运行时并不被用到.

5. **分析 Pulley 字节码**: 用 G-Pulley 的 cwasm 加载器再次导入
   宿主二进制 (选择 "Pulley cwasm" 格式). G-Pulley
   会提取内嵌的 cwasm 数据块, 反汇编所有 Pulley 操作码,
   并识别出客体函数, 包括 `Guest1::run()` 和
   `Guest2::run()`, 以及它们的字符串分配与格式化逻辑.
