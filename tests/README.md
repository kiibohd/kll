# KLL Compiler - tests

Unit and functional tests for the KLL compiler.
Some tests are stand-alone, while others require some additional git repositories (automatically downloaded).


## Tests

Description of each of the KLL compiler tests.

To run the tests, use pytest

```bash
# All tests
pytest

# Multiple in parallel
pytest -n 8

# Show all output, even if test passes
pytest -s

# Run a specific file of tests
pytest tests/test_sanity.py

# Run a specific test in a file of tests
pytest tests/test_sanity.py -k test_help
```


### [controller](test_controller.py)

Calls `kll_regen` target on each of the main keyboard targets of the [Kiibohd Controller firmware](https://github.com/kiibohd/controller).
Validates that no KLL compiler changes have broken Input Club keyboards.
Uses the [kiibohd](../emitters/kiibohd) KLL compiler emitter.
Will clone a copy of the Kiibohd Controller firmware to `/tmp`.


### [kiibohd](test_kiibohd.py)

Call the KLL compiler in the same way the [Kiibohd Controller firmware](https://github.com/kiibohd/controller) would, but for test cases that are not used in a typical keyboard.
Used for KLL compiler feature testing.
Uses the [kiibohd](../emitters/kiibohd) KLL compiler emitter.
Will clone a copy of the Kiibohd Controller firmware to `/tmp`.


### [regen](test_regen.py)

Using the [kll](../emitters/kll) KLL compiler emitter regenerate KLL files, then validate the final kll against [cmp_regen](cmp_regen) using the `diff` tool.


### [sanity](test_sanity.py)

Call `--version` to make sure there are no Python syntax errors.
Call `--help` to make sure there are no Python syntax errors.


### [syntax](test_syntax.py)

Using the [none](../emitters/none) KLL compiler emitter, use various kll files to validate syntax parsing and tokenization.


## Files

Brief description of some general files.

* [klltest.py](klltest.py) - Functions used across many/all of the tests.

