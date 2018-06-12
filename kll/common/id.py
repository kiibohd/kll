#!/usr/bin/env python3
'''
KLL Id Containers
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

from kll.common.channel import ChannelList
from kll.common.modifier import AnimationModifierList, PixelModifierList
from kll.common.position import Position
from kll.common.schedule import Schedule

from kll.extern.funcparserlib.parser import NoParseError



### Decorators ###

# Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'



### Classes ###

class Id:
    '''
    Base container class for various KLL types
    '''

    def __init__(self):
        self.type = None
        self.uid = None

    def get_uid(self):
        '''
        Some Id types have alternate uid mappings
        self.uid stores the original uid whereas it may be updated due to multi-node configurations
        '''
        return self.uid

    def json(self):
        '''
        JSON representation of Id
        Generally each specialization of the Id class will need to enhance this function.
        '''
        return {
            'type' : self.type,
            'uid'  : self.uid,
        }

    def kllify(self):
        '''
        Returns KLL version of the Id

        In most cases we can just the string representation of the object
        '''
        return "{0}".format(self)


class HIDId(Id, Schedule):
    '''
    HID/USB identifier container class
    '''
    secondary_types = {
        'USBCode': 'USB',
        'SysCode': 'SYS',
        'ConsCode': 'CONS',
        'IndCode': 'IND',
    }

    kll_types = {
        'USBCode': 'U',
        'SysCode': 'SYS',
        'ConsCode': 'CONS',
        'IndCode': 'I',
    }

    type_width = {
        'USBCode': 1,
        'SysCode': 1,
        'ConsCode': 2,
        'IndCode': 1,
    }

    type_locale = {
        'USBCode': 'to_hid_keyboard',
        'SysCode': 'to_hid_sysctrl',
        'ConsCode': 'to_hid_consumer',
        'IndCode': 'to_hid_led',
    }

    def __init__(self, type, uid, locale):
        '''
        @param type:   String type of the Id
        @param uid:    Unique integer identifier for the Id
        @param locale: Locale layout object used to decode used to decode uid
        '''
        Id.__init__(self)
        Schedule.__init__(self)
        self.type = type
        self.uid = uid
        self.locale = locale
        self.locale_type = self.type_locale[self.type]

        # Set secondary type
        self.second_type = self.secondary_types[self.type]

        # Set kll type
        self.kll_type = self.kll_types[self.type]

        # Determine hex_str padding
        self.padding = 2
        if self.type == 'ConsCode':
            self.padding = 3

        # Validate uid is in locale based on what type of HID field it is
        if self.hex_str() not in self.locale.json()[self.locale_type].keys():
            print("{} Unknown HID({}) UID('{}') in locale '{}'".format(
                WARNING,
                self.type,
                self.uid,
                self.locale.name()
            ))

    def hex_str(self):
        '''
        Returns hex string used by locale for uid lookup
        '''
        return "0x{0:0{1}X}".format(self.uid, self.padding)

    def get_hex_str(self):
        '''
        Returns hex string used by locale for uid lookup, uses self.get_uid() instead of self.uid
        '''
        return "0x{0:0{1}X}".format(self.get_uid(), self.padding)

    def width(self):
        '''
        Returns the bit width of the HIDId

        This is the maximum number of bytes required for each type of HIDId as per the USB spec.
        Generally this is just 1 byte, however, Consumer elements (ConsCode) requires 2 bytes.
        '''
        return self.type_width[self.type]

    def __repr__(self):
        '''
        Use string name instead of integer, easier to debug
        '''
        try:
            name = self.locale.json()[self.locale_type][self.hex_str()]
            schedule = self.strSchedule()
            if len(schedule) > 0:
                schedule = "({0})".format(schedule)

            output = 'HID({},{})"{}"{}'.format(self.type, self.locale.name(), self.uid, name, schedule)
            return output
        except:
            print("{} '{}' is an invalid dictionary lookup.".format(
                WARNING,
                (self.second_type, self.uid),
            ))
            return "<INVALID>"

    def json(self):
        '''
        JSON representation of HIDId
        '''
        output = Id.json(self)
        output.update(Schedule.json(self))
        return output

    def kllify(self):
        '''
        Returns KLL version of the Id
        '''
        schedule = self.strSchedule()
        if len(schedule) > 0:
            schedule = "({0})".format(schedule)

        output = "{0}{1:#05x}{2}".format(self.kll_type, self.uid, schedule)
        return output


class ScanCodeId(Id, Schedule, Position):
    '''
    Scan Code identifier container class
    '''

    def __init__(self, uid):
        Id.__init__(self)
        Schedule.__init__(self)
        Position.__init__(self)
        self.type = 'ScanCode'
        self.uid = uid

        # This uid is used for any post-processing of the uid
        # The original uid is maintained in case it is needed
        self.updated_uid = None

    def inferred_type(self):
        '''
        Always returns ScanCode (simplifies code when mixed with PixelAddressId)
        '''
        return 'PixelAddressId_ScanCode'

    def get_uid(self):
        '''
        Determine uid
        May have been updated due to connect_id setting for interconnect offsets
        '''
        uid = self.uid
        if self.updated_uid is not None:
            uid = self.updated_uid

        return uid

    def uid_set(self):
        '''
        Returns a tuple of uids, always a single element for ScanCodeId
        '''
        return tuple([self.get_uid()])

    def unique_key(self):
        '''
        Returns the key string used for datastructure sorting
        '''
        # Positions are a special case
        if self.positionSet():
            return "S{0:03d}".format(self.get_uid())

    def __repr__(self):
        # Positions are a special case
        if self.positionSet():
            return "{0} <= {1}".format(self.unique_key(), self.strPosition())

        schedule = self.strSchedule()
        if len(schedule) > 0:
            return "S{0:03d}({1})".format(self.get_uid(), schedule)
        else:
            return "S{0:03d}".format(self.get_uid())

    def json(self):
        '''
        JSON representation of ScanCodeId
        '''
        output = Id.json(self)
        output.update(Schedule.json(self))
        output.update(Position.json(self))
        return output

    def kllify(self):
        '''
        Returns KLL version of the Id
        '''
        schedule = self.strSchedule()
        if len(schedule) > 0:
            schedule = "({0})".format(schedule)

        output = "S{0:#05x}{1}".format(self.get_uid(), schedule)

        # Position enabled
        if self.isPositionSet():
            output += " <= {0}".format(self.strPosition())
        return output


class LayerId(Id, Schedule):
    '''
    Layer identifier container class
    '''

    def __init__(self, type, layer):
        Id.__init__(self)
        Schedule.__init__(self)
        self.type = type
        self.uid = layer

    def __repr__(self):
        schedule = self.strSchedule()
        if len(schedule) > 0:
            return "{0}[{1}]({2})".format(
                self.type,
                self.uid,
                schedule,
            )
        else:
            return "{0}[{1}]".format(
                self.type,
                self.uid,
            )

    def width(self):
        '''
        Returns the bit width of the LayerId

        This is currently 2 bytes.
        '''
        return 2

    def json(self):
        '''
        JSON representation of LayerId
        '''
        output = Id.json(self)
        output.update(Schedule.json(self))
        return output

    def kllify(self):
        '''
        Returns KLL version of the Id
        '''
        # The string __repr__ is KLL in this case
        return str(self)


class TriggerId(Id, Schedule):
    '''
    Generic trigger identifier container class
    '''

    def __init__(self, idcode, uid):
        Id.__init__(self)
        Schedule.__init__(self)
        self.type = 'GenericTrigger'
        self.uid = uid
        self.idcode = idcode

    def __repr__(self):
        schedule = self.strSchedule()
        schedule_val = ""
        if len(schedule) > 0:
            schedule_val = "({})".format(schedule)

        return "T[{0},{1}]{2}".format(
            self.idcode,
            self.uid,
            schedule_val,
        )

    def json(self):
        '''
        JSON representation of TriggerId
        '''
        output = Id.json(self)
        output.update(Schedule.json(self))
        return output

    def kllify(self):
        '''
        Returns KLL version of the Id
        '''
        # The string __repr__ is KLL in this case
        return str(self)


class AnimationId(Id, Schedule, AnimationModifierList):
    '''
    Animation identifier container class
    '''
    name = None

    def __init__(self, name, state=None):
        Id.__init__(self)
        Schedule.__init__(self)
        AnimationModifierList.__init__(self)
        self.name = name
        self.type = 'Animation'
        self.second_type = 'A'
        self.state = state

    def __repr__(self):
        state = ""
        if self.state is not None:
            state = ", {}".format(self.state)
        schedule = self.strSchedule()
        if len(schedule) > 0:
            return "A[{0}{1}]({2})".format(self.name, state, self.strSchedule())
        if len(self.modifiers) > 0:
            return "A[{0}{1}]({2})".format(self.name, state, self.strModifiers())
        return self.base_repr()

    def base_repr(self):
        '''
        Returns string of just the identifier, exclude animation modifiers
        '''
        state = ""
        if self.state is not None:
            state = ", {}".format(self.state)
        return "A[{0}{1}]".format(self.name, state)

    def width(self):
        '''
        Returns the bit width of the AnimationId

        This is currently 2 bytes.
        '''
        return 2

    def json(self):
        '''
        JSON representation of AnimationId
        '''
        output = Id.json(self)
        output.update(AnimationModifierList.json(self))
        output.update(Schedule.json(self))
        output['name'] = self.name
        output['setting'] = "{}".format(self)
        output['state'] = self.state
        del output['uid']
        return output


class AnimationFrameId(Id, AnimationModifierList):
    '''
    Animation Frame identifier container class
    '''

    def __init__(self, name, index):
        Id.__init__(self)
        AnimationModifierList.__init__(self)
        self.name = name
        self.index = index
        self.type = 'AnimationFrame'

    def __repr__(self):
        return "AF[{0}, {1}]".format(self.name, self.index)

    def kllify(self):
        '''
        Returns KLL version of the Id
        '''
        return "A[{0}, {1}]".format(self.name, self.index)


class PixelId(Id, Position, PixelModifierList, ChannelList):
    '''
    Pixel identifier container class
    '''

    def __init__(self, uid):
        Id.__init__(self)
        Position.__init__(self)
        PixelModifierList.__init__(self)
        ChannelList.__init__(self)
        self.uid = uid
        self.type = 'Pixel'

    def unique_key(self, kll=False):
        '''
        Returns the key string used for datastructure sorting

        @param kll: Kll output format mode
        '''
        if isinstance(self.uid, HIDId) or isinstance(self.uid, ScanCodeId):
            if kll:
                return "{0}".format(self.uid.kllify())
            return "P[{0}]".format(self.uid)

        if isinstance(self.uid, PixelAddressId):
            if kll:
                return "P[{0}]".format(self.uid.kllify())
            return "P[{0}]".format(self.uid)

        if kll:
            return "P{0:#05x}".format(self.uid)

        return "P{0}".format(self.uid)

    def __repr__(self):
        # Positions are a special case
        if self.positionSet():
            return "{0} <= {1}".format(self.unique_key(), self.strPosition())

        extra = ""
        if len(self.modifiers) > 0:
            extra += "({0})".format(self.strModifiers())
        if len(self.channels) > 0:
            extra += "({0})".format(self.strChannels())
        return "{0}{1}".format(self.unique_key(), extra)

    def kllify(self):
        '''
        KLL syntax compatible output for Pixel object
        '''
        # Positions are a special case
        if self.positionSet():
            return "{0} <= {1}".format(self.unique_key(kll=True), self.strPosition())

        extra = ""
        if len(self.modifiers) > 0:
            extra += "({0})".format(self.strModifiers())
        if len(self.channels) > 0:
            extra += "({0})".format(self.strChannels())
        return "{0}{1}".format(self.unique_key(kll=True), extra)


class PixelAddressId(Id):
    '''
    Pixel address identifier container class
    '''

    def __init__(self, index=None, col=None, row=None, relCol=None, relRow=None):
        Id.__init__(self)

        # Check to make sure index, col or row is set
        if index is None and col is None and row is None and relRow is None and relCol is None:
            print("{0} index, col or row must be set".format(ERROR))

        self.index = index
        self.col = col
        self.row = row
        self.relCol = relCol
        self.relRow = relRow

        self.type = 'PixelAddress'

    def inferred_type(self):
        '''
        Determine which PixelAddressType based on set values
        '''

        if self.index is not None:
            return 'PixelAddressId_Index'
        if self.col is not None and self.row is None:
            return 'PixelAddressId_ColumnFill'
        if self.col is None and self.row is not None:
            return 'PixelAddressId_RowFill'
        if self.col is not None and self.row is not None:
            return 'PixelAddressId_Rect'
        if self.relCol is not None and self.relRow is None:
            return 'PixelAddressId_RelativeColumnFill'
        if self.relCol is None and self.relRow is not None:
            return 'PixelAddressId_RelativeRowFill'
        if self.relCol is not None and self.relRow is not None:
            return 'PixelAddressId_RelativeRect'

        print("{0} Unknown PixelAddressId, this is a bug!".format(ERROR))
        return "<UNKNOWN PixelAddressId>"

    def uid_set(self):
        '''
        Returns a tuple of uids, depends on what has been set.
        '''
        if self.index is not None:
            return tuple([self.index])
        if self.col is not None and self.row is None:
            return tuple([self.col, self.row])
        if self.col is None and self.row is not None:
            return tuple([self.col, self.row])
        if self.col is not None and self.row is not None:
            return tuple([self.col, self.row])
        if self.relCol is not None and self.relRow is None:
            return tuple([self.relCol, self.relRow])
        if self.relCol is None and self.relRow is not None:
            return tuple([self.relCol, self.relRow])
        if self.relCol is not None and self.relRow is not None:
            return tuple([self.relCol, self.relRow])

        print("{0} Unknown uid set, this is a bug!".format(ERROR))
        return "<UNKNOWN uid set"

    def merge(self, address):
        '''
        Merge in a PixelAddressId

        Will error-out instead of overwriting

        @param address: PixelAddressId object to merge in
        '''
        # Make sure we are either index or col/row
        if not self.index is None or not address.index is None:
            print("{0} Cannot merge into index PixelAddressIds".format(ERROR))
            raise NoParseError

        # Make sure we don't overwrite
        if not self.col is None and not address.col is None:
            print("{0} Duplicate column fields '{1}' '{2}'".format(ERROR, self, address))
            raise NoParseError
        if not self.row is None and not address.row is None:
            print("{0} Duplicate row fields '{1}' '{2}'".format(ERROR, self, address))
            raise NoParseError

        # Merge over values
        if not address.col is None:
            self.col = address.col
        if not address.row is None:
            self.row = address.row
        if not address.relCol is None:
            self.relCol = address.relCol
        if not address.relRow is None:
            self.relRow = address.relRow

    def valueStr(self, value):
        '''
        Prepare numerical value based on type

        @param value: Float or Integer position

        @return: String
        '''
        output = ""

        # Check if float
        if isinstance(value, float):
            output += "{0}%".format(value * 100)
        else:
            output += "{0:03d}".format(value)

        return output

    def outputStrList(self):
        '''
        List of string items used for __repr__ and kllify

        @returns: List of strings
        '''
        output = []

        # Construct representation
        if not self.index is None:
            output.append("{0}".format(self.valueStr(self.index)))
        if not self.row is None:
            cur_out = "r:{0}".format(self.valueStr(self.row))
            output.append(cur_out)
        if not self.col is None:
            cur_out = "c:{0}".format(self.valueStr(self.col))
            output.append(cur_out)
        if not self.relRow is None:
            cur_out = "r:i"
            cur_out += self.relRow >= 0 and "+" or ""
            cur_out += "{0}".format(self.valueStr(self.relRow))
            output.append(cur_out)
        if not self.relCol is None:
            cur_out = "c:i"
            cur_out += self.relCol >= 0 and "+" or ""
            cur_out += "{0}".format(self.valueStr(self.relCol))
            output.append(cur_out)

        return output

    def __repr__(self):
        return "{0}".format(self.outputStrList())

    def kllify(self):
        '''
        KLL syntax compatible output for PixelAddress object
        '''
        return ",".join(self.outputStrList())


class PixelLayerId(Id, PixelModifierList):
    '''
    Pixel Layer identifier container class
    '''

    def __init__(self, uid):
        Id.__init__(self)
        PixelModifierList.__init__(self)
        self.uid = uid
        self.type = 'PixelLayer'

    def __repr__(self):
        if len(self.modifiers) > 0:
            return "PL{0}({1})".format(self.uid, self.strModifiers())
        return "PL{0}".format(self.uid)


class CapId(Id):
    '''
    Capability identifier
    '''

    def __init__(self, name, type, arg_list=[]):
        '''
        @param name:     Name of capability
        @param type:     Type of capability definition, string
        @param arg_list: List of CapArgIds, empty list if there are none
        '''
        Id.__init__(self)
        self.name = name
        self.type = type
        self.arg_list = arg_list

    def __repr__(self):
        # Generate prettified argument list
        arg_string = ""
        for arg in self.arg_list:
            arg_string += "{0},".format(arg)
        if len(arg_string) > 0:
            arg_string = arg_string[:-1]

        return "{0}({1})".format(self.name, arg_string)

    def json(self):
        '''
        JSON representation of CapId
        '''
        return {
            'type' : self.type,
            'name' : self.name,
            'args' : [arg.json() for arg in self.arg_list]
        }

    def total_arg_bytes(self, capabilities_dict=None):
        '''
        Calculate the total number of bytes needed for the args

        @param capabilities_dict: Dictionary of capabilities used, just in case no widths have been assigned

        return: Number of bytes
        '''
        # Zero if no args
        total_bytes = 0
        for index, arg in enumerate(self.arg_list):
            # Lookup actual width if necessary (wasn't set explicitly)
            if capabilities_dict is not None and (arg.type == 'CapArgValue' or arg.width is None):
                # Check if there are enough arguments
                expected = len(capabilities_dict[self.name].association.arg_list)
                got = len(self.arg_list)
                if got != expected:
                    print("{0} incorrect number of arguments for {1}. Expected {2} Got {3}".format(
                        ERROR,
                        self,
                        expected,
                        got,
                    ))
                    print("\t{0}".format(capabilities_dict[self.name].kllify()))
                    raise AssertionError("Invalid arguments")

                total_bytes += capabilities_dict[self.name].association.arg_list[index].width

            # Otherwise use the set width
            else:
                total_bytes += arg.width

        return total_bytes


class NoneId(CapId):
    '''
    None identifier

    It's just a capability...that does nothing (instead of infering to do something else)
    '''

    def __init__(self):
        super().__init__('None', 'None')

    def json(self):
        '''
        JSON representation of NoneId
        '''
        return {
            'type' : self.type,
        }

    def __repr__(self):
        return "None"


class CapArgId(Id):
    '''
    Capability Argument identifier
    '''

    def __init__(self, name, width=None):
        '''
        @param name:  Name of argument
        @param width: Byte-width of the argument, if None, this is not port of a capability definition
        '''
        Id.__init__(self)
        self.name = name
        self.width = width
        self.type = 'CapArg'

    def __repr__(self):
        if self.width is None:
            return "{0}".format(self.name)
        else:
            return "{0}:{1}".format(self.name, self.width)

    def json(self):
        '''
        JSON representation of CapArgId
        '''
        return {
            'name' : self.name,
            'width' : self.width,
            'type' : self.type,
        }


class CapArgValue(Id):
    '''
    Capability Argument Value identifier
    '''

    def __init__(self, value):
        '''
        @param value: Value of argument
        '''
        Id.__init__(self)
        self.value = value
        self.type = 'CapArgValue'

    def __repr__(self):
        return "{}".format(self.value)

    def json(self):
        '''
        JSON representation of CapArgValue
        '''
        return {
            'value' : self.value,
            'type' : self.type,
        }

