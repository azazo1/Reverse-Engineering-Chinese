## Part 15: 栈

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

函数是软件开发中最基本的特性. 函数让你能够以合乎逻辑的方式组织代码, 去执行指定的任务. 在这个阶段, 你是否理解函数如何工作并不关键, 重要的只是要明白: 当我们开始学习开发时, 我们希望尽量减少重复, 办法是使用可以被多次调用的函数, 而不是让重复的代码占用过多的内存.

当程序开始执行时, 会为程序预留一块连续的内存区域, 这块区域叫作栈.

栈指针是一个保存栈顶位置的寄存器. 栈指针保存的是最小的地址, 举例来说可以是 0x00001000, 这样一来, 任何小于 0x00001000 的地址都被视为垃圾, 而任何大于 0x00001000 的地址都被视为有效.

上面这个地址是随机的, 并非绝对不变, 不同程序里栈指针所在的位置会有所不同. 让我们从抽象的角度看看栈是什么样子:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520235829712.jpg"/></div>

上面这张图是我希望你牢记在心的, 因为那才是内存中实际发生的事情. 接下来的一系列图会展示与上面相反的情形.

在下面的图中你会看到栈在向上增长, 然而在现实中它是从高地址内存向低地址内存向下增长的.

在下面的 addMe 示例中, 在 main 函数的断点处检查内存时, 栈指针 (ESP) 显示为 0xffffd050. 当程序从 main 调用 addMe 函数时, ESP 现在是 0xffffd030, 这在内存中是更低的位置. 因此, 尽管图示显示它向上, 栈实际上是向下增长的. 只要记住, 下面图中的箭头指向上方时, 它们实际上指向的是更低的内存地址.

栈底是栈中最大的有效地址, 位于地址较大的区域, 也就是内存模型的顶部. 这可能会让人困惑, 因为栈底在内存中的位置更高. 栈在内存中向下增长, 在我们继续往下讲之前, 你务必现在就理解这一点.

栈界限是栈中最小的有效地址. 如果栈指针变得比这个地址还小, 就发生了栈溢出 (stack overflow), 它可能破坏程序, 让攻击者得以控制系统. 恶意软件会试图利用栈溢出. 近来, 现代操作系统中内置了一些防护措施, 试图阻止这种情况发生.

栈上有两种操作, 即 push 和 pop. 你可以通过把栈指针设置为一个更小的值来压入一个或多个寄存器. 通常的做法是减去要压入栈的寄存器数量的四倍, 然后把寄存器复制到栈上.

你可以通过把数据从栈复制到寄存器, 然后给栈指针加上一个值, 来弹出一个或多个寄存器. 通常的做法是加上要从栈上弹出的寄存器数量的四倍.

让我们看看栈是如何用来实现函数的. 每一次函数调用都会为这个函数预留栈中的一块区域. 这被称为栈帧 (stack frame).

让我们看看在第 12 节教程中创建的 C 程序, 检查一下 main 函数是什么样子:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520622740099.jpg"/></div>

这里我们看到两个函数. 第一个是 unreachableFunction, 它在正常情况下永远不会执行; 我们还看到 main 函数, 它总是第一个被调用到栈上的函数.

当我们运行这个程序时, 栈看起来是这样的:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520622738609.jpg"/></div>

上面我们可以看到 int main(void) 的栈帧.&nbsp;它也被称为活动记录 (activation record).&nbsp;只要函数已经开始但尚未完成, 就存在一个栈帧.&nbsp;例如, 在 int main(void) 的函数体内部有一次对 int addMe(int a, int b) 的调用, 它接受两个参数 a 和 b.&nbsp;int main(void) 中需要有汇编语言代码, 把 int addMe(int a, int b) 的参数压入栈.&nbsp;让我们检查一些代码.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520231875596.jpg"/></div>

当我们编译并运行这个程序时, 会看到数值 5 像这样被打印出来:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520622737902.jpg"/></div>

很简单, int main(void) 会先调用 int addMe(int a, int b), 它像这样被放到栈上:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520144504701.jpg"/></div>

你可以看到, 通过把参数放到栈上, __int main(void)__ 的栈帧变大了. 我们还为返回值预留了空间, 该返回值由 __int addMe(int a, int b)__ 计算得出; 当函数返回时, __int main(void)__ 中的返回值被恢复, 执行在 __int main(void)__ 中继续, 直到它结束.

一旦我们进入 __int addMe(int a, int b)__ 的指令, 这个函数可能需要局部变量, 因此它需要在栈上压入一些空间, 看起来像这样:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520622739277.jpg"/></div>

__int addMe(int a, int b)__ 能够访问从 __int main(void)__ 传给它的参数, 因为 __int main(void)__ 中的代码完全按照 __int addMe(int a, int b)__ 的预期来放置这些参数.&nbsp;

FP 是帧指针 (frame pointer), 它指向的位置正是 __int addMe(int a, int b)__ 为 int __addMe(int a, int b)__ 自己的局部变量移动栈指针或 SP 之前, 栈指针所在的地方.

当一个函数在运行过程中很可能多次移动栈指针时, 使用帧指针就非常必要. 其思路是在 __int addMe(int a, int b)__ 的栈帧存在期间让帧指针保持固定. 与此同时, 栈指针则可以改变其值.

我们可以用帧指针来计算参数以及局部变量在内存中的位置. 由于它不会移动, 这些位置的计算结果应该是相对帧指针的某个固定偏移.

当该退出 __int addMe(int a, int b)__ 时, 栈指针被设置为帧指针所在的位置, 这就把 __int addMe(int a, int b)__ 的栈帧弹出了.

总而言之, 栈是一块特殊的内存区域, 用来存放包括 main 在内的每个函数所创建的临时变量. 栈是一种 LIFO (last in, first out, 后进先出) 数据结构, 由 CPU 紧密地管理和优化. 每当函数声明一个新变量, 它就被压入栈. 每当函数退出, 由该函数压入栈的所有变量都会被释放或删除. 一旦某个栈变量被释放, 那块内存区域就可以供其他栈变量使用.

用栈来存放变量的好处是内存由系统为你管理. 你不必手动分配内存, 也不必手动释放. CPU 管理并组织栈内存的效率非常高, 速度也非常快.

至关重要的一点是, 你要明白当函数退出时, 它的所有变量都会从栈上弹出并永远丢失. 栈变量是局部的. 随着函数压入和弹出局部变量, 栈会增长和收缩.

我能看到你已经晕头转向了. 请记住, 这些话题很复杂, 并且会在今后的教程中继续展开. 我们一直在处理许多令人困惑的话题, 比如寄存器, 内存, 现在又加上栈, 这可能会让人吃不消. 如果你有任何疑问, 请在下面留言, 我会帮你更好地理解这套框架.

在下一节教程中, 我们将讨论堆.