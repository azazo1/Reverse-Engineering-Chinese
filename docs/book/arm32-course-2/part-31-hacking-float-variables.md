## Part 31 - 修改浮点变量

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们重新检查一下我们的代码.

<pre spellcheck="false">#include &lt;iostream&gt;

&nbsp;

int main(void) {

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; int myNumber = 1337.1;

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; std::cout &lt;&lt; myNumber &lt;&lt; std::endl;

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; return 0;

}
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1521799049547.jpg"/></div>

让我们回顾一下上周的教程.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1521799097861.jpg"/></div>

让我们在 __main+20__ 处下断点, 然后继续运行到该点.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1521799125882.jpg"/></div>

让我们看看 __r11-8__ 里的值是多少.&nbsp;可以清楚地看到它是 __1337.09998__, 这近似于我们原始 c++ 代码中的值.&nbsp;请记住, float 大约有 7 位十进制有效数字的精度, 这就是我们看不到 __1337.1__ 的原因, 所以今后请牢记这一点.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1521799166328.jpg"/></div>

我们也可以在高地址内存中看到这个值.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1521799204709.jpg"/></div>

让我们在 __main+28__ 处下断点并继续.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1521799242840.jpg"/></div>

我们看到一条陌生的新指令.&nbsp;我们看到 __vldr__, 还有 __r11, \#8__ 中的值被移入__ s0__.&nbsp;那么 __s0__ 是什么?&nbsp;我们有一个数学协处理器, 它带有一系列用于处理十进制数或浮点数的额外寄存器.&nbsp;这里就是一个例子, 值 __1337.09998 __正被移入 __s0__.&nbsp;__vldr__ 指令会把一个常量值加载到单精度或双精度寄存器的每一个元素中, 例如__ s0__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1521799279756.jpg"/></div>

只有像下面这样执行 info registers all 命令, 我们才能看到这些特殊寄存器.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1521799307421.jpg"/></div>

下面我们看到该值现在正被移入 __s0__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1521799331767.jpg"/></div>

开始修改!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1521799362535.jpg"/></div>

现在让我们看看寄存器, 看看发生了什么变化.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1521799386349.jpg"/></div>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1521799407513.jpg"/></div>

如你所见, 我们已经修改了这个值 (除了浮点变量精度只能精确到 6 位小数的问题)!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1521799441419.jpg"/></div>

最后, 继续执行时, 当 c++ 的 __cout __函数执行时, 我们看到修改后的值被回显到终端.

下周我们将深入探讨双精度变量.