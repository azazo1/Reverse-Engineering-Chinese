## Part 10 - 调试字符基本数据类型

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题. https://github.com/mytechnotalent/hacking\_c-\_arm64

今天我们要调试这个非常简单的字符基本数据类型.

首先, 让我们在 Radare2 中打开我们的二进制文件.

<pre spellcheck="false">radare2 ./0x03_asm64_char_primitive_datatype
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

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1608824475984.jpg"/></div>

你可以右键点击并&nbsp;__在新标签页中打开图片&nbsp;__以获得放大的视图.

可以看到, 在 _0x5576bff9ec_ 处我们正把 _0x63_ 或者说 ascii 的 _'c'_ 移入 _w0_ 寄存器.

让我们在&nbsp;_0x5576bff9ec_&nbsp;处设置一个断点, 并验证其中的内容.

<pre spellcheck="false">[0x5576bff9e4]&gt; db 0x5576bff9ec
[0x5576bff9e4]&gt; dc
hit breakpoint at: 0x5576bff9ec
[0x5576bff9ec]&gt; dr w0
0x00000001
[0x5576bff9ec]&gt; ds
[0x5576bff9ec]&gt; dr w0
0x00000063
[0x5576bff9ec]&gt;

</pre>

<pre spellcheck="false"></pre>

这非常简单, 不过我们来把它拆解一下. 我们设置好断点然后继续执行. 我们查看寄存器 w0 里面, 看到值是 0x01. 

然后我们单步执行一次再看, 0x63 已经成功移入 w0, 因为现在我们可以看到它确实包含 0x63.

如果我们再次 dc, 就会看到它按预期回显到 stdout.

<pre spellcheck="false">[0x5576bff9ec]&gt; dc
c
(10845) Process exited with status=0x0
</pre>

<pre spellcheck="false">[0x7f9727503c]&gt;
</pre>

在下一节 Lesson 中, 我们将把这个 char 修改成我们选定的另一个值.

  