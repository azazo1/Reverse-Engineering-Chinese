## Part 38 - ASM 调试 6 \[CMOV 指令\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们重新看一些源代码.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520234974923.jpg"/></div>

让我们在 0x08048092 处下断点, 它对应第 31 行. 让我们用 r 来运行, 然后输入 __print $ebx__. 可以看到值是 7.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520240729383.jpg"/></div>

好, 现在让我们在 0x080480b1 处下断点, 它对应第 46 行. 记住, 当我们查看 __answer__ 的值时, 它已经被转换成对应的可打印 ascii 字符, 所以要看到 '7' 这个值, 你要输入 __x/1c &amp;answer__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520498895208.jpg"/></div>

期待下周与大家再见, 届时我们会深入修改我们的第六个汇编程序!