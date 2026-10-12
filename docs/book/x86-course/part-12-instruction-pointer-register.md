## Part 12: 指令指针寄存器

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

被称为 EIP 寄存器的指令指针寄存器 (instruction pointer register), 就是你在任何逆向工程中要打交道的最重要的寄存器. EIP 跟踪下一条要执行的指令代码. EIP 指向下一条要执行的指令. 如果你修改这个指针, 让它跳转到代码中的另一个区域, 你就完全控制了这个程序.

让我们先跳到前面, 深入看一些代码. 下面是一个用 C 写的简单 hello world 应用程序示例, 我们会在教程系列的后续部分更详细地讲解它. 就今天的目的而言, 我们将看到汇编语言原始的力量, 尤其是 EIP 寄存器的力量, 以及我们能做些什么来彻底夺取程序的控制权.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520174518917.jpg"/></div>

如果你不明白它做了什么, 或者它有什么功能, 不用担心. 这里要注意的是, 我们有一个名为 unreachableFunction 的函数, 它从未被 main 函数调用过. 正如你将看到的, 如果我们能控制 EIP 寄存器, 就能修改这个程序, 让它去执行那段代码!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520572373327.jpg"/></div>

我们只是把代码编译成适用于 IA32 指令集的形式并运行了它.&nbsp;如你所见, 没有任何形式对 __unreachableFunction__ 的调用, 因为它在正常情况下不可达, 你可以看到执行时打印出了 'Hello World!\`.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520572374855.jpg"/></div>

我们用 GDB 调试器反汇编了这个程序.&nbsp;我们在 main 函数上下了断点并运行了程序.&nbsp;当我们单步执行到下一条指令时, =&gt; 显示的就是 EIP 指向的位置.&nbsp;如果我们按正常的程序流程走下去, 'Hello World! 会被打印到控制台然后退出.&nbsp;

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520191047777.jpg"/></div>

如果我们再次运行程序, 检查一下 EIP 指向哪里, 就会看到:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520173635003.jpg"/></div>

我们可以看到 EIP 指向 main+17, 或者说地址 0x680cec83.

让我们检查一下 __unreachableFunction__, 看看它在内存中的起始位置, 并把这个地址记下来.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520572373912.jpg"/></div>

下一步是把 EIP 设置为地址 0x0804843b, 这样我们就能劫持程序流程去运行 unreachableFunction.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520572373288.jpg"/></div>

现在我们已经夺取了 EIP 的控制权, 让我们继续执行, 看看我们是如何把运行中程序的操作劫持过来为自己所用的!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520192688705.jpg"/></div>

哇哦! 我们成功修改了这个程序!

那么你心里的疑问是, 在我对这些东西一无所知的时候, 你为什么给我看这个? 重要的是要明白, 在进行像这样漫长的教程时, 我们有时应该向前看一看, 弄清为什么在真正深入之前要花这么多步骤去学基础. 但同样重要的是让你看到, 如果你坚持跟着教程走, 你的努力会有回报, 因为我们将学会劫持任何正在运行的程序, 让它做我们想让它做的任何事, 同时还能主动拆解恶意程序, 这样我们不仅能禁用它, 还能把它追溯到一个可能的 IP, 也就是攻击的源头.

在下一节教程中, 我们将继续讨论 IA-32 架构, 介绍控制寄存器.