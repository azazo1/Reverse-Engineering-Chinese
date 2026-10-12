## Part 21 - 调试字符变量

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们回顾一下代码.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520147096734.jpg"/></div>

开始调试!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520229910793.jpg"/></div>

哇!&nbsp;这真让人困惑.&nbsp;我看不到有什么明确的内存地址被加载到寄存器里去操作数据.&nbsp;

请记住, 我们处理的是一个单字节的字符变量.&nbsp;

如果你还记得上周的内容, 每个字符都会转换成处理器能理解的十六进制 ASCII 码.&nbsp;__n__ 的值是十六进制 __0x6e__, 也就是十进制 __110__.&nbsp;你可以查看任意 ASCII 表, 看看这个值是怎么得来的.

我们确实在 __main+12__ 处看到了 __0x6e__, 它就是字符 '__n__'.&nbsp;&nbsp;

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520209360741.jpg"/></div>

如果我们单步进入几次, 就会注意到该值已被放入 __r3__.&nbsp;当我们打印 __r3__ 中的值时, 就能看到 '__n__' 这个字符.

让我们继续.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520149197565.jpg"/></div>

现在我们看到 '__n__' 如预期那样被打印到标准输出.

重要的是你要理解这个过程, 并且明白每个字符都会转换成一个 ASCII 值, 处理器会直接把它加载到对应的寄存器中.&nbsp;在我们之前的经验里, 字符串是被直接加载到某个内存位置的, 而这里并非如此.

下周我们将深入探讨修改字符变量.