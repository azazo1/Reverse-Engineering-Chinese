## Part 22 - 引导扇区基础 \[Part 5\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

我们先来看一些对代码的简单补充. 今天我们要完成的是创建一个简单操作系统, 它除了启动之外确实什么也不做. 我们会用 QEMU 作为模拟器, 因为我懒得去装 VirtualBox 或 VMWare, 不过如果你愿意, 也可以很容易地把 .bin 转成 .iso, 然后从其中任意一个启动.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1547203117260.png"/></div>

我们只是在第 7 行加了一个填充 (padding) 算法, 它先看看用 200h 也就是 512 减去之后还剩多少字节, 然后用零把剩下的字节填满. 在末尾你会看到我们所说的魔数 (magic number), 也就是 __0xaa55__, 因为这是 cpu 用来识别引导扇区的签名. 记住这段代码在启动时位于扇区 0, 因为此时还没有文件系统, 所以只要它找到正确的签名, 就会尝试引导它.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1547203262774.jpg"/></div>

我们用上面的代码构建这个二进制文件. 现在让我们用十六进制编辑器看看这段代码.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1547203298648.png"/></div>

如你所见, 它正如我们预期的那样, 用 0 把剩余的字节填充到 200h 也就是 512. 下面是这个二进制文件剩下的部分.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1547203339833.png"/></div>

如你所见, 在最末尾处是 __55 AA__. 我们记得我们的处理器是小端序 (little endian), 所以我们写代码时写的是 __aa 55__, 这就是它映射后的格式. 当它进入 cpu 时, 字节顺序会被反转. 理解这一点至关重要.

下周我们要做的仅仅是把我们的新操作系统启动起来. 敬请期待.