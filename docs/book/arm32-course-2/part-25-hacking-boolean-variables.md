## Part 25 - 修改布尔变量

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们重新检查一下代码.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520191957701.jpg"/></div>

开始修改!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520210981189.jpg"/></div>

让我们在 main 处下断点, 运行并反汇编, 再单步进入四次.&nbsp;

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520146846926.jpg"/></div>

我们看到 __0__, 也就是 __FALSE__, 在 main+12 处被移入 __r3__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520218746699.jpg"/></div>

非常简单, 我们把 __r3__ 设为 __1__, 也就是 __TRUE__, 然后继续执行, 就会注意到布尔变量 __isHacked__ 现在变成了 __TRUE__.

就是这么简单, 各位!&nbsp;这些基础示例会帮你积累一套思维素材, 让你知道该如何应对代码中的一切, 并理解怎样才能无论面对什么情况都掌控代码的执行!

下周我们将深入探讨整型变量.