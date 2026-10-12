## Part 19 - 引导扇区基础 \[Part 2\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

现在我们到了开始引入真实代码的阶段. 如果你没有在用的 Linux 桌面环境, 我建议你在 Windows 或 Mac 上装好 Virtualbox 和 Ubuntu. 我在下方有一个先前的教程会带你走完这个过程. 由于某些原因我无法嵌入链接, 所以请你直接把它复制粘贴到浏览器中.

__https://www.linkedin.com/pulse/assembly-language-basic-malware-reverse-engineering-kevin-m-thomas-16/ __

你还需要一个用于终端的文本编辑器. 我使用 VIM. 下面也有一个链接可以帮你把它配置好.

__https://www.linkedin.com/pulse/assembly-language-basic-malware-reverse-engineering-kevin-m-thomas-17/__

此外你还得安装 nasm, 只需输入:

__sudo apt-get install nasm__

NASM 是我们要使用的汇编器 (assembler), 我们会专注于 Intel 语法. 首先进入终端, 启动 Vim 并输入以下内容:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1545386856569.png"/></div>

记得输入 'i' 进入插入模式, 然后按 'esc' 和 'wq' 进入命令模式并保存你的文件.

上面这一行只是设置了一个无限循环, 除此之外什么也不做. 这里创建了 __loop __标签, 我们只是 __jmp__ 回到它自身. 这段代码本身可以编译, 但它无法在操作系统里运行, 因为它没有触发我们所说的魔数 (magic number), BIOS 正是靠它来认定这是你的引导扇区的结尾. 我们会在以后的课程中更详细地讨论这一点.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1545387039903.png"/></div>

我们输入上面的命令, 假设你在 vim 中把文件保存为 __bootsector.asm__. 这会生成一个二进制文件, 我们将在十六进制编辑器中查看它的内容. 十六进制编辑器是一种逐字节查看编译进文件中的数据的应用. 我们会看到上面的汇编指令最终会被翻译成它们的原始操作码值. 处理器只理解原始操作码, 也就是操作代码. 下面是一个标识操作码的表格链接. 我替你省去了查阅 Intel 数据集的工作, 因为它确实有几千页, 还有好几卷:

__http://ref.x86asm.net/coder64.html__

我们用 ghex 这样的十六进制编辑器打开我们的 bin 文件.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1545387311381.png"/></div>

我们看到 __EB FE__, 它们是十六进制字节, 每个字母是一个半字节 (nibble, 也就是 4 位或半个字节). __EB FE__ 一起构成两个完整字节. 请记住处理器从磁盘读取时采用反向的字节顺序, 因此 __FE __先被读到, 然后才是 __EB__. 这个过程称为小端序 (little endian), x64 处理器就是这样工作的.

如果你查看我给出链接的那个表格, 你会看到 __FE __ 表示 __INC__, 也就是加一. 这就是我们循环的值.

接下来你会发现 __EB__ 表示 __JMP__, 也就是我们上面那条跳转指令.

如果你是刚开始接触汇编, 这些信息量很大. 一步一步来, 在一个真实的 Linux 操作系统中跟着我一起做, 每学一节, 你对基础知识的理解都会更好.

下周我们会在这节课的基础上, 往我们的二进制文件里添加一些简单的数据.