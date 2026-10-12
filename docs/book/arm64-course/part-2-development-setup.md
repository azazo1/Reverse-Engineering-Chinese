## Part 2 - 开发环境搭建

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题. https://github.com/mytechnotalent/hacking\_c-\_arm64

今天我们要搭建自己的开发环境. 我们需要准备以下东西:

<pre spellcheck="false">Raspberry Pi 4
64GB MicroSD 卡
Micro SD 卡读写器
下载 64 位 Kali Linux ARM 镜像
下载 balenaEtcher
烧录 Kali Linux ARM 镜像
Git Clone 并构建 Radare2 软件
VIM 或 Nano 文本编辑器软件
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1606060809296.png"/></div>

<iframe allowfullscreen="true" class="center lazy-load" data-delayed-url="https://www.linkedin.com/embeds/publishingEmbed.html?articleId=7727169611615228100" frameborder="0" height="294" src="about:blank" title="Raspberry Pi 4 Model B - 2 GB RAM" width="744"></iframe>

<iframe allowfullscreen="true" class="center lazy-load" data-delayed-url="https://www.linkedin.com/embeds/publishingEmbed.html?articleId=8531784840398647030" frameborder="0" height="124" src="about:blank" title="Kingston Canvas Go! Plus 64GB MicroSD Card with Adapter" width="744"></iframe>

<iframe allowfullscreen="true" class="center lazy-load" data-delayed-url="https://www.linkedin.com/embeds/publishingEmbed.html?articleId=7824989292602458319" frameborder="0" height="326" src="about:blank" title="Iogear GFR204SD SD/MicroSD/MMC Card Reader and Writer - Walmart.com" width="744"></iframe>

<a href="https://images.kali.org/arm-images/kali-linux-2020.4-rpi4-nexmon-64.img.xz" rel="nofollow noopener" target="_blank">__Kali Linux RaspberryPi 2 (v1.2), 3 and 4 (64-Bit) (img.xz)__</a>__ \[__https://www.offensive-security.com/kali-linux-arm-images/\]

<iframe allowfullscreen="true" class="center lazy-load" data-delayed-url="https://www.linkedin.com/embeds/publishingEmbed.html?articleId=7382995876954764581" frameborder="0" height="294" src="about:blank" title="balena - The complete IoT fleet management platform" width="744"></iframe>

<iframe allowfullscreen="true" class="center lazy-load" data-delayed-url="https://www.linkedin.com/embeds/publishingEmbed.html?articleId=7082048844677902563" frameborder="0" height="419" src="about:blank" title="Load Kali Linux on a Raspberry Pi 4 Model B for a Mini Hacking Computer [Tutorial]" width="744"></iframe>

准备好所有必要的设备和软件之后, 请观看这段关于如何搭建环境的视频, Null Byte 做了一份非常出色的分步教程, 几分钟就能让你上手.

下一步是 git clone 并构建 Radare2 软件, 我们想要最新版本, 因为 Kali 内置的标准版本不足以满足我们的需求.

<iframe allowfullscreen="true" class="center lazy-load" data-delayed-url="https://www.linkedin.com/embeds/publishingEmbed.html?articleId=8901357596711809999" frameborder="0" height="274" src="about:blank" title="radareorg/radare2" width="744"></iframe>

<pre spellcheck="false">cd Documents
git clone https://github.com/radareorg/radare2.git
sys/install.sh
</pre>

最后我们会用文本编辑器来编写代码. Kali 内置了 VIM 和 Nano 两款文本编辑器. 我们会用 VIM, 不过你完全可以用自己顺手的任意一款.

在下一节 Lesson 中, 我们将编写第一个 C++ 程序, 也就是 "Hello World!".