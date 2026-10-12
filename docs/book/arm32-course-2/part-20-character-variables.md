## Part 20 - 字符变量

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

我们旅程的下一站是字符变量.&nbsp;与我们到目前为止处理过的字符串不同, 一个字符只占一个字节的数据.

请记住, 处理任何字符数据时, 我们实际上处理的是两个十六进制数字, 它们就是 ASCII 码, 代表我们在各自终端上看到的真实字符.

记住, 每个十六进制数字的长度是 4 位.&nbsp;因此两个十六进制数字的长度就是 8 位, 也就是一个字节.&nbsp;

回顾一下, 每个字符都会转换成处理器能理解的十六进制 ASCII 码.&nbsp;__n__ 的值是十六进制 __0x6e__, 也就是十进制 __110__.&nbsp;你可以查看任意 ASCII 表, 看看这个值是怎么得来的.&nbsp;这在下一课会派上用场.

我们从第三个 C++ 程序开始, 也就是我们的 "字符变量" 程序.&nbsp;让我们深入进去, 逐行拆解, 看看这门语言是如何工作的.&nbsp;我们把它命名为 example3.cpp 并保存到设备上.

<pre spellcheck="false">#include &lt;iostream&gt;

&nbsp;

int main(void) {

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; char yes_no = ‘n’;

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; std::cout &lt;&lt; yes_no &lt;&lt; std::endl;

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; return 0;

}
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520190636660.jpg"/></div>

要编译它, 我们只需输入:

g++ example3.cpp -o example3

然后我们只需输入:

./example3

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520211586776.jpg"/></div>

成功!&nbsp;我们看到 "__n__" 被打印到标准输出也就是终端上!

让我们拆解一下:

我们使用 __char __关键字来声明一个字符变量, 并把它的值赋为 __n__.

接着我们用 __cout __函数把它打印到标准输出也就是终端上, 并用 __endl__ 函数添加一个换行.

就是这样!&nbsp;非常简单.

下周我们将深入探讨调试字符变量.