## Part 32 - 双精度变量

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

我们旅程的下一站是双精度 (double-precision) 浮点变量.&nbsp;

双精度浮点变量与浮点变量不同, 它宽 64 位, 有 15-17 位有效数字的精度.

让我们来看看代码.

<pre spellcheck="false">#include &lt;iostream&gt;

&nbsp;

int main(void) {

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; double myNumber = 1337.77;

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; std::cout &lt;&lt; myNumber &lt;&lt; std::endl;

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; return 0;

}
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1522403579256.png"/></div>

编译它只需要输入:

g++ example7.cpp -o example7

./example7

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1522403604790.png"/></div>

成功!&nbsp;我们看到 1337.77 被打印到标准输出或者终端!

让我们拆解一下:

我们把浮点变量__ __直接赋给变量 __myNumber __, 然后用 c++ 的 __cout__ 函数把它打印到终端.

下周我们将深入调试双精度变量.