## Part 39 - ASM 修改 6 \[CMOV 指令\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

我们把二进制文件加载到 gdb 中.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520490808741.jpg"/></div>

现在让我们运行这个二进制文件. 我们看到最小值是 7, 这是符合预期的. 本教程中最后一点指令内容将教你如何跳转到执行流程里你自行选定的任何位置.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520241582923.jpg"/></div>

我们 __set $eip = 0x080480dd__, 也就是退出例程. 现在我们看到, 当我们在 \_start 处下断点时, 它绕过了 nop 指令之后的所有代码. 现在你可以在调试器里用这条命令, 跳转到任何二进制文件内部的任何位置.

期待下周与大家再见, 届时我们将结束这个教程系列.