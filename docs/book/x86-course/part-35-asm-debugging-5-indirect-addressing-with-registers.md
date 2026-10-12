## Part 35 - ASM 调试 5 \[用寄存器间接寻址\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

在我们的第五个程序里, 我们演示了如何用寄存器来操纵间接寻址.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520483251669.jpg"/></div>

我想先回答一个问题, 就是我为什么使用 AT&amp;T 语法. 在之前的 Lesson 里, 我给出了许多在 AT&amp;T 语法与 Intel 语法之间轻松来回转换的办法.

我故意选这条路, 是为了迫使你熟悉 x86 中最复杂的那种写法. 如果你对这种语法感到困惑, 请回顾之前的 Lesson, 因为我在那里详细讲了两种语法之间的差异.

让我们回顾一下. 我们会用 objdump 来拿一个已编译的二进制文件, 比如上一节 Lesson 里我们编译的那个, 并展示如何查看它的 Intel 源代码.

__objdump -d -M intel indirect\_addressing\_with\_registers | grep \_start.: -A24 __

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520148750030.jpg"/></div>

现在回到我们正常安排的节目.

让我们把二进制文件加载进 GDB, 在 \_start 处下断点, 单步执行几步, 然后查看 constants 标签里 11 个值中的 6 个.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520145698959.jpg"/></div>

接着我们把 constants 标签的内存地址移入 edi, 并把立即值十进制 25 移入数组的第二个索引. 这本质上是一次源代码层面的修改, 因为我们把原来的值 8 改成了 25.

如果你查看源代码, 会看到第 18 行, 我们在那里把值 1 加载进 edi. 记住这是第二个值, 因为数组是从 0 开始计数的.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520241367735.jpg"/></div>

你可以看到, 如前面解释的那样, 我们把十进制 8 改成了 25.

这是我们第一次接触汇编语言中的数组. 理解它们的工作方式至关重要, 因为你将来可能成为恶意软件分析师或逆向工程师, 需要查看由各种高级语言程序编译出来的数组的二进制文件.

在下一节 Lesson 里, 我们会在 GDB 中手动修改其中一个值. 记住, 我们将不得不用一个立即值覆盖真实内存地址里的内容. 乐趣才刚刚开始!

期待下周与大家再见, 届时我们会深入修改我们的第五个汇编程序!