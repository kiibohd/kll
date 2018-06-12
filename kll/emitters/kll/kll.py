#!/usr/bin/env python3
'''
Re-Emits KLL files after processing. May do simplification.
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

import os

from kll.common.emitter import Emitter, FileEmitter



### Decorators ###

# Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'



### Classes ###

class KLL(Emitter, FileEmitter):
    '''
    Re-Emits KLL files, may simplify and re-order expressions.
    '''

    def __init__(self, control):
        '''
        Emitter initialization

        @param control: ControlStage object, used to access data from other stages
        '''
        Emitter.__init__(self, control)
        FileEmitter.__init__(self)

        # Defaults
        self.target_dir = "generated"
        self.output_debug = False
        self.kll_debug = False

    def command_line_args(self, args):
        '''
        Group parser for command line arguments

        @param args: Name space of processed arguments
        '''
        self.target_dir = args.target_dir
        self.output_debug = args.output_debug
        self.kll_debug = args.kll_debug

    def command_line_flags(self, parser):
        '''
        Group parser for command line options

        @param parser: argparse setup object
        '''
        # Create new option group
        group = parser.add_argument_group('\033[1mKLL Emitter Configuration\033[0m')

        group.add_argument('--target-dir', type=str, default=self.target_dir,
            help="Target directory for generated files.\n"
            "\033[1mDefault\033[0m: {0}\n".format(self.target_dir)
        )
        group.add_argument('--output-debug', action='store_true', default=self.output_debug,
            help="Enable kll reconstitution in-file debug output.\n",
        )
        group.add_argument(
            '--kll-debug',
            action='store_true',
            default=self.kll_debug,
            help="Show debug info from kll emitter.",
        )

    def output(self):
        '''
        Final Stage of Emitter

        Generate KLL files
        '''
        if self.kll_debug:
            print("-- Generating --")
            print(self.target_dir)

        # Make sure output directory exists
        os.makedirs(self.target_dir, exist_ok=True)

        # Output list of files to disk
        self.generate(self.target_dir)

    def reconstitute_elem(self, elem, key):
        '''
        Re-constitute single element
        May recurse if this is a list of elements

        @param elem:  Element to reconstitute
        @param key:   Identifier, used in debug output

        @return: Re-constituted string
        '''
        # If the element is a list, iterate through it
        if isinstance(elem, list):
            output = ""
            for index, subelem in enumerate(elem):
                output += self.reconstitute_elem(subelem, "{0}[{1}]".format(key, index))
            return output

        # NOTE: Useful line when debugging issues
        #print( type( elem ), elem )

        # Otherwise format each element
        if self.output_debug:
            return "{0} # {1} # {2}\n".format(elem.kllify(), elem.regen_str(), key)
        else:
            return "{0}\n".format(elem.kllify())

    def reconstitute_store(self, stores, name):
        '''
        Takes a list of organization stores and re-constitutes them into a kll file

        @param stores: List of organization stores
        @param name:   Filename to call list of stores

        @return: kll file contents
        '''
        output = ""

        for store in stores:
            # Show name of store
            section_name = type(store).__name__
            output += "# {0}\n".format(section_name)

            # NOTE: Useful for debugging
            #print( section_name )

            # Sort by output string, rather than by key
            for key, value in sorted(
                store.data.items(),
                key=lambda x: self.reconstitute_elem(x[1], x[0])
            ):
                output += self.reconstitute_elem(value, key)
            output += "\n"

        self.output_files.append((name, output))

    def process(self):
        '''
        Emitter Processing

        Takes KLL datastructures and Analysis results then outputs them individually as kll files
        '''
        # Acquire Datastructures
        early_contexts = self.control.stage('DataOrganizationStage').contexts
        base_context = self.control.stage('DataFinalizationStage').base_context
        default_context = self.control.stage('DataFinalizationStage').default_context
        partial_contexts = self.control.stage('DataFinalizationStage').partial_contexts
        full_context = self.control.stage('DataFinalizationStage').full_context

        # Re-constitute KLL files using contexts of various stages
        for key, context in early_contexts.items():
            self.reconstitute_store(context.organization.stores(), "{0}.kll".format(key))

        self.reconstitute_store(base_context.organization.stores(), "base.kll")

        self.reconstitute_store(default_context.organization.stores(), "default.kll")

        for index, partial in enumerate(partial_contexts):
            self.reconstitute_store(partial.organization.stores(), "partial-{0}.kll".format(index))

        self.reconstitute_store(full_context.organization.stores(), "final.kll")
