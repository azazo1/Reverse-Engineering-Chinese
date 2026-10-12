## Part 25 - 引导扇区基础 \[Part 8\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

今天我们把所有部分拼到一起. 我们会创建自己的定制 OS, 它除了启动, 设置一个视频模式, 然后只接受控制台里的数字字符之外什么也不做. 这是引导扇区基础这个小系列里的最后一节教程.

让我们来看看我们的代码:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1549024795636.png"/></div>

我们要做的第一件事是移动到地址 0x7c00 处引导扇区代码的可编程区域. 然后我们设置栈基址, 确定栈所在的区域, 并把基址指针设置到栈指针里.

接着我们调用视频模式函数, 在里面设置一个 640x200 的灰度控制台. 然后我们调用获取字符输入的函数, 它只允许数字 0 到 9, 如你所见 0x30 是 0 的十六进制 ascii 值, 0x39 是 9 的十六进制 ascii 值. 如果用户在控制台里输入任何其他内容, 那么实际上什么都不会进入控制台. 这就是你在汇编语言里拥有的绝对控制权.

让我们编译并运行:

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1549025055903.jpg"/></div>

然后我们就能看到 qemu 控制台:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1549025085922.png"/></div>

如你所见, 在我们的 OS 里我只能输入数字字符. 你自己也试试. 把代码写出来, 在 qemu 编辑器里编译并运行. 如果你还没装 qemu, 我在前面两节教程里详细讲了怎么安装它.

花点时间好好回顾我在这里做的事, 因为理解你的计算机在进入 32 位再到 64 位模式之前是这样启动的, 这一点至关重要.

下周我们只讨论一下高层概念, 也就是你的计算机是如何过渡到 64 位操作系统的.