## Part 41 - 修改变量!

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

在 C 里我们有几种数据类型可以用来创建变量. 我会用几个简单的例子:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1566059490750.jpg"/></div>

我们编译并运行:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1566059504696.jpg"/></div>

好, 可以看到我们有一个 character, 一个 integer 和一个 double. 这些是 C 里最基本的数据类型, 我们像上面那样创建了一系列变量.

我们把这个二进制文件加载到 Radare 里:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1566059659639.jpg"/></div>

我们在 main 处反汇编:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1566059725847.png"/></div>

好, 很简单, 我们在顶部看到 3 个反向排列的变量声明, 分别是 __local\_1h __, 也就是我们的 __char a,__ __local\_8h__, 也就是我们的 __int b__, 以及 __local\_10h__, 也就是我们的 __double c__. 你还能看到 __rbp__ 基址指针在为这些变量分配空间. 这是调试器显示在上方的一段不错的伪代码.

好, 跟紧我!

在内存的 __0x0000113d __处, 我们看到指令 __mov byte \[local1\_h\], 0x61__, 在我们的 ascii 表里它对应小写的 '__a'__. 我们知道 \[local1\_h\] 并不是真实的代码, 不过底层实际发生的是: 正如我们上面看到的, 这些变量以相反的顺序被压入栈. 因此, 如果我们把代码改成类似 __mov byte \[rbp-0x1\], 0x62 __这样的形式, 你觉得会发生什么? 很简单, 我们知道在映射内存地址 __0x0000113d__ 处, 实际发生的其实是 __mov byte \[rbp-0x1\], 0x61__. 说白了, 我们刚才做的就是把自己 '__a__' 的值改成了 '__b__'. 希望这样讲你能明白.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1566060689050.jpg"/></div>

现在我们重新看一下我们的二进制文件:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1566060755864.png"/></div>

可以清楚地看到, 在内存地址 __0x0000113d __处, 我们看到的确实是 '__b__'. 这一部分我们成功改掉了.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1566060872094.jpg"/></div>

我们退出 Radare, 重新运行这个二进制文件, 可以看到我们成功地改掉了这个值.

作业时间! 我希望你带着这些知识, 现在去修改 __int__ 和 __double__. 请把你的结果贴在下面的评论区. 你自己动手把这些都敲一遍, 真正去探索这些练习, 这非常重要, 我很期待在评论区看到你的修改!