## Part 36 - ASM 修改 5 \[用寄存器间接寻址\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们再次重新看一下源代码.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520173944761.jpg"/></div>

让我们再次把二进制文件加载进 GDB, 并在 \_start 处下断点.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520175535307.jpg"/></div>

看上面, 我们看到命令 print \*0x804909e. 可以看到它给出的值是十进制 5. 这个二进制文件在运行时会把这些值从 constants 标签放进各自对应的内存地址.

在这个例子里我们看到, 指向 0x804909e 的指针, 也就是 \*0x804909e, 保存着如上面所说的十进制 5. 一个整数保存 4 个字节的数据. 我们数组里的下一个值会存放在 0x80490a2. 这个内存位置保存的值是 8.

如果我们继续在数组里往前走, 就会移动 4 个字节到下一个值, 依此类推. 记住, x86 32 位汇编中的每个内存位置保存 4 个字节的数据.

让我们来修改!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520450492026.jpg"/></div>

在 \_start 处下断点并运行之后, 我们像上一节 Lesson 里那样查看了这个数组. 这里我们把 0x80490a2 处的值从十进制 8 修改成十进制 66, 可以看到我们成功地改变了数组中的一个元素.

这节 Lesson 对于理解数组最终如何存储在内存中, 以及如何操纵和修改它们非常重要. 如果你有任何问题, 请在下面的评论里提出.

期待下周与大家再见, 届时我们会深入编写我们的第六个汇编程序!