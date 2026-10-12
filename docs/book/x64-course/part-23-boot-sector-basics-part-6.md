## Part 23 - 引导扇区基础 \[Part 6\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

本周我们重点看如何使用 QEMU 这个模拟器来引导我们那个简单的新 OS.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1547804344026.jpg"/></div>

输入上面的命令来获取专门用于 x86 系统的 qemu.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1547804375264.jpg"/></div>

用我们的二进制文件运行这个模拟器.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1547804407713.png"/></div>

你会看到下面的内容. 记住它除了一个无限循环跳转之外什么也不做, 这一点我们在前面的课程里详细讨论过. 不过这是你能创建出来的最基础的 x86 OS.

它只是查找我们上周讲过的那个签名 (如果这里说不通, 请复习上周的课), 如果它正好是 200h 字节, 并且被放在引导介质的第一扇区, 这个过程就会成功.

如果你有兴趣, 不同的架构有不同的模拟器.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1547804592522.jpg"/></div>

下周我们会讨论内存寻址 (memory addressing), 这样我们就能在我们这个简单的 os 里搭建一个栈了.