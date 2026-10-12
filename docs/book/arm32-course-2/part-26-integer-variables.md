## Part 26 - 整型变量

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

我们旅程的下一站是整型变量.&nbsp;

一个 32 位寄存器可以存储 2^32 个不同的值. 32 位中能存储的整数取值范围取决于所用的整数表示法. 对于最常见的两种表示法, 以 (无符号) 二进制数表示时, 范围是 0 到 4,294,967,295 (2^32 - 1), 以二进制补码表示时, 范围是 -2,147,483,648 (-2^31) 到 2,147,483,647 (2^31 - 1).

请记住, 使用 32 位内存地址, 你最多可以直接访问 4 GB 的字节可寻址内存.

让我们看看我们的代码.

<pre spellcheck="false">#include &lt;iostream&gt;

&nbsp;

int main(void) {

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; int myNumber = 777;

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; std::cout &lt;&lt; myNumber &lt;&lt; std::endl;

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; return 0;

}
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520215369999.jpg"/></div>

要编译它, 我们只需输入:

g++ example5.cpp -o example5

./example5

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520195285687.jpg"/></div>

成功!&nbsp;我们看到 __777__ 被打印到标准输出也就是终端上!

让我们拆解一下:

我们把整数 __777 __直接赋给变量 __myNumber__, 然后用 c++ 的 __cout__ 函数把它打印到终端.

下周我们将深入探讨调试整型变量.