## Part 5 - 二进制加法

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

二进制加法有四种不同的情形:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1536919520880.jpg"/></div>

注意 (1) 表示进位位 (carry bit). 说白了, 它表示溢出.

看下面这个 4 位半字节 (nibble) 的例子:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1536919547320.jpg"/></div>

可以看到第 3 位明显产生了进位. 如果第 8 位也产生进位, 就会在 CPU 里生成进位标志 (carry flag).

再看一个 8 位的数:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1536919574450.jpg"/></div>

如果是这样:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1536919592305.jpg"/></div>

这里我们看到一个进位位, 它会让 CPU 里的进位标志变成 1, 也就是 true. 后面的教程里我们会讨论进位标志. 请先记住这个例子, 拿它作参照, 理解这一点非常重要.

下周我们深入二进制减法! 敬请期待!