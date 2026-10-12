## Part 30 - x64 汇编 \[Part 4\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

今天我们要用 x64 汇编语言编写我们那个简单的 "hello world" 程序.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1552041593157.png"/></div>

我们只是在 __.data __段里创建了一个字符串, 并在这个语句的末尾加上一个回车字符. 然后我们执行一个简单的 write 调用, 它利用 OS 的中断向量表把我们的字符串输出到标准输出也就是终端里.

我们会在下面编译并运行:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1552041719716.jpg"/></div>

如我们所见, "__Hello World__!" 已经被回显到终端里. 下周我们会在 GDB 里调试这个简单的程序.