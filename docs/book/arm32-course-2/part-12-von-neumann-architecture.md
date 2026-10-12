## Part 12 - 冯·诺依曼架构

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

ARM 是一种加载-存储型机器, 其中算术逻辑单元 (Arithmetic Logic Unit) 只对寄存器本身进行运算, 而任何需要存回 RAM 的数据, 都由控制单元在内存与寄存器之间搬运, 两者共享同一条数据总线.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520233777770.jpg"/></div>

这种架构的 CPU 芯片内部包含一个控制单元和一个算术逻辑单元 (以及一些本地内存), 而主内存则是插在主板上的内存条.

存储程序式 (stored-program) 数字计算机把程序指令和数据都保存在可读写的随机存取内存, 也就是 RAM 中.

下周我们将深入指令流水线.