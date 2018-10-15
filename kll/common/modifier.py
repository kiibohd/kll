#!/usr/bin/env python3
'''
KLL Modifier Containers
'''

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



### Decorators ###

# Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'



### Classes ###

class AnimationModifierArg:
    '''
    Animation modification arg container class
    '''

    def __init__(self, parent, value):
        self.parent = parent

        self.arg = value
        self.subarg = None

        # In case we have a bad modifier, arg is set to None
        if self.arg is None:
            return

        # Sub-arg case
        if isinstance(value, tuple):
            self.arg = value[0]
            self.subarg = value[1]

        # Validate arg
        validation = parent.valid_modifiers[parent.name]
        if isinstance(validation, dict):
            # arg
            if self.arg not in validation.keys():
                print("{0} '{1}' is not a valid modifier arg for '{2}'".format(
                    ERROR,
                    self.arg,
                    parent.name,
                ))

            # subarg
            subvalidation = validation[self.arg]
            if subvalidation is None and self.subarg is not None:
                print("{0} '{1}' is an incorrect subargument for '{2}:{3}', should be a '{4}'".format(
                    ERROR,
                    self.subarg,
                    parent.name,
                    self.arg,
                    subvalidation,
                ))
            elif subvalidation is not None and not isinstance(self.subarg, subvalidation[self.arg]):
                print("{0} '{1}' is an incorrect subargument for '{2}:{3}', should be a '{4}'".format(
                    ERROR,
                    self.subarg,
                    parent.name,
                    self.arg,
                    subvalidation,
                ))

        else:
            # arg
            if not isinstance(self.arg, validation):
                print("{0} '{1}' is an incorrect argument for '{2}', should be a '{3}'".format(
                    ERROR,
                    self.arg,
                    parent.name,
                    validation,
                ))

    def __repr__(self):
        if self.arg is None:
            return ""
        if self.subarg is not None:
            int_list = ["{0}".format(x) for x in self.subarg]
            return "{0}({1})".format(
                self.arg,
                ",".join(int_list),
            )
        return "{0}".format(self.arg)

    def like(self, other):
        '''
        Returns true if the other AnimationModifierArg is the same
        '''
        if self.arg != other.arg:
            return False
        if self.subarg is None and other.subarg is None:
            return True
        elif self.subarg is None or other.subarg is None:
            return False

        if frozenset(self.subarg) == frozenset(other.subarg):
            return True

        return False

    def json(self):
        '''
        JSON representation of AnimationModifierArg
        '''
        return {
            'arg': self.arg,
            'subarg': self.subarg,
        }

    def kllify(self):
        '''
        Returns KLL version of the Modifier

        In most cases we can just the string representation of the object
        '''
        return "{0}".format(self)


class AnimationModifier:
    '''
    Animation modification container class
    '''
    # Modifier validation tree
    valid_modifiers = {
        'loops': int,
        'loop': None,
        'framedelay': int,
        'framestretch': None,
        'start': None,
        'pause': None,
        'stop': None,
        'single': None,
        'pos': int,
        'pfunc': {
            'off': None,
            'interp': None,
            'kllinterp': None,
        },
        'ffunc': {
            'off': None,
            'interp': None,
            'kllinterp': None,
        },
        'replace': {
            'stack': None,
            'basic': None,
            'all': None,
            'state': None,
            'clear': None,
        },
    }

    def __init__(self, name, value=None):
        # Check if name is valid
        if name not in self.valid_modifiers.keys():
            print("{0} '{1}' is not a valid modifier {1}:{2}".format(
                ERROR,
                name,
                value,
            ))
            self.name = '<UNKNOWN>'
            self.value = AnimationModifierArg(self, None)
            return

        self.name = name
        self.value = AnimationModifierArg(self, value)

    def __repr__(self):
        if self.value.arg is None:
            return "{0}".format(self.name)
        return "{0}:{1}".format(self.name, self.value)

    def like(self, other):
        '''
        Returns true if AnimationModifier has the same name
        '''
        return other.name == self.name

    def __eq__(self, other):
        return self.like(other) and self.value.like(other.value)

    def json(self):
        '''
        JSON representation of AnimationModifier
        '''
        # Determine json of self.value
        value = None
        if self.value is not None:
            value = self.value.json()

        return {
            'name': self.name,
            'value': value,
        }

    def kllify(self):
        '''
        Returns KLL version of the Modifier

        In most cases we can just the string representation of the object
        '''
        return "{0}".format(self)


class AnimationModifierList:
    '''
    Animation modification container list class

    Contains a list of modifiers, the order does not matter
    '''
    frameoption_modifiers = [
        'framestretch',
    ]

    def __init__(self):
        self.modifiers = []

    def setModifiers(self, modifier_list):
        '''
        Apply modifiers to Animation
        '''
        for modifier in modifier_list:
            self.modifiers.append(AnimationModifier(modifier[0], modifier[1]))

    def clean(self, new_modifier, new, old):
        '''
        Remove conflicting modifier if necessary
        '''
        if new_modifier.name == new:
            for index, modifier in enumerate(self.modifiers):
                if modifier.name == old:
                    return False
        return True

    def replace(self, new_modifier):
        '''
        Replace modifier

        If it doesn't exist already, just add it.
        '''
        # If new_modifier is loops and loop exists, remove loop
        if not self.clean(new_modifier, 'loops', 'loop'):
            return
        # If new_modifier is loop and loops exists, remove loops
        if not self.clean(new_modifier, 'loop', 'loops'):
            return

        # Check for modifier
        for modifier in self.modifiers:
            if modifier.name == new_modifier.name:
                modifier.value = new_modifier.value
                return

        # Otherwise just add it
        self.modifiers.append(new_modifier)

    def getModifier(self, name):
        '''
        Retrieves modifier

        Returns False if doesn't exist
        Returns argument if exists and has an argument, may be None
        '''
        for mod in self.modifiers:
            if mod.name == name:
                return mod.value
        return False

    def strModifiers(self):
        '''
        __repr__ of Position when multiple inheritance is used
        '''
        output = ""
        for index, modifier in enumerate(sorted(self.modifiers, key=lambda x: x.name)):
            if index > 0:
                output += ","
            output += "{0}".format(modifier)

        return output

    def __repr__(self):
        return self.strModifiers()

    def json(self):
        '''
        JSON representation of AnimationModifierList
        '''
        output = {
            'modifiers' : [],
        }
        # Output sorted list of modifiers
        for modifier in sorted(self.modifiers, key=lambda x: x.name):
            output['modifiers'].append(modifier.json())

        # Look for any frameoption modifiers
        frameoption_list = []
        for modifier in self.modifiers:
            if modifier.name in self.frameoption_modifiers:
                frameoption_list.append(modifier.name)
        output['frameoptions'] = frameoption_list
        return output

    def kllify(self):
        '''
        Returns KLL version of the ModifierList

        In most cases we can just the string representation of the object
        '''
        return "{0}".format(self)


class PixelModifier:
    '''
    Pixel modification container class
    '''

    def __init__(self, operator, value):
        self.operator = operator
        self.value = value

    def __repr__(self):
        if self.operator is None:
            return "{0}".format(self.value)
        return "{0}{1}".format(self.operator, self.value)

    def operator_type(self):
        '''
        Returns operator type
        '''
        types = {
            None: 'Set',
            '+': 'Add',
            '-': 'Subtract',
            '+:': 'NoRoll_Add',
            '-:': 'NoRoll_Subtract',
            '<<': 'LeftShift',
            '>>': 'RightShift',
        }
        return types[self.operator]

    def kllify(self):
        '''
        Returns KLL version of the PixelModifier

        In most cases we can just the string representation of the object
        '''
        return "{0}".format(self)


class PixelModifierList:
    '''
    Pixel modification container list class

    Contains a list of modifiers
    Index 0, corresponds to pixel 0
    '''

    def __init__(self):
        self.modifiers = []

    def setModifiers(self, modifier_list):
        '''
        Apply modifier to each pixel channel
        '''
        for modifier in modifier_list:
            self.modifiers.append(PixelModifier(modifier[0], modifier[1]))

    def strModifiers(self):
        '''
        __repr__ of Position when multiple inheritance is used
        '''
        output = ""
        for index, modifier in enumerate(self.modifiers):
            if index > 0:
                output += ","
            output += "{0}".format(modifier)

        return output

    def __repr__(self):
        return self.strModifiers()

    def kllify(self):
        '''
        Returns KLL version of the PixelModifierList

        In most cases we can just the string representation of the object
        '''
        return "{0}".format(self)
