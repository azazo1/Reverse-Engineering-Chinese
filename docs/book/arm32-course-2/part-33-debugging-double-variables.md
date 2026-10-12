## Part 33 - 调试双精度变量

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

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1523008391034.jpg"/></div>

让我们开始调试!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1523008417137.jpg"/></div>

我们在 __main+24__ 处设置一个断点, 然后继续.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1523008442868.jpg"/></div>

我们看到 __strd r2, \[r11, \#-12\]__, 必须完全理解它的含义: 我们正在把寄存器 __r11__ 偏移 __-12__ 处的值存入 __r2__.&nbsp;现在我们来看看那里究竟存放着什么.&nbsp;&nbsp;

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1523008470513.jpg"/></div>

瞧!&nbsp;我们看到 __1337.77__ 就在那个偏移位置, 或者更具体地说, 它被存放在内存的 __0x7efff230__ 处.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1523008491495.jpg"/></div>

我们单步执行两次, 这会执行 __vldr d0, \[r11, \#-12\]__, 因为我们知道 __1337.77__ 现在会被加载到双精度数学协处理器 __d0 __寄存器中.&nbsp;下面我们打印该位置的值.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1523008515533.jpg"/></div>

最后我们继续执行, 观察这个值回显到终端.&nbsp;这就完成了我们的 __cout__ c++ 函数.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1523008538297.jpg"/></div>

下周我们将深入修改双精度变量.