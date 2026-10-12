## Part 10 - 栈指针

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

栈 (Stack) 是一种抽象数据类型, 它遵循 LIFO (Last In First Out, 后进先出).&nbsp;当我们把一个值压入栈时, 它是写入栈指针 (Stack Pointer) 的; 而当这个值被弹出栈时, 它会从栈中弹出, 进入你选择的某个寄存器.

代码时间! 再说一次, 如果这里的代码示例你有看不懂的地方, 不要气馁.&nbsp;在接下来的几节 Lesson 里它会变得清晰起来.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520149187367.jpg"/></div>

编译方法:

<pre spellcheck="false">as -o sp_demo.o sp_demo.s

ld -o sp_demo sp_demo.o
</pre>

让我们再次把二进制文件载入 GDB, 看看发生了什么.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520209893418.jpg"/></div>

让我们单步进入一次.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520232603248.jpg"/></div>

我们看到 __十六进制 30__ 或者说 __十进制 48__ 被移入 __r7__.&nbsp;让我们再次单步进入.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520238832288.jpg"/></div>

我们看到 __sp__ 的值从 __0x7efff3a0__ 变成了 __0xefff39c__.&nbsp;这是向后移动了 __4 个字节__.&nbsp;你可能会问, 栈指针究竟为什么会向后移动呢!

这个问题的答案基于一个事实: 栈是向__下__增长的.&nbsp;当我们说栈顶时, 你可以想象一叠盘子被一个接一个地放在彼此__下面__.

最初 __sp__ 位于 __0x7efff3a0__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520218097215.jpg"/></div>

当我们把 __r7__ 压入栈后, __栈指针__ 的新值变成了 __0x7efff39c__, 因此我们可以看出, 栈在内存中确实是向__下__增长的.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520239285552.jpg"/></div>

现在我们再次单步进入.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520143279567.jpg"/></div>

我们可以看到 __十六进制 10__ 或者说 __十进制 16__ 被移入 __r7__.&nbsp;注意 __sp__ 并没有变化.

在我们再次单步进入之前, 让我们看看 __sp__ 里面的值.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520216970660.jpg"/></div>

让我们再次单步进入.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520233070958.jpg"/></div>

我们看到栈里的那个值被弹出栈并放回了 __r7__, 因此 __十六进制 30__ 这个值又回到了 __r7__, 同样 __sp__ 也回到了 __0x73fff3a0__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520232081853.jpg"/></div>

请花点时间把代码敲出来, 编译并链接它, 然后在 GDB 中单步调试这个二进制文件.&nbsp;栈操作对于理解逆向工程 (Reverse Engineering) 与恶意软件分析 (Malware Analysis), 以及任何形式的调试都至关重要.

下周我们将深入 ARM 固件启动过程.