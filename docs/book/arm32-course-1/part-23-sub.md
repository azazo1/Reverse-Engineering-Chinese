## Part 23 - SUB

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

ARM 里的减法有四条指令, 分别是 SUB, SBC, RSB 和 RSC. 今天我们从 SUB 开始.

请记住, 在这些指令末尾加上 S 后缀, 比如 SUBS, SBCS, RSBS, RSCS, 就会影响标志位. 前面的 Lesson 里我们在标志位上花了足够多的时间, 现在你应该已经牢固掌握了.

来看一个 SUB 的例子:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520194165815.jpg"/></div>

编译:

<pre spellcheck="false">as -o sub.o sub.s
ld -o sub sub.o
</pre>

我们就是把 __67 十进制__ 移进 __r1__, 把 __53 十进制__ 移进 __r2__, 然后做 r1 - r2, 把结果放进 __r0__.

下周我们深入 SUB 调试.