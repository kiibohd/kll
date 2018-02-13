# KLL Compiler - tests

Unit and functional tests for the KLL compiler.
Some tests are stand-alone, while others require some additional git repositories (automatically downloaded).


## Tests

Description of each of the KLL compiler tests.


### [controller](controller.bash)

Calls `kll_regen` target on each of the main keyboard targets of the [Kiibohd Controller firmware](https://github.com/kiibohd/controller).
Validates that no KLL compiler changes have broken Input Club keyboards.
Uses the [kiibohd](../emitters/kiibohd) KLL compiler emitter.
Will clone a copy of the Kiibohd Controller firmware to `/tmp`.


### [kiibohd](kiibohd.bash)

Call the KLL compiler in the same way the [Kiibohd Controller firmware](https://github.com/kiibohd/controller) would, but for test cases that are not used in a typical keyboard.
Used for KLL compiler feature testing.
Uses the [kiibohd](../emitters/kiibohd) KLL compiler emitter.
Will clone a copy of the Kiibohd Controller firmware to `/tmp`.


### [regen](regen.bash)

Using the [kll](../emitters/kll) KLL compiler emitter regenerate KLL files, then validate the final kll against [cmp_regen](cmp_regen) using the `diff` tool.


### [sanity](sanity.bash)

Call `--version` to make sure there are no Python syntax errors.


### [syntax](syntax.bash)

Using the [none](../emitters/none) KLL compiler emitter, use various kll files to validate syntax parsing and tokenization.


## Files

Brief description of some general files.

* [common.bash](common.bash) - Generic bash library of functions for KLL compiler tests.

