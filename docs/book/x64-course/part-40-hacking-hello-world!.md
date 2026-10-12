## Part 40 - 修改 Hello World!

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

好, 现在该来看看最基础的 C 程序, 调试它, 然后再修改它了. 如果想要精通, 我们就必须创造与摧毁一步到位, 这样才能真正掌握这个领域.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1565910335250.jpg"/></div>

我们打开 VIM, 把下面这段内容敲出来. 我们引入标准库, 创建一个 main 函数, 在函数里用库函数 printf 回显一串字符; 由于 main 的类型是 int, 也就是整数, 所以我们返回 0.

我们编译一下, 看看运行时会怎样:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1565910684168.jpg"/></div>

和我们 C++ 那个例子一样, 可以看到 '__Hello World!__' 成功回显了.

我们在 Radare 里调试一下:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1566057508295.jpg"/></div>

这很简单, 我们用 __aaa__ 分析这个二进制文件, 再用 __s sym.main__ 定位到 main.

我们看看汇编并分析一下:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1566057552155.jpg"/></div>

汇编! 这才是赤裸裸的性感!

在之前关于汇编的几节 Lesson 里我详细讲过这些, 不过我们还是复习一下.

1)我们 __push rbp __, 也就是把当前基址指针里的值压入栈.

2)我们 __lea rdi, qword str.Hello\_World __, 也就是把字符串这个 quad word 的有效地址加载进 __rdi__ 寄存器. 到目前为止你应该很容易跟上.

3)接着我们 __call sym.imp.puts__ 呃等等! 我们明明用的是 __printf__, 搞什么! 其实是编译器优化了我们的代码, 它选择了 stdio 库里的 __puts__ 函数把字符串回显到终端. 同样很简单.

4)我们清空 __eax__, 然后把 __rbp__ 寄存器里原来的值弹出, 放回 __rbp__. 如果你对这点感到困惑, 请复习本系列前面的内容.

我们知道字符串 '__Hello World!__' 住在弗吉尼亚州阿灵顿一栋漂亮的房子里, 地址是 __0x2004__; 好吧, 它其实不在阿灵顿, 但它确实在映射内存里 (严格说我们并不是在调试, 而是在摆弄映射的代码, 也就是说磁盘上的值是相同的).

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1565911732441.jpg"/></div>

为确认这一点, 我们看到 __0x2004__ 处的值就是 '__Hello World!__'. 我们用 __w__ 命令把这个值改成任意我们想要的内容, 直接写入那个映射内存地址.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1565911764019.jpg"/></div>

我们再来看看, 现在谁住在我们阿灵顿的那栋房子里!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1565911840111.jpg"/></div>

成功! 我们改掉了这个值, 退出调试器后可以看到:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1565911868600.jpg"/></div>

我们成功地改动了这个二进制文件.

这里要消化的东西不少. 如果你卡住了, 请在评论区提问, 拜托了! 不要硬往下看, 我在这里就是为了帮你. 在我们继续之前, 你务必理解这些最基础的内容!