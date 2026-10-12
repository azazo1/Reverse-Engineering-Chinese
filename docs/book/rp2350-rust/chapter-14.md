# Chapter 14: The Embassy Executor

## Introduction

Futures run only when someone polls them. On a microcontroller that someone is
the **executor**: a tiny, never-returning loop that keeps a queue of ready
futures, polls each one, and sleeps when nothing is ready. Embassy's executor
is distributed as `embassy-executor`, and its face in our code is one attribute
and one parameter: `#[embassy_executor::main]` and the `Spawner`. This chapter
dissects both.

## #[embassy_executor::main]

Every driver's entry point looks the same:

```rust
/// Main application entry point.
///
/// # Details
/// Initializes Embassy runtime and runs the main blink loop.
/// Uses BlinkController for state management.
///
/// # Arguments
/// * `_spawner` - Embassy task spawner (reserved for future async tasks).
///
/// # Returns
/// * `()` - Never returns (infinite loop).
#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    ...
}
```

The attribute does three jobs at startup:

1. **Initializes the executor's interrupt-driven clock** (the executor is
   ticked by a timer interrupt on `arch-cortex-m`).
2. **Constructs a `Spawner`** and passes it in as the first argument.
3. **Spawns `main` itself as the first task** and runs the executor forever.

Ignore the docstring for a moment — the signature carries real information. The
argument is a `Spawner`; in the blink driver it is unused (`_spawner`) because
the blink loop needs no extra tasks. The UART driver does not spawn extra tasks
either; our three drivers are single-task by design and pass the `Spawner`
through for future expansion, exactly as the docstring states.

## The Spawner

A `Spawner` is a **handle to the executor**. With it, running an async task is a
function call:

```rust
let spawner: Spawner = ...;          // obtained from #[embassy_executor::main]
spawner.spawn(my_task()).unwrap();   // register the future with the executor
```

What you can do with a `Spawner`:

- **`spawn`** — Submit a task future to the executor's queue.
- **Clone and share** — `Spawner` is cheap to copy; it can be moved into
  closures and other tasks so they can start new tasks later.

The spark that never appears in our simple drivers is a task pool: each
`#[embassy_executor::task]` needs a fixed-size slot at compile time, so Embassy
allocates tasks statically, not on a heap. `spawn` fails only when a pool is
full — returning a `SpawnError` we would have to handle.

## Tasks with #[embassy_executor::task]

A reusable async function (a "task") is annotated with
`#[embassy_executor::task]`. The attribute reserves the state the future needs
and wires the future into the executor's machinery:

```rust
#[embassy_executor::task]
async fn blink(peripherals) {
    loop {
        ...
        Timer::after_millis(500).await;
    }
}

// later, in main:
let _ = spawner.spawn(blink(peripherals));
```

The syntax mirrors `#[embassy_executor::main]`, which is itself just a special
task with a freely-given spawner. Our three drivers do not use the `#[task]`
variant — each `main` runs exactly one `loop` and needs nothing concurrent —
but understanding it demystifies the attribute on `main` and models what you
will write as soon as a second concurrent job appears.

## Spawn and SpawnError

Spawning is fallible, and the type system says so:

```rust
pub enum SpawnError {
    Busy,              // the task is already spawned
    NoPoolMemory,      // small-capacity pool exhausted
    LargePoolMemory,
}

let result: Result<(), SpawnError> = spawner.spawn(my_task());
```

Firmware that must not panic over a pool condition handles the `Result`. In a
single-task design there is nothing to fail, so our binaries keep the code
simple — but the pattern matters once you decompose work into multiple Embassy
tasks.

## What the Executor Does

Conceptually, the executor's entire program is a loop:

```
+-------------+     +------------+     +-------------+
|  Wake event | --> |  Poll all  | --> |  Sleep (wfi)|
|  (IRQ)      |     |  ready tasks|    |  until next |
+-------------+     +------------+     +-------------+
```

- **Wake event** — An interrupt handler marks the affected future "ready."
- **Poll ready tasks** — The executor calls `poll` on every ready future,
  yielding `Ready` results and re-queueing those that return `Pending`.
- **Sleep** — With nothing ready, the CPU executes `wfi` (wait-for-interrupt)
  and stops dead, burning microamps until the next event.

That third state is the gift of async: a not-yet-expired timer is not a spinning
loop, it is a parked future. Two tasks, three tasks, ten tasks — as long as none
is ready, the core costs nothing.

## Summary

- The executor is a poll-and-sleep loop; futures make progress only when it
  polls them.
- `#[embassy_executor::main]` initializes the executor, builds a `Spawner`,
  spawns `main`, and never returns.
- `Spawner::spawn` registers new tasks; it is `Copy` and returns a `Result`
  when no pool slot is free.
- `#[embassy_executor::task]` turns any `async fn` into a spawnable task.
- Nothing ready → the core sleeps in `wfi`, drawing almost no power.

Next: time. What `Timer::after_millis` actually does.