## Part 43 - 修改后置自增运算符

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

我们创建一个变量&nbsp;__myNumber = 16&nbsp;__, 又创建另一个变量&nbsp;__myNewNumber__, 它对&nbsp;__myNumber__ 的值做后置自增.&nbsp;我们看到执行代码时, 它把&nbsp;__16__&nbsp;显示为&nbsp;__myNewNumber__&nbsp;的值, 而把&nbsp;__17__&nbsp;显示为&nbsp;__myNumber&nbsp;__的值, 因为&nbsp;__myNewNumber__&nbsp;并没有被自增, 只有&nbsp;__myNumber__&nbsp;被自增, 毕竟这是后置运算符.

当我们做后置自增时, 变量的值是在赋给另一个变量之后才自增的.&nbsp;例如&nbsp;__myNumber__&nbsp;是&nbsp;__16__, 它在赋给&nbsp;__myNewNumber__&nbsp;之后才自增, 因此我们得到&nbsp;__17__.

让我们来调试.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1529062708632.jpg"/></div>

让我们在&nbsp;__\*main+28__&nbsp;处下断点并继续.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1529062741325.jpg"/></div>

可以看到, 其中&nbsp;__r3__&nbsp;的值是 __16__, 其中&nbsp;__r2__&nbsp;的值是 __17__. 我们可以看到, 它们在&nbsp;__\*main+12__&nbsp;处由&nbsp;__mov__&nbsp;指令直接从内存加载进寄存器, 而在&nbsp;__\*main+24__&nbsp;处, 我们把 __1__ 加到&nbsp;__r3__&nbsp;上, 再把这个值放进&nbsp;__r2__.

让我们来修改它吧!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1529062819877.jpg"/></div>

我们知道, 现在可以随心所欲地设置 __r3__ 的值了!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1529062853544.jpg"/></div>

继续执行, 我们看到 c++ 的 __cout__ 函数把我们修改后的新值回显到屏幕上!

下周我们将深入探讨前置自减运算符.