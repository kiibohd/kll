#!/usr/bin/env python3
'''
KLL Position Containers
'''

# Copyright (C) 2016-2017 by Jacob Alexander
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

class Position:
    '''
    Identifier position
    Each position can have up to 6 different types of measurements

    Distance:
    x
    y
    z

    Angular:
    ry
    ry
    rz
    '''
    _parameters = ['x', 'y', 'z', 'rx', 'ry', 'rz']
    x = None
    y = None
    z = None
    rx = None
    ry = None
    rz = None

    def __init(self):
        # Set all the _parameters to None
        for param in self._parameters:
            setattr(self, param, None)

    def positionSet(self):
        '''
        Returns True if any position has been set
        '''
        for param in self._parameters:
            if getattr(self, param) is not None:
                return True
        return False

    def isPositionSet(self):
        '''
        Check if a position is set

        @return: True if any position is not None
        '''
        for param in self._parameters:
            value = getattr(self, param)
            if value is not None:
                return True

        return False

    def setPosition(self, positions):
        '''
        Applies given list of position measurements

        None signifies an undefined position which may be assigned at a later point.
        Otherwise, it will be set to 0 at a later stage

        If a position is already set, do not overwrite, expressions are read inside->out
        '''
        for position in positions:
            name = position[0]
            value = position[1]

            # Check to make sure parameter is valid
            if name not in self._parameters:
                print("{0} '{1}' is not a valid position parameter.".format(ERROR, name))
                continue

            # Only set if None
            if getattr(self, name) is None:
                setattr(self, name, value)

    def updatePositions(self, position):
        '''
        Using another Position object update positions
        All positions are overwritten, unless set to None in the new position set

        @param position: Position object with new positions
        '''
        for param in position._parameters:
            value = getattr(position, param)
            if value is not None:
                setattr(self, param, value)

    def strPosition(self):
        '''
        __repr__ of Position when multiple inheritance is used
        '''
        output = ""

        # Check each of the position parameters, only show the ones that are not None
        count = 0
        for param in self._parameters:
            value = getattr(self, param)
            if value is not None:
                if count > 0:
                    output += ","
                output += "{0}:{1}".format(param, value)
                count += 1

        return output

    def json(self):
        '''
        JSON representation of Position
        '''
        # TODO (HaaTa) Add
        return {}

    def __repr__(self):
        return self.strPosition()
