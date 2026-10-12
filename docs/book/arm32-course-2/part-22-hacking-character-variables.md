## Part 22 - 修改字符变量

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们回顾一下代码.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520232430320.jpg"/></div>

开始修改!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520194771044.jpg"/></div>

我们再次看到 __0x6e__ 这个直接值在 __main+12__ 处被移入 __r3__, 它就是我们的 '__n__'.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520195499705.jpg"/></div>

单步进入 4 次之后, 再验证 __r3__ 中的值, 我们清楚地看到它是 '__n__'.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520233196032.jpg"/></div>

让我们把 __r3__ 中的值修改成 '__y__', 然后重新检查 __r3__ 中的值.&nbsp;现在可以清楚地看到它已经被改成 '__y__' 了.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520232999022.jpg"/></div>

继续执行, 我们成功看到修改生效了!&nbsp;我们看到 '__y__' 的值被打印到标准输出.

下周我们将深入探讨布尔变量.