## Part 5 - 修改 "Hello World"

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题. https://github.com/mytechnotalent/hacking\_c-\_arm64

上一节 Lesson 我们花了相当多的时间真正理解我们的二进制文件内部发生了什么. 这为轻松的修改打下了基础.

让我们以写模式启动 radare2.

<pre spellcheck="false">radare2 -w ./0x01_asm_64_helloworld
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

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1606475269047.jpg"/></div>

你可以右键点击并&nbsp;__在新标签页中打开图片&nbsp;__以获得放大的视图.

由于我们没有像上一节 Lesson 讨论的那样运行这个二进制文件, 我们看到的是这些内存地址在磁盘上的样子.

我们看到在 __0xb48__ 处很容易就找到了我们的字符串.

让我们回到终端视图.

<pre spellcheck="false">q
</pre>

让我们验证一下这个字符串.

<pre spellcheck="false">[0x000009e4]&gt; ps @0xb48
Hello World!
[0x000009e4]&gt;

</pre>

让我们修改这个字符串.

<pre spellcheck="false">[0x000009e4]&gt; w Hacked World @0xb48
</pre>

让我们验证这次修改.

<pre spellcheck="false">[0x000009e4]&gt; ps @0xb48
Hacked World
[0x000009e4]&gt;
</pre>

让我们退出 radare2.

<pre spellcheck="false">q
</pre>

现在我们再次运行这个二进制文件!

<pre spellcheck="false">./0x01_asm_64_helloworld
Hacked World
</pre>

可以看到我们非常轻松地修改了这个二进制文件. 这些 Lesson 会帮助你理解攻击者是如何形成一套工作流程的, 从而学会如何预判并更好地进行逆向工程.

在下一节 Lesson 中, 我们将研究简单的 I/O.