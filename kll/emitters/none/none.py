#!/usr/bin/env python3
'''
KLL Data Dropper (Doesn't emit anything)
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

from kll.common.emitter import Emitter



### Decorators ###

# Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'



### Classes ###

class Drop(Emitter):
    '''
    Doesn't emit at all, just ignores everything
    '''

    def __init__(self, control):
        '''
        Emitter initialization

        @param control: ControlStage object, used to access data from other stages
        '''
        Emitter.__init__(self, control)

    def command_line_args(self, args):
        '''
        Group parser for command line arguments

        @param args: Name space of processed arguments
        '''

    def command_line_flags(self, parser):
        '''
        Group parser for command line options

        @param parser: argparse setup object
        '''

    def output(self):
        '''
        Final Stage of Emitter

        Nothing to do
        '''

    def process(self):
        '''
        Emitter Processing

        Nothing to do, just dropping all the results
        '''
