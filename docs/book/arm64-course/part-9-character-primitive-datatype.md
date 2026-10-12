## Part 9 - 字符基本数据类型

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题. https://github.com/mytechnotalent/hacking\_c-\_arm64

今天我们来谈谈 C++ 的第一个基本类型. _char_ 数据类型用于存储单个字符, 并且必须用单引号括起来.

让我们看看基础示例.

<pre spellcheck="false">#include &lt;iostream&gt;

int main()
{
    char my_char = 'c';

    std::cout &lt;&lt; my_char &lt;&lt; std::endl;

    return 0;
}
</pre>

极其简单. 我们只是创建一个名为 _my\_char _的 char 变量, 并把字符 _c_ 赋给它.

然后我们把它打印到标准输出, 仅此而已.

让我们编译并链接.

<pre spellcheck="false">g++ -o 0x03_asm64_char_primitive_datatype 0x03_asm64_char_primitive_datatype.cpp
</pre>

让我们运行.

<pre spellcheck="false">./0x03_asm64_char_primitive_datatype
</pre>

很简单, 我们看到如下输出.

<pre spellcheck="false">c
</pre>

它成功地把 c 回显到终端标准输出. 非常简单.

下周我们将调试这个非常简单的示例.

  