## Part 42 - 调试后置自增运算符

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们重新检查一下代码.

<pre spellcheck="false">#include &lt;iostream&gt;

int main(void) {
&nbsp;&nbsp; &nbsp;int myNumber = 16;
&nbsp;&nbsp; &nbsp;int myNewNumber = ++myNumber;

&nbsp;&nbsp; &nbsp;std::cout &lt;&lt; myNewNumber &lt;&lt; std::endl;

&nbsp;&nbsp; &nbsp;return 0;
}
</pre>

我们创建一个变量 __myNumber = 16__, 又创建另一个变量 __myNewNumber__, 它对 __myNumber__ 的值做后置自增.&nbsp;我们看到执行代码时, __myNewNumber__ 的值显示为 __16__, 而 __myNumber__ 的值显示为 __17__, 因为 __myNewNumber__ 并没有被自增, 只有 __myNumber__ 被自增, 毕竟这是后置运算符.

当我们做后置自增时, 变量的值是在赋给另一个变量之后才自增的.&nbsp;例如 __myNumber__ 是 __16__, 它在赋给 __myNewNumber__ 之后才自增, 因此我们得到 __17__.

让我们来调试.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1528458112325.jpg"/></div>

让我们在 __\*main+28 __处下断点, 然后继续.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1528458131421.jpg"/></div>

可以看到, 其中 __r3 __的值是 16, 其中 __r2 __的值是 17. 我们可以看到, 它们在 __\*main+12__ 处由 __mov__ 指令直接从内存加载进寄存器, 而在 __\*main+24__ 处, 我们把 1 加到 __r3__ 上, 再把这个值放进 __r2__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1528458142344.jpg"/></div>

继续执行, 我们可以看到 __cout __这个 c++ 函数被调用, 它按预期把值回显到终端 (标准输出).

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1528458154804.jpg"/></div>

下周我们将深入探讨修改后置自增运算符.