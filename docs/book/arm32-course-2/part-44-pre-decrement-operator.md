## Part 44 - 前置自减运算符

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们看看前置自减运算符的例子. 前置自减运算符会在赋值动作发生之前, 先把给定的值减一.

让我们检查一下代码.

<pre spellcheck="false">#include &lt;iostream&gt;

int main(void) {
&nbsp;&nbsp; &nbsp;int myNumber = 16;
&nbsp;&nbsp; &nbsp;int myNewNumber = --myNumber;

&nbsp;&nbsp; &nbsp;std::cout &lt;&lt; myNewNumber &lt;&lt; std::endl;
    std::cout &lt;&lt; myNumber &lt;&lt; std::endl;

&nbsp;&nbsp; &nbsp;return 0;
}
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1529666614196.png"/></div>

编译并运行后, 我们看到终端上回显出 15.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1529666685691.png"/></div>

__myNumber __的值原来是 __16 __, 用前置自减运算符赋值之后, 我们看到新值是 __15__, 因为它被赋进了 __myNewNumber__.

下周我们将深入探讨调试前置自减运算符.