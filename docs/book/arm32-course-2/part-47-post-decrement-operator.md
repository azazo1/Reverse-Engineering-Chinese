## Part 47 - 后置自减运算符

本周我们来讲后置自减运算符. 让我们检查一下代码.

<pre spellcheck="false"><span class="hljs-meta">#include &lt;iostream&gt;</span>

<span class="hljs-function"><span class="hljs-keyword">int</span> <span class="hljs-title">main</span><span class="hljs-params">(<span class="hljs-keyword">void</span>)</span> </span>{
&nbsp;&nbsp; &nbsp;<span class="hljs-keyword">int</span> myNumber = <span class="hljs-number">16</span>;
&nbsp;&nbsp; &nbsp;<span class="hljs-keyword">int</span> myNewNumber = myNumber--;

&nbsp;&nbsp; &nbsp;<span class="hljs-built_in">std</span>::<span class="hljs-built_in">cout</span> &lt;&lt; myNewNumber &lt;&lt; <span class="hljs-built_in">std</span>::<span class="hljs-built_in">endl</span>;
    <span class="hljs-built_in">std</span>::<span class="hljs-built_in">cout</span> &lt;&lt; myNumber &lt;&lt; <span class="hljs-built_in">std</span>::<span class="hljs-built_in">endl</span>;

&nbsp;&nbsp; &nbsp;<span class="hljs-keyword">return</span> <span class="hljs-number">0</span>;
}
</pre>

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width">
<img src="/imgs/1531481191370.jpg"/>
</div>

 编译后我们看到分别打印出 __16__ 和 __15__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width">
<img src="/imgs/1531481259797.jpg"/>
</div>

我们看到, 在这种情况下 __myNewNumber__ 确实被自减了, 因为 __myNumber-- __取值为 16 并把它减到 15.

下周我们将深入探讨调试后置自减运算符.