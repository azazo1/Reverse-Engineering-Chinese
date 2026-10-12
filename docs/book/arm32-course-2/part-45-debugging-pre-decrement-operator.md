## Part 45 - 调试前置自减运算符

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们重新检查一下代码.

<pre spellcheck="false">#include &lt;iostream&gt;

int main(void) {
&nbsp;&nbsp; &nbsp;int myNumber = 16;
&nbsp;&nbsp; &nbsp;int myNewNumber = --myNumber;

&nbsp;&nbsp; &nbsp;std::cout &lt;&lt; myNewNumber &lt;&lt; std::endl;
    std::cout &lt;&lt; myNumber &lt;&lt; std::endl;

&nbsp;&nbsp; &nbsp;return 0;
}
</pre>

我们记得, 编译后得到的是 15.

让我们来调试.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1530270075261.jpg"/></div>

让我们下断点.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1530270088297.jpg"/></div>

可以看到, __r3 __中存放着 15. 请记住, 你要修改的这个位置可能并不是它最终被存储的位置. 下周请记住这一点, 并重新检查上面的调试过程, 看看你能不能想明白.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1530270183626.jpg"/></div>

可以看到, __r1__ 中也存放着 15. 请记住上面那句话.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1530270209438.jpg"/></div>

继续执行, 我们看到 __cout __函数按预期在两处都回显出 15.

下周我们将深入探讨修改前置自减运算符.