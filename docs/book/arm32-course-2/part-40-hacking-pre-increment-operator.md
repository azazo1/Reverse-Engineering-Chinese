## Part 40 - 修改前置自增运算符

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们再一次重新检查一下代码.

<pre spellcheck="false">#include &lt;iostream&gt;

&nbsp;

int main(void) {

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; int myNumber
= 16;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; int
myNewNumber = ++myNumber;

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; std::cout
&lt;&lt; myNewNumber &lt;&lt; std::endl;

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; return 0;

}
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1527247718232.jpg"/></div>

编译它只需要输入:

g++ example9.cpp -o example9

./example9

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1527247743089.jpg"/></div>

  

我们看到屏幕上打印出了 17.

让我们拆解一下:

我们创建了一个变量 __myNumber = 16__, 又创建了另一个变量 __myNewNumber__, 它对 __myNumber__ 的值做前置自增.&nbsp;我们看到执行代码时显示的是 17.

做前置自增时, 变量的值会先自增, 然后再赋给另一个变量.&nbsp;例如 __myNumber__ 是 __16__, 它在赋给 __myNewNumber__ 之前先自增, 所以我们得到 __17__.

让我们开始调试.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1527247841094.jpg"/></div>

我们像往常一样在 gdb 中启动并在 main 处下断点.&nbsp;注意在 __main+24__ 处, 我们正把值 __1__ 移入 __r3__.&nbsp;接着在 __main+28__ 处我们看到, 我们把这个值存到 __r11-8__, 我们将在此处设置断点并继续.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1527247877140.jpg"/></div>

此刻我们查看 __r3__ 中的值, 看到是 __17__.&nbsp;回想一下原始代码中 __myNumber__ 变量的值是 __16__.&nbsp;可以看到前置自增运算符成功地把值自增了 __1__, 从而得到 __17__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1527247908955.jpg"/></div>

我们看到继续执行代码后, 值 __17__ 如预期那样成功回显到终端.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1527247930003.jpg"/></div>

我们重新运行这个程序.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1527248017494.jpg"/></div>

我们来修改!&nbsp;这里我们查看 r3 中的值, 我们知道它是 17.&nbsp;我们把它改成别的值.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1527248050749.jpg"/></div>

成功!&nbsp;可以看到继续执行后, 修改过的值现在回显到了终端.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1527248118408.jpg"/></div>

下周我们将深入后置自增运算符.

  

  