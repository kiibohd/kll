kll - keyboard layout language
==============================

[![https://travis-ci.org/kiibohd/kll](https://travis-ci.org/kiibohd/kll.svg?branch=master)](https://travis-ci.org/kiibohd/kll)

[![Visit our IRC channel](https://kiwiirc.com/buttons/irc.freenode.net/input.club.png)](https://kiwiirc.com/client/irc.freenode.net/#input.club)

## If you're trying to compile keyboard firmware, you want [THIS](https://github.com/kiibohd/controller/)

KLL Compiler
------------

Most current version of the [KLL Spec](http://input.club/kll).

Uses [funcparserlib](https://code.google.com/p/funcparserlib/)


Usage
-----

### General Usage

```bash
kll.py <kll files>
```

### Kiibohd Controller Usage

```bash
kll.py <basemap kll files> --default <default layer kll files> --partial <partial layer 1 kll files> --partial <partial layer 2 kll files> --backend kiibohd --templates templates/kiibohdKeymap.h templates/kiibohdDefs.h --outputs generatedKeymap.h kll_defs.h
```

See `kll.py --help` for the most up to date documentation


Patches/Features/Backends
-------------------------

Completely welcome :D
