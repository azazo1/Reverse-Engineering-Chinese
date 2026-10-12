# Chapter 20: 构建流水线 - 从汇编到可烧录二进制

## 引言

我们的构建系统把人类可读的汇编源文件, 变成 RP2350 能执行的 UF2 固件镜像. 整个过程分四个阶段: 汇编, 链接, 提取二进制, 转换成 UF2. 本章逐条讲解 build.bat 和 clean.bat 里的每一条命令, 说明每个工具做什么, 各个参数控制什么, 以及上一阶段的输出是怎样喂给下一阶段的.

## 构建流水线

```
Source Files (.s)
      |
      v
  [riscv32-unknown-elf-as]    Stage 1: Assemble
      |
      v
Object Files (.o)
      |
      v
  [riscv32-unknown-elf-ld]    Stage 2: Link
      |
      v
  blink.elf
      |
      v
  [riscv32-unknown-elf-objcopy] Stage 3: Extract binary
      |
      v
  blink.bin
      |
      v
  [python uf2conv.py]          Stage 4: Convert to UF2
      |
      v
  blink.uf2
```

## 工具链自动检测

build.bat 一上来先找 RISC-V 工具链:

```bat
set TOOLCHAIN_PREFIX=riscv32-unknown-elf
```

然后按顺序搜索:
1. 系统 PATH
2. `%RISCV_TOOLCHAIN_BIN%` 环境变量
3. `%USERPROFILE%\OneDrive\Documents\riscv-toolchain-14\bin`
4. `%USERPROFILE%\Documents\riscv-toolchain-14\bin`

如果找不到任何工具链, 构建就会失败, 并提示应该把工具链装在哪里.

## 阶段 1: 汇编

每个源文件都单独汇编:

```bat
riscv32-unknown-elf-as -g -march=rv32imac_zicsr -mabi=ilp32 vector_table.s -o vector_table.o
riscv32-unknown-elf-as -g -march=rv32imac_zicsr -mabi=ilp32 reset_handler.s -o reset_handler.o
riscv32-unknown-elf-as -g -march=rv32imac_zicsr -mabi=ilp32 stack.s -o stack.o
riscv32-unknown-elf-as -g -march=rv32imac_zicsr -mabi=ilp32 xosc.s -o xosc.o
riscv32-unknown-elf-as -g -march=rv32imac_zicsr -mabi=ilp32 reset.s -o reset.o
riscv32-unknown-elf-as -g -march=rv32imac_zicsr -mabi=ilp32 coprocessor.s -o coprocessor.o
riscv32-unknown-elf-as -g -march=rv32imac_zicsr -mabi=ilp32 gpio.s -o gpio.o
riscv32-unknown-elf-as -g -march=rv32imac_zicsr -mabi=ilp32 delay.s -o delay.o
riscv32-unknown-elf-as -g -march=rv32imac_zicsr -mabi=ilp32 main.s -o main.o
riscv32-unknown-elf-as -g -march=rv32imac_zicsr -mabi=ilp32 image_def.s -o image_def.o
```

### 汇编器参数

| 参数 | 含义 |
|------|---------|
| `-g` | 生成调试信息 (DWARF) |
| `-march=rv32imac_zicsr` | 目标为 RV32I + M + A + C + Zicsr 扩展 |
| `-mabi=ilp32` | 使用 ILP32 ABI (int, long, 指针都是 32 位) |

每个 `.s` 文件都产出一个对应的 `.o` (目标) 文件, 里面装着:

- 机器码, 以及尚未解析的重定位信息
- 符号表 (局部符号和全局符号)
- 段头 (.text, .data, .bss 等)
- 调试信息 (源码行号映射)

### 汇编器参数细节

**`-march=rv32imac_zicsr`** 指定了确切的指令集:

| 组成部分 | 含义 |
|-----------|---------|
| `rv32i` | 基础 32 位整数指令 |
| `m` | 乘除法 (mul, div, rem) |
| `a` | 原子操作 |
| `c` | 压缩 (16 位) 指令 |
| `_zicsr` | CSR 读写指令 |

**`-mabi=ilp32`** 指定了调用约定:

| ABI | int | long | 指针 |
|-----|-----|------|---------|
| ilp32 | 32 位 | 32 位 | 32 位 |

### 十个源文件

| 源文件 | 作用 |
|-------------|---------|
| vector_table.s | 向量表 (处理程序地址的占位) |
| reset_handler.s | 启动流程, 调用所有初始化函数 |
| stack.s | 栈指针初始化 |
| xosc.s | 晶振初始化与时钟使能 |
| reset.s | 释放外设复位 |
| coprocessor.s | 空操作的兼容桩 |
| gpio.s | GPIO pad 配置, 以及通过 SIO 置位/清零 |
| delay.s | 毫秒级延时函数 |
| main.s | 应用入口点与闪烁循环 |
| image_def.s | PICOBIN 启动元数据 (RISC-V) |

## 阶段 2: 链接

```bat
riscv32-unknown-elf-ld -g -T linker.ld ^
  vector_table.o reset_handler.o stack.o xosc.o reset.o ^
  coprocessor.o gpio.o delay.o main.o image_def.o ^
  -o blink.elf
```

### 链接器参数

| 参数 | 含义 |
|------|---------|
| `-g` | 保留调试信息 |
| `-T linker.ld` | 用我们的链接脚本来决定内存布局 |
| `-o blink.elf` | 输出文件名 |

链接器会:

1. 读取全部十个目标文件
2. 合并同名的段 (所有 `.text` 段合并成一个)
3. 按 linker.ld 分配绝对地址
4. 解析所有符号引用 (比如 `call GPIO_Set` 会被回填成正确的偏移)
5. 生成一个 ELF (Executable and Linkable Format) 文件

### ELF 文件的内容

ELF 文件里装着:

- 已经定位到最终地址的全部机器码
- 描述内存布局的段头
- 地址已解析完毕的符号表
- 把代码映射到源码行的调试信息

调试器 (GDB + OpenOCD) 就用这个 ELF 来做源码级调试.

## 阶段 3: 提取二进制

```bat
riscv32-unknown-elf-objcopy -O binary blink.elf blink.bin
```

`objcopy` 剥掉所有 ELF 元数据, 产出一个裸二进制 - 就是从 `0x10000000` 开始要写进 flash 的那些字节, 一个不多一个不少. 这个文件里没有文件头, 没有符号表, 也没有调试信息 - 只有机器码和数据.

## 阶段 4: 转换成 UF2

```bat
python uf2conv.py -b 0x10000000 -f 0xe48bff5a -o blink.uf2 blink.bin
```

### UF2 参数

| 参数 | 含义 |
|------|---------|
| `-b 0x10000000` | 基地址 (flash 起始处) |
| `-f 0xe48bff5a` | RP2350 RISC-V 的 family ID |
| `-o blink.uf2` | 输出文件名 |

UF2 (USB Flashing Format) 把二进制包进一种 RP2350 的 USB 引导程序能识别的格式. 每个 512 字节的 UF2 块里装着:

- 用于识别的魔数
- 该块数据的目标地址
- 最多 256 字节的有效载荷
- family ID, 用来防止把固件烧进错误的芯片

### Family ID

family ID `0xe48bff5a` 表明目标是 RP2350 RISC-V. ARM 的 family ID 是 `0xe48bff59` (只差一位). 如果你把 RISC-V 的 UF2 烧到配置成 ARM 的引导程序上, 或者反过来, 引导程序都会拒绝.

## 错误处理

build.bat 里每条命令后面都跟着:

```bat
if errorlevel 1 goto error
```

只要有一个阶段失败 (语法错误, 未定义符号, 文件缺失), 构建就立刻停下并报错. 这样可以避免连锁失败 - 否则后面的阶段会拿着已经损坏或根本不存在的输入继续干活.

## 烧录固件

build.bat 会打印两种烧录方法的说明:

### UF2 (USB 大容量存储)

1. 按住 Pico 2 上的 BOOTSEL 按钮
2. 插上 USB 线
3. 把 blink.uf2 复制到 RP2350 那个盘里

RP2350 会以 USB 大容量存储设备的身份出现. 复制 UF2 文件就会触发引导程序, 把固件写进 flash 并复位.

### OpenOCD (调试探针)

```bat
openocd -f interface/cmsis-dap.cfg -f target/rp2350.cfg ^
  -c "adapter speed 5000" ^
  -c "program blink.elf verify reset exit"
```

这里用的是调试探针 (Raspberry Pi Debug Probe 或兼容的 CMSIS-DAP 适配器), 它做的事是:
1. 通过 SWD 连上 RP2350
2. 把 ELF 文件烧进 flash
3. 校验写入的数据
4. 复位芯片, 开始执行

## 清理脚本

```bat
del *.o *.elf *.bin *.uf2 2>nul
```

clean.bat 删掉所有构建产物, 把目录恢复到只有源码的状态. `2>nul` 用来在文件本来就不存在时压掉报错.

## 与 ARM 构建对照

| 方面 | ARM | RISC-V |
|--------|-----|--------|
| 汇编器 | `arm-none-eabi-as` | `riscv32-unknown-elf-as` |
| CPU 参数 | `-mcpu=cortex-m33 -mthumb` | `-march=rv32imac_zicsr -mabi=ilp32` |
| 链接器 | `arm-none-eabi-ld` | `riscv32-unknown-elf-ld` |
| Objcopy | `arm-none-eabi-objcopy` | `riscv32-unknown-elf-objcopy` |
| Family ID | `0xe48bff59` | `0xe48bff5a` |
| 输出名 | `blink.elf` / `blink.uf2` | `blink.elf` / `blink.uf2` |

流水线的结构完全一样 - 只是工具前缀, 架构参数和 family ID 不同.

## 小结

- 构建流水线分四个阶段: 汇编 → 链接 → 提取二进制 → 转换成 UF2.
- `-march=rv32imac_zicsr -mabi=ilp32` 让汇编器针对我们这颗 RISC-V 内核工作.
- 链接器按 linker.ld 把十个目标文件合并成 blink.elf.
- `objcopy` 剥掉 ELF 元数据, 产出裸二进制.
- `uf2conv.py` 用 RISC-V 的 family ID `0xe48bff5a` 把二进制包装起来.
- 错误处理让构建在任何一个环节失败时立刻停下.
- 固件可以通过 UF2 (USB) 或 OpenOCD (调试探针) 烧录.
