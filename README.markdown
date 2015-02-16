kll - keyboard layout language
==============================

KLL Compiler
------------

Most current version of the [KLL Spec](https://www.writelatex.com/read/zzqbdwqjfwwf).
Or visit [kiibohd.com](http://kiibohd.com)

Uses [funcparserlib](https://code.google.com/p/funcparserlib/)


Usage
-----

### General Usage
```kll.py <kll files>
```

### Kiibohd Controller Usage
```kll.py <basemap kll files> --default <default layer kll files> --partial <partial layer 1 kll files> --partial <partial layer 2 kll files> --backend kiibohd --template templates/kiibohdKeymap.h --output generatedKeymap.h --defines-template templates/kiibohdDefs.h --defines-output kll_defs.h
```

See `kll.py --help` for the most up to date documentation


Patches/Features/Backends
-------------------------

Completely welcome :D


Spec Additions/Fixes
--------------------

Contact HaaTa via IRC (#geekhack@irc.freenode.net or #deskthority).
Or by email -> haata@kiibohd.com

