## Part 41 - 后置自增运算符

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们深入看看代码.

<pre spellcheck="false">#include &lt;iostream&gt;

int main(void) {
&nbsp;&nbsp; &nbsp;int myNumber = 16;
&nbsp;&nbsp; &nbsp;int myNewNumber = ++myNumber;

&nbsp;&nbsp; &nbsp;std::cout &lt;&lt; myNewNumber &lt;&lt; std::endl;

&nbsp;&nbsp; &nbsp;return 0;
}
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1527849027049.jpg"/></div>

编译它只需要输入:

g++ example10.cpp -o example10

./example10

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1527849063244.jpg"/></div>

我们看到屏幕上打印出了 16 和 17.

让我们拆解一下:

我们创建了一个变量 __myNumber = 16__, 又创建了另一个变量 __myNewNumber__, 它对 __myNumber__ 的值做后置自增.&nbsp;我们看到执行代码时, __myNewNumber__ 的值显示为 __16__, 而 __myNumber __的值显示为 __17__, 因为 __myNewNumber__ 并没有自增, 只有 __myNumber__ 自增了, 因为这是个后置运算符.

做后置自增时, 变量的值会先赋给另一个变量, 然后再自增.&nbsp;例如 __myNumber__ 是 __16__, 它在赋给 __myNewNumber__ 之后才自增, 所以我们得到 __17__.

下周我们将深入调试后置自增运算符.