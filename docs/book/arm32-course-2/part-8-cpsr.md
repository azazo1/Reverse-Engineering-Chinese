## Part 8 - CPSR

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

CPSR 寄存器存储关于程序的信息以及某次特定运算的结果. 这些寄存器里的某些位带有预先分配的条件, 用来测试某种情况是否发生, 它们就是标志位 (flags).

这个寄存器一共 32 位. 我们最关心的是最高的 4 位, 它们分别是:

第 31 位 - N = 负标志 (Negative Flag)

第 30 位 - Z = 零标志 (Zero Flag)

第 29 位 - C = 进位标志 (Carry Flag, 无符号运算)

第 28 位 - V = 溢出标志 (Overflow Flag, 有符号运算)

当指令执行完成时, 如果落入上述情形之一, CPSR 就会被更新. 只要其中某个条件发生, 对应的位就会被置为 1.

有两条指令会直接影响 CPSR 的标志位, 它们是 CMP 和 CMN. CMP 就是比较, 例如:

<pre spellcheck="false">CMP R1, R0 @ 记法上的减法, 即 R1 - R0, 若结果为 0, 第 30 位的 Z 就会被置为 1
</pre>

紧随其后最合逻辑的指令通常是 BEQ = branch if equal, 意思是零标志被置位, 于是分支到代码中的另一个标号.

关于 CMP, 如果两个操作数相等, 结果就是零. CMN 做同样的比较, 只是会把第二个操作数取负, 例如:

<pre spellcheck="false">CMN R1, R0 @ R1 - (-R0) 或 R1 + R0
</pre>

使用 SUB 指令时, 结果不会更新 CPSR, 你必须使用 SUBS 指令才能让标志位相应地更新.

下周我们会深入介绍更多关于链接寄存器 (Link Register) 的内容! 敬请关注!