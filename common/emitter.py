#!/usr/bin/env python3
'''
KLL Emitter Base Classes
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

import json
import os
import re
import sys



### Decorators ###

# Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'



### Classes ###

class Emitter:
    '''
    KLL Emitter Base Class

    NOTE: Emitter should do as little as possible in the __init__ function.
    '''

    def __init__(self, control):
        '''
        Emitter initialization

        @param control: ControlStage object, used to access data from other stages
        '''
        self.control = control
        self.color = False

        # Signal erroring due to an issue
        # We may not want to exit immediately as we could find other potential
        # issues that need fixing
        self.error_exit = False

    def command_line_args(self, args):
        '''
        Group parser for command line arguments

        @param args: Name space of processed arguments
        '''
        print("{0} '{1}' '{2}' has not been implemented yet"
                .format(
                        WARNING,
                        self.command_line_args.__name__,
                        type(self).__name__
                )
        )

    def command_line_flags(self, parser):
        '''
        Group parser for command line options

        @param parser: argparse setup object
        '''
        print("{0} '{1}' '{2}' has not been implemented yet"
            .format(
                WARNING,
                self.command_line_flags.__name__,
                type(self).__name__
            )
        )

    def process(self):
        '''
        Emitter Processing
        '''
        print("{0} '{1}' '{2}' has not been implemented yet"
            .format(
                WARNING,
                self.process.__name__,
                type(self).__name__
            )
        )

    def output(self):
        '''
        Final Stage of Emitter

        Generate desired outputs
        '''
        print("{0} '{1}' '{2}' has not been implemented yet"
            .format(
                WARNING,
                self.output.__name__,
                type(self).__name__
            )
        )

    def check(self):
        '''
        Determines whether or not we've successfully emitted.
        '''
        return not self.error_exit


class FileEmitter:
    '''
    KLL File Emitter Class

    Base class for any emitter that wants to output a file.
    Generally, it is recommended to use the TextEmitter as templates are more readable.
    '''

    def __init__(self):
        '''
        FileEmitter Initialization
        '''
        self.output_files = []

    def generate(self, output_path):
        '''
        Generate output file

        @param contents: String contents of file
        @param output_path: Path to output file
        '''
        for name, contents in self.output_files:
            with open("{0}/{1}".format(output_path, name), 'w') as outputFile:
                outputFile.write(contents)


class TextEmitter:
    '''
    KLL Text Emitter Class

    Base class for any text emitter that wants to use the templating functionality

    If multiple files need to be generated, call load_template and generate multiple times.
    e.g.
    load_template('_myfile.h')
    generate('/tmp/myfile.h')

    load_template('_myfile2.h')
    generate('/tmp/myfile2.h')

    TODO
    - Generate list of unused tags
    '''

    def __init__(self):
        '''
        TextEmitter Initialization
        '''
        # Dictionary used to do template replacements
        self.fill_dict = {}
        self.tag_list = []

        self.template = None

    def load_template(self, template):
        '''
        Loads template file

        Looks for <|tags|> to replace in the template

        @param template: Path to template
        '''

        # Does template exist?
        if not os.path.isfile(template):
            print("{0} '{1}' does not exist...".format(ERROR, template))
            sys.exit(1)

        self.template = template

        # Generate list of fill tags
        with open(template, 'r') as openFile:
            for line in openFile:
                match = re.findall(r'<\|([^|>]+)\|>', line)
                for item in match:
                    self.tag_list.append(item)

    def generate(self, output_path):
        '''
        Generates the output file from the template file

        @param output_path: Path to the generated file
        '''
        # Make sure we've called load_template at least once
        if self.template is None:
            print(
                "{0} TextEmitter template (load_template) has not been called.".format(ERROR))
            sys.exit(1)

        # Process each line of the template, outputting to the target path
        with open(output_path, 'w') as outputFile:
            with open(self.template, 'r') as templateFile:
                for line in templateFile:
                    # TODO Support multiple replacements per line
                    # TODO Support replacement with other text inline
                    match = re.findall(r'<\|([^|>]+)\|>', line)

                    # If match, replace with processed variable
                    if match:
                        try:
                            outputFile.write(self.fill_dict[match[0]])
                        except KeyError as err:
                            print("{0} '{1}' not found, skipping...".format(
                                WARNING, match[0]
                            ))
                        outputFile.write("\n")

                    # Otherwise, just append template to output file
                    else:
                        outputFile.write(line)


class JsonEmitter:
    '''
    '''

    def __init__(self):
        '''
        JsonEmitter Initialization
        '''
        self.json_dict = {}

    def generate_json(self, output_path):
        '''
        Generates the output json file using an self.json_dict
        '''
        output = json.dumps(self.json_dict, indent=4, sort_keys=True)

        # Write json file
        with open(output_path, 'w') as outputFile:
            outputFile.write(output)
