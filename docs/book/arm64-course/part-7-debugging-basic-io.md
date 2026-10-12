## Part 7 - 调试基本 I/O

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题. https://github.com/mytechnotalent/hacking\_c-\_arm64

今天我们要调试上一讲那个非常基础的输入校验程序.

首先, 让我们在 Radare2 中打开我们的二进制文件.

<pre spellcheck="false">radare2 ./0x02_asm_64_basicio
</pre>

让我们用上 Radare2 的自动分析功能.

<pre spellcheck="false">aaa
</pre>

接下来合乎逻辑的一步, 是以调试模式启动这个程序, 这样它就会把磁盘上的原始机器码映射到一个正在运行的进程.

<pre spellcheck="false">ood
</pre>

现在我们有了一个运行中的实例, 可以定位到这个二进制文件的 main 入口点.

<pre spellcheck="false">s main
</pre>

让我们按下面的方式做一次初步检查.

<pre spellcheck="false">v
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1607682836896.jpg"/></div>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1607683092302.jpg"/></div>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1607683246880.jpg"/></div>

你可以右键点击并&nbsp;__在新标签页中打开图片&nbsp;__以获得放大的视图.

有几点值得注意: 在 _0x5566be00cc_ 处我们看到 _"Enter Age: "_ 的输出, 在 _0x5566be017c_ 处有一次对 _istream_ 的调用, 它会从 _stdin_ 捕获值; 在 0x5566be01d0 处我们识别出一个失败条件, 那里是 _"Dude be real!"_, 而从 _0x5566be0218 _开始我们看到一次正常输入校验的结果, 那里是 _"You are "_, 接着在 _0x5566be0238_ 处看到一次对输出流的调用, 然后在 _0x5566be0244_ 处是校验字符串的后半段, 那里是 _" years old, seems legit!"_.

下一步是用可视化图形来看这个二进制文件.

<pre spellcheck="false">q
VV
ppppp
</pre>

我们看到如下内容:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1607685699956.jpg"/></div>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1607685723107.jpg"/></div>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1607685740119.jpg"/></div>

这是我们缩小后的可视化图形. 可以看到程序是如何在各个函数之间流转的. 你会注意到有一系列标签, 比如 \[ol\] 或 \[ok\], 你完全可以像下面这样直接键入:

<pre spellcheck="false">p
ol
</pre>

现在我们就在那个函数里面了:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1607686001944.jpg"/></div>

然后回到 main.

<pre spellcheck="false">qq
s main
VV
</pre>

这会带我们进入一个展开的图形, 我们还可以用方向键四处查看.

让我们在 _0x5566be00c4_ 处设置一个断点, 那里我们 _bne 0x5566be0214_, 也就是我们看到的这个二进制文件的成功路径.

<pre spellcheck="false">[0x5566be0194]&gt; db 0x5566be00c4
[0x5566be0194]&gt; dc
hit breakpoint at: 0x5566be00c4
Enter Age: 33
hit breakpoint at: 0x5566be00c4
[0x5566be0194]&gt; dc
Your are 33 years old, seems legit!
(2215) Process exited with status=0x0
</pre>

如你所见, 我们在循环里转了一圈, 输入了正确的校验值, 并成功拿到了返回值.

在下一节 Lesson 中, 我们将修改这个校验.

  