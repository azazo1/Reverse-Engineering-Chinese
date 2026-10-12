## Part 35 - SizeOf 运算符

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

我们旅程的下一站是 SizeOf 运算符.&nbsp;

让我们看看我们的代码.

<pre spellcheck="false">#include &lt;iostream&gt;

&nbsp;

int main(void) {

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; int myNumber = 16;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; int myNumberSize = sizeof(myNumber);

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; std::cout &lt;&lt; myNumberSize &lt;&lt; std::endl;

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; return 0;

}
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1524218995477.png"/></div>

编译它只需要输入:

g++ example8.cpp -o example8

./example8

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1524219035247.png"/></div>

我们看到屏幕上打印出了 4.

让我们拆解一下:

我们创建了一个变量 __myNumber = 16__, 又创建了另一个变量 __myNumberSize__, 它保存着 __myNumber__ 的大小.&nbsp;我们看到执行代码时显示的是 4, 因此可以看出 SizeOf operator 表明一个整数宽 4 字节.

下周我们将深入调试 SizeOf 运算符.