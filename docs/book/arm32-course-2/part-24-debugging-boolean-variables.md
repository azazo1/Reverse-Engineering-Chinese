## Part 24 - 调试布尔变量

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们重新检查一下代码.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520236715844.jpg"/></div>

开始调试.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520194325794.jpg"/></div>

让我们单步 4 次, 然后反汇编.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520190876822.jpg"/></div>

让我们看看现在 __r3__ 里是什么.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520171350771.jpg"/></div>

可以清楚地看到, __isHacked__ 中的值是 __0__, 也就是 __false__, 这与我们的 c++ 源代码相符, 合情合理.

我知道这些 Lesson 看上去可能很琐碎, 但逆向工程的核心就是把事物拆解到最基本的组成部分.&nbsp;逆向工程关乎耐心与逻辑流程.&nbsp;你务必要花时间在 Raspberry Pi 设备上把所有这些示例亲手过一遍, 这样才能真正体会这个过程究竟是如何运作的.

下周我们将深入探讨修改布尔变量.