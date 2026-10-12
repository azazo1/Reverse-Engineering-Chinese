## Part 4 - 二进制减法

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

二进制减法不过是把要减去的数取负值再加进去而已. 以 8 + - 4 为例, 起点是零, 先沿正方向移动 8 个单位, 再沿负方向移动 4 个单位, 得到的结果是 4.

我们用二进制里的一个符号位 (sign bit) 表示正负, 第 7 位表示数的符号, 其中 0 表示正, 1 表示负.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520215170654.jpg"/></div>

上面这个表示的是 -2.

我们用到了二进制补码 (two's complement) 的概念, 也就是把每一位取反, 最后再加 1.

来看看&nbsp;二进制形式的 2.

__00000010__

把各位取反.

__11111101__

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520247605526.jpg"/></div>

来看一次减法运算:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520212177447.jpg"/></div>

那么你可能会问 (1) 是什么, 那就是溢出位. 在后面的教程里我们会看看所谓的溢出标志和进位标志.

下周我们深入字长! 敬请期待!