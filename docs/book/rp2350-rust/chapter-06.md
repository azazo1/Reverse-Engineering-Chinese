# Chapter 6: Traits and Generics

## Introduction

Traits are Rust's answer to interfaces, and generics are its answer to code that
"just works" for many types. Together they are the connective tissue of the
whole ecosystem — and Embassy is built on them. The GPIO `Output`, the UART
`Uart`, the `Wait` trait used by `Timer` — every one of these is a type or a
contract expressed with traits and generics.

## What Is a Trait?

A **trait** defines a contract of behavior: a set of methods a type promises to
implement. Rust *cannot compile a program* unless every type used where that
trait is expected actually implements it.

In this course we meet three categories of traits:

1. **Derived traits** — `Clone`, `Copy`, `Debug`, `PartialEq`, `Eq` — whose
   implementations come from `#[derive(...)]` (Chapter 5).
2. **Trait implementations we write** — such as `impl Default for LedController`.
3. **Trait bounds used by Embassy** — the contracts that let one piece of code
   drive any supported hardware.

## Defining and Implementing Traits

We saw a hand-written `Default` implementation in Chapter 5. Write it again with
an eye to its structure:

```rust
impl Default for LedController {
    /// Returns default LedController instance.
    ///
    /// # Details
    /// Delegates to new() for initialization.
    ///
    /// # Returns
    /// * `Self` - New LedController with default values
    #[allow(dead_code)]
    fn default() -> Self {
        Self::new()
    }
}
```

`impl Default for LedController` says: "LedController gets the behavior the
`Default` trait requires." The docstring above `fn default()` is our strict
standard — every trait method in the drivers documents `# Details`,
`# Arguments` where present, and `# Returns`.

Defining your own trait works the same way:

```rust
pub trait HasPulse {
    fn pulse(&self) -> u32;
}

impl HasPulse for LedState {
    fn pulse(&self) -> u32 {
        match self {
            LedState::On => 65535,
            LedState::Off => 0,
        }
    }
}
```

## Generics

A **generic** function or type works across many types through parameters. The
classic example — and one you will use constantly — is `Option<T>`: the `T`
means "any type," so `Option<u8>` and `Option<&[u8]>` are distinct uses of one
definition.

```rust
fn take_seat<T>(thing: Option<T>) -> T {
    match thing {
        Some(value) => value,   // the generic T flows through
        None => panic!("no value"),
    }
}
```

On a microcontroller, generics cost nothing: each concrete type gets its own
compiled copy (see Monomorphization below). Embassy exploits this — a GPIO bank,
a UART channel, and a DMA channel are all described generically but become
exactly the right register addresses after compilation.

## Trait Bounds

A **trait bound** restricts which types a generic may use. `T: Copy` means the
generic works only with types that implement `Copy`:

```rust
fn echo_value<T: Copy>(value: T) -> T { value }

echo_value(5u8);         // fine — u8 is Copy
// echo_value(some_string); // ERROR — String is not Copy
```

Bounds combine with `where` clauses for readability:

```rust
fn handle<T, E>(r: Result<T, E>)
where
    T: Copy,
    E: Debug,
{
    // T can be copied; E can be debug-printed
}
```

Every Embassy driver you write reads as a list of such bounds. They are the
compiler's guarantee list: "this code works for anything that provides these
behaviors, and only those."

## Monomorphization

Rust compiles each generic instantiation into dedicated, specialized code — no
virtual dispatch, no hidden pointer jumps. This is **monomorphization**, and it
is why there is zero runtime cost: a generic over `u8` produces the same bytes a
hand-written `u8` function would. Embedded Rust depends on this property, and it
is a core reason "abstractions" here never mean "overhead."

```
Generic source            Compiled target
fn get<T>(x: T) -> T        get_u8:  mov w0, w0; ret
{ x }                       get_u32: mov w0, w0; ret
```

## Traits in Embassy

The three drivers touch Embassy types that are generic and trait-driven:

- **`Output<'d, T>`** — a GPIO output pin, generic over the pin type.
- **`Input<'d, T>`** — a GPIO input pin, generic over the pin type.
- **`Uart<'d, T, D>`** — a UART instance, generic over channel and DMA.
- **`Timer`** — an async wait primitive; `.await` on it sleeps without blocking.

You rarely name these generic parameters yourself — `embassy_rp` infers and
specializes them. But now you know what the `<'d, T>` angle brackets mean: a
borrow for the device's lifetime, and a concrete pin/peripheral type that the
compiler has already proven is valid.

## Summary

- Traits define behavior contracts; `derive` generates common ones free.
- Generic parameters (`<T>`) make one definition serve many types.
- Trait bounds (`T: Copy`) encode the contracts generics must satisfy.
- Monomorphization gives generics zero runtime cost — essential on a
  microcontroller.
- Embassy's `Output`, `Input`, and `Uart` types are generics over pins,
  channels, and DMA; the compiler specializes them at build time.

Foundations complete. Next we leave the host and go bare metal: `no_std`,
`no_main`, and the build system.