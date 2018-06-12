#!/usr/bin/env python3
'''
KLL Data Organization
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
import re

import kll.common.expression as expression

from kll.common.id import PixelAddressId


### Decorators ###

# Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'

ansi_escape = re.compile(r'\x1b[^m]*m')


### Classes ###

class Data:
    '''
    Base class for KLL datastructures
    '''
    # Debug output formatters
    debug_output = {
        'add': "\t\033[1;42;37m++\033[0m\033[1mADD KEY\033[1;42;37m++\033[0m \033[1m<==\033[0m {0}",
        'app': "\t\033[1;45;37m**\033[0m\033[1mAPP KEY\033[1;45;37m**\033[0m \033[1m<==\033[0m {0}",
        'mod': "\t\033[1;44;37m##\033[0m\033[1mMOD KEY\033[1;44;37m##\033[0m \033[1m<==\033[0m {0}",
        'rem': "\t\033[1;41;37m--\033[0m\033[1mREM KEY\033[1;41;37m--\033[0m \033[1m<==\033[0m {0}",
        'drp': "\t\033[1;43;37m@@\033[0m\033[1mDRP KEY\033[1;43;37m@@\033[0m \033[1m<==\033[0m {0}",
        'dup': "\t\033[1;46;37m!!\033[0m\033[1mDUP KEY\033[1;46;37m!!\033[0m \033[1m<==\033[0m {0}",
    }

    def __init__(self, parent):
        '''
        Initialize datastructure

        @param parent: Parent organization, used to query data from other datastructures
        '''
        self.data = {}
        self.parent = parent
        self.connect_id = 0
        self.merge_in_log = []

    def merge_in_log_prune(self, debug):
        '''
        Prune the merge_in_log

        Reverse searches the list, if the key already exists, disable the key
        '''
        new_log = []
        found = []
        # We have to manually reverse, then modify the referenced items
        # i.e. we're still modifying self.merge_in_log
        # This is done so we still have a proper index, and do the invalidation in the correct order
        reversed_log = self.merge_in_log[::-1]
        for index, elem in enumerate(reversed_log):
            key, expr, enabled = elem
            # Add to found list
            if key not in found:
                found.append(key)
                new_log.insert(0, elem)
            # Otherwise mark as disabled
            else:
                reversed_log[index] = [
                    key,
                    expr,
                    False,
                ]

        return new_log

    def merge_in_log_expression(self, key, expression, debug):
        '''
        Logs a given merge_in expressions
        This is used to determine the order in which the merges occurred

        Duplicate entries are pruned after the merge

        @param key:        Hash entry for (text)
        @param expression: Expression object
        @param debug:      Enable debug out
        '''
        # Debug output
        if debug[0]:
            output = "{0} Log Add: {1} {2}".format(
                self.parent.parent.layer_info(),
                key,
                expression,
            )
            print(debug[1] and output or ansi_escape.sub('', output))

        # Add to log, and enable key
        self.merge_in_log.append([key, expression, True])

    def add_expression(self, expression, debug):
        '''
        Add expression to data structure

        May have multiple keys to add for a given expression

        @param expression: KLL Expression (fully tokenized and parsed)
        @param debug:      Enable debug output
        '''
        # Lookup unique keys for expression
        keys = expression.unique_keys()

        # Add/Modify expressions in datastructure
        for key, uniq_expr in keys:
            # Check which operation we are trying to do, add or modify
            if debug[0]:
                if key in self.data.keys():
                    output = self.debug_output['mod'].format(key)
                else:
                    output = self.debug_output['add'].format(key)
                print(debug[1] and output or ansi_escape.sub('', output))

            self.data[key] = uniq_expr

            # Add to log
            self.merge_in_log_expression(key, uniq_expr, debug)

    def merge(self, merge_in, map_type, debug):
        '''
        Merge in the given datastructure to this datastructure

        This datastructure serves as the base.

        @param merge_in: Data structure from another organization to merge into this one
        @param map_type: Used fo map specific merges
        @param debug:    Enable debug out
        '''
        # The default case is just to add the expression in directly
        for key, kll_expression in merge_in.data.items():
            # Set ConnectId in expression
            kll_expression.connect_id = merge_in.connect_id

            # Display key:expression being merged in
            if debug[0]:
                output = merge_in.elem_str(key, True)
                print(debug[1] and output or ansi_escape.sub('', output), end="")

            self.add_expression(kll_expression, debug)

            # Add to log
            self.merge_in_log_expression(key, kll_expression, debug)

    def reduction(self, debug=False):
        '''
        Simplifies datastructure

        Most of the datastructures don't have a reduction. Just do nothing in this case.
        '''
        pass

    def cleanup(self, debug=False):
        '''
        Post-processing step for merges that may need to remove some data in the organization.
        Mainly used for dropping BaseMapContext expressions after generating a PartialMapContext.
        '''
        pass

    def connectid(self, connect_id):
        '''
        Sets the Data store with a given connect_id
        By default, this is 0, but may be set prior to an organization merge
        '''
        self.connect_id = connect_id

    def elem_str(self, key, single=False):
        '''
        Debug output for a single element

        @param key:    Index to datastructure
        @param single: Setting to True will bold the key
        '''
        if single:
            return "\033[1;33m{0: <20}\033[0m \033[1;36;41m>\033[0m {1}\n".format(key, self.data[key])
        else:
            return "{0: <20} \033[1;36;41m>\033[0m {1}\n".format(key, self.data[key])

    def __repr__(self):
        output = ""

        # Display sorted list of keys, along with the internal value
        for key in sorted(self.data):
            output += self.elem_str(key)

        return output


class MappingData(Data):
    '''
    KLL datastructure for data mapping

    ScanCode  trigger -> result
    USBCode   trigger -> result
    Animation trigger -> result
    '''
    def add_expression(self, expression, debug):
        '''
        Add expression to data structure

        May have multiple keys to add for a given expression

        Map expressions insert into the datastructure according to their operator.

        +Operators+
        :   Add/Modify
        :+  Append
        :-  Remove
        ::  Lazy Add/Modify

        i:  Add/Modify
        i:+ Append
        i:- Remove
        i:: Lazy Add/Modify

        The i or isolation operators are stored separately from the main ones.
        Each key is pre-pended with an i

        The :: or lazy operators act just like : operators, except that they will be ignore if the evaluation
        merge cannot resolve a ScanCode.

        @param expression: KLL Expression (fully tokenized and parsed)
        @param debug:      Enable debug output
        '''
        # Lookup unique keys for expression
        keys = expression.unique_keys()

        # Add/Modify expressions in datastructure
        for ukey, uniq_expr in keys:
            # Determine which the expression operator
            operator = expression.operator

            # Except for the : operator, all others have delayed action
            # Meaning, they change behaviour depending on how Contexts are merged
            # This means we can't simplify yet
            # In addition, :+ and :- are stackable, which means each key has a list of expressions
            # We append the operator to differentiate between the different types of delayed operations
            key = "{0}{1}".format(operator, ukey)

            # Determine if key exists already
            exists = key in self.data.keys()

            # Add/Modify
            if operator in [':', '::', 'i:', 'i::']:
                debug_tag = exists and 'mod' or 'add'

            # Append/Remove
            else:
                # Check to make sure we haven't already appended expression
                # Use the string representation to do the comparison (general purpose)
                if exists and "{0}".format(uniq_expr) in ["{0}".format(elem) for elem in self.data[key]]:
                    debug_tag = 'dup'

                # Append
                elif operator in [':+', 'i:+']:
                    debug_tag = 'app'

                # Remove
                else:
                    debug_tag = 'rem'

            # Debug output
            if debug[0]:
                output = self.debug_output[debug_tag].format(key)
                print(debug[1] and output or ansi_escape.sub('', output))

            # Don't append if a duplicate
            if debug_tag == 'dup':
                continue

            # Append, rather than replace
            if operator in [':+', ':-', 'i:+', 'i:-']:
                if exists:
                    self.data[key].append(uniq_expr)

                # Create initial list
                else:
                    self.data[key] = [uniq_expr]
            else:
                self.data[key] = [uniq_expr]

            # Append to log
            self.merge_in_log_expression(key, uniq_expr, debug)

    def set_interconnect_id(self, interconnect_id, triggers):
        '''
        Traverses the sequence of combo of identifiers to set the interconnect_id
        '''
        for sequence in triggers:
            for combo in sequence:
                for identifier in combo:
                    identifier.interconnect_id = interconnect_id

    def connectid(self, connect_id):
        '''
        Sets the Data store with a given connect_id
        By default, this is 0, but may be set prior to an organization merge
        '''
        self.connect_id = connect_id

        # Update dictionary keys using new connect_id
        for key, value in self.data.items():
            if value[0].type == 'ScanCode':
                # Update connect_id, then regenerate dictionary item
                value[0].connect_id = connect_id
                new_key = "{0}{1}".format(
                    value[0].operator,
                    value[0].unique_keys()[0][0],
                )

                # Replace dictionary item
                self.data[new_key] = self.data.pop(key)

    def maxscancode(self):
        '''
        Find max scancode per connect id

        @return: Dictionary of max Scan Codes (keys are the connect id)
        '''
        max_dict = {}
        for key, value in self.data.items():
            connect_id = value[0].connect_id
            max_uid = value[0].max_trigger_uid()

            # Initial value
            if connect_id not in max_dict.keys():
                max_dict[connect_id] = 0

            # Update if necessary
            if max_dict[connect_id] < max_uid:
                max_dict[connect_id] = max_uid

        return max_dict

    def merge_lazy_operators(self, debug):
        '''
        Lazy Set :: is not applied as a Set : until after the merge_in_log has been pruned

        Intended to be called during reduction.
        '''
        # Build dictionary of single ScanCodes first
        result_code_lookup = {}
        for key, expr in self.data.items():
            if expr[0].elems()[0] == 1 and expr[0].triggers[0][0][0].type == 'ScanCode':
                result_code_lookup.setdefault(expr[0].result_str(), []).append(key)

        # Build list of lazy keys from log
        lazy_keys = {}
        for key, expr, enabled in reversed(self.merge_in_log):
            if key[0:2] == '::' or key[0:3] == 'i::':
                if key not in lazy_keys.keys():
                    # Debug info
                    if debug:
                        print("\033[1mLazy\033[0m", key, expr)

                    # Determine the target key from the expression
                    target_key = expr.trigger_str()
                    lazy_keys[target_key] = expr

                    # Check if we need to do a lazy replacement
                    if target_key in result_code_lookup.keys():
                        expr_keys = result_code_lookup[target_key]
                        for target_expr_key in expr_keys:
                            # Calculate new key
                            new_expr = self.data[target_expr_key][0]
                            new_key = "{0}{1}".format(
                                new_expr.operator,
                                new_expr.unique_keys()[0][0]
                            )

                            # Determine action based on the new_expr.operator
                            orig_expr = self.data[new_key][0]

                            if debug:
                                print("\t\033[1;32mREPLACE\033[0m {0} -> {1}\n\t{2} => {3}".format(
                                    target_expr_key,
                                    new_key,
                                    expr,
                                    new_expr
                                ))

                            # Do replacement
                            self.data[new_key] = [expression.MapExpression(
                                    orig_expr.triggers,
                                    orig_expr.operator,
                                    expr.results
                            )]
                            self.data[new_key][0].connect_id = orig_expr.connect_id

                            # Unset basemap on expression
                            self.data[new_key][0].base_map = False

    def merge(self, merge_in, map_type, debug):
        '''
        Merge in the given datastructure to this datastructure

        This datastructure serves as the base.

        Map expressions merge differently than insertions.

        +Operators+
        :   Add/Modify       - Replace
        :+  Append           - Add
        :-  Remove           - Remove
        ::  Lazy Add/Modify  - Replace if found, otherwise drop

        i:  Add/Modify       - Replace
        i:+ Append           - Add
        i:- Remove           - Remove
        i:: Lazy Add/Modify  - Replace if found, otherwise drop

        @param merge_in: Data structure from another organization to merge into this one
        @param map_type: Used fo map specific merges
        @param debug:    Enable debug out
        '''
        # Get unique list of ordered keys
        # We can't just query the keys directly from the as we need them in order of being added
        # In addition, we need a unique list of keys, where the most recently added is the most important
        cur_keys = []
        for key, expr, enabled in reversed(merge_in.merge_in_log):
            if key not in cur_keys:
                cur_keys.insert(0, key)

        # Lazy Set ::
        lazy_keys = [key for key in cur_keys if key[0:2] == '::' or key[0:3] == 'i::']
        cur_keys = list(set(cur_keys) - set(lazy_keys))

        # Append :+
        append_keys = [key for key in cur_keys if key[0:2] == ':+' or key[0:3] == 'i:+']
        cur_keys = list(set(cur_keys) - set(append_keys))

        # Remove :-
        remove_keys = [key for key in cur_keys if key[0:2] == ':-' or key[0:3] == 'i:-']
        cur_keys = list(set(cur_keys) - set(remove_keys))

        # Set :
        # Everything left is just a set
        set_keys = cur_keys

        # First process the :: (or lazy) operators
        # We need to read into this datastructure and apply those first
        # Otherwise we may get undesired behaviour
        for key in lazy_keys:
            # Display key:expression being merged in
            if debug[0]:
                output = merge_in.elem_str(key, True)
                print(debug[1] and output or ansi_escape.sub('', output), end="")

            # Construct target key
            # XXX (HaaTa) We now delay lazy operation application till reduction
            #target_key = key[0] == 'i' and "i{0}".format(key[2:]) or key[1:]
            target_key = key

            # Lazy expressions will be dropped later at reduction
            debug_tag = 'mod'

            # Debug output
            if debug[0]:
                output = self.debug_output[debug_tag].format(key)
                print(debug[1] and output or ansi_escape.sub('', output))

            # Only replace
            self.data[target_key] = merge_in.data[key]

            # Unset BaseMapContext tag if not a BaseMapContext
            if map_type != 'BaseMapContext':
                self.data[target_key][0].base_map = False

        # Then apply : assignment operators
        for key in set_keys:
            # Display key:expression being merged in
            if debug[0]:
                output = merge_in.elem_str(key, True)
                print(debug[1] and output or ansi_escape.sub('', output), end="")

            # Construct target key
            target_key = key

            # Indicate if add or modify
            if target_key in self.data.keys():
                debug_tag = 'mod'
            else:
                debug_tag = 'add'

            # Debug output
            if debug[0]:
                output = self.debug_output[debug_tag].format(key)
                print(debug[1] and output or ansi_escape.sub('', output))

            # Set into new datastructure regardless
            self.data[target_key] = merge_in.data[key]

            # Unset BaseMap flag if this is not a BaseMap merge
            if map_type != 'BaseMapContext':
                self.data[target_key][0].base_map = False

        # Now apply append operations
        for key in append_keys:
            # Display key:expression being merged in
            if debug[0]:
                output = merge_in.elem_str(key, True)
                print(debug[1] and output or ansi_escape.sub('', output), end="")

            # Construct target key
            # XXX (HaaTa) Might not be correct, but seems to work with the merge_in_log
            #target_key = key[0] == 'i' and "i:{0}".format(key[3:]) or ":{0}".format(key[2:])
            target_key = key

            # Alwyays appending
            debug_tag = 'app'

            # Debug output
            if debug[0]:
                output = self.debug_output[debug_tag].format(key)
                print(debug[1] and output or ansi_escape.sub('', output))

            # Extend list if it exists
            if target_key in self.data.keys():
                self.data[target_key].extend(merge_in.data[key])
            else:
                self.data[target_key] = merge_in.data[key]

        # Finally apply removal operations to this datastructure
        # If the target removal doesn't exist, ignore silently (show debug message)
        for key in remove_keys:
            # Display key:expression being merged in
            if debug[0]:
                output = merge_in.elem_str(key, True)
                print(debug[1] and output or ansi_escape.sub('', output), end="")

            # Construct target key
            # XXX (HaaTa) Might not be correct, but seems to work with the merge_in_log
            #target_key = key[0] == 'i' and "i:{0}".format(key[3:]) or ":{0}".format(key[2:])
            target_key = key

            # Drop right away if target datastructure doesn't have target key
            if target_key not in self.data.keys():
                debug_tag = 'drp'

                # Debug output
                if debug[0]:
                    output = self.debug_output[debug_tag].format(key)
                    print(debug[1] and output or ansi_escape.sub('', output))

                continue

            # Compare expressions to be removed with the current set
            # Use strings to compare
            remove_expressions = ["{0}".format(expr) for expr in merge_in.data[key]]
            current_expressions = [("{0}".format(expr), expr) for expr in self.data[target_key]]
            for string, expr in current_expressions:
                debug_tag = 'drp'

                # Check if an expression matches
                if string in remove_expressions:
                    debug_tag = 'rem'

                # Debug output
                if debug[0]:
                    output = self.debug_output[debug_tag].format(key)
                    print(debug[1] and output or ansi_escape.sub('', output))

                # Remove if found
                if debug_tag == 'rem':
                    self.data[target_key] = [value for value in self.data.values() if value != expr]

        # Now append the merge_in_log
        self.merge_in_log.extend(merge_in.merge_in_log)

    def cleanup(self, debug=False):
        '''
        Post-processing step for merges that may need to remove some data in the organization.
        Mainly used for dropping BaseMapContext expressions after generating a PartialMapContext.
        '''
        # Using this dictionary, replace all the trigger USB codes
        # Iterate over a copy so we can modify the dictionary in place
        for key, expr in self.data.copy().items():
            if expr[0].base_map:
                if debug[0]:
                    output = "\t\033[1;34mDROP\033[0m {0}".format(self.data[key][0])
                    print(debug[1] and output or ansi_escape.sub('', output))
                del self.data[key]
            elif debug[0]:
                output = "\t\033[1;32mKEEP\033[0m {0}".format(self.data[key][0])
                print(debug[1] and output or ansi_escape.sub('', output))

    def reduction(self, debug=False):
        '''
        Simplifies datastructure

        Used to replace all trigger HIDCode(USBCode)s with ScanCodes

        NOTE: Make sure to create a new MergeContext before calling this as you lose data and prior context
        '''
        result_code_lookup = {}

        # Prune merge_in_log
        merge_in_pruned = self.merge_in_log_prune(debug)

        # Build dictionary of single ScanCodes first
        for key, expr in self.data.items():
            if expr[0].elems()[0] == 1 and expr[0].triggers[0][0][0].type == 'ScanCode':
                result_code_lookup[expr[0].result_str()] = expr

        # Skip if dict is empty
        if len(self.data.keys()) == 0:
            return

        # Instead of using the .data dictionary, use the merge_in_log which maintains the expression application order
        # Using this list, replace all the trigger USB codes
        for key, log_expr, active in self.merge_in_log:
            # Skip if not active
            if not active:
                continue

            # Lookup currently merged expression
            if key not in self.data.keys():
                continue
            expr = self.data[key]

            for sub_expr in expr:
                # 1) Single USB Codes trigger results will replace the original ScanCode result
                if sub_expr.elems()[0] == 1 and sub_expr.triggers[0][0][0].type in ['USBCode', 'SysCode', 'ConsCode']:
                    # Debug info
                    if debug:
                        print("\033[1mSingle\033[0m", key, expr)

                    # Lookup trigger to see if it exists
                    trigger_str = sub_expr.trigger_str()
                    if trigger_str in result_code_lookup.keys():
                        # Calculate new key
                        new_expr = result_code_lookup[trigger_str][0]
                        new_key = "{0}{1}".format(
                            new_expr.operator,
                            new_expr.unique_keys()[0][0]
                        )

                        # Determine action based on the new_expr.operator
                        orig_expr = self.data[new_key][0]

                        # Replace expression
                        if sub_expr.operator in [':']:
                            if debug:
                                print("\t\033[1;32mREPLACE\033[0m {0} -> {1}\n\t{2} => {3}".format(
                                    key,
                                    new_key,
                                    sub_expr,
                                    new_expr
                                ))

                            # Do replacement
                            self.data[new_key] = [expression.MapExpression(
                                    orig_expr.triggers,
                                    orig_expr.operator,
                                    sub_expr.results
                            )]

                            # Transfer connect_id
                            self.data[new_key][0].connect_id = orig_expr.connect_id

                            # Unset basemap on expression
                            self.data[new_key][0].base_map = False

                        # Add expression
                        elif sub_expr.operator in [':+']:
                            if debug:
                                print("\t\033[1;42mADD\033[0m {0} -> {1}\n\t{2} => {3}".format(
                                    key,
                                    new_key,
                                    sub_expr,
                                    new_expr
                                ))

                            # Add expression
                            self.data[new_key].append(expression.MapExpression(
                                orig_expr.triggers,
                                orig_expr.operator,
                                sub_expr.results
                            ))

                            # Unset basemap on sub results
                            for sub_expr in self.data[new_key]:
                                sub_expr.base_map = False

                        # Remove expression
                        elif sub_expr.operator in [':-']:
                            if debug:
                                print("\t\033[1;41mREMOVE\033[0m {0} -> {1}\n\t{2} => {3}".format(
                                    key,
                                    new_key,
                                    sub_expr,
                                    new_expr
                                ))

                        # Remove old key
                        if key in self.data.keys():
                            del self.data[key]

                    # Otherwise drop HID expression
                    else:
                        if debug:
                            print("\t\033[1;34mDROP\033[0m")
                        if key in self.data.keys():
                            del self.data[key]

                # 2) Complex triggers are processed to replace out any USB Codes with Scan Codes
                elif sub_expr.elems()[0] > 1:
                    # Debug info
                    if debug:
                        print("\033[1;4mMulti\033[0m ", key, expr)

                    # Lookup each trigger element and replace
                    # If any trigger element doesn't exist, drop expression
                    # Dive through sequence->combo->identifier (sequence of combos of ids)
                    replace = False
                    drop = False
                    for seq_in, sequence in enumerate(sub_expr.triggers):
                        for com_in, combo in enumerate(sequence):
                            for ident_in, identifier in enumerate(combo):
                                ident_str = "({0})".format(identifier)

                                # Replace identifier
                                if ident_str in result_code_lookup.keys():
                                    match_expr = result_code_lookup[ident_str]
                                    sub_expr.triggers[seq_in][com_in][ident_in] = match_expr[0].triggers[0][0][0]
                                    replace = True

                                # Ignore non-USB triggers
                                elif identifier.type in ['IndCode', 'GenericTrigger', 'Layer', 'LayerLock', 'LayerShift', 'LayerLatch', 'ScanCode']:
                                    pass

                                # Drop everything else
                                else:
                                    drop = True

                    # Trigger Identifier was replaced
                    if replace:
                        if debug:
                            print("\t\033[1;32mREPLACE\033[0m", expr)

                    # Trigger Identifier failed (may still occur if there was a replacement)
                    if drop:
                        if debug:
                            print("\t\033[1;34mDROP\033[0m")
                        del self.data[key]

        # Finally we can merge in the Lazy :: Set operators
        self.merge_lazy_operators(debug)

        # Show results of reduction
        if debug:
            print(self)


class AnimationData(Data):
    '''
    KLL datastructure for Animation configuration

    Animation -> modifiers
    '''


class AnimationFrameData(Data):
    '''
    KLL datastructure for Animation Frame configuration

    Animation -> Pixel Settings
    '''


class CapabilityData(Data):
    '''
    KLL datastructure for Capability mapping

    Capability -> C Function/Identifier
    '''


class DefineData(Data):
    '''
    KLL datastructure for Define mapping

    Variable -> C Define/Identifier
    '''


class PixelChannelData(Data):
    '''
    KLL datastructure for Pixel Channel mapping

    Pixel -> Channels
    '''

    def maxpixelid(self):
        '''
        Find max pixel id per connect id

        @return: dictionary of connect id to max pixel id
        '''
        max_pixel = {}
        for key, value in self.data.items():
            connect_id = value.connect_id

            # Make sure this is a PixelAddressId
            if isinstance(value.pixel.uid, PixelAddressId):
                max_uid = value.pixel.uid.index
            else:
                max_uid = value.pixel.uid

            # Initial value
            if connect_id not in max_pixel.keys():
                max_pixel[connect_id] = 0

            # Update if necessary
            if max_pixel[connect_id] < max_uid:
                max_pixel[connect_id] = max_uid

            # TODO REMOVEME
            #print( key,value, value.__class__, value.pixel.uid.index, value.connect_id )
        return max_pixel


class PixelPositionData(Data):
    '''
    KLL datastructure for Pixel Position mapping

    Pixel -> Physical Location
    '''

    def add_expression(self, expression, debug):
        '''
        Add expression to data structure

        May have multiple keys to add for a given expression

        @param expression: KLL Expression (fully tokenized and parsed)
        @param debug:      Enable debug output
        '''
        # Lookup unique keys for expression
        keys = expression.unique_keys()

        # Add/Modify expressions in datastructure
        for key, uniq_expr in keys:
            # Check which operation we are trying to do, add or modify
            if debug[0]:
                if key in self.data.keys():
                    output = self.debug_output['mod'].format(key)
                else:
                    output = self.debug_output['add'].format(key)
                print(debug[1] and output or ansi_escape.sub('', output))

            # If key already exists, just update
            if key in self.data.keys():
                self.data[key].update(uniq_expr)
            else:
                self.data[key] = uniq_expr

            # Append to log
            self.merge_in_log_expression(key, uniq_expr, debug)


class ScanCodePositionData(Data):
    '''
    KLL datastructure for ScanCode Position mapping

    ScanCode -> Physical Location
    '''

    def add_expression(self, expression, debug):
        '''
        Add expression to data structure

        May have multiple keys to add for a given expression

        @param expression: KLL Expression (fully tokenized and parsed)
        @param debug:      Enable debug output
        '''
        # Lookup unique keys for expression
        keys = expression.unique_keys()

        # Add/Modify expressions in datastructure
        for key, uniq_expr in keys:
            # Check which operation we are trying to do, add or modify
            if debug[0]:
                if key in self.data.keys():
                    output = self.debug_output['mod'].format(key)
                else:
                    output = self.debug_output['add'].format(key)
                print(debug[1] and output or ansi_escape.sub('', output))

            # If key already exists, just update
            if key in self.data.keys():
                self.data[key].update(uniq_expr)
            else:
                self.data[key] = uniq_expr

            # Append to log
            self.merge_in_log_expression(key, uniq_expr, debug)


class VariableData(Data):
    '''
    KLL datastructure for Variables and Arrays

    Variable -> Data
    Array    -> Data
    '''

    def add_expression(self, expression, debug):
        '''
        Add expression to data structure

        May have multiple keys to add for a given expression

        In the case of indexed variables, only replaced the specified index

        @param expression: KLL Expression (fully tokenized and parsed)
        @param debug:      Enable debug output
        '''
        # Lookup unique keys for expression
        keys = expression.unique_keys()

        # Add/Modify expressions in datastructure
        for key, uniq_expr in keys:
            # Check which operation we are trying to do, add or modify
            if debug[0]:
                if key in self.data.keys():
                    output = self.debug_output['mod'].format(key)
                else:
                    output = self.debug_output['add'].format(key)
                print(debug[1] and output or ansi_escape.sub('', output))

            # Check to see if we need to cap-off the array (a position parameter is given)
            if uniq_expr.type == 'Array' and uniq_expr.pos is not None:
                # Modify existing array
                if key in self.data.keys():
                    self.data[key].merge_array(uniq_expr)

                # Add new array
                else:
                    uniq_expr.merge_array()
                    self.data[key] = uniq_expr

            # Otherwise just add/replace expression
            else:
                self.data[key] = uniq_expr

            # Append to log
            self.merge_in_log_expression(key, uniq_expr, debug)


class Organization:
    '''
    Container class for KLL datastructures

    The purpose of these datastructures is to symbolically store at first, and slowly solve/deduplicate expressions.
    Since the order in which the merges occurs matters, this involves a number of intermediate steps.
    '''

    def __init__(self, parent):
        '''
        Intialize data structure
        '''
        self.parent = parent

        # Setup each of the internal sub-datastructures
        self.animation_data = AnimationData(self)
        self.animation_frame_data = AnimationFrameData(self)
        self.capability_data = CapabilityData(self)
        self.define_data = DefineData(self)
        self.mapping_data = MappingData(self)
        self.pixel_channel_data = PixelChannelData(self)
        self.pixel_position_data = PixelPositionData(self)
        self.scan_code_position_data = ScanCodePositionData(self)
        self.variable_data = VariableData(self)

        # Expression to Datastructure mapping
        self.data_mapping = {
            'AssignmentExpression': {
                'Array': self.variable_data,
                'Variable': self.variable_data,
            },
            'DataAssociationExpression': {
                'Animation': self.animation_data,
                'AnimationFrame': self.animation_frame_data,
                'PixelPosition': self.pixel_position_data,
                'ScanCodePosition': self.scan_code_position_data,
            },
            'MapExpression': {
                'TriggerCode': self.mapping_data,
                'PixelChannel': self.pixel_channel_data,
            },
            'NameAssociationExpression': {
                'Capability': self.capability_data,
                'Define': self.define_data,
            },
        }

    def __copy__(self):
        '''
        On organization copy, return a safe object

        Attempts to only copy the datastructures that may need to diverge
        '''
        new_obj = Organization(self.parent)

        # Copy only .data from each organization
        new_obj.animation_data.data = copy.copy(self.animation_data.data)
        new_obj.animation_frame_data.data = copy.copy(self.animation_frame_data.data)
        new_obj.capability_data.data = copy.copy(self.capability_data.data)
        new_obj.define_data.data = copy.copy(self.define_data.data)
        new_obj.mapping_data.data = copy.copy(self.mapping_data.data)
        new_obj.pixel_channel_data.data = copy.copy(self.pixel_channel_data.data)
        new_obj.pixel_position_data.data = copy.copy(self.pixel_position_data.data)
        new_obj.scan_code_position_data.data = copy.copy(self.scan_code_position_data.data)
        new_obj.variable_data.data = copy.copy(self.variable_data.data)

        # Also copy merge_in_log
        new_obj.animation_data.merge_in_log = copy.copy(self.animation_data.merge_in_log)
        new_obj.animation_frame_data.merge_in_log = copy.copy(self.animation_frame_data.merge_in_log)
        new_obj.capability_data.merge_in_log = copy.copy(self.capability_data.merge_in_log)
        new_obj.define_data.merge_in_log = copy.copy(self.define_data.merge_in_log)
        new_obj.mapping_data.merge_in_log = copy.copy(self.mapping_data.merge_in_log)
        new_obj.pixel_channel_data.merge_in_log = copy.copy(self.pixel_channel_data.merge_in_log)
        new_obj.pixel_position_data.merge_in_log = copy.copy(self.pixel_position_data.merge_in_log)
        new_obj.scan_code_position_data.merge_in_log = copy.copy(self.scan_code_position_data.merge_in_log)
        new_obj.variable_data.merge_in_log = copy.copy(self.variable_data.merge_in_log)

        return new_obj

    def stores(self):
        '''
        Returns list of sub-datastructures
        '''
        return [
            self.animation_data,
            self.animation_frame_data,
            self.capability_data,
            self.define_data,
            self.mapping_data,
            self.pixel_channel_data,
            self.pixel_position_data,
            self.scan_code_position_data,
            self.variable_data,
        ]

    def add_expression(self, expression, debug):
        '''
        Add expression to datastructure

        Will automatically determine which type of expression and place in the relevant store

        @param expression: KLL Expression (fully tokenized and parsed)
        @param debug:      Enable debug output
        '''
        # Determine type of of Expression
        expression_type = expression.__class__.__name__

        # Determine Expression Subtype
        expression_subtype = expression.type

        # Locate datastructure
        data = self.data_mapping[expression_type][expression_subtype]

        # Debug output
        if debug[0]:
            output = "\t\033[4m{0}\033[0m".format(data.__class__.__name__)
            print(debug[1] and output or ansi_escape.sub('', output))

        # Add expression to determined datastructure
        data.add_expression(expression, debug)

    def merge(self, merge_in, map_type, debug):
        '''
        Merge in the given organization to this organization

        This organization serves as the base.

        @param merge_in: Organization to merge into this one
        @param map_type: Used fo map specific merges
        @param debug:    Enable debug out
        '''
        # Merge each of the sub-datastructures
        for this, that in zip(self.stores(), merge_in.stores()):
            this.merge(that, map_type, debug)

    def cleanup(self, debug=False):
        '''
        Post-processing step for merges that may need to remove some data in the organization.
        Mainly used for dropping BaseMapContext expressions after generating a PartialMapContext.
        '''
        for store in self.stores():
            store.cleanup(debug)

    def reduction(self, debug=False):
        '''
        Simplifies datastructure

        NOTE: This will remove data, therefore, context is lost
        '''
        for store in self.stores():
            store.reduction(debug)

    def maxscancode(self):
        '''
        Find max scancode per connect id

        @return: dictionary of connect id to max scancode
        '''
        return self.mapping_data.maxscancode()

    def maxpixelid(self):
        '''
        Find max pixel id per connect id

        @return: dictionary of connect id to max pixel id
        '''
        return self.pixel_channel_data.maxpixelid()

    def __repr__(self):
        return "{0}".format(self.stores())
