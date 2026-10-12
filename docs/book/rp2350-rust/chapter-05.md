# Chapter 5: Structs, Enums, and Pattern Matching

## Introduction

The three drivers are built from just a few user-defined types: `struct`s for
controllers, `enum`s for states, and deep use of `match` to turn states into
hardware actions. This chapter builds those tools. By the end you will recognize
every type and `match` arm that appears in `led.rs`, `button.rs`, and `uart.rs`.

## Structs

A `struct` groups named fields into one value. Our `LedController` is a struct
with two fields:

```rust
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[allow(dead_code)]
pub struct LedController {
    state: LedState,
    delay_ms: u64,
}
```

Creating a struct value requires naming every field:

```rust
let ctrl = LedController {
    state: LedState::Off,
    delay_ms: BLINK_DELAY_MS,
};
```

Field access uses a dot: `ctrl.delay_ms`. Fields are private by default — other
modules cannot touch them, so the struct controls its own invariants through
methods.

## Methods and impl Blocks

Behavior attached to a type lives in an `impl` block. A method whose first
parameter is `self` or `&self` is callable on a value; methods with `&mut self`
can change the value:

```rust
impl LedController {
    pub fn new() -> Self {
        Self {
            state: LedState::Off,
            delay_ms: BLINK_DELAY_MS,
        }
    }

    pub fn toggle(&mut self) -> LedState {
        self.state = match self.state {
            LedState::On => LedState::Off,
            LedState::Off => LedState::On,
        };
        self.state
    }
}
```

Note two things. First, `toggle` needs `&mut self` because it writes to
`self.state` — the borrow checker watched us do it. Second, `match self.state`
is how Rust models state transition: a table from old state to new state written
explicitly, with no edge case forgotten.

## Enums

An `enum` is a type with a fixed, exhaustive set of variants. Our `LedState` is
the simplest kind — a set of named values:

```rust
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[allow(dead_code)]
pub enum LedState {
    On,
    Off,
}
```

Unlike C, Rust's enums are exhaustive: any code that handles `LedState` must
handle both `On` and `Off`, or the compiler refuses to build. There is no
"impossible" stray integer value, which is a real bug source in register-flag
mirroring.

## Option and Result

Two enums do so much work that they are built into the language:

- **`Option<T>`** — `Some(value)` or `None`. Expresses a value that may be
  absent.
- **`Result<T, E>`** — `Ok(value)` or `Err(error)`. Expresses an operation that
  may fail, and carries the failure reason.

The UART driver's `read` is async and returns a `Result`. The main loop checks
it before writing anything back:

```rust
if uart.read(&mut buf).await.is_ok() {
    let echo_bytes = controller.process_char(buf[0]);
    let _ = uart.write(echo_bytes).await;
}
```

`.is_ok()` converts success into a boolean, but pattern matching gives us the
payload too, as we do throughout.

## Pattern Matching

`match` is Rust's workhorse. It handles every enum variant, binds values, and
guards conditions — and the compiler proves it is exhaustive:

```rust
match ch {
    b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' => {
        // Alphanumeric: find this byte in the 62-entry table.
        let idx = CHARS.iter().position(|&c| c == ch).unwrap();
        &CHARS[idx..idx + 1]
    }
    b' ' => b" ",
    b'!' => b"!",
    b'\n' => b"\n",
    _ => b"",
}
```

This is the actual core of the UART driver's `process_char`. Study the pieces:

- **Range patterns** — `b'A'..=b'Z'` matches any byte in range, inclusive.
- **Or patterns** — `|` combines alternatives.
- **Binding** — `|&c| c == ch` is a closure; `.position()` returns `Option`.
- **`unwrap()`** — We know the byte is in the table, so a missing match is a
  programming error; `unwrap` is only safe when the invariant is guaranteed.
- **`_` wildcard** — Catches anything else; without it the match would not
  compile.

The `matches!` macro makes a single-variant test concise — `led_state_to_level`
is exactly that:

```rust
pub fn led_state_to_level(state: LedState) -> bool {
    matches!(state, LedState::On)
}
```

## Deriving Traits

`#[derive(...)]` asks the compiler to generate standard trait implementations
for a type automatically. Our driver types derive the same four traits:

```rust
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
```

| Trait        | Provides                              | Why we need it                     |
|--------------|---------------------------------------|------------------------------------|
| `Clone`      | A `clone()` method                    | Duplicate values in tests          |
| `Copy`       | Bit-copy on assignment                | Pass by value and keep using       |
| `Debug`      | `{:?}` formatting                     | Test failure output                |
| `PartialEq`  | `==` and `!=`                         | `assert_eq!` in tests              |
| `Eq`         | Full equivalence (no `NaN`)           | Stronger `==` guarantee            |

Because these are derived, our structs compare, copy, and print for free. The
test suites in every driver lean on `PartialEq` + `Debug` for readable failure
messages.

## Summary

- Structs group fields; impl blocks attach methods, including `&mut self`
  methods that transition state.
- Enums are exhaustive and remove entire classes of invalid-value bugs.
- `Option` and `Result` express absence and failure in the type system.
- `match` is exhaustive pattern matching — the core of our state machines.
- `derive` generates `Clone`, `Copy`, `Debug`, `PartialEq`, and `Eq`
  implementations that tests rely on.

Next, the final language pillar before bare metal: traits and generics.