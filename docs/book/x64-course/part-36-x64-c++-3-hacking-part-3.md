## Part 36 - x64 C++ 3 修改 \[Part 3\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

我们回顾一下代码:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1564757193950.jpg"/></div>

编译:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1564758303402.jpg"/></div>

运行:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1564757239511.jpg"/></div>

记住上面这一行, 待会我们要拿它和被修改过的二进制文件做对比.

我们以写模式打开这个二进制文件, 直接分析它.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1564757311281.jpg"/></div>

好, 这里信息量很大, 我们拆开来看. 首先, 输入 '__r2 -w ./1__' 以写模式打开 Radare 2, 然后用 '__aaa__' 命令分析这个二进制文件. 接着用 '__s sym.main__' 定位到二进制的 main 例程, 也就是我们的入口点. 最后执行 '__pdf__' 命令反汇编这个二进制文件.

我们看到所谓的序言, 把栈基址指针&nbsp;__rbp__&nbsp;压入栈. 然后把&nbsp;__rsp__&nbsp;移到&nbsp;__rbp__&nbsp;里妥善保存, 再在栈上预留&nbsp;__0x10__&nbsp;个十六进制字节, 也就是 16 个十进制字节, 给我们的字符串腾地方.

如果这些你完全看不懂, 请回到教程系列的开头复习基础汇编和寄存器, 因为在我们继续往下走之前, 你务必理解这些内容.

我们可以清楚地看到 '__Hello World\\n__' 这个 qword 位于内存地址&nbsp;__0x2005__&nbsp;处, 然后还能看到我们调用 C++ 的输出流库&nbsp;__cout__&nbsp;, 把字符串显示到终端.

我们检查一下&nbsp;__0x2005__&nbsp;, 确认字符串确实在那个位置:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1564757423920.jpg"/></div>

现在是修改时间!

我们把这个值改成类似这样:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1564757454631.jpg"/></div>

现在我们看看内存地址 @ __0x2005__ 处的内容变成了什么!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1564757528202.jpg"/></div>

砰! 可以看到我们已经改掉了这个值, 当我们退出 Radare 2 时, 它会把改动写回去, 照这样修改我们的二进制文件.,

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1564757568026.jpg"/></div>

可以看到, 我们把这个二进制文件改掉了! 这非常基础, 但现在你已经对 C++ 二进制的逆向工程有了入门级的理解.

下周我们会继续 C 语言的旅程, 一步一步做逆向工程.