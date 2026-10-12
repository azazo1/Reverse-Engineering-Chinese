## Part 9 - 链接寄存器

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

链接寄存器 (Link Register), 也就是 R14, 用来保存函数调用的返回地址.

当一条 BL (branch with link) 指令执行子程序调用时, 链接寄存器会被设为子程序的返回地址.&nbsp;BL 会跳到代码中的另一个位置, 执行完毕后就允许返回到紧接 BL 代码段之后的位置.&nbsp;当子程序返回时, 链接寄存器把这个地址交回给程序计数器.

链接寄存器不需要对存有栈的那块内存进行读写, 这在反复调用小子程序时能省下相当可观的执行时间比例.

当 BL 执行之后, 返回地址, 也就是下一条将要执行指令的地址, 会被装入 LR, 即 R14.&nbsp;当子程序执行完毕, LR 会被直接复制到 PC (程序计数器) 也就是 R15, 代码执行就继续在顺序代码中原先的位置进行.

代码时间! 如果你没看懂这里代码示例中的全部内容, 不要灰心.&nbsp;在接下来的几节课里它就会变得清晰.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520232099195.jpg"/></div>

编译方法:

<pre spellcheck="false">as -o lr_demo.o lr_demo.s

ld -o lr_demo lr_demo.o
</pre>

我在这里创建的简单示例基本上不用多解释.&nbsp;我们从 __no\_return__ 子程序开始, 接着进入 __my\_function__ 子程序, 然后到 __wrap\_up__ 子程序, 最后是 __exit__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520190659000.jpg"/></div>

我们有必要进入 GDB, 也就是我们的调试器, 看看每一步到底发生了什么:

你可以看到, 调试器里的每一步都清清楚楚地展示了从 __no\_return__ 到 __my\_function__ 的推进过程, 期间跳过了 __wrap\_up__, 直到程序计数器从链接寄存器取到地址.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520221355382.jpg"/></div>

这里我们看到从 __wrap\_up__ 到 __exit__ 的推进过程.

这是一项基础操作, 下周我们看栈如何运作时就会明白, 因为 LR 是这个过程中必不可少的一部分.

下周我们会深入介绍栈指针 (Stack Pointer)!&nbsp;敬请关注!