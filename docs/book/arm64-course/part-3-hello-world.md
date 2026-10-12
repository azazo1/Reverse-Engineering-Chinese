## Part 3 - "Hello World"

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题. https://github.com/mytechnotalent/hacking\_c-\_arm64

今天我们从最开头讲起, 拿一个非常简单的 C++ 程序: 它做的仅仅是用流插入运算符把一个字符串字面量送到 stdout, 再用行结束操纵符刷新输出缓冲区.

我们先创建一个文件 0x01\_asm64\_helloworld.cpp, 然后把下面的内容敲进去.

<pre spellcheck="false">#include &lt;iostream&gt;

int main()
{
&nbsp; &nbsp; std::cout &lt;&lt; "Hello World!" &lt;&lt; std::endl;
&nbsp; &nbsp; return 0;
}
</pre>

让我们编译并链接.

<pre spellcheck="false">g++ -o 0x01_asm64_helloworld 0x01_asm64_helloworld.cpp
</pre>

让我们运行.

<pre spellcheck="false">./0x01_asm64_helloworld
</pre>

我们看到简单的结果.

<pre spellcheck="false">Hello World!
</pre>

这些 Lesson 是刻意做得又短又简单的. 我知道你们中不少人水平更高, 但我真的很想让这门 Course 尽可能对初学者友好.

在下一节 Lesson 中, 我们将用自己构建的 Radare2 开发版来调试这个非常简单的二进制文件.