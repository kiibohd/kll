kll - keyboard layout language
==============================

[![https://travis-ci.org/kiibohd/kll](https://travis-ci.org/kiibohd/kll.svg?branch=master)](https://travis-ci.org/kiibohd/kll)

[![Visit our IRC channel](https://kiwiirc.com/buttons/irc.freenode.net/input.club.png)](https://kiwiirc.com/client/irc.freenode.net/#input.club)

[Visit our Discord Channel](https://discord.gg/GACJa4f)

## If you're trying to compile keyboard firmware, you want [THIS](https://github.com/kiibohd/controller/)



KLL Compiler
------------

Most current version of the [KLL Spec](https://github.com/kiibohd/kll-spec).

Uses [funcparserlib](https://code.google.com/p/funcparserlib/)



Usage
-----

### General Usage

```bash
kll <kll files>
```

### Kiibohd Controller Usage

```bash
kll <misc kll files> --config <config/capability kll files> --base <basemap kll files) --default <default layer kll files> --partial <partial layer 1 kll files> --partial <partial layer 2 kll files>
```

See `kll --help` for the most up to date documentation



Unit Tests
----------

Unit tests can be found in the [tests](tests) directory.
They are run by Travis-CI, but can be useful when testing your own changes.

Remember to add new tests when adding new features/changes.



Code Organization
-----------------

* [common](common) - Main portion of KLL compiler.
* [emitters](emitters) - Various output formats of the KLL compiler.
* [examples](examples) - Example kll files, often used for test cases.
* [funcparserlib](funcparserlib) - Copy of funcparserlib with a few debugging enhancements.
* [layouts](layouts) - Layout kll files used for various keyboards and tests.
* [templates](templates) - Templates used by emitters when generating output.
* [tests](tests) - Unit tests for the KLL compiler.



Patches/Features/Backends
-------------------------

Completely welcome :D
