#!/usr/bin/env python3
'''
Emits internal KLL state to files for inspecting.
'''

# Copyright (C) 2019 by Rowan Decker
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

import json
import os
import sys
import traceback

from kll.common.emitter import Emitter



### Classes ###

class ClassEncoder(json.JSONEncoder):
    '''
    Turn's all self.___ class variables into a json object
    '''

    def default(self, o):
        # Avoid infinite nesting
        if type(o).__name__ in [
            "ThreadPool",
            "Emitters",
            "ControlStage",

            "ConfigurationContext",
            "BaseMapContext",
            "DefaultMapContext",
            "PartialMapContext",

            "MapExpression",
            "Organization",
        ]:
            return str(o)

        # Print all class variables
        result = dict()
        for key, value in o.__dict__.items():
            # Avoid circular reference
            if type(o).__name__ == "AnimationModifierArg" and key=="parent":
                value = str(value)

            # May be a bit large to look at
            #if key in ['organization', 'context', 'contexts']:
            #    continue

            result[key] = value
        return result

class State(Emitter):
    '''
    Write the state of every stage to a file
    '''

    def __init__(self, control):
        '''
        Emitter initialization

        @param control: ControlStage object, used to access data from other stages
        '''
        Emitter.__init__(self, control)

        self.output_dir = "state"

    def command_line_args(self, args):
        '''
        Group parser for command line arguments

        @param args: Name space of processed arguments
        '''

        self.output_dir = args.state_output

    def command_line_flags(self, parser):
        '''
        Group parser for command line options

        @param parser: argparse setup object
        '''

        # Create new option group
        group = parser.add_argument_group('\033[1mInternal State Emitter Configuration\033[0m')

        group.add_argument('--state-output', type=str, default=self.output_dir,
            help="Specify internal state output directory.\n"
            "\033[1mDefault\033[0m: {0}\n".format(self.output_dir)
        )

    def output(self):
        '''
        Final Stage of Emitter

        Nothing to do
        '''

        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)
        for stage in self.control.stages:
            stage_name = type(stage).__name__
            stage_dir = os.path.join(self.output_dir, stage_name)
            if not os.path.exists(stage_dir):
                os.mkdir(stage_dir)

            for key, value in stage.__dict__.items():
                # May not be interesting
                #if key in ['color', 'control', '_status']:
                #    continue
                with open(os.path.join(stage_dir, key+".json"), 'w') as f:
                    json.dump({key: value}, f, indent=4, cls=ClassEncoder)

    def process(self):
        '''
        Emitter Processing

        Get output path
        '''

        processed_save_path = self.control.stage('PreprocessorStage').processed_save_path
        if not self.output_dir:
            self.output_dir = os.path.join(processed_save_path, "state") # Usually in /tmp
