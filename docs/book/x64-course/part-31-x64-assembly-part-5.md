## Part 31 - x64 汇编 \[Part 5\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

这节课会比大多数课稍长一些, 不过重要的是你们都要花时间真正动手写代码, 练习下面讨论的这些主题. 让我们回顾一下我们的代码:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1552642996672.jpg"/></div>

让我们编译并运行:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1552643024086.jpg"/></div>

如我们上周所见, 我们成功地创建了我们那个简单的 "Hello World" 程序.

在之前的课程里我提到过 x64 寄存器组, 不过我会用这张表再复习一遍:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1552643419886.jpg"/></div>

在之前的课程里我们讲过这些寄存器的基本功能都包含什么, 不过理解寄存器从 64 位到 8 位的各个切片很重要. 寄存器保存的是临时内存. 这是这里的关键要点.

在基于 Linux 的汇编里我们有三个段, 它们包括:

__.data = 由数据定义组成__

__.bss = 由变量数据分配组成__

__.text = 实际的代码__

在上面的例子里我们用了 __text__ 这个标签, 不要把它和 __.text __段混淆. 我们的编译器会取走我们所有的标签, 确定一个实际映射的内存位置, 并在实际的二进制文件里把每个标签替换成那个内存位置.

理解每个字符串字符的长度是一个字节, 并且用两个十六进制数字表示, 这一点很重要. 你可以上网搜一张 ascii 表, 它会把所有这些值都列出来. 每个十六进制数字是一个半字节 (nibble), 也就是 4 位长. 例如我们的 '__H__' 是 __0x48__, '__e__' 是 __0x65__. 让我们在十六进制编辑器里看看我们的二进制文件, 以便说明这一点.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1552644071133.jpg"/></div>

在上周课程的评论里, Aaron 指出了非常重要的一点, 当你对比操作系统里的汇编与固件里的汇编 (比如我们前几节课为操作系统写的那段代码) 时, 理解这一点非常关键.

上周 Aaron 在评论里仔细指出, SYSCALL 完全取决于操作系统. 系统调用会因 OS 不同而不同, 因为每个 OS 有不同的内核 (Kernel), 而且各自有自己的一套向量中断表, 表里的每一项都关联着一个 ID 以及对应的编号值.

SYSCALL 不过是二进制文件向相应的内核请求一项服务, 而这项服务会接收参数或者一组输入. 在 x64 里理解系统调用的参数或者输入对应特定的寄存器很重要:

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1552644487957.jpg"/></div>

传统 linux 内核里有 328 个 SYSCALL. 如我们在上面的代码里所见, 我们同时用到了 __SYS\_WRITE __和 __SYS\_EXIT__. 我们来演示一下:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1552644760322.jpg"/></div>

请花点时间看看上面我们的代码, 理解它是怎么工作的. 在 __SYS\_WRITE__ 里我们把 __1__ 加载到 __RAX__, 也就是我们的 SYSCALL. 我们把 __1__ 加载到 __RDI__, 这是我们的第一个参数, 它代表我们的标准输出 (0 = 标准输入 &amp; 2 = 标准错误). 我们的第二个参数被加载到 __RSI__, 它对应我们的 __text__ 标签, 编译之后它会有实际的内存地址, 你会在调试器里看到这一点. 最后我们的第三个参数保存字符串长度, 在我们的例子里是 __13__, 被加载到 __RDX__. 作为一个练习, 我要你写出来 __SYS\_EXIT__ 是如何做同样的事, 记住那里只有 1 个参数. 在继续往下之前请务必回顾上面的代码, 把它彻底弄明白!

此外我们还有 __\_start __标签, 相应的操作系统会去找它, 否则当它试图寻找我们代码的入口点时会抛出错误. __global __声明告诉链接器数据的实际地址.

下周我们会在 GDB 里调试这个二进制文件.

  