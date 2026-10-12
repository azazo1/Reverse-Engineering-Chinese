## Part 42 - 修改分支!

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

我们来看一些分支逻辑:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1566729104643.jpg"/></div>

可以清楚地看到, 我们把一个 int 初始化为 1, 如果这个变量等于 1, 第一个 if 语句就会向标准输出打印一条响应.

我们来编译:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1566729192665.jpg"/></div>

我们来运行:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1566729212374.jpg"/></div>

从逻辑上可以看出, 走的是第一个分支. 我们把它放进 Radare 里, 看看汇编:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1566729291450.jpg"/></div>

借助浅绿色 (aqua) 的箭头可以看到分支逻辑. 在 __0x0000114a__ 处, 我们看到第一个分支被加载进 __rdi__. 注意在 __0x00001148__ 处有一个 __jne 0x1158__. 在 __0x00001158__ 处, 我们看到第二个分支被加载进 __rdi__.

__jne__ 的意思是 jump if not equal, 即不相等则跳转. 也就是说, 如果在 __0x00001144__ 处参与比较的东西不等于 1 (我们看到是拿 __1__ 与 __local\_4h__ 里的内容作比较, 我们知道 __local\_4h__ 是伪代码, 实际指的是 __rbp-0x4__ 里的内容. 这一点应该说得通, 上周我详细讲过这些, 如果你还有困惑, 请回顾我们上一节 Lesson.

要修改, 我们只需把 __jne__ 语句改成 __je__, 也就是 jump if equal, 即相等则跳转; 我们知道 __cmp__ 也就是比较的结果是相等的, 所以现在它会跳转到 "__A is NOT 1!__".

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1566729757650.jpg"/></div>

退出 Radare 后, 可以看到我们已经成功修改了这个二进制文件:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1566729786175.jpg"/></div>

敬请期待!