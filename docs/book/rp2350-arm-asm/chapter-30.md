# Chapter 30: 完整集成 - 从源码到闪烁的 LED

## 引言

在 29 章里, 我们研究了构成这个闪烁驱动的每一个概念, 指令, 硬件模块和源文件. 这最后一章把所有东西合到一起: 我们构建固件, 连接硬件, 烧录芯片, 并确认 LED 在闪. 这就是从源代码到一个能工作的嵌入式系统的完整旅程.

## 第 1 步: 确认工具链

打开 PowerShell, 确认 ARM 工具链已经安装:

```powershell
arm-none-eabi-as --version
arm-none-eabi-ld --version
arm-none-eabi-objcopy --version
```

三条命令都必须报出版本信息. 如果有命令找不到, 请回看 README 里的安装 ARM 工具链一节.

## 第 2 步: 构建固件

在项目根目录下运行:

```powershell
.\build.bat
```

构建脚本会:

1. **汇编** 10 个源文件 → 10 个目标文件 (.o)
2. **链接** 所有目标文件 (使用 linker.ld) → blink.elf
3. **提取** 原始二进制 → blink.bin
4. **转换** 成 UF2 格式 → blink.uf2

构建成功时会打印:

```
Building...

=================================
SUCCESS! Created blink.uf2
=================================
```

如果有任何一步失败, 脚本会停下并给出错误信息, 指明是哪一阶段出的问题.

## 第 3 步: 检查构建产物

构建成功之后, 会出现这些文件:

| 文件 | 大小 (约) | 用途 |
|------|---------------|---------|
| `*.o` (10 个文件) | 每个约 1 KB | 中间目标文件 |
| `blink.elf` | 约 10 KB | 带调试信息的链接后二进制 |
| `blink.bin` | 约 1 KB | 原始二进制 (flash 内容) |
| `blink.uf2` | 约 2 KB | 用于 USB 烧录的 UF2 镜像 |

## 第 4 步: 连接硬件

### 需要的元件

| 元件 | 数量 |
|-----------|----------|
| Raspberry Pi Pico 2 (RP2350) | 1 |
| LED (任意颜色) | 1 |
| 330 Ω 电阻 | 1 |
| 面包板 | 1 |
| 杜邦线 | 2 |
| USB 线 (Micro-B 或 USB-C) | 1 |

### 接线图

```
Pico 2 Pin 21 (GPIO16) ---[330 Ω]---[LED anode (+)]
                                      [LED cathode (-)]--- Pico 2 Pin 23 (GND)
```

### 实物布局

```
+---------------------------+
|       Raspberry Pi        |
|         Pico 2            |
|                           |
|  Pin 21 (GPIO16) o--------+---[330Ω]---[>|]-----+
|                           |                     |
|  Pin 23 (GND)    o--------+---------------------+
|                           |
+---------------------------+
```

**LED 的方向很重要:** 阳极 (较长的引脚) 接电阻那一侧. 阴极 (较短的引脚, 透镜上的平面那一侧) 接地.

**电阻取值:** 330 Ω 把电流限制在 3.3V 下约 10 mA, 这对 LED 和 GPIO 引脚都是安全的. 220 Ω 到 1 kΩ 都能用 - 阻值越低, LED 越亮.

## 第 5 步: 烧录固件

### 方法 A: UF2 (USB 大容量存储)

1. 按住 Pico 2 上的 **BOOTSEL** 按钮
2. 把 USB 线接到电脑
3. 松开 BOOTSEL - 会出现一个名为 **RP2350** 的驱动器
4. 把 `blink.uf2` 复制到 RP2350 驱动器
5. 驱动器消失, 固件开始运行

### 方法 B: OpenOCD (调试探针)

如果你接好了 CMSIS-DAP 调试探针:

```powershell
openocd -f interface/cmsis-dap.cfg -f target/rp2350.cfg -c "adapter speed 5000" -c "program blink.elf verify reset exit"
```

这条命令会烧录 ELF 文件, 校验 flash 内容, 复位芯片, 然后退出.

### 方法 C: picotool

```powershell
picotool load blink.uf2 -f
```

这条命令加载 UF2 文件并强制重启.

## 第 6 步: 确认运行

烧录之后, LED 应该开始闪烁:

```
Time:  0s    0.5s   1.0s   1.5s   2.0s   2.5s
LED:   ON    OFF    ON     OFF    ON     OFF
       |-----|------|------|------|------|
       500ms  500ms  500ms  500ms  500ms
```

LED 亮 500 ms, 灭 500 ms, 如此无限重复. 闪烁频率是 1 Hz.

## 故障排查

| 现象 | 原因 | 解决 |
|---------|-------|-----|
| LED 不亮 | GPIO 引脚错了 | 检查接线是否接到 Pin 21 (GPIO16) |
| LED 一直亮着 | LED 接到了 3.3V 而不是 GPIO | 检查接线 |
| LED 很暗 | 电阻太大 | 换一个更小的阻值 (330Ω) |
| 构建在汇编阶段失败 | 语法错误 | 看错误信息里的文件名和行号 |
| 构建在链接阶段失败 | 未定义的符号 | 检查所有 `.global` 声明 |
| UF2 驱动器不出现 | 没有按住 BOOTSEL | 插 USB 之前先按住 BOOTSEL |
| 芯片不启动 | 缺少 PICOBIN 块 | 检查 image_def.s 和链接脚本 |

## 完整架构

```
+----------------------------------------------------------+
|                    Source Files                          |
|                                                          |
|  image_def.s   constants.s   vector_table.s   stack.s    |
|  reset_handler.s   xosc.s   reset.s   coprocessor.s      |
|  gpio.s   delay.s   main.s                               |
+----------------------------+-----------------------------+
                             |
                       [build.bat]
                             |
                        blink.uf2
                             |
                     [Flash to Pico 2]
                             |
              +-----------------------------+
              |         RP2350              |
              |                             |
              |  Boot ROM → PICOBIN check   |
              |         ↓                   |
              |  Reset_Handler              |
              |    Init_Stack               |
              |    Init_XOSC                |
              |    Enable_XOSC_Peri_Clock   |
              |    Init_Subsystem           |
              |    Enable_Coprocessor       |
              |         ↓                   |
              |  main                       |
              |    GPIO_Config(GPIO16)      |
              |    Loop:                    |
              |      GPIO_Set → Delay_MS    |
              |      GPIO_Clear → Delay_MS  |
              |      ↻                      |
              +-----------------------------+
                             |
                      GPIO16 Pin 21
                             |
                      [330Ω + LED]
                             |
                           GND
```

## 你学到了什么

在这 30 章里, 你从零开始建立起了理解:

- **第 1-6 章:** 计算机基础 - 二进制, 内存, 寄存器, 执行模型
- **第 7-12 章:** ARM Cortex-M33 指令集 - 传送, 算术, 逻辑, 内存, 分支, 调用
- **第 13-17 章:** 汇编编程 - 指示符, 符号, 段, 系统寄存器, 位操作
- **第 18 章:** RP2350 硬件 - XOSC, 时钟, 复位, GPIO, SIO 协处理器
- **第 19-20 章:** 构建系统 - 链接脚本与构建流水线
- **第 21-29 章:** 源码讲解 - 每个文件, 每个函数, 每条指令

现在你已经理解了一个能工作的裸机固件的每一个字节, 从 PICOBIN 引导块一直到最后那条让 LED 持续闪烁的 `b .Loop`.

## 小结

- 用 `.\build.bat` 构建, 产出 blink.uf2.
- 把 LED 和 330 Ω 电阻接在 GPIO16 (Pin 21) 与 GND (Pin 23) 之间.
- 通过 UF2 拖放, OpenOCD 或 picotool 烧录.
- LED 以 1 Hz 闪烁: 亮 500 ms, 灭 500 ms.
- 固件里的每条指令都在前面 29 章里讲解过了.
