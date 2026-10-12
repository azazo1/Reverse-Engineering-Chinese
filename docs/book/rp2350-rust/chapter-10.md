# Chapter 10: build.rs, Makefile, and Flashing

## Introduction

Producing a bootable `.uf2` requires several stages: compiling target Rust,
running the linker with our `memory.x`, generating the boot image metadata, and
finally invoking `probe-rs` to flash the RP2350. This chapter walks through the
two automation files every driver ships: `build.rs` and the `Makefile`.

## build.rs — The Build Script

A Rust crate can ship a special file named `build.rs` at the crate root. Cargo
compiles and runs it *before* building the crate, and anything it prints with
the `cargo:` prefix becomes build instructions. Our `build.rs` is small and
crucial:

```rust
use std::env;
use std::fs::File;
use std::io::Write;
use std::path::PathBuf;

fn main() {
    let out = &PathBuf::from(env::var_os("OUT_DIR").unwrap());
    File::create(out.join("memory.x"))
        .unwrap()
        .write_all(include_bytes!("memory.x"))
        .unwrap();
    println!("cargo:rustc-link-search={}", out.display());
    println!("cargo:rerun-if-changed=memory.x");
}
```

Reading it line by line:

1. **`env::var_os("OUT_DIR")`** — Cargo gives build scripts a private output
   directory. The linker script is copied there.
2. **`include_bytes!("memory.x")`** — Embeds the file's bytes at compile time
   and writes them into `OUT_DIR/memory.x`.
3. **`cargo:rustc-link-search=...`** — Tells the linker to search that
   directory, so the startup crate's `-Tlink.x` can find our `memory.x`.
4. **`cargo:rerun-if-changed=memory.x`** — If `memory.x` changes, rebuild
   instead of reusing a stale result.

The net effect: the linker consumed a `memory.x` that lives *inside the
repository*, not a hidden system default. One source of truth.

## The Makefile

A `Makefile` wraps the common operations behind short, memorable targets. The
full file also carries the MIT header and `@file`/`@brief`/`@author`/`@date`
docstring block — proof the standard applies to every file, even build
automation:

```make
.PHONY: test build clean flash

test:
	cargo test --lib --target $(shell rustc --print host-tuple) --no-default-features

build:
	cargo build --release

flash: build
	probe-rs run --chip RP2350 target/thumbv8m.main-none-eabihf/release/rp2350-blink

clean:
	cargo clean
```

## make test — Host Tests

```
cargo test --lib --target $(shell rustc --print host-tuple) --no-default-features
```

- `--target $(shell rustc --print host-tuple)` — Build for the *host*, not the
  RP2350, so the tests run as a normal desktop program.
- `--no-default-features` — Drop Embassy (`embassy-executor`, `embassy-rp`,
  `cortex-m`, `cortex-m-rt`, `panic-halt`). Only the pure, testable logic is
  compiled — which is precisely why the design keeps logic in the library
  (Chapter 18) and why `lib.rs` is `no_std` only when *not* testing.
- `--lib` — Test the library target, which is where all the state machines live.

This command is Chapter 25 in one line. It is the whole feedback loop: write a
driver, run the state machine on the host, and see 20+ tests pass in a second.

## make build — Release Firmware

`cargo build --release` compiles optimized firmware. The release profile in
`Cargo.toml` is tuned for a microcontroller:

```toml
[profile.release]
debug = true
lto = true
opt-level = "z"
panic = "abort"
```

- `debug = true` — Keep debug info so `probe-rs` can resolve names.
- `lto = true` — Link-time optimization across crates; significant size savings.
- `opt-level = "z"` — Optimize for size. Flash is measured in kilobytes.
- `panic = "abort"` — No unwinding metadata; panics halt immediately (matches
  `panic-halt`).

## make flash — probe-rs

`probe-rs run` both flashes and opens an on-chip debug session:

```
probe-rs run --chip RP2350 target/thumbv8m.main-none-eabihf/release/rp2350-blink
```

From Pico 1 to Pico 2 the chip name changed: **`RP2040`** becomes **`RP2350`**.
`probe-rs run` needs the debug probe (a Pico with the "debugprobe" firmware, or
a Picoprobe) on one USB port, and the target Pico on another. This is the "flash
and go" experience from each driver's README.

## Summary

- `build.rs` copies our `memory.x` into the build output and tells the linker
  where to find it.
- `make test` runs the state-machine tests on the host with
  `--no-default-features`.
- `make build` produces a size-optimized release image with LTO.
- `make flash` uses `probe-rs` and the `RP2350` chip profile to flash and run.
- `make clean` removes build artifacts.

Now we look at the idea underneath all of this: memory-mapped I/O, and how
firmware touches hardware at all.