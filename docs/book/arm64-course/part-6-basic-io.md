## Part 6 - 基本 I/O

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题. https://github.com/mytechnotalent/hacking\_c-\_arm64

今天我们要看一个带少量校验的基本 I/O C++ 程序.

在进入简短讲解之前 (我尽量把这些内容讲短), 我想先解释一下, 为什么我不用你在世界各地都能见到的那种教科书式 _cin_ 示例.

_cin_ 即标准输入流, 它从键盘获取输入, 我们称之为 stdin.

_cin_ 的做法是把空白, 制表符和换行当作输入流的终止符. 例如你输入 _'abc'_ 然后按一下制表符, 或者敲一个空格, 或者按回车产生换行, 那么它右边的数据都会被忽略.

问题在于, 如果你不刷新输入缓冲区, 再次从 _cin_ 读取时它会把流中剩余的数据取走.

比如你有下面这样的代码:

<pre spellcheck="false">std::cin &gt;&gt; val1;
std::cin &gt;&gt; val2;
</pre>

如果用户输入 _1_, 然后留一个空格, 再输入 _2_ 并按回车, 那就没有问题. 由于它们是串联的, _1_ 会赋给 _val1_, _2_ 会赋给 _val2_.

问题在于, 如果你输入的不是整数而是 _'Hey Jude'_ 会怎样? 它会尝试读取一个整数, 于是进入失败状态, 从那一刻起它提取到的其他一切数据都不可靠了.

我并不想啰嗦, 但我确实想强调为什么你绝不应该单独使用 _cin_, 我说的是绝不!

我们来看看这个基本 I/O 程序, 它是一个用于校验输入的非常基础的 C++ 程序, 我们将在下一节 Lesson 中调试它.

<pre spellcheck="false">#include &lt;iostream&gt;
#include &lt;sstream&gt;
#include &lt;string&gt;

int main()
{
    int age = 0;
    bool valid = false;
    char null = '\0';

    while (!valid)
    {
        std::cout &lt;&lt; "Enter Age: ";

        // 以字符串形式获取输入
        std::string line;
        getline(std::cin, line);

        // 初始化 stringstream
        std::stringstream is(line);

        // 尝试从 stringstream 中读出一个合法的年龄,
        // 如果读不出数字, 或者数字之后的字符串里
        // 除了空白还有别的东西, 就让这次读取失败,
        // 再从用户那里取一个新的字符串, 并确保 
        // 这家伙至少有一岁, 且小于或等于
        // 100 岁
        if (!(is &gt;&gt; age) || (is &gt;&gt; std::ws &amp;&amp; is.get(null)) || age &gt;= 100 || age &lt;= 0)
            std::cout &lt;&lt; "Dude be real!" &lt;&lt; std::endl;
        else
            valid = true ;
    }

    std::cout &lt;&lt; "Your are " &lt;&lt; age &lt;&lt; " years old, seems legit!" &lt;&lt; std::endl;

    return 0;
}
</pre>

我们首先引入 _iostream_, _sstream_ 和 _string_. 到这里并没有什么难点.

接着我们提示用户输入年龄. 然后创建一个名为 _line_ 的字符串对象, 并利用 C++ 的 _getline()_, 它是一个标准 C++ 库函数, 用于正确地从输入流中读取一个字符串或一行.

接着我们利用 _stringstream_, 它把一个字符串对象与一个流关联起来, 让你能像对待原始的 _cin_ 那样, 把这个字符串当作流来读取. 在这个简单的例子里, 我们创建了一个 _is_ 对象, 它是 input stringstream 的缩写, 并与我们的 _line_ 对象连接起来.

然后, 在把数据回显到 stdout 之前, 我们做一点校验. 首先检查 _age_ 是不是它被定义时的类型, 也就是 _int_, 或者给定整数之后的流中是否还有空白, 又或者 age 是否大于 _100_ 或小于 _0_. 很简单, 如果输入不满足这些条件, 它就给出一个回应.

最后, 如果一切正常, 它就用一个简单的 _cout_ 输出.

让我们编译并链接.

<pre spellcheck="false">g++ -o 0x02_asm64_basicio 0x02_asm64_basicio.cpp
</pre>

让我们运行.

<pre spellcheck="false">./0x02_asm64_basicio
</pre>

你输入什么, 它就会像上面描述的那样做出相应的校验. 请务必亲自试试这个例子, 并动手改动源码, 以充分理解这里发生的一切.

在下一节 Lesson 中, 我们将用自己构建的 Radare2 开发版来调试这个非常简单的二进制文件.