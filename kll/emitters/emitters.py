#!/usr/bin/env python3
'''
KLL Emitters Container Classes
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

import kll.emitters.kiibohd.kiibohd as kiibohd
import kll.emitters.kll.kll as kll
import kll.emitters.none.none as none



### Decorators ###

# Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'



### Classes ###

class Emitters:
    '''
    Container class for KLL emitters

    NOTES: To add a new emitter
    - Add a new directory for your emitter (e.g. kiibohd)
    - Add at least two files in this directory (<name>.py and __init__.py)
    - In <name>.py have one class that inherits the Emitter class from common.emitter
    - Add to list of emitters below
    - Add import statement to the top of this file
    - The control object allows access to the entire set of KLL datastructures
    '''

    def __init__(self, control):
        '''
        Emitter initialization

        @param control: ControlStage object, used to access data from other stages
        '''
        # Default emitter
        self.default = "kiibohd"

        # Dictionary of Emitters
        self.emitters = {
            'kiibohd': kiibohd.Kiibohd(control),
            'kll': kll.KLL(control),
            'none': none.Drop(control)
        }

    def emitter_default(self):
        '''
        Returns string name of default emitter
        '''
        return self.default

    def emitter_list(self):
        '''
        List of emitters available
        '''
        return list(self.emitters.keys())

    def emitter(self, emitter):
        '''
        Returns an emitter object
        '''
        return self.emitters[emitter]

    def command_line_args(self, args):
        '''
        Group parser fan-out for emitter command line arguments

        @param args: Name space of processed arguments
        '''
        # Always process command line args in the same order
        for key, emitter in sorted(self.emitters.items(), key=lambda x: x[0]):
            emitter.command_line_args(args)

    def command_line_flags(self, parser):
        '''
        Group parser fan-out for emitter for command line options

        @param parser: argparse setup object
        '''
        # Always process command line flags in the same order
        for key, emitter in sorted(self.emitters.items(), key=lambda x: x[0]):
            emitter.command_line_flags(parser)
