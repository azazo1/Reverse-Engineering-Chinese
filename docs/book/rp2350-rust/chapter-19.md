# Chapter 19: config.rs - Blink 配置

## 引言

`config.rs` 是闪灯驱动里的第一个文件, 也是最小的一个. 它里面只有
三个常量以及它们的测试 - 但仔细读它, 你会学到本课程赖以为生的
整套 **文档字符串标准**. 所有三个驱动里的每一个常量,
每一个函数, 每一个类型, 都按照下面这个文件的方式为
自己写文档.

## 完整源代码

下面是 `src/config.rs` 的完整内容 - 也就是闪灯驱动实际发布的那个文件:

```rust
/*
 * @file config.rs
 * @brief Application configuration constants
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

//! FILE: config.rs
//!
//! DESCRIPTION:
//! RP2350 闪灯配置常量.
//!
//! BRIEF:
//! 定义 LED 闪灯时序的配置常量.
//! 包含延时区间以及 GPIO 引脚配置.
//!
//! AUTHOR: Kevin Thomas
//! CREATION DATE: November 28, 2025
//! UPDATE DATE: December 4, 2025

/// LED 闪烁延时的默认值, 单位毫秒.
///
/// # Details
/// 配置 LED 状态切换之间的延时.
/// 亮和灭两个阶段都使用它.
///
/// # Value
/// 500 毫秒
#[allow(dead_code)]
pub const BLINK_DELAY_MS: u64 = 500;

/// 允许的最小闪烁延时, 单位毫秒.
///
/// # Details
/// 防止闪得太快而引发问题.
///
/// # Value
/// 10 毫秒
#[allow(dead_code)]
pub const MIN_BLINK_DELAY_MS: u64 = 10;

/// 允许的最大闪烁延时, 单位毫秒.
///
/// # Details
/// 从实用角度看, 防止闪得过慢.
///
/// # Value
/// 10000 毫秒 (10 秒)
#[allow(dead_code)]
pub const MAX_BLINK_DELAY_MS: u64 = 10000;

#[cfg(test)]
mod tests {
    use super::*;

    // ==================== LED 配置测试 ====================

    #[test]
    fn test_blink_delay_default() {
        assert_eq!(BLINK_DELAY_MS, 500);
    }

    #[test]
    fn test_min_delay_less_than_default() {
        assert!(MIN_BLINK_DELAY_MS < BLINK_DELAY_MS);
    }

    #[test]
    fn test_max_delay_greater_than_default() {
        assert!(MAX_BLINK_DELAY_MS > BLINK_DELAY_MS);
    }

    #[test]
    fn test_delay_range_valid() {
        assert!(MIN_BLINK_DELAY_MS < MAX_BLINK_DELAY_MS);
    }
}
```

一个小小的文件, 结构却很严格. 下面我们把它拆成
三层来看: 许可证文件头, 模块内部文档, 以及
每一项各自的文档字符串.

## 许可证文件头

每个源文件都以完全相同的一段块注释开头:

```
/*
 * @file config.rs
 * @brief Application configuration constants
 * @author Kevin Thomas
 * @date 2025
 *
 * MIT License
 * ... full license text ...
 */
```

这四个 `@` 标签就是文件的身份证:

| 标签      | 含义                                     |
|-----------|------------------------------------------|
| `@file`   | 文件的名字 - 不值一提, 但好扫读          |
| `@brief`  | 用一行描述这个文件的职责                 |
| `@author` | 谁写的, 谁负责维护                       |
| `@date`   | 写作的年份                               |

在它们下面就是完整的 MIT 许可证正文. 每个驱动文件 - 无论是 Rust 还是 Makefile
还是别的什么 - 都重复这段一模一样的文件头, 这样不管文件被怎样
再分发, 它都能自我署名, 自带许可证.

## 模块内部文档

紧跟许可证文件头之后, 模块内部文档注释会整体描述这个
模块. 注意用的是 `//!`, 这使它成为附着在文件上的 *模块* 文档,
并且采用严格的固定块格式:

```
//! FILE: config.rs
//!
//! DESCRIPTION:
//! RP2350 Blink Configuration Constants.
//!
//! BRIEF:
//! Defines configuration constants for LED blink timing.
//! Contains delay intervals and GPIO pin configuration.
//!
//! AUTHOR: Kevin Thomas
//! CREATION DATE: November 28, 2025
//! UPDATE DATE: December 4, 2025
```

这个块是一份固定契约: `FILE`, `DESCRIPTION`, `BRIEF`, `AUTHOR`,
`CREATION DATE`, `UPDATE DATE`. 只要文件有改动, 就要更新 `UPDATE DATE`.
这就是那份人类可读的索引, 它让一个三十个文件的多驱动
项目可以一眼扫过去.

## 给常量写文档

每个常量都遵循同一套条目文档模式 - `///` (附着在条目上的
外部文档), 然后是一份 `#` 分节的账目, 常量用 `# Details`, `# Value`
(函数则用 `# Arguments`/`# Returns`), 最后是一行
具体的值:

```rust
/// LED 闪烁延时的默认值, 单位毫秒.
///
/// # Details
/// 配置 LED 状态切换之间的延时.
/// 亮和灭两个阶段都使用它.
///
/// # Value
/// 500 毫秒
```

这三个常量用不同的侧面把这套模式教了一遍:

- **`BLINK_DELAY_MS`** - 驱动真正会用的那个值: 500 ms.
- **`MIN_BLINK_DELAY_MS`** - 10 ms; 一个下限, 防止快到荒唐的
  翻转.
- **`MAX_BLINK_DELAY_MS`** - 10000 ms; 实用意义上的闪灯上限.

每一个上面都写着 `#[allow(dead_code)]`. 今天闪灯的 `main` 循环只会读
`BLINK_DELAY_MS`, 所以那两个上下限守卫否则就会因为未被使用的
代码而报警告. 这个属性是有意的取舍: 保留完整且有文档的
配置面, 同时让 linter 闭嘴.

## 常量为什么住在这里

除了整洁, 还有两个理由:

1. **单一事实来源.** `led.rs` 通过导入来读 `BLINK_DELAY_MS`;
   硬件驱动里永远不会出现魔法数字. 改一个常量, 所有调用方
   都跟着变.
2. **可测性.** 常量是 `pub` 的, 通过 `use super::*` 就能到达
   测试模块. 下面的四个测试既钉住确切的值, 也钉住它们 *之间*
   的不变式.

## 测试

测试模块让这个文件保持诚实:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    // ==================== LED 配置测试 ====================
    ...
}
```

注意那个 **分节横幅** - `// ==================== NAME Tests
====================` - 它按关注点给测试分组. 每个驱动文件都用
同样的横幅风格, 大致呼应 Rust "测试即文档" 的精神.

这些测试断言三类事实:

- **确切的值** - `assert_eq!(BLINK_DELAY_MS, 500)` 能抓住那种会悄悄
  改变固件时序的随手改动.
- **顺序** - `MIN < DEFAULT` 和 `DEFAULT < MAX` 守住预期的
  层级关系.
- **范围合理性** - `MIN < MAX` 保护整个配置空间.

这些测试都不碰硬件; 它们在宿主机上几毫秒就跑完. 这正是
全部重点 - 配置里的笔误会变成测试失败, 而不是难以解释的硬件故障.

## 小结

- 每个源文件都以 `@file/@brief/@author/@date` 许可证文件头开头.
- 模块内部文档遵循固定的 `FILE/DESCRIPTION/BRIEF/AUTHOR/CREATION
  DATE/UPDATE DATE` 块.
- 常量用 `# Details` 和 `# Value` 记录具体数字.
- `#[allow(dead_code)]` 让有文档但暂时没被用到的配置保持安静.
- 测试模块用分节横幅钉住具体值以及常量之间的不变式.

接下来: 闪灯驱动核心的那个状态机 - `led.rs`.