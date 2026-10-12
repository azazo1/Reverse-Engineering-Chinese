# Chapter 20: 构建系统

## 引言

我们的构建系统把人能读懂的汇编源文件, 变成 RP2350 可以执行的 UF2 固件镜像. 整个过程分三个阶段: 汇编, 链接, 转换. 本章逐条讲解 build.bat 和 clean.bat 里的每条命令, 说明每个工具做什么, 各个标志控制什么, 以及上一阶段的输出如何喂给下一阶段.

## 构建流水线

```
Source Files (.s)
      |
      v
  [arm-none-eabi-as]     Stage 1: Assemble
      |
      v
Object Files (.o)
      |
      v
  [arm-none-eabi-ld]     Stage 2: Link
      |
      v
  blink.elf
      |
      v
  [arm-none-eabi-objcopy] Stage 3: Extract binary
      |
      v
  blink.bin
      |
      v
  [python uf2conv.py]     Stage 4: Convert to UF2
      |
      v
  blink.uf2
```

## 阶段 1: 汇编

每个源文件独立汇编:

```bat
arm-none-eabi-as -g -mcpu=cortex-m33 -mthumb vector_table.s -o vector_table.o
arm-none-eabi-as -g -mcpu=cortex-m33 -mthumb reset_handler.s -o reset_handler.o
arm-none-eabi-as -g -mcpu=cortex-m33 -mthumb stack.s -o stack.o
arm-none-eabi-as -g -mcpu=cortex-m33 -mthumb xosc.s -o xosc.o
arm-none-eabi-as -g -mcpu=cortex-m33 -mthumb reset.s -o reset.o
arm-none-eabi-as -g -mcpu=cortex-m33 -mthumb coprocessor.s -o coprocessor.o
arm-none-eabi-as -g -mcpu=cortex-m33 -mthumb gpio.s -o gpio.o
arm-none-eabi-as -g -mcpu=cortex-m33 -mthumb delay.s -o delay.o
arm-none-eabi-as -g -mcpu=cortex-m33 -mthumb main.s -o main.o
arm-none-eabi-as -g -mcpu=cortex-m33 -mthumb image_def.s -o image_def.o
```

### 汇编器标志

| 标志 | 含义 |
|------|---------|
| `-g` | 生成调试信息 (DWARF) |
| `-mcpu=cortex-m33` | 目标处理器为 Cortex-M33 |
| `-mthumb` | 生成 Thumb 指令 |

每个 `.s` 文件都会产出一个对应的 `.o` (目标) 文件, 里面包含:

- 带有未解析重定位的机器码
- 一张符号表 (局部符号与全局符号)
- 各个段的头部 (.text, .data, .bss 等)
- 调试信息 (源码行号映射)

### 十个源文件

| 源文件 | 用途 |
|-------------|---------|
| vector_table.s | 向量表 (栈指针 + 复位向量) |
| reset_handler.s | 引导流程, 调用所有初始化函数 |
| stack.s | 栈指针初始化 |
| xosc.s | 晶振初始化与时钟使能 |
| reset.s | 外设复位释放 |
| coprocessor.s | CP0 (SIO) 访问使能 |
| gpio.s | GPIO pad 配置以及置位, 清除函数 |
| delay.s | 毫秒级延时函数 |
| main.s | 应用入口与闪烁循环 |
| image_def.s | PICOBIN 引导元数据 |

## 阶段 2: 链接

```bat
arm-none-eabi-ld -g -T linker.ld ^
  vector_table.o reset_handler.o stack.o xosc.o reset.o ^
  coprocessor.o gpio.o delay.o main.o image_def.o ^
  -o blink.elf
```

### 链接器标志

| 标志 | 含义 |
|------|---------|
| `-g` | 保留调试信息 |
| `-T linker.ld` | 使用我们的链接脚本决定内存布局 |
| `-o blink.elf` | 输出文件名 |

链接器做的事情是:

1. 读取全部十个目标文件
2. 合并同名的段 (所有 `.text` 段合成一个)
3. 按 linker.ld 分配绝对地址
4. 解析所有符号引用 (例如把 `bl GPIO_Set` 补上正确的偏移)
5. 产出一个 ELF (Executable and Linkable Format) 文件

### ELF 文件的内容

ELF 文件里包含:

- 位于最终地址上的全部机器码
- 描述内存布局的段头部
- 带已解析地址的符号表
- 把代码映射到源码行的调试信息

## 阶段 3: 提取二进制

```bat
arm-none-eabi-objcopy -O binary blink.elf blink.bin
```

`objcopy` 剥掉所有 ELF 元数据, 产出裸二进制 - 也就是从 `0x10000000` 开始原样写入 flash 的那些字节. 这个文件里没有头部, 没有符号表, 没有调试信息 - 只有机器码和数据.

## 阶段 4: 转成 UF2

```bat
python uf2conv.py -b 0x10000000 -f 0xe48bff59 -o blink.uf2 blink.bin
```

### UF2 标志

| 标志 | 含义 |
|------|---------|
| `-b 0x10000000` | 基地址 (flash 起始) |
| `-f 0xe48bff59` | RP2350 的 family ID |
| `-o blink.uf2` | 输出文件名 |

UF2 (USB Flashing Format) 把二进制包进一种 RP2350 的 USB 引导程序能读懂的格式. 每个 512 字节的 UF2 块里包含:

- 用于识别的魔数
- 该块数据的目标地址
- 最多 256 字节的载荷
- 防止把固件烧进错误芯片的 family ID

## 错误处理

build.bat 里的每条命令后面都跟着:

```bat
if errorlevel 1 goto error
```

只要任何阶段失败 (语法错误, 未定义符号, 文件缺失), 构建就立刻带着错误信息停下. 这样能避免连锁失败 - 否则后面的阶段会拿着损坏或缺失的输入继续干活.

## 烧录固件

build.bat 会打印出两种烧录方式的说明:

### UF2 (USB 大容量存储)

1. 按住 Pico 2 上的 BOOTSEL 按钮
2. 接上 USB 线
3. 把 blink.uf2 复制到 RP2350 盘符

### OpenOCD (调试探针)

```bat
openocd -f interface/cmsis-dap.cfg -f target/rp2350.cfg ^
  -c "adapter speed 5000" ^
  -c "program blink.elf verify reset exit"
```

它通过 CMSIS-DAP 调试探针直接烧写 ELF 文件, 校验内容, 复位芯片, 然后退出.

## 清理脚本

```bat
@echo off
echo Cleaning...
del *.o *.elf *.bin *.uf2 2>nul
echo Clean complete.
```

clean.bat 会删掉所有构建产物:

| 通配 | 删除的文件 |
|---------|---------------|
| `*.o` | 全部目标文件 |
| `*.elf` | 链接出来的 ELF 二进制 |
| `*.bin` | 裸二进制 |
| `*.uf2` | UF2 固件镜像 |

如果文件不存在, `2>nul` 会把错误信息压掉. 清理完之后, 只剩源文件.

## 小结

- 构建流水线分四个阶段: 汇编 → 链接 → 提取二进制 → 转成 UF2.
- `arm-none-eabi-as` 用 `-mcpu=cortex-m33 -mthumb` 把每个源文件汇编成目标文件.
- `arm-none-eabi-ld` 按 linker.ld 把所有目标文件链接成 blink.elf.
- `arm-none-eabi-objcopy` 把 ELF 剥成裸二进制.
- `uf2conv.py` 把二进制包装成带 RP2350 family ID 的 UF2 格式.
- 每个阶段之后的错误检查能防止连锁的构建失败.
- clean.bat 删掉所有生成的文件, 只留下源代码.
