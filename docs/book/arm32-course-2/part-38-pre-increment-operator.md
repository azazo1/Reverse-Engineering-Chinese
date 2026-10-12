## Part 38 - 前置自增运算符

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

我们旅程的下一站是前置自增运算符.&nbsp;

让我们来看看代码.

<pre spellcheck="false">#include &lt;iostream&gt;

&nbsp;

int main(void) {

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; int myNumber = 16;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; int myNewNumber = ++myNumber;

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; std::cout &lt;&lt; myNewNumber &lt;&lt; std::endl;

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; return 0;

}
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1526036616866.jpg"/></div>

编译它只需要输入:

g++ example9.cpp -o example9

./example9

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1526036640627.jpg"/></div>

我们看到屏幕上打印出了 17.

让我们拆解一下:

我们创建了一个变量 __myNumber = 16__, 又创建了另一个变量 __myNewNumber__, 它对 __myNumber__ 的值做前置自增.&nbsp;我们看到执行代码时显示的是 17.

做前置自增时, 变量的值会先自增, 然后再赋给另一个变量.&nbsp;例如 __myNumber__ 是 __16__, 它在赋给 __myNewNumber__ 之前先自增, 所以我们得到 __17__.

下周我们将深入调试前置自增运算符.