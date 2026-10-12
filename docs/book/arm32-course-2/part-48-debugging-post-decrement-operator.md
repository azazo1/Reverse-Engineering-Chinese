## Part 48 - 调试后置自减运算符

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们重新检查一下代码.

<pre spellcheck="false">#include &lt;iostream&gt;

int main(void) {
&nbsp;&nbsp; &nbsp;int myNumber = 16;
&nbsp;&nbsp; &nbsp;int myNewNumber = myNumber--;

&nbsp;&nbsp; &nbsp;std::cout &lt;&lt; myNewNumber &lt;&lt; std::endl;
    std::cout &lt;&lt; myNumber &lt;&lt; std::endl;

&nbsp;&nbsp; &nbsp;return 0;
}
</pre>

上面这段非常简单的 C++ 代码, 所做的不过是把一个数字赋给一个变量, 再初始化另一个 int 变量并把原变量赋给它, 而这里对原变量做的是后置自减. 然后我们把每个值输出到终端.

让我们来调试.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1532085310684.png"/></div>

很明显, 后置自减运算符的值是在 __main+68 __处被加载进 __r1__ 的, 所以我们把断点下在 __main+72__ 处.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1532085326445.png"/></div>

我们可以清楚地看到, __r1 __中确实存放着 __15__, 它是从我们的原值自减而来的.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1532085443370.png"/></div>

下周我们将深入探讨修改后置自减运算符.