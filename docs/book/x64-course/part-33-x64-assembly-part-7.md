## Part 33 - x64 汇编 \[Part 7\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们再一次回顾我们的源代码.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1553853169947.jpg"/></div>

让我们编译...

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1553853185424.jpg"/></div>

如我们之前所见, 它输出了我们的字符串.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1553853213341.jpg"/></div>

我们调试, 看到这个字符串被移动到 __0x6000d8__, 然后是 __RSI__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1553853259407.jpg"/></div>

只是为了确认, 我们可以在前面提到的地址处看到这个字符串. 现在来点好玩的 :)...

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1553853296959.jpg"/></div>

这里我们演示了我们有能力直接在内存里修改并重新定义这个字符串. 我们只是设置了一个 char 字节长度, 并设置了一个新字符串.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1553853373225.jpg"/></div>

如我们所见, 我们成功地改掉了内存里的这个字符串.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1553853413835.jpg"/></div>

我们继续, 单步走过这个二进制文件, 看到我们的修改延续到了 __RSI__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1553853461475.jpg"/></div>

最后我们看到, 当我们运行这个二进制文件时, 我们成功地修改了它的行为. 这是一个非常简单的例子, 不过它展示了在这个层面上真正理解汇编的力量. GUI 调试器工具也能提供这种功能, 不过我喜欢用命令行工具, 这样它们在任何环境里都能用.

这些工具的目的是让你理解这件事是怎么做的, 以及当你在专业地进行实时逆向时该关注什么. 你需要理解攻击者如何修改内存和/或指令. 我们需要更多专业的逆向工程师来帮助保护全世界的基础设施, 也希望这些教程能激励你走向这样的职业.