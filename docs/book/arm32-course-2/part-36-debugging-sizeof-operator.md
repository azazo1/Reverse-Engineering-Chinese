## Part 36 - 调试 SizeOf 运算符

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们重新检查一下代码.

<pre spellcheck="false">#include &lt;iostream&gt;

&nbsp;

int main(void) {

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; int myNumber = 16;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; int myNumberSize = sizeof(myNumber);

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; std::cout &lt;&lt; myNumberSize &lt;&lt; std::endl;

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; return 0;

}
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1524823603695.png"/></div>

请记住, 我们创建了一个变量 __myNumber = 16__, 又创建了另一个变量 __myNumberSize__, 它保存着 __myNumber__ 的大小.&nbsp;我们看到执行代码时显示的是 4, 因此可以看出 SizeOf operator 表明一个整数宽 4 字节.

让我们调试并在 main 处下断点.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1524823663114.png"/></div>

我们在 __main+20__ 处下断点, 因为可以看到 __4__ 这个值正被移入 __r3__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1524823735285.png"/></div>

我们来看看 __main+16__ 处发生了什么, 可以看到我们把 __r3__ 中的内容存入 __$r11-8__ 的值里, 而在本例中 __r3__ 里是 __16__.&nbsp;这说得通, 因为回头看原始代码, __myNumber__ 的值确实是 __16__.&nbsp;我们在这里检查 __$r11-8__ 里面的值就能看到.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1524823766343.png"/></div>

正如上面所见, __$r11-12__ 里面的值是__ 4__, 因为这代表 __SizeOf__ 返回的值, 整数 __16 __确实宽 4 字节.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1524823791885.png"/></div>

最后, 当我们继续执行时, 果然看到值 __4__ 回显到终端.

下周我们将深入修改 SizeOf 运算符.