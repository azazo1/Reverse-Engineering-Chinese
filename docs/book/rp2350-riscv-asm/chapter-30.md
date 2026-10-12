# Chapter 30: 完整集成 - 构建, 烧录, 接线与测试

## 简介

每一块拼图都到位了. 十个汇编源文件, 一个链接脚本和一个构建脚本合在一起, 产出一个能让 RP2350 上的 LED 闪烁的固件镜像. 这最后一章把一切串起来: 我们从通电一路追到 LED 闪烁的完整执行路径, 构建固件, 连接硬件, 烧录芯片, 并验证它确实能工作.

## 完整的源码树

```
RP2350_Blink_Driver_RISCV/
├── constants.s          Ch 22  - All memory-mapped addresses
├── image_def.s          Ch 21  - PICOBIN boot metadata (RISC-V)
├── vector_table.s       Ch 23  - Vector table section
├── stack.s              Ch 23  - Stack pointer initialization
├── reset_handler.s      Ch 24  - Boot sequence orchestrator
├── xosc.s               Ch 25  - Crystal oscillator init + clock enable
├── reset.s              Ch 26  - Peripheral reset release
├── gpio.s               Ch 27-28 - GPIO config, set, clear (SIO)
├── delay.s              Ch 28  - Millisecond delay loop
├── coprocessor.s        Ch 28  - No-op compatibility stub
├── main.s               Ch 29  - Application entry, blink loop
├── linker.ld            Ch 19  - Memory layout and section placement
├── build.bat            Ch 20  - Build pipeline script
├── clean.bat            Ch 20  - Build artifact cleanup
├── uf2conv.py                  - UF2 conversion utility
└── uf2families.json            - UF2 family ID database
```

## 完整的执行路径

### 阶段 1: Boot ROM

```
Power-on / Reset
  │
  └── RP2350 boot ROM starts
        ├── Scans first 4 KB of flash
        ├── Finds PICOBIN_BLOCK_MARKER_START (0xffffded3)
        ├── Reads image type: 0x1101 → RISC-V + RP2350 + EXE
        ├── Reads entry point: Reset_Handler address
        ├── Reads stack: STACK_TOP (0x20082000)
        ├── Sets sp = 0x20082000
        └── Sets pc = Reset_Handler
```

### 阶段 2: 硬件初始化

```
Reset_Handler (reset_handler.s)
  │
  ├── call Init_Stack (stack.s)
  │     └── li sp, 0x20082000
  │
  ├── call Init_Trap_Vector (reset_handler.s)
  │     ├── la t0, Default_Trap_Handler
  │     └── csrw mtvec, t0
  │
  ├── call Init_XOSC (xosc.s)
  │     ├── XOSC_STARTUP = 0x00c4
  │     ├── XOSC_CTRL = 0x00FABAA0 (enable, 1-15MHz)
  │     └── Poll XOSC_STATUS bit31 via bgez
  │
  ├── call Enable_XOSC_Peri_Clock (xosc.s)
  │     ├── Set ENABLE bit (bit 11)
  │     └── Set AUXSRC = XOSC (bit 7)
  │
  ├── call Init_Subsystem (reset.s)
  │     ├── Clear IO_BANK0 reset (bit 6)
  │     └── Poll RESETS_RESET_DONE bit 6
  │
  ├── call Enable_Coprocessor (coprocessor.s)
  │     └── ret (no-op on RISC-V)
  │
  └── j main
```

### 阶段 3: 应用程序

```
main (main.s)
  │
  ├── GPIO16_Config:
  │     └── call GPIO_Config(0x44, 0x84, 16)
  │           ├── PADS: clear OD, set IE, clear ISO
  │           ├── CTRL: FUNCSEL = 5 (SIO)
  │           └── SIO_GPIO_OE_SET: bit 16
  │
  └── .Loop (infinite):
        ├── GPIO_Set(16)   → SIO_GPIO_OUT_SET bit 16 → LED ON
        ├── Delay_MS(500)  → 1,800,000 loop iterations
        ├── GPIO_Clear(16) → SIO_GPIO_OUT_CLR bit 16 → LED OFF
        ├── Delay_MS(500)  → 1,800,000 loop iterations
        └── j .Loop
```

## 链接之后的内存映射

```
Flash (0x10000000):
  0x10000000  IMAGE_DEF block (image_def.s)
  0x10000080  Vector table (vector_table.s, 128-byte aligned)
  0x10000088+ .text (all functions merged)
              - Reset_Handler, Default_Trap_Handler, Init_Trap_Vector
              - Init_Stack
              - Init_XOSC, Enable_XOSC_Peri_Clock
              - Init_Subsystem
              - Enable_Coprocessor
              - GPIO_Config, GPIO_Set, GPIO_Clear
              - Delay_MS
              - main

RAM (0x20000000):
  0x2007a000  Stack limit (bottom of 32 KB stack)
  0x20082000  Stack top (sp starts here, grows down)
```

## 硬件接线

### 需要的元件

| 元件 | 规格 |
|-----------|---------------|
| Raspberry Pi Pico 2 | 基于 RP2350 的板子 |
| LED | 标准 3mm 或 5mm, 任意颜色 |
| 电阻 | 330Ω (或 220Ω - 1kΩ) |
| 面包板 | 标准尺寸 |
| 跳线 | 公对公 |

### 接线图

```
Pico 2 GPIO16 (Pin 21) ──── Resistor (330Ω) ──── LED (+) ──── LED (-) ──── GND (Pin 23)
```

### 引脚参考

| Pico 2 引脚 | 功能 | 连接 |
|------------|----------|------------|
| Pin 21 | GPIO16 | 电阻 → LED 阳极 |
| Pin 23 | GND | LED 阴极 |

电阻把电流限制在约 `(3.3V - 2V) / 330Ω ≈ 4 mA`, 稳稳地在 LED 和 GPIO 的额定范围内. LED 较长的那条腿是阳极 (+), 较短的是阴极 (-).

## 构建固件

### 前置条件

1. **RISC-V 工具链**: 从 [pico-sdk-tools](https://github.com/raspberrypi/pico-sdk-tools/releases) 下载 - 选 `riscv-toolchain-14-*-x86_64-w64-mingw32.zip`
2. **Python**: `uf2conv.py` 需要它
3. 把工具链解压到 `%USERPROFILE%\Documents\riscv-toolchain-14\`

### 构建

在项目目录里打开终端并运行:

```
build.bat
```

构建会产出:

| 文件 | 用途 |
|------|---------|
| `*.o` | 目标文件 (每个源文件一个) |
| `blink.elf` | 带调试信息的已链接可执行文件 |
| `blink.bin` | 用于烧录的原始二进制 |
| `blink.uf2` | 可烧录的固件镜像 |

### 清理

```
clean.bat
```

删除所有构建产物 (`.o`, `.elf`, `.bin`, `.uf2`).

## 烧录固件

### 方法 1: UF2 (USB 大容量存储)

1. 按住 Pico 2 上的 **BOOTSEL** 按钮
2. 在按住 BOOTSEL 的同时插上 USB 线
3. 松开 BOOTSEL - Pico 2 会以一个 USB 驱动器的形式出现
4. 把 `blink.uf2` 复制到这个驱动器里
5. Pico 2 会自动复位并开始闪烁

### 方法 2: OpenOCD (调试探针)

```
openocd -f interface/cmsis-dap.cfg -f target/rp2350.cfg ^
  -c "adapter speed 5000" ^
  -c "program blink.elf verify reset exit"
```

这需要一个通过 SWD 连接的 CMSIS-DAP 兼容调试探针.

### 方法 3: Picotool

```
picotool load blink.uf2 -f
```

Picotool 通过 USB 和 Pico 2 通信, 不需要进入 BOOTSEL 模式.

## 验证

烧录之后, 接在 GPIO16 上的 LED 应该开始闪烁:

- **亮** 500 ms
- **灭** 500 ms
- **重复**, 永不停歇

如果 LED 不闪:

| 现象 | 可能原因 | 解决办法 |
|---------|---------------|-----|
| 不闪, LED 全黑 | GPIO 引脚错了 | 检查接线: GPIO16 是 Pin 21 |
| 不闪, LED 全黑 | LED 装反了 | 把 LED 掉个方向 |
| 不闪, LED 很暗 | 忘接电阻 | 加上 330Ω 电阻 |
| 不闪, LED 长亮 | 固件不对 | 重新构建并重新烧录 |
| 引导程序不出现 | 板子没进 BOOTSEL | 插 USB 之前先按住 BOOTSEL |

## 硬件寄存器访问汇总

| 外设 | 基地址 | 访问方式 | 功能 |
|-----------|-------------|---------------|----------|
| XOSC | `0x40048000` | APB (读/改/写) | 晶体振荡器 |
| Clocks | `0x40010000` | APB (读/改/写) | 时钟路由 |
| Resets | `0x40020000` | APB (读/改/写) | 外设复位控制 |
| IO Bank 0 | `0x40028000` | APB (读/改/写) | GPIO 功能选择 |
| Pads Bank 0 | `0x40038000` | APB (读/改/写) | GPIO pad 配置 |
| SIO | `0xd0000000` | 内存映射 (原子) | GPIO 输出 + 使能 |

## 指令盘点

整个闪烁驱动只用到 RV32IMAC 指令集里很小的一部分:

| 类别 | 用到的指令 |
|----------|------------------|
| 加载/存储 | `li`, `la`, `lw`, `sw` |
| 算术 | `add`, `addi`, `mul` |
| 逻辑 | `and`, `andi`, `or`, `ori`, `not` |
| 移位 | `sll` |
| 分支 | `beqz`, `bnez`, `bgez`, `blez` |
| 跳转 | `j`, `call`, `ret` |
| 系统 | `csrw` |

一共 19 条指令 (含伪指令), 就驱动起了真实的硬件.

## 你造出了什么

从最基本的原理出发 - 计算机是什么, 数字如何表示, 寄存器做什么用 - 你已经造出了一个完整的裸机 RISC-V 固件, 它会:

1. 从 RP2350 的 PICOBIN 元数据启动
2. 初始化晶体振荡器以获得稳定的时钟
3. 把 GPIO 硬件从复位中释放出来
4. 把一个引脚配置成由 SIO 驱动的输出
5. 在死循环里翻转这个引脚, 让 LED 闪烁

固件里每一个字节都有出处. 没有操作系统, 没有运行时库, 没有藏起来的代码. 每一条指令都是你写的, 你也知道每一条在做什么.

## 小结

- 完整的闪烁驱动由 10 个汇编文件, 一个链接脚本和一个构建脚本组成.
- 启动流程是: IMAGE_DEF → Reset_Handler → Init_Stack → Init_Trap_Vector → Init_XOSC → Enable_XOSC_Peri_Clock → Init_Subsystem → Enable_Coprocessor → main.
- GPIO16 是通过三块硬件配置的: PADS_BANK0, IO_BANK0 和 SIO.
- 闪烁循环把 GPIO_Set, Delay_MS, GPIO_Clear, Delay_MS 串成一个死循环.
- 固件用 `build.bat` 构建, 通过 UF2, OpenOCD 或 picotool 烧录.
- 1 Hz 的 LED 闪烁确认了每一个部件 - 从元数据到主循环 - 都工作正常.
