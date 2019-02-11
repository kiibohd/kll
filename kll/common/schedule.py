#!/usr/bin/env python3
'''
KLL Schedule Containers
'''

# Copyright (C) 2016-2019 by Jacob Alexander
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

import numbers



### Decorators ###

# Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'



### Classes ###

class Time:
    '''
    Time parameter
    '''
    multipliers = {
        's' : 1,
        'ms' : 10 ** 3,
        'us' : 10 ** 6,
        'ns' : 10 ** 9,
    }

    def __init__(self, time, unit):
        self.time = time
        self.unit = unit

    def to_ms(self):
        '''
        Convert time to ms

        @returns: <ms>
        '''
        seconds = self.time / self.multipliers[self.unit]
        return seconds * self.multipliers['ms']

    def to_ms_ticks(self, frequency):
        '''
        Convert time to ms and ticks

        @param frequency: CPU frequency to convert to ticks (in Hz)
        @returns: (<ms>, <ticks>)
        '''
        seconds = self.time / self.multipliers[self.unit]

        # Calculate ms and remainder (for ticks)
        ms_full = seconds * self.multipliers['ms']
        ms = int(ms_full)
        ms_remainder = ms_full - ms

        # Calculate ticks
        seconds_remainder = ms_remainder / self.multipliers['ms']
        ticks = seconds_remainder * frequency

        return (ms, ticks)

    def __repr__(self):
        return "{0}{1}".format(self.time, self.unit)

    def json(self):
        '''
        JSON representation of Time
        '''
        output = {
            'time' : self.time,
            'unit' : self.unit,
        }
        return output


class Schedule:
    '''
    Identifier schedule
    Each schedule may have multiple parameters configuring how the element is scheduled

    Used for trigger and result elements
    '''

    def __init__(self):
        self.parameters = None

    def setSchedule(self, parameters):
        '''
        Applies given list of Schedule Parameters to Schedule

        None signifies an undefined schedule which allows free-form scheduling
        at either a later stage or at the convenience of the device firmware/driver

        If schedule is already set, do not overwrite, expressions are read inside->out
        '''
        # Ignore if already set
        if self.parameters is not None or parameters is None:
            return

        # Morph parameter based on Schedule type
        for param in parameters:
            param.setType(self)
            param.checkParam()
        self.parameters = parameters

    def strSchedule(self, kll=False):
        '''
        __repr__ of Schedule when multiple inheritance is used
        '''
        output = ""
        if self.parameters is not None:
            for index, param in enumerate(self.parameters):
                if index > 0:
                    output += ","
                output += "{0}".format(param.kllify())
        return output

    def json(self):
        '''
        JSON representation of Schedule
        '''
        output = dict()
        output['schedule'] = []
        if self.parameters is not None:
            for param in self.parameters:
                output['schedule'].append(param.json())
        return output

    def kllify(self):
        '''
        KLL representation of object
        '''
        return self.strSchedule(kll=True)

    def __repr__(self):
        return self.strSchedule()


class ScheduleParam:
    '''
    Schedule parameter

    In the case of a Timing parameter, the base type is unknown and must be inferred later
    '''
    button_schedule_lookup = {
        'P': ('Press', 'P'),
        'H': ('Hold', 'H'),
        'R': ('Release', 'R'),
        'O': ('Off', 'O'),
        'UP': ('Unique Press', 'UP'),
        'UR': ('Unique Release', 'UR'),
    }
    indicator_schedule_lookup = {
        'A': ('Activate', 'A'),
        'On': ('On', 'On'),
        'D': ('Deactivate', 'D'),
        'Off': ('Off', 'Off'),
    }

    animation_schedule_lookup = {
        'D': ('Done', 'Done'),
        'R': ('Repeat', 'Repeat'),
    }

    def __init__(self, state, timing=None):
        '''
        @param state: State identifier (string)
        @param timing: Timing parameter
        '''
        self.state = state
        self.timing = timing
        self.parent = None

    def scheduleLookup(self):
        '''
        Using the class name determine which state to lookup
        '''
        if self.__class__ == IndicatorScheduleParam:
            return self.indicator_schedule_lookup[self.state]
        elif self.__class__ == AnalogScheduleParam:
            return self.state
        elif self.__class__ == ButtonScheduleParam:
            return self.button_schedule_lookup[self.state]
        elif self.__class__ == AnimationScheduleParam:
            return self.animation_schedule_lookup[self.state]
        elif self.__class__ == IndexScheduleParam:
            return self.state

        return None

    def isAnalog(self):
        '''
        @returns: True if an analog schedule parameter
        '''
        return self.__class__ == AnalogScheduleParam

    def isIndex(self):
        '''
        @returns: True if an index schedule parameter
        '''
        return self.__class__ == IndexScheduleParam

    def setType(self, parent):
        '''
        Change class type to match the Schedule object

        @param parent: Parent Schedule object
        '''
        self.parent = parent

        if self.parent.__class__.__name__ in ["HIDId"] and self.parent.type == 'IndCode':
            self.__class__ = IndicatorScheduleParam
        elif self.parent.__class__.__name__ in ["LayerId"]:
            self.__class__ = IndicatorScheduleParam
        elif self.parent.__class__.__name__ in ["TriggerId"] and isinstance(self.state, int):
            self.__class__ = IndexScheduleParam
        elif self.parent.__class__.__name__ in ["HIDId", "ScanCodeId", "TriggerId", "CapId"]:
            # Check if an analog
            if isinstance(self.state, numbers.Number):
                self.__class__ = AnalogScheduleParam
            else:
                self.__class__ = ButtonScheduleParam
        elif self.parent.__class__.__name__ in ["AnimationId"]:
            self.__class__ = AnimationScheduleParam

    def checkParam(self):
        '''
        Validate that parameter is valid

        @returns: If assigned state is valid for the assigned class
        '''
        # Check for invalid state
        invalid_state = True

        if self.state in ['P', 'H', 'R', 'O', 'UP', 'UR'] and self.__class__.__name__ == 'ButtonScheduleParam':
            invalid_state = False
        elif self.state in ['A', 'On', 'D', 'Off'] and self.__class__.__name__ == 'IndicatorScheduleParam':
            invalid_state = False
        elif self.state in ['D', 'R', 'O'] and self.__class__.__name__ == 'AnimationScheduleParam':
            invalid_state = False
        elif isinstance(self.state, numbers.Number) and (self.__class__.__name__ == 'AnalogScheduleParam' or self.__class__.__name__ == 'IndexScheduleParam'):
            invalid_state = False
        elif self.state is None and self.timing is not None:
            invalid_state = False

        if invalid_state:
            print("{0} Invalid {2} state '{1}'".format(ERROR, self.state, self.__class__.__name__))
        return not invalid_state

    def setTiming(self, timing):
        '''
        Set parameter timing
        '''
        self.timing = timing

    def json(self):
        '''
        JSON representation of ScheduleParam
        '''
        output = dict()
        output['state'] = self.state
        if self.timing is not None:
            output['timing'] = self.timing.json()
        return output

    def kllify(self):
        '''
        KLL representation of ScheduleParam object
        '''
        output = ""
        if self.state is None and self.timing is not None:
            output += "{0}".format(self.timing)
        return output

    def __repr__(self):
        output = ""
        if self.state is None and self.timing is not None:
            output += "{0}".format(self.timing)
        else:
            output += "??"
            print("{0} Unknown ScheduleParam state '{1}'".format(ERROR, self.state))
        return output


class ButtonScheduleParam(ScheduleParam):
    '''
    Button Schedule Parameter

    Accepts:
    P  - Press
    H  - Hold
    R  - Release
    O  - Off
    UP - Unique Press
    UR - Unique Release

    Timing specifiers are valid.
    Validity of specifiers are context dependent, and may error at a later stage, or be stripped altogether
    '''

    def __repr__(self):
        output = ""
        if self.state is not None:
            output += "{0}".format(self.state)
        if self.state is not None and self.timing is not None:
            output += ":"
        if self.timing is not None:
            output += "{0}".format(self.timing)
        return output

    def kllify(self):
        '''
        KLL representation of object
        '''
        return "{0}".format(self)


class AnalogScheduleParam(ScheduleParam):
    '''
    Analog Schedule Parameter

    Accepts:
    Value from 0 to 100, indicating a percentage pressed

    XXX: Might be useful to accept decimal percentages
    '''

    def __repr__(self):
        output = ""
        if self.state is not None:
            output += "{0}".format(self.state)
        if self.state is not None and self.timing is not None:
            output += ":"
        if self.timing is not None:
            output += "{0}".format(self.timing)
        return output

    def kllify(self):
        '''
        KLL representation of object
        '''
        return "{0}".format(self.state)


class IndexScheduleParam(ScheduleParam):
    '''
    Index Schedule Parameter

    Accepts:
    Value from 0 to 255
    '''

    def __repr__(self):
        output = ""
        if self.state is not None:
            output += "{0}".format(self.state)
        if self.state is not None and self.timing is not None:
            output += ":"
        if self.timing is not None:
            output += "{0}".format(self.timing)
        return output

    def kllify(self):
        '''
        KLL representation of object
        '''
        return "{0}".format(self.state)


class IndicatorScheduleParam(ScheduleParam):
    '''
    Indicator Schedule Parameter

    Accepts:
    A   - Activate
    On
    D   - Deactivate
    Off

    Timing specifiers are valid.
    Validity of specifiers are context dependent, and may error at a later stage, or be stripped altogether
    '''

    def __repr__(self):
        output = ""
        if self.state is not None:
            output += "{0}".format(self.state)
        if self.state is not None and self.timing is not None:
            output += ":"
        if self.timing is not None:
            output += "{0}".format(self.timing)
        return output

    def kllify(self):
        '''
        KLL representation of object
        '''
        return "{0}".format(self)


class AnimationScheduleParam(ScheduleParam):
    '''
    Animation Schedule Parameter

    Accepts:
    D   - Done
    R   - Repeat
    O   - Off

    Timing specifiers are valid.
    Validity of specifiers are context dependent, and may error at a later stage, or be stripped altogether
    '''

    def __repr__(self):
        output = ""
        if self.state is not None:
            output += "{0}".format(self.state)
        if self.state is not None and self.timing is not None:
            output += ":"
        if self.timing is not None:
            output += "{0}".format(self.timing)
        return output

    def kllify(self):
        '''
        KLL representation of object
        '''
        return "{0}".format(self)
