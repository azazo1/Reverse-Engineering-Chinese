# Chapter 7: RISC-V Hazard3 ISA 概览

## 引言

指令集架构 (ISA) 定义了处理器能做的每一种操作. RP2350 里的 Hazard3 内核实现的是 **RV32IMAC_Zicsr** 架构 - 一个 32 位 RISC-V 基础整数 ISA, 再补上整数乘除, 原子操作, 压缩指令以及控制和状态寄存器访问. 本章从高处纵览这个 ISA, 并列出我们闪烁驱动用到的每一条指令.

## RISC-V 的设计哲学

RISC-V 遵循一套格外干净的 RISC (精简指令集计算机) 哲学:

- **定宽指令** - 基础指令永远是 32 位 (4 字节)
- **加载-存储架构** - 只有 `lw`/`sw` 系列指令访问内存
- **大寄存器组** - 32 个通用整数寄存器 (x0-x31)
- **简单的寻址方式** - 基址寄存器加 12 位有符号立即数
- **没有条件标志位** - 分支直接比较寄存器
- **模块化扩展** - 功能通过字母命名的扩展加入 (M, A, C, Zicsr)

## RV32IMAC_Zicsr 扩展

Hazard3 内核支持以下扩展:

| 扩展 | 名称 | 用途 |
|-----------|------|---------|
| I | 基础整数 | 核心指令集: 算术, 逻辑, 加载, 存储, 分支 |
| M | 乘除 | `mul`, `div`, `rem` 及其变体 |
| A | 原子 | 原子内存操作 (我们的固件未使用) |
| C | 压缩 | 常见指令的 16 位编码 |
| Zicsr | CSR 访问 | 用于控制和状态寄存器的 `csrr`, `csrw`, `csrrw` |

## 指令编码格式

RV32I 定义了六种基础指令格式. 每条 32 位指令都使用其中一种:

| 格式 | 字段 | 用于 |
|--------|--------|----------|
| R-type | funct7, rs2, rs1, funct3, rd, opcode | 寄存器-寄存器运算: `add`, `sub`, `and`, `or`, `sll`, `mul` |
| I-type | imm[11:0], rs1, funct3, rd, opcode | 立即数和加载: `addi`, `ori`, `andi`, `lw`, `jalr` |
| S-type | imm[11:5], rs2, rs1, funct3, imm[4:0], opcode | 存储: `sw` |
| B-type | imm[12\|10:5], rs2, rs1, funct3, imm[4:1\|11], opcode | 分支: `beq`, `bne`, `bge`, `blt` |
| U-type | imm[31:12], rd, opcode | 高位立即数: `lui`, `auipc` |
| J-type | imm[20\|10:1\|11\|19:12], rd, opcode | 跳转: `jal` |

```
R-type:  [funct7 ][rs2  ][rs1  ][f3 ][rd   ][opcode ]
         31    25 24  20 19  15 14 12 11   7 6      0

I-type:  [imm[11:0]      ][rs1  ][f3 ][rd   ][opcode ]
         31            20 19  15 14 12 11   7 6      0

S-type:  [imm[11:5]  ][rs2  ][rs1  ][f3 ][imm[4:0] ][opcode ]
         31        25 24  20 19  15 14 12 11       7 6      0
```

## C 扩展 (压缩指令)

C 扩展为最常见的操作提供了 16 位 (2 字节) 编码. 只要可能, 汇编器会自动选用压缩编码:

| 32 位指令 | 16 位等价形式 | 条件 |
|--------------------|--------------------|-----------|
| `addi rd, rd, imm` | `c.addi rd, imm` | imm 能用 6 位表示 |
| `lw rd, off(rs1)` | `c.lw rd, off(rs1)` | 寄存器在 x8-x15 内, 偏移对齐 |
| `sw rs2, off(rs1)` | `c.sw rs2, off(rs1)` | 寄存器在 x8-x15 内, 偏移对齐 |
| `jal x1, offset` | `c.jal offset` | 偏移能用 12 位表示 (仅 RV32) |
| `jalr x0, 0(x1)` | `c.jr x1` | 总是 |
| `add rd, x0, rs2` | `c.mv rd, rs2` | 总是 |
| `addi x2, x2, imm` | `c.addi16sp imm` | 栈指针调整 |

压缩指令提高了代码密度 - 同样的逻辑占用更少的 flash. 程序员照常写标准指令, 汇编器在背后透明地压缩它们.

## 固件中用到的指令

下面是闪烁驱动里出现的完整指令清单:

| 指令 | 格式 | 说明 |
|-------------|--------|-------------|
| `li rd, imm` | 伪指令 | 加载立即数 (展开为 `lui`+`addi`, 或只用 `addi`) |
| `la rd, symbol` | 伪指令 | 加载地址 (展开为 `auipc`+`addi`) |
| `lw rd, off(rs1)` | I-type | 从内存加载字 |
| `sw rs2, off(rs1)` | S-type | 把字存储到内存 |
| `add rd, rs1, rs2` | R-type | 两个寄存器相加 |
| `addi rd, rs1, imm` | I-type | 寄存器加立即数 |
| `mul rd, rs1, rs2` | R-type (M) | 两个寄存器相乘 |
| `and rd, rs1, rs2` | R-type | 按位与 |
| `andi rd, rs1, imm` | I-type | 与立即数按位与 |
| `or rd, rs1, rs2` | R-type | 按位或 |
| `ori rd, rs1, imm` | I-type | 与立即数按位或 |
| `not rd, rs1` | 伪指令 | 按位取反 (展开为 `xori rd, rs1, -1`) |
| `sll rd, rs1, rs2` | R-type | 逻辑左移 |
| `beqz rs1, label` | 伪指令 | 等于零则跳转 (展开为 `beq rs1, x0, label`) |
| `bnez rs1, label` | 伪指令 | 不等于零则跳转 (展开为 `bne rs1, x0, label`) |
| `bgez rs1, label` | 伪指令 | 大于等于零则跳转 (展开为 `bge rs1, x0, label`) |
| `blez rs1, label` | 伪指令 | 小于等于零则跳转 (展开为 `ble rs1, x0, label`) |
| `j label` | 伪指令 | 无条件跳转 (展开为 `jal x0, label`) |
| `jal rd, label` | J-type | 跳转并链接 |
| `jalr rd, off(rs1)` | I-type | 跳转并链接到寄存器 |
| `call label` | 伪指令 | 调用函数 (展开为 `auipc ra, ...` + `jalr ra, ...`) |
| `ret` | 伪指令 | 返回 (展开为 `jalr x0, 0(x1)`) |
| `csrw csr, rs1` | 伪指令 | 写 CSR (展开为 `csrrw x0, csr, rs1`) |

## 小结

- Hazard3 内核实现 RV32IMAC_Zicsr: 基础整数, 乘法, 原子操作, 压缩指令和 CSR 访问.
- 所有基础指令都是 32 位, 共有六种编码格式 (R, I, S, B, U, J).
- C 扩展为常见指令自动提供 16 位压缩形式.
- 我们的闪烁驱动大约用了 22 条不同的指令 (含伪指令), 就在裸机上实现了完整的 GPIO 控制.
