## Part 27 - x64 汇编 \[Part 1\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

今天我们开始真正的 x64 代码基础. 在接下来的几周里我会写一些非常简单的例子, 让我们对 x64 架构有所把握. 我们先从一个基础代码块开始:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1550227269983.jpg"/></div>

我们首先声明 __.data__ 段, 我们所有的全局数据都存放在这里. 如果我们有字符串或者其他形式的硬编码数据, 它就会放进这个块里. 在我们的例子里, 我们让它保持为空.

__.text__ 段声明程序的入口点从哪里开始, 在我们的例子里我们用 __\_start__, 你也可以用 __main__.

我们只是把十进制 16 也就是十六进制 10 这个值移动到 64 位的 RAX 寄存器里. 我们稍后会看到, 当我们在 GDB 里调试时, 处理器只会用到它较低的那部分 EAX.

最后一部分只是一个简单的退出例程, 我们把 60 移动到 RAX, 然后执行 syscall. 它只是把操作交还给 OS.

让我们编译并链接:

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1550227507149.jpg"/></div>

让我们在 GDB 里调试:

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1550227529034.jpg"/></div>

让我们把调试器设成 intel 语法, 并在 start 处设置一个断点:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1550227565697.jpg"/></div>

如我们所见, 十进制 16 也就是十六进制 10 即将被移动到 EAX 里, 但如我们所见, 直到我们单步向前之后它才会完成.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1550227619555.jpg"/></div>

现在我们可以查看我们的寄存器了.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1550227646545.jpg"/></div>

我们可以看到 RAX 成功地保存了十进制 16 也就是十六进制 10.

我们会在这些简单的例子上花上几周时间, 好让你熟悉处理器是如何运作的以及它内部的机制.