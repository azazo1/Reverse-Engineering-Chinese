## Part 19 - 修改常量

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们回顾一下最初的代码.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520195148562.jpg"/></div>

开始修改!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520144504108.jpg"/></div>

如你所见, 内存地址 __0x10730 __处的值等于 __2017__.&nbsp;让我们把内存中的这个值改成 __1981__.&nbsp;继续执行, 你会看到该值变成 __1981__!&nbsp;修改成功!

我们再用第二种方式来修改!&nbsp;重新启动程序, 在 main+28 处设置断点, 然后继续运行到该断点.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520146785758.jpg"/></div>

继续执行, 可以看到 __r1__ 中的值是 __2017__.&nbsp;让我们把 __r1__ 中的值改成 __1981__.&nbsp;继续执行, 可以看到程序被成功修改为 __1981__!&nbsp;&nbsp;

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520148769675.jpg"/></div>

下周我们将深入探讨字符变量.