## Part 4 - 调试 "Hello World"

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题. https://github.com/mytechnotalent/hacking\_c-\_arm64

今天我们将用自己构建的 Radare2 开发版来调试我们的第一个程序.

如果这是你第一次接触汇编语言, 我建议你看看这个系列, 它可以让你为接下来的 Lesson 做更充分的准备.

<iframe allowfullscreen="true" class="center lazy-load" data-delayed-url="https://www.linkedin.com/embeds/publishingEmbed.html?articleId=7574498398602237511" frameborder="0" height="294" src="about:blank" title="mytechnotalent/Reverse-Engineering-Tutorial" width="744"></iframe>

首先, 让我们在 Radare2 中打开我们的二进制文件.

<pre spellcheck="false">radare2 ./0x01_asm_64_helloworld
</pre>

让我们用上 Radare2 的自动分析功能.

<pre spellcheck="false">aaa
</pre>

接下来合乎逻辑的一步, 是以调试模式启动这个程序, 这样它就会把磁盘上的原始机器码映射到一个正在运行的进程.

<pre spellcheck="false">ood
</pre>

现在我们有了一个运行中的实例, 可以定位到这个二进制文件的 main 入口点.

<pre spellcheck="false">s main
</pre>

让我们按下面的方式做一次初步检查.

<pre spellcheck="false">v
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1606325530734.jpg"/></div>

你可以右键点击并 __在新标签页中打开图片 __以获得放大的视图.

请记住, 磁盘上的可执行文件与它被映射之后驻留的样子是不同的. 它待在磁盘上时称为未映射. 我们会在本课最后看这一点. 现在我们看到的是映射后的版本, 如你所见, 它是我们稍后要检查的映射代码的一个偏移.

你注意到你的映射内存值和我的不一样吗? 这是因为 ALSR.

地址空间布局随机化 (Address Space Layout Randomization, ASLR) 是操作系统中使用的一种安全技术, 最早于 2001 年实现. 当前所有主流操作系统 (iOS, Android, Windows, macOS 和 Linux) 的各个版本都具备 ASLR 保护.

ASLR 主要用于防范缓冲区溢出攻击. 在缓冲区溢出中, 攻击者先用一个函数能承受的尽可能多的垃圾数据把它灌满, 随后再跟上恶意的载荷.

我们注意到, 在我的映射内存中, 地址 _0x55629cab48_ 处就是我们的字符串_ "Hello World!"_. 如我们讨论过的, 你的偏移量会不同, 但会找到相同的结果.

让我们按下面的方式回到控制台窗口.

<pre spellcheck="false">q
</pre>

让我们验证一下最初的分析.

<pre spellcheck="false">[0x55629ca9e4]&gt; ps @0x55629cab48
Hello World!
[0x55629ca9e4]&gt;
</pre>

可以看到事实确实如此: 在映射内存地址 _0x55629cab48_ 处, 我们看到的就是字符串 _"Hello World!"_.

我们再来看看十六进制视图, 这样就能看到并更好地理解机器码层面发生了什么.

<pre spellcheck="false">px @0x55629cab48
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1606325962588.jpg"/></div>

我们看到了 "Hello World!" 字符串, 也能再次看到它从映射内存地址 0x55629cab48 开始存在.

我们看到机器码指令长 16 个字节, 也就是 64 位, 可以看到第一列以 _48_ 开始, 以 _00_ 结束.

我们必须弄明白几件关键的事情, 这非常重要. 第一, 一个十六进制数字宽 4 位, 也就是一个 nibble, 或者说半个字节. 在我们这个例子里, _4_ 是字节的一半, _8_ 是字节的另一半. 两者合起来构成一个字节, 在我们的例子里就是一个合法的 ascii 字符编码.

我们去看看在线 ascii 表.

<iframe allowfullscreen="true" class="center lazy-load" data-delayed-url="https://www.linkedin.com/embeds/publishingEmbed.html?articleId=7387163987651632632" frameborder="0" height="104" src="about:blank" title="ASCII Table and Description" width="744"></iframe>

第二, 我们需要理解这段机器码翻译过来是什么. 让我们查一下十六进制的 _48_ 是什么. 可以看到它是大写字母 'H'. 这完全对得上, 正如你在上面图片最右列看到的那样, 那里有个 0, 它下面是字母 H.

显然十六进制的 _65_ 就是 ___'e'___, 以此类推. 既然你已经对自己在看什么有了基本的理解, 剩下的你可以自己推出来.

现在我们在 main 上定义一个断点并执行这个二进制文件, 以验证当我们从 main 继续执行时, 它确实会把 _"Hello World"_ 打印到 stdout.

<pre spellcheck="false">[0x55629ca9e4]&gt; db 0x55629ca9e4
[0x55629ca9e4]&gt;
</pre>

我们继续执行, 验证一下我们的假设. 首先继续运行并在 main 上中断.

<pre spellcheck="false">[0x55629ca9e4]&gt; dc
hit breakpoint at: 0x55629ca9e4
[0x55629ca9e4]&gt;
</pre>

现在我们再次继续, 由于没有其他断点, 执行会就此结束, 我们再去 stdout 里验证结果.

<pre spellcheck="false">[0x55629ca9e4]&gt; dc
Hello World!
(59575) Process exited with status=0x0
[0x7fb146cb8c]&gt;
</pre>

让我们退出 Radare2.

<pre spellcheck="false">q
y
y
</pre>

让我们再次运行 Radare2, 这次不运行这个二进制文件, 只是看看磁盘上未映射的二进制文件.

<pre spellcheck="false">radare2 ./0x01_asm_64_helloworld
</pre>

让我们自动分析.

<pre spellcheck="false">aaa
</pre>

让我们定位到 main.

<pre spellcheck="false">s main
</pre>

然后查看.

<pre spellcheck="false">v
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1606327203401.jpg"/></div>

你可以右键点击并 __在新标签页中打开图片 __以获得放大的视图.

请注意, 这次 _"Hello World!"_ 位于未映射的内存地址 _0xb48_. 你会注意到, 当你运行这个二进制文件时, 可执行文件里这个值带有偏移, 但它的最低有效字节是十六进制的 _48_.

希望这节 Lesson 能帮助你理解 64 位 ARM 汇编的基础, 以及如何正确地逆向它.

在下一节 Lesson 中, 我们将修改这个值.