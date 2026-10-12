# Chapter 9: memory.x and the Linker Script

## Introduction

A microcontroller does not load firmware into a blank process. Code must land at
specific addresses: the bootrom looks for specific headers in flash, the vector
table must be at the flash base, and the stack pointer must be initialized to
the top of RAM before the first Rust instruction runs. The **linker script**
expresses those facts. In embedded Rust it is a file called `memory.x`, and it
is the same for all three of our drivers.

## The RP2350 Memory Regions

The linker script starts by naming the chip's physical memory regions and their
sizes:

```
0x10000000  FLASH  4096K   (XIP, firmware)
0x20000000  RAM    512K    (stack + data)
0x20080000  SRAM8   4K     (bootrom scratch)
0x20081000  SRAM9   4K     (bootrom scratch)
```

In linker script syntax this becomes the `MEMORY` block:

```
MEMORY {
    FLASH : ORIGIN = 0x10000000, LENGTH = 4096K
    RAM   : ORIGIN = 0x20000000, LENGTH = 512K
    SRAM8 : ORIGIN = 0x20080000, LENGTH = 4K
    SRAM9 : ORIGIN = 0x20081000, LENGTH = 4K
}
```

`SRAM8` and `SRAM9` are the bootrom's private scratch regions. They appear in
the script because the RP2350 bootrom implements part of its secure-boot
handshake there, but our firmware itself runs from `FLASH` and `RAM`.

## Complete Linker Script

Here is the full `memory.x` shared by all three drivers:

```
MEMORY {
    FLASH : ORIGIN = 0x10000000, LENGTH = 4096K
    RAM   : ORIGIN = 0x20000000, LENGTH = 512K
    SRAM8 : ORIGIN = 0x20080000, LENGTH = 4K
    SRAM9 : ORIGIN = 0x20081000, LENGTH = 4K
}

_stack_start = ORIGIN(RAM) + LENGTH(RAM);

SECTIONS {
    .start_block : ALIGN(4)
    {
        __start_block_addr = .;
        KEEP(*(.start_block));
        KEEP(*(.boot_info));
    } > FLASH
} INSERT AFTER .vector_table;

_stext = ADDR(.start_block) + SIZEOF(.start_block);

SECTIONS {
    .bi_entries : ALIGN(4)
    {
        __bi_entries_start = .;
        KEEP(*(.bi_entries));
        . = ALIGN(4);
        __bi_entries_end = .;
    } > FLASH
} INSERT AFTER .text;

SECTIONS {
    .end_block : ALIGN(4)
    {
        __end_block_addr = .;
        KEEP(*(.end_block));
    } > FLASH
} INSERT AFTER .uninit;

PROVIDE(start_to_end = __end_block_addr - __start_block_addr);
PROVIDE(end_to_start = __start_block_addr - __end_block_addr);
```

## The Start Block

The RP2350 bootrom does not boot a raw executable. It boots an **image
definition** — a preamble plus a list of "boot info" entries that describe the
image type, the entry point, and signatures. Embassy generates this preamble for
us when we enable `imagedef-secure-exe` (Chapter 8); the linker must reserve
space for it at a known offset.

```
0x10000000 +---------------------+
           |  .vector_table      |   (cortex-m-rt)
           |                     |
           +---------------------+
           |  .start_block       |   INSERT AFTER .vector_table
           |   __start_block_addr|
           |   KEEP .start_block |
           |   KEEP .boot_info   |
           +---------------------+
           |  .text ...          |
           +---------------------+
```

`.start_block` collects every `.start_block` and `.boot_info` input section and
keeps them even if the linker would otherwise garbage-collect them (`KEEP`).
`INSERT AFTER .vector_table` places this block immediately after the vector
table, which is where the RP2350 bootrom expects the image definition.

## Boot Info Entries

The bootrom also needs an array of boot-info entries — the tag list describing
size, flags, and image type. The `.bi_entries` section collects them and
publishes their bounds so firmware can locate them:

```
SECTIONS {
    .bi_entries : ALIGN(4)
    {
        __bi_entries_start = .;
        KEEP(*(.bi_entries));
        . = ALIGN(4);
        __bi_entries_end = .;
    } > FLASH
} INSERT AFTER .text;
```

The `.` symbols are **location counters** — read them as "memory address right
now." `__bi_entries_start` is the address of the first byte of the array;
`__bi_entries_end` is one past the last byte, aligned up to four. Any code that
must walk the phrase table uses these two symbols to know its extents.

## The End Block

The end marker closes the image:

```
SECTIONS {
    .end_block : ALIGN(4)
    {
        __end_block_addr = .;
        KEEP(*(.end_block));
    } > FLASH
} INSERT AFTER .uninit;
```

`INSERT AFTER .uninit` places it at the very end of the image, after all code,
data, and uninitialized sections. The bootrom uses these blocks plus the size
symbols to validate the image.

## Provided Symbols

The final statements expose computed addresses to the firmware:

```
PROVIDE(start_to_end = __end_block_addr - __start_block_addr);
PROVIDE(end_to_start = __start_block_addr - __end_block_addr);
```

`PROVIDE` defines a symbol **only if the firmware has not already defined it**.
`start_to_end` is the image size in bytes (distance from the start-block address
to the end-block address); `end_to_start` is its negative. The Embassy RP2350
support code reads these to help the bootrom verify the image.

## Why This Matters

Every one of these addresses is a *number* in the language of Chapter 2:

```
0x10000000  firmware base (BOOT2 image start)
0x20000000  stack base; top of RAM is the first SP value
0x20080000  SRAM8 — secure-boot scratch
0x20081000  SRAM9 — secure-boot scratch
```

When your board flashes and boots, the hardware is literally reading these
regions: the vector table, then the image definition, then code. If the linker
places the start block in the wrong spot, the bootrom radios nothing but
silence. `memory.x` is how we keep the promise that code lands where the
hardware expects it.

## Summary

- `MEMORY` declares `FLASH` at `0x10000000`, `RAM` at `0x20000000`, and the two
  SRAM8/9 scratch regions.
- `_stack_start` is the top of RAM — the initial stack pointer.
- `.start_block` + `.boot_info` form the RP2350 image definition after the
  vector table.
- `.bi_entries` holds the boot-info entry array with published bounds.
- `.end_block` closes the image; `start_to_end`/`end_to_start` expose sizes.
- The side effects (`imagedef-secure-exe`) and this script together make the
  .uf2 bootable.

Next, `build.rs`, the Makefile, and getting firmware onto the chip.