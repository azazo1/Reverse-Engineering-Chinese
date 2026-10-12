## Part 17 - 常量

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

到目前为止, 我们已经创建, 调试并修改过一个向标准终端回显字符串的简单程序.&nbsp;我们要在这个例子上做扩展, 加一个常量.

C++ 里的常量是指在程序执行过程中不会改变的值 (除非被修改).&nbsp;它的用法是让你在代码靠前的位置做一次声明, 这样将来程序架构一旦变化, 你可以在一个地方重新定义这个常量, 而不必在整个代码库里到处更新代码.

把常量全部用大写字母来写是标准做法, 这样当我们在代码某处看到它被引用时, 就知道那个值是一个常量.

我们从第二个 C++ 程序开始, 也就是我们的 "Constant" 程序.&nbsp;让我们入手, 一步步拆解每一行, 看看这门语言是怎么工作的.&nbsp;我们把它命名为 __example2.cpp__ 并保存到设备上.

<pre spellcheck="false">#include &lt;iostream&gt;
&nbsp;
int main(void) {
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; cons tint YEAR = 2017;
&nbsp;
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; std::cout &lt;&lt; YEAR &lt;&lt; std::endl;
&nbsp;
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; return 0;
}
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520149852856.jpg"/></div>

要编译它, 我们只需输入:

<pre spellcheck="false">g++ example2.cpp -o example2
</pre>

然后我们只需输入:

<pre spellcheck="false">./example2
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520148263310.jpg"/></div>

成功!&nbsp;我们看到 "__2017__" 打印到了标准输出也就是终端!

我们拆解一下:

我们用 __const __关键字来表示一个常量, 并给它赋整数值 2017.

然后我们用 __cout __函数把它打印到标准输出也就是终端, 并用 __endl__ 函数另起一行.

就这样!&nbsp;非常简单.

下周我们会深入常量的调试.