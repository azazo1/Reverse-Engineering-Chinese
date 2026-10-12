## Part 9 - 调用约定

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

x64 处理器使用我们所说的 \_\_fastcall.&nbsp;

\_\_fastcall&nbsp;调用约定规定, 函数的参数在可能时应通过寄存器传递. 这种调用约定只适用于 x86 架构.

在参数列表中从左到右出现的前两个 DWORD 或更小的参数通过 __ecx__ 和 __edx__ 寄存器传递; 其余所有参数从右到左在栈上传递.

被调用的函数从栈中弹出这些参数.

名称前会加上 @ 符号 (at sign); 名称后也会加上 @ 符号, 后面跟着参数列表中的字节数 (十进制).

不进行大小写转换.

下面用一个简单的分解来说明:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1539336219028.png"/></div>

如果你在一个函数中传递两个参数, 例如 int __x__ 和 int __y__, 而且它是 QWORD, 那么 __x__ 会进入 __rcx__, __y__ 会进入__ rdx__.&nbsp;

如果你传递五个参数, 例如 int __a__, int __b__, int __c__, int __d__, int __e__, 而且它的长度是 WORD, 那么 __a__ 会进入 __cx__, __b__ 进入 __dx__, __c__ 进入 __r8w__, __d__ 进入 r9w, e 进入栈.

  

下周我们深入布尔指令 (boolean instruction)! 敬请期待!