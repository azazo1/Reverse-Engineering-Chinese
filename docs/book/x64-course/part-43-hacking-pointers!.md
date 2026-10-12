## Part 43 - 修改指针!

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

我们已经走到了路的尽头. 这是 x64 系列的最后一个视频. 最后一个主题是指针.

什么是指针? 我们先从一个例子开始.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1567286671465.jpg"/></div>

指针不过是一个内存地址. 编译之后我们就会清楚地看到 lottery\_number 位于映射内存中的什么位置 (这是一个运行中的例子, 与我们那些未映射的 Radare 例子不同).

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1567286745307.jpg"/></div>

我们给这个例子加上一个真正的指针:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1567287725406.jpg"/></div>

我们看到的是同一个值:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1567287787090.jpg"/></div>

我们再多做些实验:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1567288396508.jpg"/></div>

我们看到指针地址指向了一个新地址:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1567288456995.jpg"/></div>

记住, 指针是其他变量的内存地址. 我们换一种方式来看:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1567289354121.jpg"/></div>

我们来编译:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1567289368216.jpg"/></div>

我们通过下面的做法来解引用 (dereference):

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1567289646596.jpg"/></div>

然后我们编译:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1567289657671.jpg"/></div>

可以看到解引用得到的值等于 777.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1567290644015.jpg"/></div>

我们来看一个使用数组的例子:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1567290665083.jpg"/></div>

我们来调试:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1567290786481.jpg"/></div>

然后我们反汇编:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1567290800965.png"/></div>

我们来修改!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1567292294462.jpg"/></div>

我们重新检查这个二进制文件:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1567292311387.png"/></div>

可以看到我们把 3 这个值改成了 6.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1567292376880.jpg"/></div>

可以看到我们成功完成了修改.

希望这些年来, 通过这实实在在数百篇 x86, ARM 和 x64 教程, 你已经掌握了基本知识, 懂得如何通过理解敌人的运作方式来行善, 保护关键基础设施不被恶意之手染指. 去做善事吧!

  