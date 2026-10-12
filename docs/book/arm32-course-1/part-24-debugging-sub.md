## Part 24 - 调试 SUB

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

如前所述, ARM 里的减法有四条指令, 分别是 SUB, SBC, RSB 和 RSC. 今天我们从 SUB 开始.

请记住, 在这些指令末尾加上 S 后缀, 比如 SUBS, SBCS, RSBS, RSCS, 就会影响标志位. 前面的 Lesson 里我们在标志位上花了足够多的时间, 现在你应该已经牢固掌握了.

我们再来看看前面那个 SUB 的例子:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520242319262.jpg"/></div>

我们就是把 __67 十进制__ 移进 __r1__, 把 __53 十进制__ 移进 __r2__, 然后做 r1 - r2, 把结果放进 __r0__.

我们来调试.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520211071860.jpg"/></div>

可以看到寄存器都是清空的. 我们来单步执行, 看看 __r0__ 的值会变成什么.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520241790816.jpg"/></div>

如上所示, __r0__ 现在的值是 __14__ __十进制__, 结果符合预期.

下周我们深入 SUB 修改.