## Part 29 - 浮点变量

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

我们旅程的下一站是浮点变量.&nbsp;

浮点变量与整数不同, 它带有一个小数部分, 我们用小数点来标示.

让我们看看我们的代码.

<pre spellcheck="false">#include &lt;iostream&gt;

&nbsp;

float main(void) {

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; int myNumber = 1337.1;

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; std::cout &lt;&lt; myNumber &lt;&lt; std::endl;

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; return 0;

}
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520592872663.jpg"/></div>

要编译它, 我们只需输入:

g++ example6.cpp -o example6

./example6

成功!&nbsp;我们看到 1337.1 被打印到标准输出也就是终端上!

让我们拆解一下:

我们把浮点变量__ __直接赋给变量 __myNumber__, 然后用 c++ 的 __cout__ 函数把它打印到终端.

到目前为止, 我们对 ARM 寄存器已经有了不错的理解, 不过下周我们会介绍数学协处理器中用于处理浮点变量的寄存器.&nbsp;你目前接触过的寄存器只能存储整数, 而在汇编层面, 任何小数值都必须通过数学协处理器的寄存器来处理.

下周我们将深入探讨调试浮点变量.