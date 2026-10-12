## Part 8 - 修改基本 I/O

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题. https://github.com/mytechnotalent/hacking\_c-\_arm64

今天我们来修改上一节 Lesson 里的输入校验.

让我们以写模式启动 radare2.

<pre spellcheck="false">radare2 -w ./0x02_asm_64_basicio
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

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1607709949903.jpg"/></div>

你可以右键点击并&nbsp;__在新标签页中打开图片&nbsp;__以获得放大的视图.

让我们回到终端视图.

<pre spellcheck="false">q
</pre>

让我们看看可视化图形, 从第一个 _b.ne_ 开始, 在预期的正常条件下, 它只接受 _0_ 到 _100_ 之间的有效整数, 正如我们在上一讲中演示的那样.

_b.ne_ 的意思是 _branch if not equal_. 在这种情况下, 它前面的汇编根本不重要, 因为我们知道, 只要让 b.ne 保持原样, 输入校验就完好无损.

我们需要把那条指令改成 _b.eq_, 即 _branch if equal_, 从而让这个输入校验失效.

让我们看看那个代码块.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1607710722312.jpg"/></div>

可以看到, 如果条件为真, 也就是校验通过, 我们拿到一个 0 到 100 之间的整数, 就会沿着绿色的真分支线走到下一个函数, 如下所示:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1607710870812.jpg"/></div>

你可以右键点击并&nbsp;__在新标签页中打开图片&nbsp;__以获得放大的视图.

如果校验失败, 我们会被送到假分支去获取新的输入:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1607710976917.jpg"/></div>

让我们用 q 回到终端提示符.

<pre spellcheck="false">qq
</pre>

让我们定位到想修改的那条语句.

<pre spellcheck="false">[0x000010a4]&gt; s 0x000010c4
</pre>

现在我们按前面讨论的来修改这个分支.

<pre spellcheck="false">[0x000010c4]&gt; wa b.eq 0x1214
Written 4 byte(s) (b.eq 0x1214) = wx 800a0054
[0x000010c4]&gt;
</pre>

让我们退出.

<pre spellcheck="false">q
</pre>

现在运行这个二进制文件时, 它会完全忽略任何输入, 更不用说输入校验了, 直接到达我们想要的位置.

<pre spellcheck="false">kali@kali:~/Documents/0x02_asm_64_basicio$ ./0x02_asm_64_basicio
Your are 0 years old, seems legit!
kali@kali:~/Documents/0x02_asm_64_basicio$
</pre>

尽管 0 是有效值, 但它只是一个不稳定值, 恰好出现在程序期望在正常流程中被正确赋值的某个寄存器里. 这里我们永久性地改动了这个二进制文件, 从而完成了这次修改.

这些例子都非常简单, 不过随着你不断深入并把它们组合起来, 你真的能对任何东西做逆向工程.

在下一节 Lesson 中, 我们将讨论 char 基本数据类型.

  

  