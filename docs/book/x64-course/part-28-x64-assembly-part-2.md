## Part 28 - x64 汇编 \[Part 2\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

我们继续看另一个例子:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1550829629337.png"/></div>

如我们所见, 我们把 __0x10__ 移动到 __RAX__ 里, 然后把 __0x05__ 加到 __RAX__ 里.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1550829671542.jpg"/></div>

我们编译, 然后来反汇编.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1550829696687.jpg"/></div>

如你所见, 我们如预期地在调试里看到了我们的代码.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1550829787663.jpg"/></div>

我们单步执行两次, 然后...

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1550829821644.jpg"/></div>

我们看到 __0x15 __或者十进制的 __21__ 被移动到 __RAX__ 里. 在继续往下走的过程中, 请花时间仔细尝试这些非常简单的例子.