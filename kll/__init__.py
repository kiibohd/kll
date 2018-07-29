#!/usr/bin/env python3
'''
KLL Compiler
KLL - Keyboard Layout Language
'''

# Copyright (C) 2018 by Jacob Alexander
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

## Imports

import argparse
import os
import sys

import kll.common.stage as stage



## Variables

__version__ = '0.5.5.2'
kll_name = 'kll'



### Decorators ###

# Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'


# Python Text Formatting Fixer...
# Because the creators of Python are averse to proper capitalization.
textFormatter_lookup = {
    "usage: ": "\033[1mUsage\033[0m: ",
    "optional arguments": "\033[1mOptional Arguments\033[0m",
}


def textFormatter_gettext(s):
    return textFormatter_lookup.get(s, s)


argparse._ = textFormatter_gettext



### Misc Utility Functions ###

def git_revision(kllPath):
    '''
    Retrieve git information using given path

    @return: (revision, changed, revision_date)
    '''
    import subprocess

    # Change the path to where kll.py is
    origPath = os.getcwd()
    os.chdir(kllPath)

    # Just in case git can't be found
    try:
        # Get hash of the latest git commit
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode()[:-1]

        # Get list of files that have changed since the commit
        changed = subprocess.check_output(['git', 'diff-index', '--name-only', 'HEAD', '--']).decode().splitlines()

        # Get commit date
        date = subprocess.check_output(['git', 'show', '-s', '--format=%ci']).decode()[:-1]
    except BaseException:
        revision = "<no git>"
        changed = []
        date = "<no date>"

    # Change back to the old working directory
    os.chdir(origPath)

    return revision, changed, date


### Argument Parsing ###

def checkFileExists(filename):
    '''
    Validate that file exists

    @param filename: Path to file
    '''
    if not os.path.isfile(filename):
        print("{0} {1} does not exist...".format(ERROR, filename))
        sys.exit(1)


def command_line_args(control, input_args):
    '''
    Initialize argparse and process all command line arguments

    @param control: ControlStage object which has access to all the group argument parsers
    '''
    # Setup argument processor
    parser = argparse.ArgumentParser(
        usage="{} [options..] [<generic>..]".format(kll_name),
        description="KLL Compiler - Generates specified output from KLL .kll files.",
        epilog="Example: {0} scan_map.kll".format(kll_name),
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False,
    )

    # Get git information
    control.git_rev, control.git_changes, control.git_date = git_revision(
            os.path.dirname(os.path.realpath(__file__))
    )
    control.version = "{2}.{0} - {1}".format(control.git_rev, control.git_date, __version__)

    # Optional Arguments
    parser.add_argument(
        '-h', '--help',
        action="help",
        help="This message."
    )
    parser.add_argument(
        '-v', '--version',
        action="version",
        version="{0} {1}".format(kll_name, control.version),
        help="Show program's version number and exit"
    )
    parser.add_argument(
        '--path',
        action="store_true",
        help="Shows the absolute path to the kll compiler installation directory. Then exits.",
    )
    parser.add_argument(
        '--layout-cache-path',
        action="store_true",
        help="Shows the absolute path to the kll layouts cache director. Then exits.",
    )

    # Add stage arguments
    control.command_line_flags(parser)

    # Process Arguments
    args = parser.parse_args(input_args)

    # If --path defined, lookup installation path, then exit
    if args.path:
        install_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
        print(install_path)
        sys.exit(0)

    # If --layout-cache-path defined, lookup cache directory for layouts cache, then exit
    if args.layout_cache_path:
        import layouts
        mgr = layouts.Layouts()
        layout_path = mgr.layout_path
        print(layout_path)
        sys.exit(0)

    # Utilize parsed arguments in each of the stages
    control.command_line_args(args)


### Main Entry Point ###

def main(args):
    # Initialize Control Stages
    control = stage.ControlStage()

    # Process Command-Line Args
    command_line_args(control, args)

    # Process Control Stages
    control.process()

    # Successful completion
    sys.exit(0)


if __name__ == '__main__':
    main(sys.argv[1:])

