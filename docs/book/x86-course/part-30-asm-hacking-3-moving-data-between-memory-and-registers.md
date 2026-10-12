## Part 30 - ASM 修改 3 \[在内存与寄存器之间移动数据\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们来修改!&nbsp;

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520588657073.jpg"/></div>

具体来说, 和之前一样, 我们会把常量整数里十进制 10 这个值移入 ECX.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520171419386.jpg"/></div>

我们以安静模式打开 GDB, 在 \_start 处下断点, 然后按照上面的命令运行.&nbsp;

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520145740732.jpg"/></div>

如我们所见, 当我们 info registers 时, ECX 的值是 0. 让我们来一个 si, 再来一个 si.&nbsp;

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520198737146.jpg"/></div>

如你所见, ECX 的值和上一节 Lesson 里一样是十进制 10, 也就是十六进制 0xa, 现在我们把这个值修改成别的.

让我们 __set $ecx = 1337 __然后执行一个 i r.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520588657130.jpg"/></div>

如你清楚看到的, 我们已经把 ECX 的值修改成了十六进制 0x539, 也就是十进制 1337.

正如我在整个系列中一直说的. 这些 Lesson 都是很小的例子, 目的是让你形成牢固的肌肉记忆, 知道如何应对各种情况下的修改, 从而最终完全掌握对处理器的控制.

期待下周与大家再见, 届时我们会开始创建第四个汇编程序!