## Part 18 - 调试常量

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们回顾一下上周的代码.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520147783406.jpg"/></div>

开始调试!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520194203208.jpg"/></div>

我们可以看到, 内存地址 __0x10730 __处的值等于 __2017__.&nbsp;让我们继续, 看这个值像上周我们运行时那样打印到标准输出 (终端).

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520152068447.jpg"/></div>

我们可以非常清楚地看到, 我们把值从内存移到 __r1 __, 然后分支到 __cout__ 函数打印到终端.&nbsp;到了这个阶段, 理解上面这段汇编在做什么, 你应该感觉稍微自在一些了.

下周我们会深入常量的修改.