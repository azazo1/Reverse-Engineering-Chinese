## Part 20 - 指令代码处理

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

CPU 会读取存储在内存中的指令代码, 因为每个代码集可以包含一或若干个字节的信息, 用来引导处理器执行某个非常具体的任务. 当每条指令代码从内存中读入时, 该指令代码所需的任何数据也会被存储并读入内存.

请记住, 存放指令代码的内存与存放 CPU 所用数据的字节没有任何不同, 并且会使用特殊的指针来帮助 CPU 跟踪数据在内存中的位置以及指令代码存放在哪里.

数据指针帮助 CPU 跟踪内存中数据区从哪里开始, 也就是栈. 当新的数据元素被放入栈时, 栈指针在内存中向下移动; 当从栈中读取数据时, 栈指针在内存中向上移动. 如果你不理解这个概念, 请回顾 Part 15 - 栈.

指令指针用来帮助 CPU 跟踪哪些指令代码已经被处理过, 以及接下来要处理哪段代码. 如果你不理解这个概念, 请回顾 Part 12 - 指令指针寄存器.

每一条指令代码都必须包含一个操作码 (opcode), 它定义了 CPU 要执行的基本功能或任务, 操作码的长度在 1 到 3 个字节之间, 并唯一地定义所执行的功能.

我们先来看一个名为 test.c 的简单 C 程序, 作为开始.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520446165914.jpg"/></div>

我们所做的就是创建一个 integer 类型的 main 函数, 它有一个 void 参数, 并返回 0. 这个程序所做的只是简单地退出操作系统.

我们来编译并运行这个程序.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520147571659.jpg"/></div>

我们使用 objdump 工具在其中找到 main 函数.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520190277217.jpg"/></div>

下面是运行上述命令会得到的结果片段.&nbsp;以下是 main 函数的内容.&nbsp;请记住, 下面的内容是 Intel 语法, 正如我们在上一节教程中谈到的.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520446166055.jpg"/></div>

最左边是对应的内存地址. 中间是操作码, 最后右边是对应的 Intel 语法汇编语言.

为了简单起见, 我们来看内存地址 __80483de__, 在那里我们看到操作码 __b8 00 00 00 00__. 可以看到 __b8__ 操作码对应右边那条 __mov eax, 0x0__ 指令. 接下来的那串 00 00 00 00 表示 4 个字节的值 0. 我们看到 __mov eax, 0x0__, 因此值 0 被移入 eax, 也就代表了上面的代码. 请记住, IA-32 平台使用我们所说的小端 (little-endian) 记法, 也就是说从右往左读时, 数值较低的字节排在前面.

我想确保你把这一点理清楚了, 所以我们假设上面的值是:

__mov eax, 0x1__

在这种情况下, 对应的操作码会是:

__b8 01 00 00 00__

如果你感到困惑, 没关系. 还记得小端吗? 请记住 eax 是 32 位宽, 也就是 4 个字节 (8 位 = 1 字节). 这些值按相反的顺序排列, 因此我们看到上面那种表示.

期待下周与大家再见, 届时我们会深入探讨如何编译一个程序的细节.