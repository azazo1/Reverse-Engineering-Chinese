## Part 29 - x64 汇编 \[Part 3\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

今天我们用一个简单的减法例子继续我们的教程. 让我们来看看源代码:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1551437589689.png"/></div>

让我们编译并运行调试器:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1551437628625.jpg"/></div>

让我们运行并反汇编:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1551437662831.jpg"/></div>

如我们所见, 我们把 __16__ 也就是十六进制的 __0x10__ 加载到 __EAX__ 里, 然后在下一条指令里从它里面减去 __5__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1551437723578.jpg"/></div>

我们单步执行两次, 然后查看 __RAX__ 里得到的值.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1551437759416.jpg"/></div>

如我们所见, 结果是 0xb 也就是十进制的 11, 正如预期. 你把这些简单的例子动手试一遍很重要, 这样当我们在以后的教程里开始调试 C++ 代码时, 你才能把握会发生什么.