## Part 15 - SHR 指令

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

SHR 命令表示右移 (shift right).

假设寄存器 __al__ 中保存着 00010100b, 这是一个 8 位二进制值. 假设指令是 __shr al, 2__. 下面展示了数值向左移动两位时发生的情况.

 00010100

   00010100

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1542995744073.png"/></div>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1542995747116.jpg"/></div>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1542995744391.jpg"/></div>

00000101

下周我们将深入 ROL! 敬请期待!