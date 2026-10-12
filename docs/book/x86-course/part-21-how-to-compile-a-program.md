## Part 21 - 如何编译一个程序

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们再次看看上周的 C 程序, 并更深入地研究我们是如何把那份源代码变成一个可执行文件的.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520461365362.jpg"/></div>

要在 C 中编译这个程序, 我们只需输入:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520190744251.jpg"/></div>

这一个步骤会创建 __exit.o__, 它是二进制目标文件, 还会创建 __exit__, 它是二进制可执行文件.

如果我们想把这份 C 源代码转换成汇编, 就需要按下面的方式使用 GNU 编译器. 我们先在终端里运行下面这条命令:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520193559694.jpg"/></div>

我们从 -S 开关说起.&nbsp;-S 开关会生成对应的 AT&amp;T 语法汇编源代码.&nbsp;-m32 会生成 32 位可执行文件, 而 -O0 会告诉编译器在编译这个二进制文件时使用多少优化.&nbsp;那是大写字母 O 和数字 0.&nbsp;此处的数字 0 表示不做优化, 也就是说它处于最便于人阅读的指令形态.&nbsp;如果你把它换成 1, 2 或 3, 优化程度会随数值增大而提高.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520230747774.jpg"/></div>

上面这一步会生成 exit.s, 也就是我们上面提到的等价汇编语言源代码.

接着我们需要把汇编源代码编译成二进制目标文件, 这会生成一个 __exit.o__ 文件.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520191376275.jpg"/></div>

最后我们需要用链接器从二进制目标文件生成真正的二进制可执行代码, 它会创建一个名为 exit 的可执行文件.&nbsp;

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520231891958.jpg"/></div>

上周我们在一个名为 objdump 的程序里检查了可执行文件 exit, 并查看了 main 区域, 看到的是下面这些内容, 只不过这一次我们会使用 AT&amp;T 汇编语言语法:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520461365373.jpg"/></div>

上面这条命令会生成下面这样的输出:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520142510413.jpg"/></div>

让我们在调试器里检查这段代码.&nbsp;我们启动 GDB, 也就是 GNU 调试器, 先输入 l 列出源代码, 然后在 main 上设置一个断点并运行程序.&nbsp;最后我们反汇编并查看下面的输出:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520461365667.jpg"/></div>

在上面这三次检查中, 你基本上会看到同一组指令, 至于其中究竟发生了什么, 我们会在后续教程中更深入地看看.

在这个教程系列到目前为止的内容里, 我们一直在看 Intel 语法的汇编语言. 接下来我们会把重点转向 AT&amp;T 语法, 正如我上面所说, 这是 Linux 上 GNU 汇编器与 GNU 调试器所使用的原生语法.

你会看到的最大区别是, 在 AT&amp;T 语法中, 源和目标的位置是反过来的.

AT&amp;T 语法 : __movl %esp, %ebp__ \[这表示把 esp 移入 ebp.\]

Intel 语法 : __mov esp, ebp__ \[这表示把 ebp 移入 esp.\]

你还会看到一些别的差异, 因为 AT&amp;T 还用了另外一些不同的写法, 我们会在后面的教程中讲到.

如果我们想写一个纯汇编代码的程序来完成上面同样的事情, 我们会输入:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520248174155.jpg"/></div>

要编译它, 我们会使用 GAS 汇编器和链接器:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520170234389.jpg"/></div>

要在 Linux 中运行任何可执行文件, 你输入 ./ 以及这个二进制可执行文件的名字. 在这里我们输入 ./exit 然后按回车. 这么做之后什么也没有发生. 这很好, 因为我们所做的不过是创建了一个向操作系统退出返回的程序.

期待下周与大家再见, 届时我们会深入更多汇编代码!