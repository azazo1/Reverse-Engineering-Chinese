## Part 14 - Hello World

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

今天, 我们开始走进 C++ 的世界, 更好地理解 C++ 是如何与我们的 ARM 处理器交互的.

本系列前面的 Lesson 关注 ARM 处理器的基础, 也涉及它的架构, 以及所有内容最终如何一路向下翻译成汇编语言, 再最终变成操作码进入机器语言.

我们从第一个 C++ 程序开始, 也就是我们的 "Hello World" 程序.&nbsp;让我们入手, 一步步拆解每一行, 看看这门语言是怎么工作的.&nbsp;我们把它命名为 __example1.cpp__ 并保存到设备上.

<pre spellcheck="false">#include &lt;iostream&gt;
&nbsp;
int main(void) {
    std::cout &lt;&lt; “Hello World” std::endl;
&nbsp;
&nbsp;&nbsp;&nbsp;&nbsp;return 0;
}
</pre>

<div class="slate-resizable-image-embed"><img src="/imgs/1520191083072.jpg"/></div>

要编译它, 我们只需输入:

<pre spellcheck="false">g++ example1.cpp -o example1
</pre>

然后我们只需输入:

<pre spellcheck="false">./example1
</pre>

![](/imgs/1520237920732.jpg)

  

成功!&nbsp;我们看到 "Hello World" 打印到了标准输出也就是终端!

我们逐行拆解一下:

__\#include &lt;iostream&gt; __被称为预处理语句.&nbsp;这些预处理语句发生在其余代码编译之前.&nbsp;\#include 关键字会找到一个名为 __iostream__ 的文件, 取出该文件的全部内容, 粘贴到我们刚写好的现有代码里.&nbsp;这类文件也叫头文件.&nbsp;

我们引入 __iostream__, 是因为我们需要 __cout__ 和 __endl__ 这两个函数的声明.&nbsp;__cout__ 函数让我们把文本打印到标准输出也就是终端, __endl__ 函数则在文本显示之后另起一行.

main 这一段属于整数类型, 它是主应用程序也就是二进制的入口点.&nbsp;你会注意到 __()__ 里的 __void__, 它表示不会向该函数传入任何参数.

__std __表示命名空间, 说白了它就是一种把代码组织成逻辑分组的机制, 以便你在处理多个库时防止名称冲突.

你会看到很多例子里都会声明 using namespace std; 但我绝不会采用这种做法, 因为它在更复杂的应用中可能导致命名冲突.

__&lt;&lt;__ 运算符被称为重载运算符.&nbsp;它们本质上是一个函数, 与 C 语言里的 __printf__ 非常相似.&nbsp;我们只是借助 __&lt;&lt;__ 重载运算符把 __"Hello World" __这个字符串送进 __cout__ 函数.&nbsp;随后我们推入 __endl__, 它会在控制台里另起一行.

最后一行是 return 0.&nbsp;由于我们的 main 函数是 int 类型, 我们必须返回点东西.&nbsp;在 C++ 11 里, main 函数并不需要它, 但其他所有函数都需要.&nbsp;我还是遵循传统, 直接把它写上.

下一个阶段是编译这个文件.&nbsp;首先发生的事情是, 正如我们讨论过的, iostream 头文件的全部内容进入源文件.&nbsp;编译过程就是把 C++ 代码翻译成机器码.&nbsp;编译的下一个阶段, 发生在我们现有代码的其余各行被解析完毕的时候.&nbsp;本质上, 我们把 iostream 的全部内容放进一个新文件, 再把我们现有文件的全部内容也加进去, 合成一个文件.

编译会把我们的文本文件也就是 cpp 文件, 转换成一种称为 obj 文件的中间格式.&nbsp;此时会创建一棵抽象语法树, 它是常量数据, 变量和指令的一种转换结果.

语法树创建完成之后, 就生成代码.&nbsp;这意味着我们现在有了 ARM CPU 将要执行的机器码.&nbsp;每个 cpp 文件 (翻译单元) 都会有各自对应的 obj 文件.&nbsp;

链接会把我们的 obj 文件也就是编译产物, 连同 C++ 标准库一起处理, 找到每个符号和函数所在的位置, 再把它们全部链接成一个可执行文件.&nbsp;&nbsp;&nbsp;

如果你是编程新手, 上面的概念可能看起来有点让人困惑, 但当你写代码, 编译, 之后再用汇编语言调试和修改时, 一切都会变得非常清楚, 你也会学会驾驭这颗处理器.

下周我们会深入 Hello World 的调试.