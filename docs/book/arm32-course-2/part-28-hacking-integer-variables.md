## Part 28 - 修改整型变量

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们回顾一下我们的代码.&nbsp;&nbsp;

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1519988583160.jpg"/></div>

开始修改!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1519988510636.jpg"/></div>

让我们再次看看 __0x10730__ 这个内存位置里的内容.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1519988543593.jpg"/></div>

可以清楚地看到整数值 __777__ 出现了, 继续执行时, 它会把值 __777__ 回显到终端, 这与我们的 c++ 函数 __cout__ 相符.

让我们修改 __0x10730__ 里的值, 把它设为 __666__, 然后重新检查 __0x10730__ 里的值并继续执行.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1519988571825.jpg"/></div>

成功!&nbsp;可以看到我们把值修改成了 __666__, 继续执行时就能看到它被回显到 stdout.

下周我们将深入探讨浮点变量.