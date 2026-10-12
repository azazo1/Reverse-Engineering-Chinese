## Part 20 - ADC

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

ADC 和 ADD 一样, 区别在于如果进位标志被置位, 它会额外加 1. 使用 ADC 时, 我们要特别留意 CPSR, 也就是状态寄存器.

看一个例子来说明:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520238027219.jpg"/></div>

我们把十进制数 __100__ 加进 __r1__, 把 __4,294,967,295__ 加进 __r2__, 把十进制数 __100__ 加进 __r3__, 把十进制数 __100__ 加进 __r4__. 然后把 __r1__ 和 __r2__ 相加, 结果放进 __r0__, 再把 __r3__ 和 __r4__ 相加, 结果放进 __r5__.

我们看到 __adds __, 它会设置 CPSR 里的各个标志. 再说一次, 要记住在 GDB 里调试时, CPSR 的值是十六进制的. 要想看清哪些标志被设置了, 我们必须把这个十六进制值转成二进制. 等我们在接下来的教程里开始调试和修改这个例子, 你就会明白.

可以这样编译上面的代码:

<pre spellcheck="false">as -o adc.o adc.s
ld -o adc adc.o
</pre>

请你自问一下: 当 __r3(十进制 100)__ 加到 __r4(十进制 100)__ 上时会发生什么? 在上面这个用 adds 结果设置标志的例子中, 你觉得 __r5__ 的值会是多少? 想想本教程的第一句话, 并为下一节教程记住这一点.

下周我们深入调试 ADC.