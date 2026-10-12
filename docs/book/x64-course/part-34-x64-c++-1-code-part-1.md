## Part 34 - x64 C++ 1 代码 \[Part 1\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

今天我们从 C++ 语言开始做逆向工程 (Reverse Engineering). 绝大多数恶意软件都是用 C++ 写的, 在接下来的几个月里, 走一遍简单的代码示例, 并在调试器里把它们拆解开来, 能让你真正上手, 学会真正的逆向工程.

接下来我们会使用 Kali Linux 搭配 Radare 2. 你可以装一个 VirtualBox, 下载 Kali Linux x64 虚拟机映像来跟着做.

我们从一个 C++ 1 的代码示例开始:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1561023464535.jpg"/></div>

这里我们只是创建了一个 main 函数, 用 C++ 的输出流库把 "Hello World" 这段文本输出到终端, 并在末尾带一个换行. 我们来编译并链接:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1561023530059.jpg"/></div>

我们在终端里运行一下:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1561023550876.jpg"/></div>

可以看到, "Hello World" 成功地回显到了终端.

下周我们会介绍 Radare 2, 调试这段代码, 看看它在 x64 汇编里是什么样子.