## Part 34 - 修改双精度变量

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们回顾一下代码.

<pre spellcheck="false">int main(void) {

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; double myNumber = 1337.77;

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; std::cout &lt;&lt; myNumber &lt;&lt; std::endl;

&nbsp;

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; return 0;

}
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1523615576064.jpg"/></div>

让我们开始调试!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1523615640968.jpg"/></div>

我们在 __main+24__ 处设置一个断点, 然后继续.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1523615666432.jpg"/></div>

我们看到 __strd r2, \[r11, \#-12\]__, 必须完全理解它的含义: 我们正在把寄存器 __r11__ 偏移 __-12__ 处的值存入 __r2__.&nbsp;现在我们来看看那里究竟存放着什么.&nbsp;&nbsp;

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1523615689648.jpg"/></div>

瞧!&nbsp;我们看到 __1337.77__ 就在那个偏移位置, 或者更具体地说, 它被存放在内存的 __0x7efff230__ 处.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1523615716304.jpg"/></div>

我们单步执行两次, 这会执行 __vldr d0, \[r11, \#-12\]__, 因为我们知道 __1337.77__ 现在会被加载到双精度数学协处理器 __d0 __寄存器中.&nbsp;下面我们打印该位置的值.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1523615745800.jpg"/></div>

我们来修改 __d0__ 寄存器!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1523615775560.jpg"/></div>

现在我们重新检查 __d0__ 里面的值.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1523615802811.jpg"/></div>

让我们继续.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1523615835964.jpg"/></div>

修改成功!

下周我们将深入 SizeOf 运算符.