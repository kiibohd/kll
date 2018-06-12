# kll - keyboard layout language

[![https://travis-ci.org/kiibohd/kll](https://travis-ci.org/kiibohd/kll.svg?branch=master)](https://travis-ci.org/kiibohd/kll)

[![Visit our IRC channel](https://kiwiirc.com/buttons/irc.freenode.net/input.club.png)](https://kiwiirc.com/client/irc.freenode.net/#input.club)

[Visit our Discord Channel](https://discord.gg/GACJa4f)

## If you're trying to compile keyboard firmware, you want [THIS](https://github.com/kiibohd/controller/)



## KLL Compiler

Most current version of the [KLL Spec](https://github.com/kiibohd/kll-spec).

Uses [funcparserlib](https://github.com/vlasovskikh/funcparserlib)


## Dependencies

Dependencies can be installed manually, or by using a pipenv.

* [layouts-python](https://github.com/hid-io/layouts-python) -> [pip](https://pypi.org/project/layouts/)

```bash
pipenv install
pipenv run kll/kll --version
```

*or*

```bash
pip install layouts
```


## Usage

### General Usage

```bash
kll <kll files>
```

### Kiibohd Controller Usage

```bash
kll <misc kll files> --config <config/capability kll files> --base <basemap kll files) --default <default layer kll files> --partial <partial layer 1 kll files> --partial <partial layer 2 kll files>
```

See `kll --help` for the most up to date documentation



## Unit Tests

Unit tests can be found in the [tests](tests) directory.
They are run by Travis-CI, but can be useful when testing your own changes.

Remember to add new tests when adding new features/changes.



## Code Organization

* [kll/common](kll/common) - Main portion of KLL compiler.
* [kll/emitters](kll/emitters) - Various output formats of the KLL compiler.
* [kll/examples](kll/examples) - Example kll files, often used for test cases.
* [kll/extern](kll/extern) - External libraries, copied into git repo for convenience.
* [kll/layouts](kll/layouts) - Layout kll files used for various keyboards and tests.
* [kll/templates](kll/templates) - Templates used by emitters when generating output.
* [tests](tests) - Unit tests for the KLL compiler.



## Patches/Features/Backends

Completely welcome :D
