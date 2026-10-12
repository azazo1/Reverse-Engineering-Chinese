## Part 49 - 修改后置自减运算符

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们再次复习一下代码.

<pre spellcheck="false">#include &lt;iostream&gt;

int main(void) {
&nbsp;&nbsp; &nbsp;int myNumber = 16;
&nbsp;&nbsp; &nbsp;int myNewNumber = myNumber--;

&nbsp;&nbsp; &nbsp;std::cout &lt;&lt; myNewNumber &lt;&lt; std::endl;
    std::cout &lt;&lt; myNumber &lt;&lt; std::endl;

&nbsp;&nbsp; &nbsp;return 0;
}
</pre>

让我们回顾一下上周的调试.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1532690049930.jpg"/></div>

可以看到, 在 __main+68__ 处 __r1__ 中的值是 __15__. 让我们来修改!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1532690140517.jpg"/></div>

我们又一次按自己的意愿操纵并改变了程序的执行. 通过这些篇幅短小的课, 你会对处理器以及它如何与二进制文件交互有越来越好的把握.

希望这个系列能为你理解 ARM 处理器打下扎实的框架. 本系列到此结束. 感谢大家一路同行!