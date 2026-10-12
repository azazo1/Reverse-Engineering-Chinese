## Part 22 - 修改 ADC

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

再回顾一次, ADC 和 ADD 一样, 区别在于如果进位标志被置位, 它会额外加 1. 使用 ADC 时, 我们要特别留意 CPSR, 也就是状态寄存器.

我们再来复习一下代码:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520144168134.jpg"/></div>

我们把十进制数 __100__ 加进 __r1__, 把 __4,294,967,295__ 加进 __r2__, 把十进制数 __100__ 加进 __r3__, 把十进制数 __100__ 加进 __r4__. 然后把 __r1__ 和 __r2__ 相加, 结果放进 __r0__, 再把 __r3__ 和 __r4__ 相加, 结果放进 __r5__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520170920932.jpg"/></div>

我们运行程序, 单步执行到把 __4,294,967,295__ 移进 __r2__ 的那一步. 我们来修改 __r2 __ 里的这个值, 把它改成 __100 十进制__.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520230872538.jpg"/></div>

再单步执行几次:

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520243287330.jpg"/></div>

好, 现在我们把 __100 十进制__ 和 __100 十进制__ 在 __r3__ 和 __r4__ 里相加, 结果在 __r5__ 里得到了 __200__ __十进制__! 还记得上周我们得到的是 __201__ 吗? 我们来看看下面的 CPSR.

再说一次, 要记住 CPSR 中的第 31, 20, 29 和 28 位表示以下含义:

__第 31 位 - N = 负标志 (Negative Flag)__

__第 30 位 - Z = 零标志 (Zero Flag)__

__第 29 位 - C = 进位标志 (Carry Flag)__

__第 28 位 - V = 溢出标志 (Overflow Flag)__

我们看到 __CPSR__ 的值是 __10 十六进制__. __10 十六进制__ 的最高几位用二进制表示是 __0001__.

因此, 如果第 31, 30, 29 和 28 位 (__NZCV__) 的二进制值是 __0001__, 那意味着:

__负标志未置位__

__零标志未置位__

__进位标志未置位__

__溢出标志已置位__

可以清楚地看到, 进位标志没有被置位. 希望你能消化并理解这些非常简单的操作, 以及它们如何影响 CPSR. 请花点时间复习一下上周那一节 Lesson, 做个对比.

下周我们深入 SUB.