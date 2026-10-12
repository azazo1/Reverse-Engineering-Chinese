## Part 17 - ADDS

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

ADDS 与 ADD 相同, 区别在于它会相应地在 CPSR 中设置标志位.

让我们看一个例子来说明:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520241718373.jpg"/></div>

我们 __add__ 把 __100__ 十进制加到 __r1__, 把 __4,294,967,295__ 加到 __r2__. 然后我们把 __add r1__ 与 __r2__ 相加, 并放入 __r0.__

我们看到 __adds __, 它会在 CPSR 中设置标志位. 我们必须记住, 在 GDB 中调试时, CPSR 的值是十六进制的. 要看清哪些标志位被设置, 我们必须把十六进制转换成二进制. 等我们在接下来的教程里开始调试和修改这个例子时, 你就会明白其中的道理.

你可以这样编译上面的代码:

<pre spellcheck="false">as -o adc.o adc.s
ld -o adc adc.o
</pre>

我们需要记住, CPSR 中的 bit 31, 20, 29 和 28 分别表示以下含义:

__bit 31 - N = 负标志位 (Negative Flag)__

__bit 30 - Z = 零标志位 (Zero Flag)__

__bit 29 - C = 进位标志位 (Carry Flag)__

__bit 28 - V = 溢出标志位 (Overflow Flag)__

因此, 如果 bit 31, 30, 29 和 28 (__NZCV__) 的二进制值是 __0110__, 那就意味着:

__负标志位未设置__

__零标志位已设置__

__进位标志位已设置__

__溢出标志位未设置 __

为了理解这里发生的一切, 你必须编译, 调试并修改每一个练习.

下周我们将深入调试 ADDS.