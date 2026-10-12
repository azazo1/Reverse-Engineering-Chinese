# Chapter 8: Cargo, Targets, and the Toolchain

## Introduction

Cargo is Rust's build system and package manager. It is also the whole
toolchain glue for embedded Rust: a single `cargo build` invokes the right
compiler, links against the right libraries, and produces a binary for our exact
CPU. This chapter walks through installing everything and reading the pieces of
a driver's `Cargo.toml`, `.cargo/config.toml`, and build commands.

## Installing the Toolchain

You need two things:

1. **Rust** via [rustup](https://rustup.rs) — the toolchain manager.
2. **The ARM GNU toolchain** for the linker and other host tools — available
   from [arm.com](https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads).
   During installation, select **Add path to environment variable**.

Verify the installation:

```bash
$ rustup --version
rustup 1.27.1

$ rustc --version
rustc 1.84.0 (9fc0cc514 2025-02-28)

$ arm-none-eabi-gcc --version
... (arm-none-eabi-gcc) 13.2.Rel1 ...
```

For flashing and on-chip debugging we use `probe-rs`:

```bash
$ cargo install probe-rs-tools
```

## The Target: thumbv8m.main-none-eabihf

Rust does not compile to "generic ARM." It compiles to a **target triple** that
names the exact architecture, ABI, and environment:

```
thumbv8m.main-none-eabihf
│       │     │       └── hard-float ABI
│       │     └────────── no standard library (bare metal)
│       └──────────────── mainline ARMv8-M (has the main features: security etc.)
└──────────────────────── Thumb instruction set
```

The RP2350's M33 core is ARMv8-M mainline with the Thumb instruction set, so
`thumbv8m.main-none-eabihf` is exactly our target. `none` means no operating
system — matching `no_std`.

Install it:

```bash
$ rustup target add thumbv8m.main-none-eabihf
```

## .cargo/config.toml

The driver's `.cargo/config.toml` tells Cargo to use this target everywhere and
pass the linker arguments the embedded runtime needs:

```toml
[build]
target = "thumbv8m.main-none-eabihf"

[target.thumbv8m.main-none-eabihf]
runner = "probe-rs run --chip RP2350"
rustflags = [
  "-C", "link-arg=--nmagic",
  "-C", "link-arg=-Tlink.x",
]
```

Two kinds of flags:

- `--nmagic` — Do not page-align the data sections; smaller and simpler binaries
  for flash.
- `-Tlink.x` — Use the `link.x` linker script produced by `cortex-m-rt` from
  our own `memory.x` (Chapter 9).

With `target` set here, plain `cargo build` targets the RP2350 and `cargo run`
flashes via `probe-rs` — exactly the README's surface API for every driver.

## Cargo.toml

A driver's `Cargo.toml` is deliberately split into a **library** and a
**binary**. The library holds all the testable logic; the binary is a thin async
shell:

```toml
[package]
name = "rp2350-blink"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "rp2350-blink"
test = false

[lib]
name = "rp2350_blink"
path = "src/lib.rs"
test = true
```

Crucially, the **binary does not run tests** (`test = false`) and the
**library does** (`test = true`). The library has no main and no interrupt
machinery, so `cargo test --lib` can run it on the host.

## Optional Dependencies and Features

Dependencies that only the embedded binary needs (Embassy, `cortex-m-rt`,
`panic-halt`) are declared `optional` and gated behind a feature:

```toml
[dependencies]
embassy-executor = { git = "https://github.com/embassy-rs/embassy", features = [
    "arch-cortex-m",
    "executor-thread",
], optional = true }
embassy-time = { git = "https://github.com/embassy-rs/embassy", optional = true }
embassy-rp = { git = "https://github.com/embassy-rs/embassy", features = [
    "time-driver",
    "rp235xa",
    "critical-section-impl",
    "imagedef-secure-exe",
], optional = true }
cortex-m = { version = "0.7.7", optional = true }
cortex-m-rt = { version = "0.7.3", optional = true }
panic-halt = { version = "1.0.0", optional = true }

[features]
default = [
    "embassy-executor",
    "embassy-time",
    "embassy-rp",
    "cortex-m",
    "cortex-m-rt",
    "panic-halt",
]
```

The `embassy-rp` features are the hardware knobs:

- `time-driver` — The RTC/timer backend that `embassy-time` uses for delays.
- `rp235xa` — Target the RP2350 (RP235xA) chip.
- `critical-section-impl` — Provide the critical-section mechanism (Chapter 16).
- `imagedef-secure-exe` — Emit the secure image definition the RP2350 bootrom
  requires (pairing with `memory.x` in Chapter 9).

The `[features] default` set is what a normal `cargo build` enables. When we run
host tests we pass `--no-default-features`, dropping every embedded option so
the crate compiles with plain `core`/`std` (Chapter 25).

## Summary

- rustup installs Rust; the ARM GNU toolchain provides the linker; probe-rs
  flashes.
- The `thumbv8m.main-none-eabihf` target names our exact CPU and bare-metal
  ABI.
- `.cargo/config.toml` makes the RP2350 the default target and provides
  `--nmagic` and `link.x`.
- `Cargo.toml` splits a testable library from a non-test binary.
- Optional + feature-gated dependencies keep the no_std binary distinct from the
  host-testable library.

Next, the linker script that puts our code in flash at the right addresses.