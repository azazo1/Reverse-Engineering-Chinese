## Part 37 - ASM 程序 6 \[CMOV 指令\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

在我们的第六个程序里, 我们会演示如何使用 CMOV 指令.

在我们深入代码之前, 先说说 CMOV 是什么. CMOV 可以让处理器不必使用 JMP 指令, 从而加快相应二进制文件的运行速度.

无符号的 CMOV 指令有:

CMOVA 或 CMOVNBE = Above \[进位标志位或零标志位 = 0\]

CMOVAE 或 CMOVNB = Above Or Equal \[进位标志位 = 0\]

CMOVNC = Not Carry \[进位标志位 = 0\]

CMOVB 或 CMOVNAE = Below \[进位标志位 = 1\]

CMOVC = Carry \[进位标志位 = 1\]

CMOVBE 或 CMOVNA = Below Or Equal \[进位标志位或零标志位 = 1\]

CMOVE 或 CMOVZ = Equal \[零标志位 = 1\]

CMOVNE 或 CMOVNZ = Not Equal \[零标志位 = 0\]

CMOVP 或 CMOVPE = Parity \[奇偶标志位 = 1\]

CMOVNP 或 CMOVPO = Not Parity \[奇偶标志位 = 0\]

还有带符号的 CMOV 指令:

CMOVGE 或 CMOVNL = Greater Or Equal \[符号标志位 xor 溢出标志位 = 0\]

CMOVL 或 CMOVNGE = Less \[符号标志位 xor 溢出标志位 = 1\]

CMOVLE 或 CMOVNG = Less Or Equal \[符号标志位 xor 溢出标志位或 ZF = 1\]

CMOVO = Overflow \[溢出标志位 = 1\]

CMOVNO = Not Overflow \[溢出标志位 = 0\]

CMOVS = Sign NEGATIVE \[符号标志位 = 1\]

CMOVNS = Not Sign POSITIVE \[符号标志位 = 0\]

记住要去回顾无符号运算与带符号运算之间的关系. 无符号指令使用 CF, ZF 和 PF 来判断两个操作数之间的差异, 而带符号指令使用 SF 和 OF 来指示操作数之间比较的结果.

如果你需要复习标志位, 请回顾本系列中关于标志位的 Part 14.

CMOV 指令依赖一条会设置 EFLAGS 寄存器的数学指令来工作, 因此让程序员不必在比较语句之后使用 JMP 语句. 让我们来看一些源代码.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520240921769.jpg"/></div>

好, 我们从第 21 行和第 22 行开始. 这里没有什么新东西, 因为我们只是把数组移入 ebx.

在第 24 行我们看到 find\_smallest\_value 函数, 我们在那里遍历数组, 并使用 CMOVB 最终找出最小的值.

我们看到 __cmp %ebx, %eax__, 其中 cmp 用第二个操作数减去第一个操作数, 并相应地设置 EFLAGS 寄存器. 此时, 如果这个值比 ebx 寄存器里原来的值更小, 就用 cmovb 把 ebx 中的值替换成 eax 中的值.

退出循环之后, 我们看到三组 sys\_writes, 第一组显示我们的消息, 第二组显示转换后的整数 ascii 值, 最后显示一个句点和换行.

记住, 汇编时我们输入:

__as -32 -o cmov\_instructions.o cmov\_instructions.s__

要链接目标文件, 我们输入:

__ld -m elf\_i386 -o cmov\_instructions cmov\_instructions.o __

期待下周与大家再见, 届时我们会深入调试我们的第六个汇编程序!