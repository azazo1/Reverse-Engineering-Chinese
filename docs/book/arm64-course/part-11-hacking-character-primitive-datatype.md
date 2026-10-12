## Part 11 - 修改字符基本数据类型

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题. https://github.com/mytechnotalent/hacking\_c-\_arm64

今天我们要修改上一节 Lesson 里的 char.

让我们以写模式启动 radare2.

<pre spellcheck="false">radare2 -w ./0x03_asm64_char_primitive_datatype
</pre>

让我们自动分析.

<pre spellcheck="false">aaa
</pre>

定位到 main.

<pre spellcheck="false">s main
</pre>

查看反汇编.

<pre spellcheck="false">v
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1608839510539.jpg"/></div>

你可以右键点击并&nbsp;__在新标签页中打开图片&nbsp;__以获得放大的视图.

让我们回到终端视图.

<pre spellcheck="false">q
</pre>

我们要做的就是把汇编写到 0x000009ec, 并指定一个我们自己挑选的新 char.

<pre spellcheck="false">[0x000009e4]&gt; wa movz w0, 0x66 @ 0x000009ec
Written 4 byte(s) (movz w0, 0x66) = wx c00c8052
[0x000009e4]&gt;
</pre>

让我们退出, 然后从终端运行新的二进制文件.

<pre spellcheck="false">[0x000009e4]&gt; q
kali@kali:~/Documents/0x03_asm64_char_primitive_datatype$ ./0x03_asm64_char_primitive_datatype
f
</pre>

<pre spellcheck="false"></pre>

如你所见, 我们成功且永久地修改了这个二进制文件! 这件事本身非常微不足道, 但当你把最近这一系列 Lesson 连同之后每一节新的 Lesson 串在一起时, 你就在积累真正可用的技能!

在下一节 Lesson 中, 我们将学习布尔基本数据类型.

  