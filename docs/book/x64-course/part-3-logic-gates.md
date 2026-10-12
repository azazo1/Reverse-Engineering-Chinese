## Part 3 - 逻辑门

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

在上一节教程里我们简单谈了二进制 (binary), 我们把它表示成真或者假.&nbsp;在二进制里, 真等于 1, 假等于 0.&nbsp;计算机最终就建立在这个非常简单的概念之上, 它的核心是四种可能的逻辑门 (logic gate), 它们能以无穷多种顺序组合起来.

让我们从下面的 __AND 门 __开始.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1535712345568.png"/></div>

在 AND 门里有两个二进制值, 只有这两个二进制值都是 1 时它才输出 1.&nbsp;

下面表示的是 __NOT 门__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1535712373734.png"/></div>

在 NOT 门里, 它只是取一个二进制值并把它取反.

下面表示的是 __OR 门__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1535712396805.png"/></div>

在 OR 门里, 只要其中一个输入是 1 就会输出 1.

下面表示的是 __XOR 门&nbsp;__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1535712436598.png"/></div>

在 XOR 门里, 如果两个输入要么都是 0 要么都是 1, 输出就是 0.

"为什么..." 好吧, 我为什么要讲这些? 这和理解汇编语言或者逆向工程有什么关系? 嗯... 所有处理器最核心的地方就是这些简单的逻辑门, 它们组合在一起就构成了复杂的指令. 我完全可以花上好几年的实打实的时间在实践中给你演示这一点, 不过我会把这份担子留给别人去挑. 重要的是, 当我们在汇编语言里写代码, 最终看到 AND, OR, XOR 之类的指令时, 更重要的是当我们做逆向工程时, 你能对这里发生的事情有个基本的理解.

敬请期待! 我们很快就会构建我们自己的非常简单的操作系统!