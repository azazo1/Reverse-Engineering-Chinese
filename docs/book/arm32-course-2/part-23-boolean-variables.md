## Part 23 - 布尔变量

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

我们旅程的下一站是布尔变量.&nbsp;这个名字可以追溯到伟大的 George Boole, 现代计算机科学全都源自于他.&nbsp;

在最底层, 一个值要么是 0 要么是 1, 要么是 false 要么是 true, 要么是 + &lt; 5 伏要么是 +5 伏, 等等.

让我们看看我们的代码.

<pre spellcheck="false">#include &lt;iostream&gt;

&nbsp;

int main(void) {

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; bool isHacked = false;

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; std::cout &lt;&lt; isHacked &lt;&lt; std::endl;

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; return 0;

}
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520192758105.jpg"/></div>

要编译它, 我们只需输入:

<pre spellcheck="false">g++ example4.cpp -o example4

./example4
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520196655358.jpg"/></div>

成功!&nbsp;我们看到 __0__ 被打印到标准输出也就是终端上!

让我们拆解一下:

我们创建一个名为 __isHacked __的布尔变量, 并把它的值赋为 __false__, 也就是 __0__.&nbsp;运行这个二进制文件时, 我们清楚地看到值 __0__ 被成功回显到标准输出.

下周我们将深入探讨调试布尔变量.