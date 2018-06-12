#!/usr/bin/env python3
'''
KLL Expression Container
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

import copy

from kll.common.id import CapId



### Decorators ###

# Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'



### Classes ###

class Expression:
    '''
    Container class for KLL expressions
    '''

    def __init__(self, lparam, operator, rparam, context):
        '''
        Initialize expression container

        @param lparam:   LOperatorData token
        @param operator: Operator token
        @param rparam:   ROperatorData token
        @param context:  Parent context of expression
        '''
        # First stage/init
        self.lparam_token = lparam
        self.operator_token = operator
        self.rparam_token = rparam
        self.context = context  # TODO, set multiple contexts for later stages

        # Second stage
        self.lparam_sub_tokens = []
        self.rparam_sub_tokens = []

        # BaseMap expression
        self.base_map = False

        # Default ConnectId
        self.connect_id = 0

        # Mutate class into the desired type
        self.__class__ = {
            '=>': NameAssociationExpression,
            '<=': DataAssociationExpression,
            '=': AssignmentExpression,
            ':': MapExpression,
        }[self.operator_type()]

    def operator_type(self):
        '''
        Determine which base operator this operator is of

        All : (map) expressions are tokenized/parsed the same way

        @return Base string representation of the operator
        '''
        if ':' in self.operator_token.value:
            return ':'

        return self.operator_token.value

    def final_tokens(self, no_filter=False):
        '''
        Return the final list of tokens, must complete the second stage first

        @param no_filter: If true, do not filter out Space tokens

        @return Finalized list of tokens
        '''
        ret = self.lparam_sub_tokens + \
            [self.operator_token] + self.rparam_sub_tokens

        if not no_filter:
            ret = [x for x in ret if x.type != 'Space']
        return ret

    def regen_str(self):
        '''
        Re-construct the string based off the original set of tokens

        <lparam><operator><rparam>;
        '''
        return "{0}{1}{2};".format(
            self.lparam_token.value,
            self.operator_token.value,
            self.rparam_token.value,
        )

    def point_chars(self, pos_list):
        '''
        Using the regenerated string, point to a given list of characters
        Used to indicate where a possible issue/syntax error is

        @param pos_list: List of character indices

        i.e.
        > U"A" : : U"1";
        >        ^
        '''
        out = "\t{0}\n\t".format(self.regen_str())

        # Place a ^ character at the given locations
        curpos = 1
        for pos in sorted(pos_list):
            # Pad spaces, then add a ^
            out += ' ' * (pos - curpos)
            out += '^'
            curpos += pos

        return out

    def rparam_start(self):
        '''
        Starting positing char of rparam_token in a regen_str
        '''
        return len(self.lparam_token.value) + len(self.operator_token.value)

    def __repr__(self):
        # Build string representation based off of what has been set
        # lparam, operator and rparam are always set
        out = "Expression: {0}{1}{2}".format(
            self.lparam_token.value,
            self.operator_token.value,
            self.rparam_token.value,
        )

        # TODO - Add more depending on what has been set
        return out

    def kllify(self):
        '''
        Returns KLL version of the expression

        May not look like the original expression if simplication has taken place
        '''
        print(
            "{0} kllify not defined for {1}".format(
                WARNING,
                self.__class__.__name__))
        out = "{0}{1}{2};".format(
            self.lparam_token.value,
            self.operator_token.value,
            self.rparam_token.value,
        )
        return out

    def unique_keys(self):
        '''
        Generates a list of unique identifiers for the expression that is mergeable
        with other functional equivalent expressions.

        This method should never get called directly as a generic Expression
        '''
        return [('UNKNOWN KEY', 'UNKNOWN EXPRESSION')]


class AssignmentExpression(Expression):
    '''
    Container class for assignment KLL expressions
    '''
    type = None
    name = None
    pos = None
    value = None

    ## Setters ##
    def array(self, name, pos, value):
        '''
        Assign array assignment parameters to expression

        @param name:  Name of variable
        @param pos:   Array position of the value (if None, overwrite the entire array)
        @param value: Value of the array, if pos is specified, this is the value of an element

        @return: True if parsing was successful
        '''
        self.type = 'Array'
        self.name = name
        self.pos = pos
        self.value = value

        # If pos is not none, flatten
        if pos is not None:
            self.value = "".join(str(x) for x in self.value)

        return True

    def merge_array(self, new_expression=None):
        '''
        Merge arrays, used for position assignments
        Merges unconditionally, make sure this is what you want to do first

        If no additional array is specified, just "cap-off" array.
        This does a proper array expansion into a python list.

        @param new_expression: AssignmentExpression type array, ignore if None
        '''
        # First, check if base expression needs to be capped
        if self.pos is not None:
            # Generate a new string array
            new_value = [""] * self.pos

            # Append the old contents to the list
            new_value.append(self.value)
            self.value = new_value

            # Clear pos, to indicate that array has been capped
            self.pos = None

        # Next, if a new_expression has been specified, merge in
        if new_expression is not None and new_expression.pos is not None:
            # Check if we need to extend the list
            new_size = new_expression.pos + 1 - len(self.value)
            if new_size > 0:
                self.value.extend([""] * new_size)

            # Assign value to array
            self.value[new_expression.pos] = new_expression.value

    def variable(self, name, value):
        '''
        Assign variable assignment parameters to expression

        @param name: Name of variable
        @param value: Value of variable

        @return: True if parsing was successful
        '''
        self.type = 'Variable'
        self.name = name
        self.value = value

        # Flatten value, often a list of various token types
        self.value = "".join(str(x) for x in self.value)

        return True

    def __repr__(self):
        if self.type == 'Variable':
            return "{0} = {1};".format(self.name, self.value)
        elif self.type == 'Array':
            # Output KLL style array, double quoted elements, space-separated
            if isinstance(self.value, list):
                output = "{0}[] =".format(self.name)
                for value in self.value:
                    output += ' "{0}"'.format(value)
                output += ";"
                return output

            # Single array assignment
            else:
                return "{0}[{1}] = {2};".format(
                    self.name, self.pos, self.value)

        return "ASSIGNMENT UNKNOWN"

    def kllify(self):
        '''
        Returns KLL version of the expression

        May not look like the original expression if simplication has taken place

        __repr__ is formatted correctly with assignment expressions
        '''
        return self.__repr__()

    def unique_keys(self):
        '''
        Generates a list of unique identifiers for the expression that is mergeable
        with other functional equivalent expressions.
        '''
        return [(self.name, self)]


class NameAssociationExpression(Expression):
    '''
    Container class for name association KLL expressions
    '''
    type = None
    name = None
    association = None

    ## Setters ##
    def capability(self, name, association, parameters):
        '''
        Assign a capability C function name association

        @param name: Name of capability
        @param association: Name of capability in target backend output

        @return: True if parsing was successful
        '''
        self.type = 'Capability'
        self.name = name
        self.association = CapId(association, 'Definition', parameters)

        return True

    def define(self, name, association):
        '''
        Assign a define C define name association

        @param name: Name of variable
        @param association: Name of association in target backend output

        @return: True if parsing was successful
        '''
        self.type = 'Define'
        self.name = name
        self.association = association

        return True

    def __repr__(self):
        return "{0} <= {1};".format(self.name, self.association)

    def kllify(self):
        '''
        Returns KLL version of the expression

        May not look like the original expression if simplication has taken place
        '''
        return "{0}".format(self)

    def unique_keys(self):
        '''
        Generates a list of unique identifiers for the expression that is mergeable
        with other functional equivalent expressions.
        '''
        return [(self.name, self)]


class DataAssociationExpression(Expression):
    '''
    Container class for data association KLL expressions
    '''
    type = None
    association = None
    value = None

    ## Setters ##
    def animation(self, animations, animation_modifiers):
        '''
        Animation definition and configuration

        @return: True if parsing was successful
        '''
        self.type = 'Animation'
        self.association = animations
        self.value = animation_modifiers

        return True

    def animationFrame(self, animation_frames, pixel_modifiers):
        '''
        Pixel composition of an Animation Frame

        @return: True if parsing was successful
        '''

        self.type = 'AnimationFrame'
        self.association = animation_frames
        self.value = pixel_modifiers

        return True

    def pixelPosition(self, pixels, position):
        '''
        Pixel Positioning

        @return: True if parsing was successful
        '''
        for pixel in pixels:
            pixel.setPosition(position)

        self.type = 'PixelPosition'
        self.association = pixels

        return True

    def scanCodePosition(self, scancodes, position):
        '''
        Scan Code to Position Mapping

        Note: Accepts lists of scan codes
        Alone this isn't useful, but you can assign rows and columns using ranges instead of individually

        @return: True if parsing was successful
        '''
        for scancode in scancodes:
            scancode.setPosition(position)

        self.type = 'ScanCodePosition'
        self.association = scancodes

        return True

    def update(self, new_expression):
        '''
        Update expression

        @param new_expression: Expression used to update this one
        '''
        supported = ['PixelPosition', 'ScanCodePosition']
        if new_expression.type in supported:
            for scancode in self.association:
                scancode.updatePositions(new_expression.association[0])

    def __repr__(self):
        if self.type in ['PixelPosition', 'ScanCodePosition']:
            output = ""
            for index, association in enumerate(self.association):
                if index > 0:
                    output += "; "
                output += "{0}".format(association)
            return "{0};".format(output)
        return "{0} <= {1};".format(self.association, self.value)

    def kllify(self):
        '''
        Returns KLL version of the expression

        May not look like the original expression if simplication has taken place

        __repr__ is formatted correctly with assignment expressions
        '''

        if self.type in ['PixelPosition', 'ScanCodePosition']:
            output = ""
            for index, association in enumerate(self.association):
                if index > 0:
                    output += "; "
                output += "{0}".format(association.kllify())
            return "{0};".format(output)

        if self.type in ['AnimationFrame']:
            output = "{0} <= ".format(self.association[0].kllify())
            for index, association in enumerate(self.value):
                if index > 0:
                    output += ", "
                output += "{0}".format(association[0].kllify())
            return "{0};".format(output)

        return "{0} <= {1};".format(
            self.association.kllify(), self.value.kllify())

    def unique_keys(self):
        '''
        Generates a list of unique identifiers for the expression that is mergeable
        with other functional equivalent expressions.
        '''
        keys = []

        # Positions require a bit more introspection to get the unique keys
        if self.type in ['PixelPosition', 'ScanCodePosition']:
            for index, key in enumerate(self.association):
                uniq_expr = self

                # If there is more than one key, copy the expression
                # and remove the non-related variants
                if len(self.association) > 1:
                    uniq_expr = copy.copy(self)

                    # Isolate variant by index
                    uniq_expr.association = [uniq_expr.association[index]]

                keys.append(("{0}".format(key.unique_key()), uniq_expr))

        # AnimationFrames are already list of keys
        # TODO Reorder frame assignments to dedup function equivalent mappings
        elif self.type in ['AnimationFrame']:
            for index, key in enumerate(self.association):
                uniq_expr = self

                # If there is more than one key, copy the expression
                # and remove the non-related variants
                if len(self.association) > 1:
                    uniq_expr = copy.copy(self)

                    # Isolate variant by index
                    uniq_expr.association = [uniq_expr.association[index]]

                keys.append(("{0}".format(key), uniq_expr))

        # Otherwise treat as a single element
        else:
            keys = [("{0}".format(self.association), self)]

        # Remove any duplicate keys
        # TODO Stat? Might be at neat report about how many duplicates were
        # squashed
        keys = list(set(keys))

        return keys


class MapExpression(Expression):
    '''
    Container class for KLL map expressions
    '''
    type = None
    triggers = None
    operator = None
    results = None
    animation = None
    animation_frame = None
    pixels = None
    position = None
    trigger_identifiers = ['IndCode', 'GenericTrigger', 'Layer', 'LayerLock', 'LayerShift', 'LayerLatch', 'ScanCode']

    def __init__(self, triggers, operator, results):
        '''
        Initialize MapExpression

        Used when copying MapExpressions from different expressions

        @param triggers: Sequence of combos of ranges of namedtuples
        @param operator: Type of map operation
        @param results: Sequence of combos of ranges of namedtuples
        '''
        self.type = 'TriggerCode'
        self.triggers = triggers
        self.operator = operator
        self.results = results

        self.connect_id = 0

    ## Setters ##
    def triggerCode(self, triggers, operator, results):
        '''
        Trigger Code mapping
        Takes in any combination of triggers and sets the expression accordingly.

        @param triggers: Sequence of combos of ranges of namedtuples
        @param operator: Type of map operation
        @param results: Sequence of combos of ranges of namedtuples

        @return: True if parsing was successful
        '''
        self.type = 'TriggerCode'
        self.triggers = triggers
        self.operator = operator
        self.results = results

        return True

    def pixelChannels(self, pixelmap, trigger):
        '''
        Pixel Channel Composition

        @return: True if parsing was successful
        '''
        self.type = 'PixelChannel'
        self.pixel = pixelmap
        self.position = trigger

        return True

    def triggersSequenceOfCombosOfIds(self, index=0):
        '''
        Takes triggers and converts into explicit ids

        Only uses the first index by default.
        @param index: Which trigger sequence to expand
        @return: list of lists

        Example (index=0)
        [[[S10, S16], [S42]], [[S11, S16], [S42]]] -> [[10, 16], [42]]
        '''
        nsequence = []
        for combo in self.triggers[index]:
            ncombo = []
            for identifier in combo:
                ncombo.append(identifier.json())
            nsequence.append(ncombo)
        return nsequence

    def resultsSequenceOfCombosOfIds(self, index=0):
        '''
        Takes results and converts into explicit capabilities

        Only uses the first index by default.
        @param index: Which result sequence to expand
        @return: list of lists
        '''
        nsequence = []
        for combo in self.results[index]:
            ncombo = []
            for identifier in combo:
                ncombo.append(identifier.json())
            nsequence.append(ncombo)
        return nsequence

    def sequencesOfCombosOfIds(self, expression_param):
        '''
        Prettified Sequence of Combos of Identifiers

        @param expression_param: Trigger or Result parameter of an expression

        Scan Code Example
        [[[S10, S16], [S42]], [[S11, S16], [S42]]] -> (S10 + S16, S42)|(S11 + S16, S42)
        '''
        output = ""

        # Sometimes during error cases, might be None
        if expression_param is None:
            return output

        # Iterate over each trigger/result variants (expanded from ranges),
        # each one is a sequence
        for index, sequence in enumerate(expression_param):
            if index > 0:
                output += "|"
            output += "("

            # Iterate over each combo (element of the sequence)
            for index, combo in enumerate(sequence):
                if index > 0:
                    output += ", "

                # Iterate over each trigger identifier
                for index, identifier in enumerate(combo):
                    if index > 0:
                        output += " + "
                    output += "{0}".format(identifier)

            output += ")"

        return output

    def sequencesOfCombosOfIds_kll(self, expression_param):
        '''
        Prettified Sequence of Combos of Identifiers, kll output edition

        @param expression_param: Trigger or Result parameter of an expression

        Scan Code Example
        [[[S10, S16], [S42]], [[S11, S16], [S42]]] -> ['S10 + S16, S42', 'S11 + S16, S42']
        '''
        output = ['']

        # Sometimes during error cases, might be None
        if expression_param is None:
            return output

        # Iterate over each trigger/result variants (expanded from ranges),
        # each one is a sequence
        for index, sequence in enumerate(expression_param):
            if index > 0:
                output.append('')

            # Iterate over each combo (element of the sequence)
            for index, combo in enumerate(sequence):
                if index > 0:
                    output[-1] += ", "

                # Iterate over each trigger identifier
                for index, identifier in enumerate(combo):
                    if index > 0:
                        output[-1] += " + "
                    output[-1] += "{0}".format(identifier.kllify())

        return output

    def trigger_id_list(self):
        '''
        Returns a list of ids within the sequence of combos
        May contain duplicates
        '''
        id_list = []

        # Iterate over each trigger/result variants (expanded from ranges)
        for sequence in self.triggers:
            # Iterate over each combo (element of the sequence)
            for combo in sequence:
                # Iterate over each trigger identifier
                for identifier in combo:
                    id_list.append(identifier)

        return id_list

    def min_trigger_uid(self):
        '''
        Returns the min numerical uid
        Used for trigger identifiers
        '''
        min_uid = 0xFFFF

        # Iterate over list of identifiers in trigger
        for identifier in self.trigger_id_list():
            if identifier.type in self.trigger_identifiers and identifier.get_uid() < min_uid:
                min_uid = identifier.get_uid()

        return min_uid

    def max_trigger_uid(self):
        '''
        Returns the max numerical uid
        Used for trigger identifiers
        '''
        max_uid = 0

        # Iterate over list of identifiers in trigger
        for identifier in self.trigger_id_list():
            if identifier.type in self.trigger_identifiers and identifier.get_uid() > max_uid:
                max_uid = identifier.get_uid()

        return max_uid

    def add_trigger_uid_offset(self, offset):
        '''
        Adds a uid/scancode offset to all triggers

        This is used when applying the connect_id interconnect offset during mapping indices generation
        '''
        # Iterate over list of identifiers in trigger
        for identifier in self.trigger_id_list():
            if identifier.type == 'ScanCode':
                identifier.updated_uid = identifier.uid + offset

    def elems(self):
        '''
        Return number of trigger and result elements

        Useful for determining if this is a trigger macro (2+)
        Should always return at least (1,1) unless it's an invalid calculation

        @return: ( triggers, results )
        '''
        elems = [0, 0]

        # XXX Needed?
        if self.type == 'PixelChannel':
            return tuple(elems)

        # Iterate over each trigger variant (expanded from ranges), each one is
        # a sequence
        for sequence in self.triggers:
            # Iterate over each combo (element of the sequence)
            for combo in sequence:
                # Just measure the size of the combo
                elems[0] += len(combo)

        # Iterate over each result variant (expanded from ranges), each one is
        # a sequence
        for sequence in self.results:
            # Iterate over each combo (element of the sequence)
            for combo in sequence:
                # Just measure the size of the combo
                elems[1] += len(combo)

        return tuple(elems)

    def trigger_str(self):
        '''
        String version of the trigger
        Used for sorting
        '''
        # Pixel Channel Mapping doesn't follow the same pattern
        if self.type == 'PixelChannel':
            return "{0}".format(self.pixel)

        return "{0}".format(
            self.sequencesOfCombosOfIds(self.triggers),
        )

    def result_str(self):
        '''
        String version of the result
        Used for sorting
        '''
        # Pixel Channel Mapping doesn't follow the same pattern
        if self.type == 'PixelChannel':
            return "{0}".format(self.position)

        return "{0}".format(
            self.sequencesOfCombosOfIds(self.results),
        )

    def __repr__(self):
        # Pixel Channel Mapping doesn't follow the same pattern
        if self.type == 'PixelChannel':
            return "{0} : {1};".format(self.pixel, self.position)

        return "{0} {1} {2};".format(
            self.sequencesOfCombosOfIds(self.triggers),
            self.operator,
            self.sequencesOfCombosOfIds(self.results),
        )

    def sort_trigger(self):
        '''
        Returns sortable trigger
        '''
        if self.type == 'PixelChannel':
            return "{0}".format(self.pixel.kllify())

        return "{0}".format(
            self.sequencesOfCombosOfIds_kll(self.triggers)[0],
        )

    def sort_result(self):
        '''
        Returns sortable result
        '''
        if self.type == 'PixelChannel':
            result = self.position
            # Handle None pixel mapping case
            if isinstance(self.position, list):
                result = self.sequencesOfCombosOfIds_kll(self.position)[0]
            return "{0}".format(result)

        return "{0}".format(
            self.sequencesOfCombosOfIds_kll(self.results)[0],
        )

    def kllify(self):
        '''
        Returns KLL version of the expression

        May not look like the original expression if simplication has taken place
        '''
        # TODO Handle variations? Instead of just the first index

        if self.type == 'PixelChannel':
            result = self.position
            # Handle None pixel mapping case
            if isinstance(self.position, list):
                result = self.sequencesOfCombosOfIds_kll(self.position)[0]
            return "{0} : {1};".format(self.pixel.kllify(), result)

        return "{0} {1} {2};".format(
            self.sequencesOfCombosOfIds_kll(self.triggers)[0],
            self.operator,
            self.sequencesOfCombosOfIds_kll(self.results)[0],
        )

    def unique_keys(self):
        '''
        Generates a list of unique identifiers for the expression that is mergeable
        with other functional equivalent expressions.

        TODO: This function should re-order combinations to generate the key.
        The final generated combo will be in the original order.
        '''
        keys = []

        # Pixel Channel only has key per mapping
        if self.type == 'PixelChannel':
            keys = [("{0}".format(self.pixel), self)]

        # Split up each of the keys
        else:
            # Iterate over each trigger/result variants (expanded from ranges),
            # each one is a sequence
            for index, sequence in enumerate(self.triggers):
                key = ""
                uniq_expr = self

                # If there is more than one key, copy the expression
                # and remove the non-related variants
                if len(self.triggers) > 1:
                    uniq_expr = copy.copy(self)

                    # Isolate variant by index
                    uniq_expr.triggers = [uniq_expr.triggers[index]]

                # Iterate over each combo (element of the sequence)
                for index, combo in enumerate(sequence):
                    if index > 0:
                        key += ", "

                    # Iterate over each trigger identifier
                    for index, identifier in enumerate(combo):
                        if index > 0:
                            key += " + "
                        key += "{0} {1}".format(self.connect_id, identifier)

                # Add key to list
                keys.append((key, uniq_expr))

        # Remove any duplicate keys
        # TODO Stat? Might be at neat report about how many duplicates were
        # squashed
        keys = list(set(keys))

        return keys
