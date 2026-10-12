## Part 16 - 修改 ADD

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们再次回顾下面这个 ADD 示例:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520148983155.jpg"/></div>

让我们调试:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520143258587.jpg"/></div>

我们看到下面 __67__ 十进制这个值正被移入 __r1__:

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520171779364.jpg"/></div>

让我们修改! 让我们设置 __r1 = 66__!

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520211664200.jpg"/></div>

现在我们看到, 我们修改了程序, 因此它做加法时会得到不同的结果. 如果你还记得上一讲, __r0 = 120__. 这里我们看到我们修改了 r1, 现在 __r0__ 的值是 __119__!

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520211540477.jpg"/></div>

这就是理解汇编的威力. 这是一个非常简单的例子, 不过正如我所说, 每开启一个新系列, 我们都会编写一个程序, 调试它并修改它.

这些指令的组合会帮你在学习如何完全掌控一个应用程序时获得实操经验, 而在恶意软件逆向的场合, 它让你有能力让这个二进制文件做你想让它做的任何事!

下周我们将深入 ADDS.