#!/usr/bin/env python3
'''
KLL Parsing Expressions

This file contains various parsing rules and processors used by funcparserlib for KLL

REMEMBER: When editing parser BNF-like expressions, order matters. Specifically lexer tokens and parser |
'''

# Parser doesn't play nice with linters, disable some checks
# pylint: disable=no-self-argument, too-many-public-methods, no-self-use, bad-builtin

# Copyright (C) 2016-2018 by Jacob Alexander
#
# This file is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This file is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this file.  If not, see <http://www.gnu.org/licenses/>.

### Imports ###

from kll.common.id import (
    AnimationId, AnimationFrameId,
    CapArgId, CapArgValue, CapId,
    HIDId,
    LayerId,
    NoneId,
    PixelAddressId, PixelId, PixelLayerId,
    ScanCodeId,
    TriggerId
)
from kll.common.modifier import AnimationModifierList
from kll.common.schedule import AnalogScheduleParam, ScheduleParam, Time

from kll.extern.funcparserlib.lexer import Token
from kll.extern.funcparserlib.parser import (some, a, many, oneplus, skip, maybe)



### Decorators ###

# Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'



### Classes ###

# Parsing Functions

class Make:
    '''
    Collection of parse string interpreters
    '''

    def scanCode(token):
        '''
        Converts a raw scan code string into an ScanCodeId /w integer

        S0x10 -> 16
        '''
        if isinstance(token, int):
            return ScanCodeId(token)
        else:
            return ScanCodeId(int(token[1:], 0))

    def hidCode(type, token):
        '''
        Convert a given raw hid token string to an integer /w a type

        U"Enter" -> USB, Enter(0x28)
        '''
        # If already converted to a HIDId, just return
        if isinstance(token, HIDId):
            return token

        # If first character is a U or I, strip
        token_val = token.value
        if token_val[0] == "U" or token_val[0] == "I":
            token_val = token_val[1:]
        # CONS specifier
        elif 'CONS' in token_val:
            token_val = token_val[4:]
        # SYS specifier
        elif 'SYS' in token_val:
            token_val = token_val[3:]

        # Determine locale
        locale = token.locale

        # Determine lookup dictionary
        lookup = None
        if type == 'USBCode':
            lookup = locale.dict('from_hid_keyboard', key_caps=True)
        elif type == 'SysCode':
            lookup = locale.dict('from_hid_sysctrl', key_caps=True)
        elif type == 'ConsCode':
            lookup = locale.dict('from_hid_consumer', key_caps=True)
        elif type == 'IndCode':
            lookup = locale.dict('from_hid_led', key_caps=True)

        # If using string representation of USB Code, do lookup, case-insensitive
        if '"' in token_val:
            try:
                match_name = token_val[1:-1].upper()
                hid_code = int(lookup[match_name], 0)
            except LookupError as err:
                print("{} {} ({}) is an invalid USB HID Code Lookup...".format(
                    ERROR,
                    err,
                    locale
                ))
                raise
        else:
            # Already tokenized
            if (
                type == 'USBCode' and token_val[0] == 'USB'
                    or
                type == 'SysCode' and token_val[0] == 'SYS'
                    or
                type == 'ConsCode' and token_val[0] == 'CONS'
                    or
                type == 'IndCode' and token_val[0] == 'IND'
            ):
                hid_code = token_val[1]
            # Convert
            else:
                hid_code = int(token_val, 0)

        return HIDId(type, hid_code, locale)

    def usbCode(token):
        '''
        Convert a given raw USB Keyboard hid token string to an integer /w a type

        U"Enter" -> USB, Enter(0x28)
        '''
        return Make.hidCode('USBCode', token)

    def consCode(token):
        '''
        Convert a given raw Consumer Control hid token string to an integer /w a type
        '''
        return Make.hidCode('ConsCode', token)

    def sysCode(token):
        '''
        Convert a given raw System Control hid token string to an integer /w a type
        '''
        return Make.hidCode('SysCode', token)

    def indCode(token):
        '''
        Convert a given raw Indicator hid token string to an integer /w a type
        '''
        return Make.hidCode('IndCode', token)

    def animation(name):
        '''
        Converts a raw animation value into an AnimationId /w name

        A"myname" -> myname
        '''
        if name[0] == "A":
            return AnimationId(name[2:-1])
        else:
            return AnimationId(name)

    def animationTrigger(animation, specifier):
        '''
        Generate an AnimationId
        '''
        trigger_list = []

        # AnimationId
        trigger_list.append(AnimationId(animation))

        return trigger_list, specifier

    def animationAssociation(animation, frame_identifier):
        '''
        Generate an AnimationFrameId
        '''
        trigger_list = []

        # AnimationFrameId
        for index in frame_identifier:
            trigger_list.append([[AnimationFrameId(animation, index)]])

        return trigger_list

    def animationCapability(animation, modifiers):
        '''
        Apply modifiers to AnimationId
        '''
        if modifiers is not None:
            animation.setModifiers(modifiers)
        return [animation]

    def animationModlist(modifiers):
        '''
        Build an AnimationModifierList

        Only used for animation data association
        '''
        modlist = AnimationModifierList()
        modlist.setModifiers(modifiers)
        return modlist

    def pixelCapability(pixels, modifiers):
        '''
        Apply modifiers to list of pixels/pixellists

        Results in a combination of pixel capabilities
        '''
        pixelcap_list = []
        for pixel in pixels:
            pixel.setModifiers(modifiers)
            pixelcap_list.append(pixel)
        return pixelcap_list

    def pixel(token):
        '''
        Converts a raw pixel value into a PixelId /w integer

        P0x3 -> 3
        '''
        if isinstance(token, int):
            return PixelId(token)
        else:
            return PixelId(int(token[1:], 0))

    def pixel_list(pixel_list):
        '''
        Converts a list a numbers into a list of PixelIds
        '''
        pixels = []
        for pixel in pixel_list:
            pixels.append(PixelId(pixel))
        return pixels

    def pixelLayer(token):
        '''
        Converts a raw pixel layer value into a PixelLayerId /w integer

        PL0x3 -> 3
        '''
        if isinstance(token, int):
            return PixelLayerId(token)
        else:
            return PixelLayerId(int(token[2:], 0))

    def pixelLayer_list(layer_list):
        '''
        Converts a list a numbers into a list of PixelLayerIds
        '''
        layers = []
        for layer in layer_list:
            layers.append(PixelLayerId(layer))
        return layers

    def pixelchan(pixel_list, chans):
        '''
        Apply channels to PixelId

        Only one pixel at a time can be mapped, hence pixel_list[0]
        '''
        pixel = pixel_list[0]
        pixel.setChannels(chans)
        return pixel

    def pixelmod(pixels, modifiers):
        '''
        Apply modifiers to list of pixels/pixellists

        Results in a combination of pixel capabilities
        '''
        pixelcap_list = []
        for pixel in pixels:
            # Convert HIDIds into PixelIds
            if isinstance(pixel, HIDId) or isinstance(pixel, ScanCodeId):
                pixel = PixelId(pixel)
            pixel.setModifiers(modifiers)
            pixelcap_list.append(pixel)
        return pixelcap_list

    def pixel_address(elems):
        '''
        Parse pixel positioning for row/column addressing

        @param elems:  index list or (operator, value)

        40
        c:0
        c:30%
        r:i+30
        '''
        pixel_address_list = []

        # Index list
        if isinstance(elems, list):
            # List of integers, possibly a range
            if isinstance(elems[0], int):
                for elem in elems:
                    pixel_address_list.append(PixelAddressId(index=elem))
            # Already ready to append
            elif isinstance(elems[0], PixelId):
                pixel_address_list.append(elems[0])

        # No value
        elif isinstance(elems, Token):
            # Row
            if "r:i" in elems.name:
                pixel_address_list.append(PixelAddressId(relRow=0))
            # Column
            if "c:i" in elems.name:
                pixel_address_list.append(PixelAddressId(relCol=0))

        # Operator with value
        elif isinstance(elems[0], Token):
            # Prepare address value
            value = elems[1]

            # Positioning
            if elems[0].type == "ColRowOperator":
                # Row
                if elems[0].name == "r:":
                    pixel_address_list.append(PixelAddressId(row=value))
                # Column
                if elems[0].name == "c:":
                    pixel_address_list.append(PixelAddressId(col=value))

            # Relative Positioning
            elif elems[0].type == "RelCROperator":
                if '-' in elems[0].name:
                    value *= -1

                # Row
                if "r:i" in elems[0].name:
                    pixel_address_list.append(PixelAddressId(relRow=value))
                # Column
                if "c:i" in elems[0].name:
                    pixel_address_list.append(PixelAddressId(relCol=value))

        return pixel_address_list

    def pixel_address_merge(elems):
        '''
        Merge pixel addresses together
        '''
        # Merge is only necessary if there is more than one element
        if len(elems) > 1:
            for elem in elems[1:]:
                elems[0].merge(elem)

        return [elems[0]]

    def position(token):
        '''
        Physical position split

        x:20 -> (x, 20)
        '''
        return token.split(':')

    def usbCode_number(token):
        '''
        USB Keyboard HID Code lookup
        '''
        return HIDId('USBCode', token.value, token.locale)

    def consCode_number(token):
        '''
        Consumer Control HID Code lookup
        '''
        return HIDId('ConsCode', token.value, token.locale)

    def sysCode_number(token):
        '''
        System Control HID Code lookup
        '''
        return HIDId('SysCode', token.value, token.locale)

    def indCode_number(token):
        '''
        Indicator HID Code lookup
        '''
        return HIDId('IndCode', token.value, token.locale)

    def none(token):
        '''
        Replace key-word with NoneId specifier (which indicates a noneOut capability)
        '''
        return [[[NoneId()]]]

    def seqString(token, spec='lspec'):
        '''
        Converts sequence string to a sequence of combinations

        'Ab'  -> U"Shift" + U"A", U"B"
        'abb' -> U"A", U"B", U"NoEvent", U"B"

        @param spec: 'lspec' or 'rspec'
        '''
        # Determine locale
        locale = token.locale

        # Compose string using set locale
        sequence = None
        if spec == 'lspec':
            sequence = locale.compose(token.value[1:-1], minimal_clears=True, no_clears=True)
        else:
            sequence = locale.compose(token.value[1:-1], minimal_clears=True)

        # Convert each element in sequence of combos to HIDIds
        hid_ids = []
        for combo in sequence:
            new_combo = []
            for elem in combo:
                # Lookup uid (usb code) from alias name (used in sequence)
                new_elem = HIDId('USBCode', int(locale.json()['from_hid_keyboard'][elem], 0), locale)
                new_combo.append(new_elem)
            hid_ids.append(new_combo)

        return hid_ids

    def seqStringL(token):
        '''
        Converts sequence string to a sequence of combinations
        lspec side

        'Ab'  -> U"Shift" + U"A", U"B"
        'abb' -> U"A", U"B", U"NoEvent", U"B"
        '''
        return Make.seqString(token, 'lspec')

    def seqStringR(token):
        '''
        Converts sequence string to a sequence of combinations
        rspec side

        'Ab'  -> U"Shift" + U"A", U"B"
        'abb' -> U"A", U"B", U"NoEvent", U"B"
        '''
        return Make.seqString(token, 'rspec')

    def string(token):
        '''
        Converts a raw string to a Python string

        "this string" -> this string
        '''
        return token[1:-1]

    def unseqString(token):
        '''
        Converts a raw sequence string to a Python string

        'this string' -> this string
        '''
        return token[1:-1]

    def number(token):
        '''
        Convert string number to Python integer
        '''
        return int(token, 0)

    def neg_number(dash, number):
        '''
        If a dash is provided, then the number is negative
        '''
        if dash is not None:
            number = number * -1
        return number

    def numberToken(token):
        '''
        Convert token value to Python integer
        '''
        try:
            token.value = int(token.value, 0)
        except TypeError:
            pass
        return token

    def percent(token):
        '''
        Convert string percent to Python float
        '''
        return int(token[:-1], 0) / 100.0

    def timing(token):
        '''
        Convert raw timing parameter to integer time and determine units

        1ms -> 1, ms
        '''
        # Find ms, us, or s
        if 'ms' in token:
            unit = 'ms'
            num = token.split('m')[0]
        elif 'us' in token:
            unit = 'us'
            num = token.split('u')[0]
        elif 'ns' in token:
            unit = 'ns'
            num = token.split('n')[0]
        elif 's' in token:
            unit = 's'
            num = token.split('s')[0]
        else:
            print("{0} cannot find timing unit in token '{1}'".format(ERROR, token))

        return Time(float(num), unit)

    def specifierTiming(timing):
        '''
        When only timing is given, infer state at a later stage from the context of the mapping
        '''
        return ScheduleParam(None, timing)

    def specifierState(state, timing=None):
        '''
        Generate a Schedule Parameter
        Automatically mutates itself into the correct object type
        '''
        return ScheduleParam(state, timing)

    def specifierAnalog(value):
        '''
        Generate an Analog Schedule Parameter
        '''
        return AnalogScheduleParam(value)

    def specifierUnroll(identifier, schedule_params):
        '''
        Unroll specifiers into the trigger/result identifier

        First, combine all Schedule Parameters into a Schedul
        Then attach Schedule to the identifier

        If the identifier is a list, then iterate through them
        and apply the schedule to each
        '''
        # Check if this is a list of identifiers
        if isinstance(identifier, list):
            for ident in identifier:
                ident.setSchedule(schedule_params)
            return identifier
        else:
            identifier.setSchedule(schedule_params)

        return [identifier]

    def layerTypeIdent(layer_type, inner_list, specifier):
        '''
        Given a layer expression, determine what kind of layer expression

        Layer
        LayerShift
        LayerLatch
        LayerLock
        '''
        # Determine layer type (remove [)
        layer_type = layer_type[:-1]

        # Add layer type to each given layer
        identifier_list = []
        for layer in inner_list:
            identifier_list.append(LayerId(layer_type, layer))

        return identifier_list, specifier

    def genericTriggerIdent(identifier, code, specifier):
        '''
        Given a generic trigger, create a TriggerId object

        Generic Triggers don't support ranges
        '''
        trigger_obj = TriggerId(identifier, code)

        return trigger_obj, specifier

    # Range can go from high to low or low to high
    def scanCode_range(rangeVals):
        '''
        Scan Code range expansion

        S[0x10-0x12] -> S0x10, S0x11, S0x12
        '''
        start = rangeVals[0]
        end = rangeVals[1]

        # Swap start, end if start is greater than end
        if start > end:
            start, end = end, start

        # Iterate from start to end, and generate the range
        values = list(range(start, end + 1))

        # Generate ScanCodeIds
        return [ScanCodeId(v) for v in values]

    # Range can go from high to low or low to high
    # Warn on 0-9 for USBCodes (as this does not do what one would expect) TODO
    # Lookup USB HID tags and convert to a number
    def hidCode_range(type, rangeVals):
        '''
        HID Code range expansion

        U["A"-"C"] -> U"A", U"B", U"C"
        '''

        # Check if already integers
        if isinstance(rangeVals[0], int):
            start = rangeVals[0]
        else:
            start = Make.hidCode(type, rangeVals[0]).uid

        if isinstance(rangeVals[1], int):
            end = rangeVals[1]
        else:
            end = Make.hidCode(type, rangeVals[1]).uid

        # Swap start, end if start is greater than end
        if start > end:
            start, end = end, start

        # Iterate from start to end, and generate the range
        listRange = list(range(start, end + 1))

        # Determine locale
        locale = rangeVals[0].locale

        # Convert each item in the list to a tuple
        for item in range(len(listRange)):
            listRange[item] = HIDId(type, listRange[item], locale)
        return listRange

    def usbCode_range(rangeVals):
        '''
        USB Keyboard HID Code range expansion
        '''
        return Make.hidCode_range('USBCode', rangeVals)

    def sysCode_range(rangeVals):
        '''
        System Control HID Code range expansion
        '''
        return Make.hidCode_range('SysCode', rangeVals)

    def consCode_range(rangeVals):
        '''
        Consumer Control HID Code range expansion
        '''
        return Make.hidCode_range('ConsCode', rangeVals)

    def indCode_range(rangeVals):
        '''
        Indicator HID Code range expansion
        '''
        return Make.hidCode_range('IndCode', rangeVals)

    def range(start, end):
        '''
        Converts a start and end points of a range to a list of numbers

        Can go low to high or high to low
        '''
        # High to low
        if end < start:
            return list(range(end, start + 1))

        # Low to high
        return list(range(start, end + 1))

    def capArg(argument, width=None):
        '''
        Converts a capability argument:width to a CapArgId

        If no width is specified, it is ignored
        '''
        return CapArgId(argument, width)

    def capArgValue(tuple_value):
        '''
        Converts a capability argument value to a CapArgValue
        '''
        sign, value = tuple_value
        if sign is not None:
            value *= -1
        return CapArgValue(value)

    def capUsage(name, arguments):
        '''
        Converts a capability tuple, argument list to a CapId Usage
        '''
        return CapId(name, 'Capability', arguments)

    def debug(tokens):
        '''
        Just prints tokens
        Used for debugging
        '''
        print(tokens)
        return tokens


### Rules ###

# Base Rules


def const(x): return lambda _: x


def unarg(f): return lambda x: f(*x)


def flatten(list): return sum(list, [])


def tokenValue(x):
    '''
    Return string value of a token

    @param x: Token
    @returns: String value of token
    '''
    return x.value


def tokenType(t):
    '''
    Returns string of token

    @param t: Name of token type
    @returns: String of token
    '''
    return some(lambda x: x.type == t) >> tokenValue


def tokenTypeOnly(t):
    '''
    Returns the full token object

    @param t: Name of token type
    @return: Token matching
    '''
    return some(lambda x: x.type == t)


def operator(s): return a(Token('Operator', s)) >> tokenValue


def parenthesis(s): return a(Token('Parenthesis', s)) >> tokenValue


def bracket(s): return a(Token('Bracket', s)) >> tokenValue


eol = a(Token('EndOfLine', ';'))


def maybeFlatten(items):
    '''
    Iterate through top-level lists
    Flatten, only if the element is also a list

    [[1,2],3,[[4,5]]] -> [1,2,3,[4,5]]
    '''
    new_list = []
    for elem in items:
        # Flatten only if a list
        if isinstance(elem, list):
            new_list.extend(elem)
        else:
            new_list.append(elem)
    return new_list


def listElem(item):
    '''
    Convert to a list element
    '''
    return [item]


def listToTuple(items):
    '''
    Convert list to a tuple
    '''
    return tuple(items)


def oneLayerFlatten(items):
    '''
    Flatten only the top layer (list of lists of ...)
    '''
    mainList = []
    for sublist in items:
        for item in sublist:
            mainList.append(item)

    return mainList


def optionCompression(sequence):
    '''
    Adds another dimension to a list of lists.

    This is the inverse operation of optionExpansion, iff there were no expanded ranges

    @param: sequence: Sequence of combos
    @returns: Squence of combos of ranges
    '''
    new_list = []
    for combo in sequence:
        new_combo = []
        for elem in combo:
            new_combo.append([elem])
        new_list.append(new_combo)

    return new_list


def optionExpansion(sequences):
    '''
    Expand ranges of values in the 3rd dimension of the list, to a list of 2nd lists

    i.e. [ sequence, [ combo, [ range ] ] ] --> [ [ sequence, [ combo ] ], <option 2>, <option 3> ]

    @param sequences: Sequence of combos of ranges
    @returns: List of sequences of combos
    '''
    expandedSequences = []

    # Total number of combinations of the sequence of combos that needs to be generated
    totalCombinations = 1

    # List of leaf lists, with number of leaves
    maxLeafList = []

    # Traverse to the leaf nodes, and count the items in each leaf list
    for sequence in sequences:
        for combo in sequence:
            rangeLen = len(combo)
            totalCombinations *= rangeLen
            maxLeafList.append(rangeLen)

    # Counter list to keep track of which combination is being generated
    curLeafList = [0] * len(maxLeafList)

    # Generate a list of permuations of the sequence of combos
    for count in range(0, totalCombinations):
        expandedSequences.append([])  # Prepare list for adding the new combination
        pos = 0

        # Traverse sequence of combos to generate permuation
        for sequence in sequences:
            expandedSequences[-1].append([])
            for combo in sequence:
                expandedSequences[-1][-1].append(combo[curLeafList[pos]])
                pos += 1

        # Increment combination tracker
        for leaf in range(0, len(curLeafList)):
            curLeafList[leaf] += 1

            # Reset this position, increment next position (if it exists), then stop
            if curLeafList[leaf] >= maxLeafList[leaf]:
                curLeafList[leaf] = 0
                if leaf + 1 < len(curLeafList):
                    curLeafList[leaf + 1] += 1

    return expandedSequences


def listit(t):
    '''
    Convert tuple of tuples to list of lists
    '''
    return list(map(listit, t)) if isinstance(t, (list, tuple)) else t


def tupleit(t):
    '''
    Convert list of lists to tuple of tuples
    '''
    return tuple(map(tupleit, t)) if isinstance(t, (tuple, list)) else t


# Sub Rules

usbCode = tokenTypeOnly('USBCode') >> Make.usbCode
scanCode = tokenType('ScanCode') >> Make.scanCode
consCode = tokenTypeOnly('ConsCode') >> Make.consCode
sysCode = tokenTypeOnly('SysCode') >> Make.sysCode
indCode = tokenTypeOnly('IndCode') >> Make.indCode
animation = tokenType('Animation') >> Make.animation
pixel = tokenType('Pixel') >> Make.pixel
pixelLayer = tokenType('PixelLayer') >> Make.pixelLayer
none = tokenType('None') >> Make.none
position = tokenType('Position') >> Make.position

comma = tokenType('Comma')
content = tokenType('VariableContents')
dash = tokenType('Dash')
name = tokenType('Name')
number = tokenType('Number') >> Make.number
neg_number = maybe(dash) + number >> unarg(Make.neg_number)
numberToken = tokenTypeOnly('Number') >> Make.numberToken
percent = tokenType('Percent') >> Make.percent
plus = tokenType('Plus')
timing = tokenType('Timing') >> Make.timing

string = tokenType('String') >> Make.string
unString = tokenTypeOnly('String')  # When the double quotes are still needed for internal processing
seqStringL = tokenTypeOnly('SequenceStringL') >> Make.seqStringL >> optionCompression # lspec
seqStringR = tokenTypeOnly('SequenceStringR') >> Make.seqStringR >> optionCompression # rspec
unseqString = tokenType('SequenceString') >> Make.unseqString  # For use with variables


def colRowOperator(s): return a(Token('ColRowOperator', s))


def relCROperator(s): return a(Token('RelCROperator', s))


pixelOperator = tokenType('PixelOperator')

# Code variants
code_begin = tokenType('CodeBegin')
code_end = tokenType('CodeEnd')

# Specifier
specifier_basic = (timing >> Make.specifierTiming) | (name >> Make.specifierState)
specifier_complex = (name + skip(operator(':')) + timing) >> unarg(Make.specifierState)
specifier_state = specifier_complex | specifier_basic
specifier_analog = number >> Make.specifierAnalog
specifier_list = skip(parenthesis('(')) + many((specifier_state | specifier_analog) + skip(maybe(comma))) + skip(parenthesis(')'))

# Scan Codes
scanCode_start = tokenType('ScanCodeStart')
scanCode_range = number + skip(dash) + number >> Make.scanCode_range
scanCode_listElem = number >> Make.scanCode
scanCode_specifier = (scanCode_range | scanCode_listElem) + maybe(specifier_list) >> unarg(Make.specifierUnroll)
scanCode_innerList = many(scanCode_specifier + skip(maybe(comma))) >> flatten
scanCode_expanded = skip(scanCode_start) + scanCode_innerList + skip(code_end) + maybe(specifier_list) >> unarg(Make.specifierUnroll)
scanCode_elem = scanCode + maybe(specifier_list) >> unarg(Make.specifierUnroll)
scanCode_combo_elem = scanCode_expanded | scanCode_elem
scanCode_single = (skip(scanCode_start) + scanCode_listElem + skip(code_end)) | scanCode
scanCode_il_nospec = oneplus((scanCode_range | scanCode_listElem) + skip(maybe(comma)))
scanCode_nospecifier = skip(scanCode_start) + scanCode_il_nospec + skip(code_end)

# Cons Codes
consCode_start = tokenType('ConsCodeStart')
consCode_number = numberToken >> Make.consCode_number
consCode_range = (consCode_number | unString) + skip(dash) + (number | unString) >> Make.consCode_range
consCode_listElemTag = unString >> Make.consCode
consCode_listElem = (consCode_number | consCode_listElemTag)
consCode_specifier = (consCode_range | consCode_listElem) + maybe(specifier_list) >> unarg(Make.specifierUnroll)
consCode_innerList = oneplus(consCode_specifier + skip(maybe(comma))) >> flatten
consCode_expanded = skip(consCode_start) + consCode_innerList + skip(code_end) + maybe(specifier_list) >> unarg(Make.specifierUnroll)
consCode_elem = consCode + maybe(specifier_list) >> unarg(Make.specifierUnroll)
consCode_il_nospec = oneplus((consCode_range | consCode_listElem) + skip(maybe(comma)))
consCode_nospecifier = skip(consCode_start) + consCode_il_nospec + skip(code_end)

# Sys Codes
sysCode_start = tokenType('SysCodeStart')
sysCode_number = numberToken >> Make.sysCode_number
sysCode_range = (sysCode_number | unString) + skip(dash) + (number | unString) >> Make.sysCode_range
sysCode_listElemTag = unString >> Make.sysCode
sysCode_listElem = (sysCode_number | sysCode_listElemTag)
sysCode_specifier = (sysCode_range | sysCode_listElem) + maybe(specifier_list) >> unarg(Make.specifierUnroll)
sysCode_innerList = oneplus(sysCode_specifier + skip(maybe(comma))) >> flatten
sysCode_expanded = skip(sysCode_start) + sysCode_innerList + skip(code_end) + maybe(specifier_list) >> unarg(Make.specifierUnroll)
sysCode_elem = sysCode + maybe(specifier_list) >> unarg(Make.specifierUnroll)
sysCode_il_nospec = oneplus((sysCode_range | sysCode_listElem) + skip(maybe(comma)))
sysCode_nospecifier = skip(sysCode_start) + sysCode_il_nospec + skip(code_end)

# Indicator Codes
indCode_start = tokenType('IndicatorStart')
indCode_number = numberToken >> Make.indCode_number
indCode_range = (indCode_number | unString) + skip(dash) + (number | unString) >> Make.indCode_range
indCode_listElemTag = unString >> Make.indCode
indCode_listElem = (indCode_number | indCode_listElemTag)
indCode_specifier = (indCode_range | indCode_listElem) + maybe(specifier_list) >> unarg(Make.specifierUnroll)
indCode_innerList = oneplus(indCode_specifier + skip(maybe(comma))) >> flatten
indCode_expanded = skip(indCode_start) + indCode_innerList + skip(code_end) + maybe(specifier_list) >> unarg(Make.specifierUnroll)
indCode_elem = indCode + maybe(specifier_list) >> unarg(Make.specifierUnroll)
indCode_il_nospec = oneplus((indCode_range | indCode_listElem) + skip(maybe(comma)))
indCode_nospecifier = skip(indCode_start) + indCode_il_nospec + skip(code_end)

# USB Codes
usbCode_start = tokenType('USBCodeStart')
usbCode_number = numberToken >> Make.usbCode_number
usbCode_range = (usbCode_number | unString) + skip(dash) + (number | unString) >> Make.usbCode_range
usbCode_listElemTag = unString >> Make.usbCode
usbCode_listElem = (usbCode_number | usbCode_listElemTag)
usbCode_specifier = (usbCode_range | usbCode_listElem) + maybe(specifier_list) >> unarg(Make.specifierUnroll)
usbCode_il_nospec = oneplus((usbCode_range | usbCode_listElem) + skip(maybe(comma)))
usbCode_nospecifier = skip(usbCode_start) + usbCode_il_nospec + skip(code_end)
usbCode_innerList = oneplus(usbCode_specifier + skip(maybe(comma))) >> flatten
usbCode_expanded = skip(usbCode_start) + usbCode_innerList + skip(code_end) + maybe(specifier_list) >> unarg(Make.specifierUnroll)
usbCode_elem = usbCode + maybe(specifier_list) >> unarg(Make.specifierUnroll)

# HID Codes
hidCode_elem = usbCode_expanded | usbCode_elem | sysCode_expanded | sysCode_elem | consCode_expanded | consCode_elem | indCode_expanded | indCode_elem

# Layers
layer_start = tokenType('LayerStart')
layer_range = (number) + skip(dash) + (number) >> unarg(Make.range)
layer_listElem = number >> listElem
layer_innerList = oneplus((layer_range | layer_listElem) + skip(maybe(comma))) >> flatten
layer_expanded = layer_start + layer_innerList + skip(code_end) + maybe(specifier_list) >> unarg(Make.layerTypeIdent) >> unarg(Make.specifierUnroll)

# Generic Triggers
gtrigger_start = tokenType('TriggerStart')
gtrigger_parts = skip(gtrigger_start) + number + skip(comma) + number + skip(code_end) + maybe(specifier_list)
gtrigger_expanded = gtrigger_parts >> unarg(Make.genericTriggerIdent) >> unarg(Make.specifierUnroll)

# Pixels
pixel_start = tokenType('PixelStart')
pixel_range = (number) + skip(dash) + (number) >> unarg(Make.range) >> Make.pixel_address
pixel_listElem = number >> listElem >> Make.pixel_address
pixel_pos = (colRowOperator('c:') | colRowOperator('r:')) + (neg_number | percent) >> Make.pixel_address
pixel_posRel = (relCROperator('c:i+') | relCROperator('c:i-') | relCROperator('r:i+') | relCROperator('r:i-')) + (neg_number | percent) >> Make.pixel_address
pixel_posRelHere = (relCROperator('c:i') | relCROperator('r:i')) >> Make.pixel_address
pixel_posMerge = oneplus((pixel_pos | pixel_posRel | pixel_posRelHere) + skip(maybe(comma))) >> flatten >> Make.pixel_address_merge
pixel_innerList = ((oneplus((pixel_range | pixel_listElem | pixel_posMerge) + skip(maybe(comma))) >> flatten) | (pixel_posMerge)) >> Make.pixel_list
pixel_expanded = skip(pixel_start) + pixel_innerList + skip(code_end)
pixel_elem = pixel >> listElem >> Make.pixel_address

# Pixel Layer
pixellayer_start = tokenType('PixelLayerStart')
pixellayer_range = (number) + skip(dash) + (number) >> unarg(Make.range)
pixellayer_listElem = number >> listElem
pixellayer_innerList = oneplus((pixellayer_range | pixellayer_listElem) + skip(maybe(comma))) >> flatten >> Make.pixelLayer_list
pixellayer_expanded = skip(pixellayer_start) + pixellayer_innerList + skip(code_end)
pixellayer_elem = pixelLayer >> listElem

# Pixel Channels
pixelchan_chans = many(number + skip(operator(':')) + number + skip(maybe(comma)))
pixelchan_elem = ((pixel_expanded | pixel_elem) + skip(parenthesis('(')) + pixelchan_chans + skip(parenthesis(')'))) >> unarg(Make.pixelchan)

# HID Id for Pixel Mods
pixelmod_hid_elem = (usbCode | sysCode | consCode | indCode | scanCode) >> listElem
pixelmod_hid = pixelmod_hid_elem | usbCode_nospecifier | scanCode_nospecifier | consCode_nospecifier | sysCode_nospecifier | indCode_nospecifier

# Pixel Mods
pixelmod_modop = maybe(pixelOperator | plus | dash) >> listElem
pixelmod_modva = number >> listElem
pixelmod_mods = oneplus((pixelmod_modop + pixelmod_modva + skip(maybe(comma))) >> flatten)
pixelmod_layer = (pixellayer_expanded | pixellayer_elem)
pixelmod_index = (pixel_expanded | pixel_elem | pixelmod_hid | pixelmod_layer)
pixelmod_elem = pixelmod_index + skip(parenthesis('(')) + pixelmod_mods + skip(parenthesis(')')) >> unarg(Make.pixelmod)

# Pixel Capability
pixel_capability = pixelmod_elem

# Animations
animation_start = tokenType('AnimationStart')
animation_name = name
animation_frame_range = (number) + skip(dash) + (number) >> unarg(Make.range)
animation_name_frame = many((animation_frame_range | number) + skip(maybe(comma))) >> maybeFlatten
animation_def = skip(animation_start) + animation_name + skip(code_end) >> Make.animation
animation_expanded = skip(animation_start) + animation_name + skip(maybe(comma)) + animation_name_frame + skip(code_end) >> unarg(Make.animationAssociation)
animation_trigger = skip(animation_start) + animation_name + skip(code_end) + maybe(specifier_list) >> unarg(Make.animationTrigger) >> unarg(Make.specifierUnroll)
animation_flattened = animation_expanded >> flatten >> flatten
animation_elem = animation

# Animation Modifier
animation_modifier_arg = number | (name + skip(parenthesis('(')) + many(number + skip(maybe(comma))) + skip(parenthesis(')'))) | name
animation_modifier = many((name | number) + maybe(skip(operator(':')) + animation_modifier_arg) + skip(maybe(comma)))
animation_modlist = animation_modifier >> Make.animationModlist

# Animation Capability
animation_capability = ((animation_def | animation_elem) + maybe(skip(parenthesis('(')) + animation_modifier + skip(parenthesis(')')))) >> unarg(Make.animationCapability)

# Capabilities
capFunc_argument = (maybe(dash) + number) >> Make.capArgValue  # TODO Allow for symbolic arguments, i.e. arrays and variables
capFunc_arguments = many(capFunc_argument + skip(maybe(comma)))
capFunc_elem = name + skip(parenthesis('(')) + capFunc_arguments + skip(parenthesis(')')) >> unarg(Make.capUsage) >> listElem
capFunc_combo = oneplus((hidCode_elem | capFunc_elem | animation_capability | pixel_capability | layer_expanded) + skip(maybe(plus))) >> listElem
capFunc_sequence = oneplus((capFunc_combo | seqStringR) + skip(maybe(comma))) >> oneLayerFlatten

# Trigger / Result Codes
triggerCode_combo = oneplus((scanCode_combo_elem | hidCode_elem | layer_expanded | animation_trigger | gtrigger_expanded) + skip(maybe(plus))) >> listElem
triggerCode_sequence = oneplus((triggerCode_combo | seqStringL | seqStringR) + skip(maybe(comma))) >> oneLayerFlatten
triggerCode_outerList = triggerCode_sequence >> optionExpansion
resultCode_outerList = ((capFunc_sequence >> optionExpansion) | none)

# Positions
position_list = oneplus(position + skip(maybe(comma)))
