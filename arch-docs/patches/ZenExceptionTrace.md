# ZenExceptionTrace

- **Source:** `src/ZenExceptionTrace/` (CommonLibSSE-NG, AE / Address Library; `build.cmd`)
- **Ships:** nothing — **testing tool, not part of the list**. Output `_ZenExceptionTrace.dll` (the `_` makes SKSE load it
  before most plugins)
- **FormID block:** _(none)_

## What it does

Adds a vectored exception handler at SKSE load. Every first-chance exception whose stack holds a frame in `kTarget`
(`Shatterveil.dll`) is logged to `My Games/Skyrim Special Edition/SKSE/_ZenExceptionTrace.log`: the code, the faulting
module + RVA, an access violation's address, a C++ exception's type and `what()`, and the stack as module + RVA. It
changes nothing. Change `kTarget` to trace another plugin.

## Why (2026-10-28)

SKSE catches an exception thrown inside a plugin's `SKSEPlugin_Load`, reports only "fatal error occurred while loading
plugin" and disables it; when that happens before the plugin's logger starts, nothing says why. The first run found
Shatterveil's null read at `+0x11793D` (its logger's missing 1.7.104 ID; see [`ShatterveilAE`](ShatterveilAE.md)).

## Deploy for a test

Copy `compiled/_ZenExceptionTrace.dll` into any enabled mod's `SKSE/Plugins/`, launch, read the log, then remove it.
