#!/usr/bin/env python3
'''
KLL File Container
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

import kll.common.context as context



### Decorators ###

# Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'



### Classes ###

class KLLFile:
    '''
    Container class for imported KLL files
    '''

    def __init__(self, path, file_context):
        '''
        Initialize file container

        @param path:    Path to filename, if relative, relative to the execution environment
        @param context: KLL Context object
        '''
        self.path = path
        self.context = file_context
        self.lines = []
        self.data = ""
        self.connect_id = None

        # Add filename to context for debugging
        self.context.kll_files.append(self.filename())

    def __repr__(self):
        context_str = type(self.context).__name__

        # Show layer info if this is a PartialMap
        if isinstance(self.context, context.PartialMapContext):
            context_str = "{0}({1})".format(context_str, self.context.layer)

        return "({}, {}, connect_id={})".format(
            self.path,
            context_str,
            self.connect_id
        )

    def check(self):
        '''
        Make sure that the file exists at the initialized path
        '''
        exists = os.path.isfile(self.path)

        # Display error message, will exit later
        if not exists:
            print("{0} {1} does not exist...".format(ERROR, self.path))

        return exists

    def filename(self):
        filename = str(os.path.basename(self.path))
        return filename

    def read(self):
        '''
        Read the contents of the file path into memory
        Reads both per line and complete copies
        '''
        try:
            # Read file into memory, removing newlines
            with open(self.path) as f:
                self.data = f.read()
                self.lines = self.data.splitlines()

        except BaseException:
            print(
                "{0} Failed to read '{1}' into memory...".format(
                    ERROR, self.path))
            return False

        return True

    def write(self, output_filename, debug=False):
        '''
        Writes the contents to a file
        This can be useful for dumping processed files to disk
        '''
        try:
            # Write the file to the specified file/folder
            if debug:
                print("Writing to {0}".format(output_filename))

            directory = os.path.dirname(output_filename)
            if not os.path.exists(directory):
                os.makedirs(directory)

            with open(output_filename, 'w') as f:
                f.write(self.data)

        except BaseException:
            print("{0} Failed to write to file '{1}'".format(ERROR, self.path))
            return False

        return True
