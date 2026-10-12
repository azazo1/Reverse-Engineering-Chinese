## Part 3 - 二进制加法

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

二进制加法有四种不同的情形:

<pre spellcheck="false">0 + 0 = 0
1 + 0 = 1
0 + 1 = 1
1 + 1 = 0 (1) [一加一等于零, 进位一]
</pre>

注意 (1) 表示进位的位. 说白了, 它表示溢出.

看下面这个 4 位半字节的例子:

<pre spellcheck="false">  0111
+ 0100
= 1011
</pre>

可以看到第 3 位明显产生了进位. 如果第 8 位也产生进位, 就会在 CPU 里生成进位标志 (carry flag).

再看一个 8 位的数:

<pre spellcheck="false">  01110000
+ 01010101
= 11000101
</pre>

如果是这样:

<pre spellcheck="false">     ﻿﻿11110000
+    11010101
= (1)11000101
</pre>

这里我们看到一个进位位, 它会让 CPU 里的进位标志变成 1, 也就是 true. 后面的教程里我们会讨论进位标志. 请先记住这个例子, 拿它作参照, 理解这一点非常重要.

下周我们深入二进制减法! 敬请期待!