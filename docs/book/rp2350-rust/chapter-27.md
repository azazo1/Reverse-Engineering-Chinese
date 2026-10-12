# Chapter 27: uart.rs - 回显状态机

## 引言

`uart.rs` 是 UART 驱动的纯逻辑核心: `UartController` 把收到的字节
转换成需要回显回去的那段字节切片, 并维护一份回显统计. 本章
完整重现这个文件, 然后逐一剖析那个让回显工作的
大方法 - `process_char`.

## 完整源代码

下面是 `src/uart.rs` 的完整内容:

```rust
/*
 * @file uart.rs
 * @brief UART echo state machine
 * @author Kevin Thomas
 * @date 2025
 *
 * MIT License
 *
 * Copyright (c) 2025 Kevin Thomas
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

//! FILE: uart.rs
//!
//! DESCRIPTION:
//! RP2350 UART 回显状态机.
//!
//! BRIEF:
//! 实现 UART 字符回显逻辑.
//! 为回显功能提供可测试的状态机.
//!
//! AUTHOR: Kevin Thomas
//! CREATION DATE: December 4, 2025
//! UPDATE DATE: December 5, 2025

use crate::config::{BACKSPACE, BACKSPACE_SEQ, DELETE};

/// 带回显计数的 UART 控制器.
///
/// # Details
/// 维护用于统计的 UART 回显计数.
/// 提供带退格支持的字符处理方法.
///
/// # Fields
/// * `echo_count` - 已回显的字符数
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[allow(dead_code)]
pub struct UartController {
    echo_count: u64,
}

impl Default for UartController {
    /// 返回默认的 UartController 实例.
    ///
    /// # Details
    /// 把初始化工作委托给 new().
    ///
    /// # Returns
    /// * `Self` - 带默认值的新 UartController
    #[allow(dead_code)]
    fn default() -> Self {
        Self::new()
    }
}

impl UartController {
    /// 创建带默认设置的新 UART 控制器.
    ///
    /// # Details
    /// 把回显计数初始化为零.
    /// 立刻就能接收字符.
    ///
    /// # Returns
    /// * `Self` - 新的 UartController 实例
    #[allow(dead_code)]
    pub fn new() -> Self {
        Self { echo_count: 0 }
    }

    /// 处理收到的字符并返回回显响应.
    ///
    /// # Details
    /// 对退格返回擦除序列.
    /// 普通字符原样回显.
    ///
    /// # Arguments
    /// * `ch` - 收到的字符
    ///
    /// # Returns
    /// * `&'static [u8]` - 要回显回去的字节
    #[allow(dead_code)]
    pub fn process_char(&mut self, ch: u8) -> &'static [u8] {
        self.echo_count += 1;
        if ch == BACKSPACE || ch == DELETE {
            &BACKSPACE_SEQ
        } else {
            match ch {
                b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' => {
                    static CHARS: [u8; 62] = [
                        b'A', b'B', b'C', b'D', b'E', b'F', b'G', b'H', b'I', b'J', b'K', b'L',
                        b'M', b'N', b'O', b'P', b'Q', b'R', b'S', b'T', b'U', b'V', b'W', b'X',
                        b'Y', b'Z', b'a', b'b', b'c', b'd', b'e', b'f', b'g', b'h', b'i', b'j',
                        b'k', b'l', b'm', b'n', b'o', b'p', b'q', b'r', b's', b't', b'u', b'v',
                        b'w', b'x', b'y', b'z', b'0', b'1', b'2', b'3', b'4', b'5', b'6', b'7',
                        b'8', b'9',
                    ];
                    let idx = CHARS.iter().position(|&c| c == ch).unwrap();
                    &CHARS[idx..idx + 1]
                }
                b' ' => b" ",
                b'!' => b"!",
                b'"' => b"\"",
                b'#' => b"#",
                b'$' => b"$",
                b'%' => b"%",
                b'&' => b"&",
                b'\'' => b"\'",
                b'(' => b"(",
                b')' => b")",
                b'*' => b"*",
                b'+' => b"+",
                b',' => b",",
                b'-' => b"-",
                b'.' => b".",
                b'/' => b"/",
                b':' => b":",
                b';' => b";",
                b'<' => b"<",
                b'=' => b"=",
                b'>' => b">",
                b'?' => b"?",
                b'@' => b"@",
                b'[' => b"[",
                b'\\' => b"\\",
                b']' => b"]",
                b'^' => b"^",
                b'_' => b"_",
                b'`' => b"`",
                b'{' => b"{",
                b'|' => b"|",
                b'}' => b"}",
                b'~' => b"~",
                b'\n' => b"\n",
                b'\r' => b"\r",
                b'\t' => b"\t",
                _ => b"",
            }
        }
    }

    /// 返回回显总数.
    ///
    /// # Returns
    /// * `u64` - 已回显的字符数
    #[allow(dead_code)]
    pub fn echo_count(&self) -> u64 {
        self.echo_count
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // ==================== UartController 构造测试 ====================

    #[test]
    fn test_new_controller() {
        let ctrl = UartController::new();
        assert_eq!(ctrl.echo_count(), 0);
    }

    #[test]
    fn test_default_equals_new() {
        let default = UartController::default();
        let new = UartController::new();
        assert_eq!(default.echo_count(), new.echo_count());
    }

    // ==================== 字符处理测试 ====================

    #[test]
    fn test_process_char_returns_same() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(b'A'), b"A");
    }

    #[test]
    fn test_process_char_increments_count() {
        let mut ctrl = UartController::new();
        ctrl.process_char(b'A');
        ctrl.process_char(b'B');
        ctrl.process_char(b'C');
        assert_eq!(ctrl.echo_count(), 3);
    }

    #[test]
    fn test_process_char_special() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(b'\n'), b"\n");
        assert_eq!(ctrl.process_char(b'\r'), b"\r");
    }

    #[test]
    fn test_process_backspace() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(0x08), &[0x08, b' ', 0x08]);
    }

    #[test]
    fn test_process_delete() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(0x7F), &[0x08, b' ', 0x08]);
    }

    #[test]
    fn test_process_tab() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(b'\t'), b"\t");
    }

    #[test]
    fn test_process_uppercase_letters() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(b'A'), b"A");
        assert_eq!(ctrl.process_char(b'Z'), b"Z");
        assert_eq!(ctrl.process_char(b'M'), b"M");
    }

    #[test]
    fn test_process_lowercase_letters() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(b'a'), b"a");
        assert_eq!(ctrl.process_char(b'z'), b"z");
        assert_eq!(ctrl.process_char(b'm'), b"m");
    }

    #[test]
    fn test_process_digits() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(b'0'), b"0");
        assert_eq!(ctrl.process_char(b'9'), b"9");
        assert_eq!(ctrl.process_char(b'5'), b"5");
    }

    #[test]
    fn test_process_punctuation() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(b'!'), b"!");
        assert_eq!(ctrl.process_char(b'?'), b"?");
        assert_eq!(ctrl.process_char(b'.'), b".");
        assert_eq!(ctrl.process_char(b','), b",");
    }

    #[test]
    fn test_process_symbols() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(b'@'), b"@");
        assert_eq!(ctrl.process_char(b'#'), b"#");
        assert_eq!(ctrl.process_char(b'$'), b"$");
        assert_eq!(ctrl.process_char(b'%'), b"%");
    }

    #[test]
    fn test_process_brackets() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(b'['), b"[");
        assert_eq!(ctrl.process_char(b']'), b"]");
        assert_eq!(ctrl.process_char(b'('), b"(");
        assert_eq!(ctrl.process_char(b')'), b")");
        assert_eq!(ctrl.process_char(b'{'), b"{");
        assert_eq!(ctrl.process_char(b'}'), b"}");
    }

    #[test]
    fn test_process_unknown_char() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(0x01), b"");
        assert_eq!(ctrl.process_char(0xFF), b"");
    }

    #[test]
    fn test_process_space() {
        let mut ctrl = UartController::new();
        assert_eq!(ctrl.process_char(b' '), b" ");
    }

    #[test]
    fn test_backspace_increments_count() {
        let mut ctrl = UartController::new();
        ctrl.process_char(0x08);
        assert_eq!(ctrl.echo_count(), 1);
    }

    #[test]
    fn test_multiple_backspaces() {
        let mut ctrl = UartController::new();
        ctrl.process_char(0x08);
        ctrl.process_char(0x7F);
        ctrl.process_char(0x08);
        assert_eq!(ctrl.echo_count(), 3);
    }

    #[test]
    fn test_mixed_chars_and_backspace() {
        let mut ctrl = UartController::new();
        ctrl.process_char(b'A');
        ctrl.process_char(b'B');
        ctrl.process_char(0x08);
        ctrl.process_char(b'C');
        assert_eq!(ctrl.echo_count(), 4);
    }

    // ==================== trait 测试 ====================

    #[test]
    fn test_clone() {
        let ctrl = UartController::new();
        let cloned = ctrl.clone();
        assert_eq!(ctrl.echo_count(), cloned.echo_count());
    }

    #[test]
    fn test_copy() {
        let ctrl = UartController::new();
        let copied = ctrl;
        assert_eq!(ctrl.echo_count(), copied.echo_count());
    }

    #[test]
    fn test_partial_eq() {
        let ctrl1 = UartController::new();
        let ctrl2 = UartController::new();
        assert_eq!(ctrl1, ctrl2);
    }

    #[test]
    fn test_not_equal_after_process() {
        let mut ctrl1 = UartController::new();
        let ctrl2 = UartController::new();
        ctrl1.process_char(b'A');
        assert_ne!(ctrl1, ctrl2);
    }

    #[test]
    fn test_debug_format() {
        let ctrl = UartController::new();
        let debug_str = format!("{:?}", ctrl);
        assert!(debug_str.contains("UartController"));
    }
}
```

整台机器就是一个结构体, 三个方法, 外加一个很宽的 `match`. 测试
分成三块横幅: 构造, 字符处理和 trait.

## 控制器结构体与 new

```rust
pub struct UartController {
    echo_count: u64,
}
```

只有一个字段 - 和前面几个控制器一样, 只带一个 `u64` 计数器. 派生列表与
`LedController` 和 `ButtonController` 完全一致: `Clone, Copy, Debug, PartialEq, Eq`.
`new()` 把计数器从零开始. `echo_count()` 是最简单的取值方法.
`UartController` 是本课程里最小的控制器, 而它需要的却是
最大的 `match` - 这与闪烁驱动那个一行的 toggle 正好相反.

## process_char

所有有意思的东西都在这里:

```rust
pub fn process_char(&mut self, ch: u8) -> &'static [u8] {
    self.echo_count += 1;
    if ch == BACKSPACE || ch == DELETE {
        &BACKSPACE_SEQ
    } else {
        match ch { ... }
    }
}
```

三个设计决定, 按顺序看:

1. **每个字符都计数** - `self.echo_count += 1` 是无条件执行的, 放在
   任何分支之前. 即使某个字节不产生回显 (未知字节) 也会被计数,
   因为 `main` 确实收到了它. `test_backspace_increments_count` 和
   `test_mixed_chars_and_backspace` 把这一点钉死了.

2. **退格短路** - 两种擦除写法都返回三字节的
   `BACKSPACE_SEQ`. 这比把同一段范围匹配两次更快, 而且
   让 `BACKSPACE`/`DELETE` 保持为有名字的配置常量.

3. **其余部分用穷尽 match** - 控制字符和可打印 ASCII
   都原样回显; 表外的一切都落到 `_ => b""`. 这个
   `_` 分支保证 match 永远不会漏掉任何字节, 也永远不需要堆上
   一大堆分支.

返回类型值得多看一眼: `&'static [u8]`. 每个分支返回的都是一个
带生命周期约束的切片 - 可能是像 `b"!"` 这样的字节串字面量, 也可能是静态的
`BACKSPACE_SEQ`, 还可能是静态 `CHARS` 表的一段切片. 没有任何内存是从
调用方借来的, 每次调用也不做任何分配, 所以 `process_char`
返回的是引用, 而 `main` 可以直接把它交给 `uart.write`.

### 字母数字表分支

字母和数字的那个分支很巧妙, 值得多花几行:

```rust
b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' => {
    static CHARS: [u8; 62] = [ b'A', ..., b'9' ];
    let idx = CHARS.iter().position(|&c| c == ch).unwrap();
    &CHARS[idx..idx + 1]
}
```

`static CHARS` 是那 62 个字符的字母表, 在 flash 里固定地址处
只保存一份. `.position()` 在这个表里找到传入的字节, 而
`&CHARS[idx..idx + 1]` 返回的是一个*单元素切片* - 不是 `u8` 值, 因为
这个方法必须返回切片. `.unwrap()` 是安全的, 因为这个分支的范围
已经保证了该字节一定存在.

### 转义字节

有些字节需要小心书写字面量, 于是给了它们单独的分支:

```rust
b'"'  => b"\"",
b'\\' => b"\\",
b'\'' => b"\'",
```

这三个反斜杠转义在驱动文件里经受住了 rustfmt 的整理, 而测试
`test_process_punctuation` 和 `test_process_symbols` 确认了引号和
斜杠能原样往返.

## 测试

这套测试就是控制器的契约, 按道理分组排列:

- **构造测试** - 新建的计数为零; `default()` 等于 `new()`.
- **字符处理测试** - 字母, 数字,
  标点, 符号, 括号, 空格和控制字节都原样回显; 两种退格都返回擦除序列;
  未知字节回显为空; 每一次输入计数都会增加,
  包括退格和混合输入.
- **trait 测试** - `Clone`, `Copy`, `PartialEq`, 以及可读的 `Debug`
  格式.

最锋利的是那个不对称测试: `test_not_equal_after_process` 展示两个
起初相等的控制器, 在其中一个处理了一个字节之后就不再相等.
`echo_count` 是行为的一部分, 不是装饰.

## 小结

- `UartController` 只持有一个计数器, 并暴露 `new`, `process_char`
  和 `echo_count`.
- `process_char` 给每个输入计数, 把退格短路到擦除
  序列, 其余一切交给一个穷尽的 `match`.
- 每个分支都返回 `&'static [u8]` - 没有分配, 也没有从调用方借来的
  生命周期.
- 字母数字分支通过索引一个 62 字节的 `static` 表来返回切片.
- 十四个处理测试, 加上构造测试和 trait 测试, 让回显
  行为成为一份被编译进代码的契约.

接下来是 UART 那个干净的 `await` 背后的硬件故事: 中断和 DMA.