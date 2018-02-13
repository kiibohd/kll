# KLL Compiler - common

This is where the bulk of the KLL compiler processing occurs.
Including all of the datastructures used to contain the parsed expressions.


## Files

Brief description of each of the files.


### Process

Files that deal with file and expression processing.
Including parsing and tokenization.


* [emitter.py](emitter.py) - Base classes for [KLL emitters](../emitters).
* [parse.py](parse.py) - Contains most of the KLL xBNF parsing rules and how to map them to datastructure.
* [stage.py](stage.py) - Handles each stage of KLL file processing, from file reading to emitter output. This is where to start if you're unsure.


### Datastructure

Datastructure assembly classes used to contain KLL data.

* [channel.py](channel.py) - Container classes for KLL pixel channels.
* [context.py](context.py) - Container classes for KLL contexts (e.g. Generic, Configuration, BaseMap, DefaultMap, PartialMap and Merge).
* [expression.py](expression.py) - Container classes for KLL expressions (e.g. MapExpression, etc.).
* [file.py](file.py) - Container class for reading kll files.
* [id.py](id.py) - Container classes for KLL id elements (e.g. HIDId, PixelId, ScanCodeId, NoneId, etc.).
* [modifier.py](modifier.py) - Container classes for KLL modifiers (e.g. AnimationModifier, PixelModifier, etc.).
* [organization.py](organization.py) - Container classes for expression organizations. Handles expression merging.
* [position.py](position.py) - Container class for physical KLL positions.
* [schedule.py](schedule.py) - Container class for KLL schedules and schedule parameters.


### Constants

Lookup tables and other static data.

* [hid_dict.py](hid_dict.py) - Dictionary lookup for USB HID codes (both symbolic and numeric).

