## Part 15 - 调试 ADD

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们回顾下面这个 ADD 示例:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520244359354.jpg"/></div>

我们再次看到, 我们把十进制 __67__ 移入 __r1__, 把十进制 __53__ 移入 __r2__. 然后我们把 __r1 __和 __r2__ 相加, 并把结果放入 __r0__.

让我们编译:

__as -o add.o add.s__

__ld -o add add.o__

让我们把它放进 GDB 中调试:

__gdb -q add__

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520594706178.jpg"/></div>

我们可以看到, 当我们用 b__ \_start__ 命令在 start 处下断点, 再 __r__, run 时, 就能看到反汇编. 如果你执行 __i r__, 就能看到寄存器信息 (info registers), 这时会注意到我们的 __cpsr__ 是 __0x10__.

当我们再次单步执行并查看寄存器信息:

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520213487826.jpg"/></div>

我们注意到 __0x43__ 十六进制或者说 __67__ 十进制被放入 __r1__. 我们还注意到标志位没有变化 (__cpsr 0x10__).

让我们再次单步执行并查看寄存器信息:

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520594706126.jpg"/></div>

我们可以看到 __r0 __现在保存着 __0x78__ 十六进制或者说 __120__ 十进制. 我们成功地看到了 add 指令在起作用, 并且再次注意到标志寄存器 (__cpsr__) 在这次操作中没有改变.

下周我们将深入修改 ADD.

  