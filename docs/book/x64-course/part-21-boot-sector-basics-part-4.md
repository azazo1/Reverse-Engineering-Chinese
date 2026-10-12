## Part 21 - 引导扇区基础 \[Part 4\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

今天我们继续引导扇区基础的内容. 我们来看看代码:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1546600881811.png"/></div>

如上所示, 我们在代码中加入一个字符串并编译.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1546600938007.png"/></div>

我们在十六进制编辑器里查看这个二进制文件.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1546600963265.png"/></div>

仔细看看上面的内容. 我们看到原来的代码, 这不必复习, 不过现在我们看到一串数字, 是表示 ASCII 字符的十六进制数字. 我们看到每个字母对应一个字母. 我们说最终一切都归结为 0 和 1, 这里就是一个概念验证. 如你所见, 上面选中了 __EB __, 我们可以看到那些十六进制值最终变成二进制中的 __11101011__.

作业: 用 Google 查一查 ASCII 转换表, 自己做一些研究, 更好地理解十六进制值是如何表示字符的.

下周我们把它提升到下一个层次. 敬请期待!