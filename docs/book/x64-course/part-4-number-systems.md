## Part 4 - 数制

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

说到底, 一切都归结为 1 和 0.&nbsp;无论未来的框架演进得多么精巧, 它们, 包括解释型语言在内, 最终都要用到 JVM 之类的东西, 一路向下到汇编, 再到机器码, 最后到二进制.

我们为什么还要讨论数制?&nbsp;它和我们这个系列有什么关系?&nbsp;答案很简单.&nbsp;除了所有东西最终都归结为 1 和 0 之外, 指令, 内存以及处理器寄存器都用到了另一种数制, 叫做十六进制 (hexadecimal).&nbsp;

我们来讨论二进制!&nbsp;微处理器的核心是一连串二进制数, 它们要么是 +5V (开, 也就是 1), 要么是 0V (关, 也就是 0). 每个 0 或 1 都代表微处理器里的一位 (bit) 信息. 8 位组合起来就是一个字节.

在深入二进制之前, 先来看看我们熟悉的十进制. 拿 2017 这个数来说, 我们会把它理解为两千零一十七.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1536316029655.jpg"/></div>

我们来看一看二进制系统, 以及它运作的基本原理.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1536316062694.jpg"/></div>

如果要把一个二进制数转成十进制, 做法非常简单, 就像下面这样. 以二进制数 0101 1101 为例, 可以看到它对应十进制的 93.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1536316087192.jpg"/></div>

把数值列里的数相加, 得到 0 + 64 + 0 + 16 + 8 + 4 + 0 + 1, 等于十进制的 93.

如果要把十进制数转成二进制, 我们会对照最高位判断能不能做一次减法, 如果能, 就在对应的二进制列写 1, 余数则带到下一行. 以十进制数 120 为例, 它对应的二进制是 0111 1000.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1536316117407.jpg"/></div>

1) 128 能装进 120 里吗: 不能, 因此为 0.

2) 64 能装进 120 里吗: 能, 因此为 1, 然后 120 - 64 = 56.

3) 32 能装进 56 里吗: 能, 因此为 1, 然后 56 - 32 = 24.

4) 16 能装进 24 里吗: 能, 因此为 1, 然后 24 - 16 = 8.

5) 8 能装进 8 里吗: 能, 因此为 1, 然后 8 - 8 = 0.

6) 4 能装进 0 里吗: 不能, 因此为 0.

7) 2 能装进 0 里吗: 不能, 因此为 0.

8) 1 能装进 0 里吗: 不能, 因此为 0.

要把二进制转成十六进制, 只需对照下面这张表.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1536316179552.jpg"/></div>

我们把 0101 1111 这样的二进制数转成十六进制. 做法就是查表, 逐个比较每个半字节 (nibble), 一个半字节由 4 位组成. 记住, 8 位等于一个字节, 2 个半字节也等于一个字节.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1536316203991.jpg"/></div>

因此二进制 0101 1111 = 十六进制的 0x5f. 0x 这种写法表示十六进制.

从十六进制回到二进制也很简单, 只要反过来做一遍就行, 例如:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1536316238835.jpg"/></div>

要明白一点: 每个十六进制数字的长度是一个半字节, 因此两个十六进制数字的长度是一个字节.

从十六进制转成十进制, 做法如下:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1536316267782.jpg"/></div>

可见 80 + 15 = 95, 也就是十六进制的 0x5f.

最后是从十进制转成十六进制. 以十进制数 850 为例, 它等于十六进制的 352.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1536316294127.jpg"/></div>

"计算机都替我把这些算好了, 我干嘛还要浪费时间学这些鬼东西!"

正如我上面提到的, 如果你想在核心层面真正理解并精通逆向工程, 那么扎实掌握这两种额外的数制就至关重要.&nbsp;有些很棒的工具能辅助逆向工程的过程, 不过你对这些内容理解得越透彻, 在成长路上就越有帮助.

我不是让你把上面这些背下来, 也不是让你每种都做上千道练习. 我只希望你花点时间真正明白: 处理器里的一切, 真的是字面意义上的一切, 最终都归结为二进制位.

无论你是在编写, 调试还是修改用汇编, Python, Java, C, C++, R, JavaScript, 或者任何其他刚问世的新语言写成的应用, 一切最终都必然归结为二进制的 0 和 1, 它们分别代表 +5V 和 0V.

我们人类使用 10 进制, 也就是十进制.&nbsp;现在把我们的思路扩展到 2 进制 (二进制) 和 16 进制 (十六进制) 吧!

下周我们深入二进制加法! 敬请期待!