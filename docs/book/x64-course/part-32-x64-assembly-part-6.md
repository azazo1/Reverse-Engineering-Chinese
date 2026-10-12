## Part 32 - x64 汇编 \[Part 6\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们回顾一下我们的代码.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1553248751760.png"/></div>

编译...

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1553248766003.jpg"/></div>

调试...

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1553248783477.jpg"/></div>

让我们看看内存地址 0x6000d8 里有什么.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1553248844375.jpg"/></div>

如我们所见, 带回车字符的 "__Hello World__" 随后会被移动到我们的 __RSI__ 寄存器里.

下周我们会更仔细地看看这个.