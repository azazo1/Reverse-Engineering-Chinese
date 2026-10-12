## Part 46 - 修改前置自减运算符

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们重新检查一下代码.

<pre spellcheck="false">#include &lt;iostream&gt;

int main(void) {
&nbsp;&nbsp; &nbsp;int myNumber = 16;
&nbsp;&nbsp; &nbsp;int myNewNumber = --myNumber;

&nbsp;&nbsp; &nbsp;std::cout &lt;&lt; myNewNumber &lt;&lt; std::endl;
    std::cout &lt;&lt; myNumber &lt;&lt; std::endl;

&nbsp;&nbsp; &nbsp;return 0;
}
</pre>

我们记得, 编译后得到的是 15.

让我们来调试.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1530875391750.jpg"/></div>

让我们下断点.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1530875474311.jpg"/></div>

让我们看看 __r3 __里面有什么, 然后修改它.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1530875492398.jpg"/></div>

现在继续执行, 我们看到修改并没有成功, 这是为什么呢?

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1530875528881.jpg"/></div>

我们重新运行这个二进制文件, 下断点后看到这里 __r1 __存放的是 __15__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1530875553276.jpg"/></div>

继续执行后我们看到 15, 这不是我们想要的结果.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1530875636786.jpg"/></div>

现在我们再次下断点并打印这个值.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1530875661356.jpg"/></div>

这次我们设置 __r1__, 可以看到我们修改成功了!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1530875673374.jpg"/></div>

这是你第一次真正深入拆解寄存器, 看清东西被存放在哪里, 以及它如何影响结果. 花点时间自己跑一遍, 这样你才能真正牢牢掌握它.

下周我们将深入探讨后置自减运算符.