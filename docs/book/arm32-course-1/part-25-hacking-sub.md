## Part 25 - 修改 SUB

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

如前所述, ARM 里的减法有四条指令, 分别是 SUB, SBC, RSB 和 RSC. 今天我们从 SUB 开始.

请记住, 在这些指令末尾加上 S 后缀, 比如 SUBS, SBCS, RSBS, RSCS, 就会影响标志位. 前面的 Lesson 里我们在标志位上花了足够多的时间, 现在你应该已经牢固掌握了.

我们再来看看前面那个 SUB 的例子:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520108821352.jpg"/></div>

我们就是把 __67 十进制__ 移进 __r1__, 把 __53 十进制__ 移进 __r2__, 然后做 r1 - r2, 把结果放进 __r0__.

我们来修改.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520481500035.jpg"/></div>

可以看到寄存器都是清空的. 我们来单步执行, 看看稍作修改之后 __r0__ 的值会变成什么.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520195082047.jpg"/></div>

如上所示, __r0__ 现在的值是 __17__ __十进制__, 这符合预期, 因为我们把 __r2__ 的值从 __十进制 53__ 修改成了 __十进制 50__.

感谢大家一路同行, 学习 ARM 汇编. 这个系列到此结束, 希望大家把学到的东西用起来, 继续钻研 ARM 指令集, 不断进步.

本教程的目的是为你的 ARM 汇编打下扎实的基础, 我相信我们已经做到了. 谢谢大家, 期待看到你们成为未来的逆向工程师!