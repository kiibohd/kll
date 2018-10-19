#!/usr/bin/env python3
'''
KLL Compiler Stage Definitions
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

from multiprocessing.dummy import Pool as ThreadPool

import copy
import io
import multiprocessing
import os
import re
import sys
import tempfile

import kll.common.context as context
import kll.common.expression as expression
import kll.common.file as file
import kll.common.id as id

import kll.emitters.emitters as emitters

from kll.extern.funcparserlib.lexer import make_tokenizer, Token, LexerError
from kll.extern.funcparserlib.parser import many, oneplus, maybe, skip, NoParseError, Parser_debug

from layouts import Layouts, Layout


### Decorators ###

# Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'

ansi_escape = re.compile(r'\x1b[^m]*m')


### Classes ###

class ControlStage:
    '''
    Top-level Stage

    Controls the order in which each stage is processed
    '''

    def __init__(self):
        '''
        Initialize stage objects and control variables
        '''

        # Initialized in process order
        # NOTE: Only unique classes in this list, otherwise stage() will get confused
        self.stages = [
            CompilerConfigurationStage(self),
            FileImportStage(self),
            PreprocessorStage(self),
            OperationClassificationStage(self),
            OperationSpecificsStage(self),
            OperationOrganizationStage(self),
            DataOrganizationStage(self),
            DataFinalizationStage(self),
            DataAnalysisStage(self),
            CodeGenerationStage(self),
            #ReportGenerationStage( self ),
        ]

        self.git_rev = None
        self.git_changes = None
        self.version = None

    def stage(self, context_str):
        '''
        Returns the stage object of the associated string name of the class

        @param context_str: String name of the class of the stage e.g. CompilerConfigurationStage
        '''
        return [stage for stage in self.stages if type(stage).__name__ is context_str][0]

    def command_line_args(self, args):
        '''
        Capture commmand line arguments for each processing stage

        @param args: Name space of processed arguments
        '''
        for stage in self.stages:
            stage.command_line_args(args)

    def command_line_flags(self, parser):
        '''
        Prepare group parser for each processing stage

        @param parser: argparse setup object
        '''
        for stage in self.stages:
            stage.command_line_flags(parser)

    def process(self):
        '''
        Main processing section
        Initializes each stage in order.
        Each stage must complete before the next one begins.
        '''
        # Run report even if stage doesn't complete
        run_report = False

        for stage in self.stages:
            stage.process()

            # Make sure stage has successfully completed
            if stage.status() != 'Completed':
                print("{0} Invalid stage status '{1}' for '{2}'.".format(
                    ERROR,
                    stage.status(),
                    stage.__class__.__name__,
                ))
                run_report = True
                break

        # Only need to explicitly run reports if there was a stage problem
        # Otherwise reports are run automatically
        if run_report:
            # TODO
            sys.exit(1)


class Stage:
    '''
    Base Stage Class
    '''

    def __init__(self, control):
        '''
        Stage initialization

        @param control: ControlStage object, used to access data from other stages
        '''
        self.control = control
        self.color = False
        self._status = 'Queued'

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
        Main procesing section
        '''
        self._status = 'Running'

        print("{0} '{1}' '{2}' has not been implemented yet"
            .format(
                WARNING,
                self.process.__name__,
                type(self).__name__
            )
        )

        self._status = 'Completed'

    def status(self):
        '''
        Returns the current status of the Stage

        Values:
        Queued     - Not yet run
        Running    - Currently running
        Completed  - Successfully completed
        Incomplete - Unsuccessfully completed
        '''
        return self._status


class CompilerConfigurationStage(Stage):
    '''
    Compiler Configuration Stage

    * Does initial setup of KLL compiler.
    * Handles any global configuration that must be done before parsing can begin
    '''

    def __init__(self, control):
        '''
        Initialize compiler configuration variables
        '''
        super().__init__(control)

        self.color = "auto"
        self.jobs = multiprocessing.cpu_count()
        self.pool = None

        # Build list of emitters
        self.emitters = emitters.Emitters(control)
        self.emitter = self.emitters.emitter_default()

    def command_line_args(self, args):
        '''
        Group parser for command line arguments

        @param args: Name space of processed arguments
        '''
        self.emitter = args.emitter
        self.color = args.color
        self.jobs = args.jobs

        # Validate color argument before processing
        if self.color not in ['auto', 'always', 'never']:
            print("Invalid color option '{0}'".format(self.color))
            sys.exit(2)

        # TODO Detect whether colorization should be used
        self.color = self.color in ['auto', 'always']

        # Validate if it's a valid emitter
        if self.emitter not in self.emitters.emitter_list():
            print("{0} Invalid emitter '{1}'".format(ERROR, self.emitter))
            print("Valid emitters: {0}".format(self.emitters.emitter_list()))
            sys.exit(2)

    def command_line_flags(self, parser):
        '''
        Group parser for command line options

        @param parser: argparse setup object
        '''
        # Create new option group
        group = parser.add_argument_group('\033[1mCompiler Configuration\033[0m')

        # Optional Arguments
        group.add_argument('--emitter', type=str, default=self.emitter,
            help="Specify target emitter for the KLL compiler.\n"
            "\033[1mDefault\033[0m: {0}\n"
            "\033[1mOptions\033[0m: {1}".format(self.emitter, self.emitters.emitter_list())
        )
        group.add_argument('--color', type=str, default=self.color,
            help="Specify debug colorizer mode.\n"
            "\033[1mDefault\033[0m: {0}\n"
            "\033[1mOptions\033[0m: auto, always, never (auto attempts to detect support)".format(self.color)
        )
        group.add_argument('--jobs', type=int, default=self.jobs,
            help="Specify max number of threads to use.\n"
            "\033[1mDefault\033[0m: {0}".format(self.jobs)
        )

    def process(self):
        '''
        Compiler Configuration Processing
        '''
        self._status = 'Running'

        # Initialize thread pool
        self.pool = ThreadPool(self.jobs)

        self._status = 'Completed'


class FileImportStage(Stage):
    '''
    FIle Import Stage

    * Loads text of all files into memory
    * Does initial sorting of KLL Contexts based upon command line arguments
    '''

    def __init__(self, control):
        '''
        Initialize file storage datastructures and variables
        '''
        super().__init__(control)

        # These lists are order sensitive
        self.generic_files = []
        self.config_files = []
        self.base_files = []
        self.default_files = []

        # This is a list of lists, each sub list is another layer in order from 1 to max
        self.partial_files = []

        # List of all files contained in KLLFile objects
        self.kll_files = []

    def command_line_args(self, args):
        '''
        Group parser for command line arguments

        @param args: Name space of processed arguments
        '''
        self.generic_files = args.generic
        self.config_files = args.config
        self.base_files = args.base
        self.default_files = args.default
        self.partial_files = args.partial

    def command_line_flags(self, parser):
        '''
        Group parser for command line options

        @param parser: argparse setup object
        '''
        # Create new option group
        group = parser.add_argument_group('\033[1mFile Context Configuration\033[0m')

        # Positional Arguments
        group.add_argument('generic', type=str, nargs='*', default=self.generic_files,
            help="Auto-detect context of .kll files, defaults to a base map configuration."
        )

        # Optional Arguments
        group.add_argument('--config', type=str, nargs='+', default=self.config_files,
            help="Specify base configuration .kll files, earliest priority"
        )
        group.add_argument('--base', type=str, nargs='+', default=self.base_files,
            help="Specify base map configuration, applied after config .kll files.\n"
            "The base map is applied prior to all default and partial maps and is used as the basis for them."
        )
        group.add_argument('--default', type=str, nargs='+', default=self.default_files,
            help="Specify .kll files to layer on top of the default map to create a combined map.\n"
            "Also known as layer 0."
        )
        group.add_argument('--partial', type=str, nargs='+', action='append', default=self.partial_files,
            help="Specify .kll files to generate partial map, multiple files per flag.\n"
            "Each -p defines another partial map.\n"
            "Base .kll files (that define the scan code maps) must be defined for each partial map."
        )

    def init_kllfile(self, path, file_context):
        '''
        Prepares a KLLFile object with the given context

        @path:         Path to the KLL file
        @file_context: Type of file context, e.g. DefaultMapContext
        '''
        return file.KLLFile(path, file_context)

    def process(self):
        '''
        Process each of the files, sorting them by command line argument context order
        '''
        self._status = 'Running'

        # Determine colorization setting
        self.color = self.control.stage('CompilerConfigurationStage').color

        # Process each type of file
        # Iterates over each file in the context list and creates a KLLFile object with a context and path
        self.kll_files += map(
            lambda path: self.init_kllfile(path, context.GenericContext()),
            self.generic_files
        )
        self.kll_files += map(
            lambda path: self.init_kllfile(path, context.ConfigurationContext()),
            self.config_files
        )
        self.kll_files += map(
            lambda path: self.init_kllfile(path, context.BaseMapContext()),
            self.base_files
        )
        self.kll_files += map(
            lambda path: self.init_kllfile(path, context.DefaultMapContext()),
            self.default_files
        )

        # Partial Maps require a third parameter which specifies which layer it's in
        for layer, files in enumerate(self.partial_files):
            self.kll_files += map(
                lambda path: self.init_kllfile(path, context.PartialMapContext(layer)),
                files
            )

        # Validate that all the file paths exist, exit if any of the checks fail
        if False in [path.check() for path in self.kll_files]:
            self._status = 'Incomplete'
            return

        # Now that we have a full list of files and their given context, we can now read the files into memory
        # Uses the thread pool to speed up processing
        # Make sure processing was successful before continuing
        pool = self.control.stage('CompilerConfigurationStage').pool
        if False in pool.map(lambda kll_file: kll_file.read(), self.kll_files):
            self._status = 'Incomplete'
            return

        self._status = 'Completed'


class PreprocessorStage(Stage):
    '''
    Preprocessor Stage

    * Does initial split and decision of contexts
    * Handles Preprocessor part of KLL
    '''

    def __init__(self, control):
        '''
        Initialize preprocessor configuration variables
        '''
        super().__init__(control)

        self.preprocessor_debug = False

        self.max_scan_code = [0]
        self.min_scan_code = [0]
        self.interconnect_scancode_offsets = [0]

        self.kll_files = []

        self.layout_mgr = None
        self.layout_list = []

        self.processed_save_path = "{temp}/kll".format(temp=tempfile.gettempdir())

    def command_line_args(self, args):
        '''
        Group parser for command line arguments

        @param args: Name space of processed arguments
        '''
        self.preprocessor_debug = args.preprocessor_debug
        self.processed_save_path = args.preprocessor_tmp_path

    def command_line_flags(self, parser):
        '''
        Group parser for command line options

        @param parser: argparse setup object
        '''
        # Create new option group
        group = parser.add_argument_group('\033[1mPreprocessor Configuration\033[0m')

        # Optional Arguments
        group.add_argument('--preprocessor-tmp-path', type=str, default=self.processed_save_path,
            help="Work directory for preprocessor.\n"
            "\033[1mDefault\033[0m: {0}\n".format(self.processed_save_path)
        )
        group.add_argument('--preprocessor-debug', action='store_true', default=self.preprocessor_debug,
            help="Enable debug output in the preprocessor."
        )

    def seed_context(self, kll_file):
        '''
        Build list of context

        TODO Update later for proper preprocessor
        Adds data from KLLFile into the Context
        '''
        kll_file.context.initial_context(kll_file.lines, kll_file.data, kll_file)

    def apply_connect_ids(self):
        '''
        Uses computed connect_ids to apply to BaseMaps
        Incoming order of the KLLFiles matters

        Ignores other contexts
        '''
        current_id = 0
        for kll_file in self.kll_files:
            # Only applicable for BaseMapContext
            if kll_file.context.__class__.__name__ == "BaseMapContext":
                # Only update the current_id if it was set (not every file will have it set)
                if kll_file.connect_id is not None:
                    current_id = kll_file.connect_id

                kll_file.context.connect_id = current_id

            # Otherwise, set as 0
            else:
                kll_file.context.connect_id = 0

    def process_connect_ids(self, kll_file, apply_offsets):
        lines = kll_file.data.splitlines()

        # Basic Tokens Spec
        # TODO Storing these somewhere central might be a reasonable idea
        spec = [
            ('Comment', (r' *#.*', )),
            ('ScanCode', (r'S((0x[0-9a-fA-F]+)|([0-9]+))', )),
            ('Operator', (r'=>|<=|i:\+|i:-|i::|i:|:\+|:-|::|:|=', )),
            ('USBCode', (r'U(("[^"]+")|(0x[0-9a-fA-F]+)|([0-9]+))', )),
            ('NumberBase10', (r'(([1-9][0-9]*))', )),
            ('Number', (r'-?((0x[0-9a-fA-F]+)|(0|([1-9][0-9]*)))', )),
            ('Name', (r'[A-Za-z_][A-Za-z_0-9]*', )),
            ('Misc', (r'.', )),  # Everything else
        ]

        # Tokens to filter out of the token stream
        useless = ['Misc']

        # Build tokenizer that appends unknown characters to Misc Token groups
        # NOTE: This is technically slower processing wise, but allows for multi-stage tokenization
        # Which in turn allows for parsing and tokenization rules to be simplified
        tokenizer = make_tokenizer(spec)

        # default Locale when un-defined
        hid_mapping_name = 'default'

        try:
            most_recent_offset = 0
            processed_lines = []
            for line in lines:
                tokens = [x for x in tokenizer(line) if x.type not in useless]

                for l_element, mid_element, r_element in zip(tokens[0::3], tokens[1::3], tokens[2::3]):
                    # Look for HIDMapping variable
                    # If set, apply to context
                    # Also verify that the HIDMapping is valid
                    if (
                        l_element.value == "HIDMapping"
                            and
                        mid_element.value == "="
                    ):
                        # Make sure this is a valid mapping
                        assert r_element.value in self.layout_list

                        # Set HID mapping for KLL Context
                        hid_mapping_name = r_element.value

                    # Preprocessor tag for offsetting the scancodes by a fixed amount
                    # This makes it eay to apply offsets to older files
                    # The scope for this term is for the current file
                    if (
                        l_element.value == "ScanCodeOffset"
                            and
                        mid_element.value == "="
                            and
                        r_element.type == "NumberBase10"
                    ):
                        most_recent_offset = int(r_element.value)

                    # Preprocessor definition for the connectId
                    # TODO these should likely be defined in their own file somewhere else
                    if (
                        l_element.value == "ConnectId"
                            and
                        mid_element.value == "="
                            and
                        r_element.type == "NumberBase10"
                    ):
                        self.most_recent_connect_id = int(r_element.value)
                        assert (self.most_recent_connect_id >= 0)

                        if self.preprocessor_debug:
                            print("Found connect ID! %s" % self.most_recent_connect_id)

                        if not apply_offsets:
                            # Set connect_id
                            kll_file.connect_id = self.most_recent_connect_id

                            # Making sure that the offsets exist
                            while (len(self.min_scan_code) <= self.most_recent_connect_id):
                                self.min_scan_code.append(sys.maxsize)

                            while (len(self.max_scan_code) <= self.most_recent_connect_id):
                                self.max_scan_code.append(0)

                        if apply_offsets:
                            assert (len(self.min_scan_code) > self.most_recent_connect_id)
                            assert (len(self.max_scan_code) > self.most_recent_connect_id)
                            assert (len(self.interconnect_scancode_offsets) > self.most_recent_connect_id)

                    if (
                        l_element.type == "ScanCode"
                            and
                        mid_element.value == ":"
                            and
                        r_element.type == "USBCode"
                    ):
                        scan_code_int = int(l_element.value[1:], 0)

                        if not apply_offsets:
                            # Checking if the min/max values need to be updated. The values are guaranteed to exist
                            # in the previous step
                            if scan_code_int < self.min_scan_code[self.most_recent_connect_id]:
                                self.min_scan_code[self.most_recent_connect_id] = scan_code_int
                            if scan_code_int > self.max_scan_code[self.most_recent_connect_id]:
                                self.max_scan_code[self.most_recent_connect_id] = scan_code_int


                        if apply_offsets:
                            # Modifying the current line
                            # The result is determined by the scancode, the interconnect offset and the preprocess
                            # term for offset
                            scan_code_with_offset = (
                                scan_code_int +
                                self.interconnect_scancode_offsets[self.most_recent_connect_id] +
                                most_recent_offset
                            )

                            scan_code_with_offset_hex = "0x{:X}".format(scan_code_with_offset)
                            original_scancode_converted_hex = "0x{:X}".format(scan_code_int)

                            # Sanity checking if we are doing something wrong
                            if int(original_scancode_converted_hex, 16) != int(l_element.value[1:], 0):
                                print(
                                    "{type} We might be converting the scancodes wrong."
                                    " Original code: {original}, the converted code"
                                    " {converted}".format(
                                        type=ERROR,
                                        original=l_element.value[1:],
                                        converted=original_scancode_converted_hex
                                    )
                                )

                            # Replacing the original scancode in the line
                            old_line = str(line)
                            line = line.replace(r_element.value[1:], scan_code_with_offset_hex)
                            if self.preprocessor_debug:
                                print("Applying offset {}".format(
                                    self.interconnect_scancode_offsets[self.most_recent_connect_id]
                                ))
                                print(
                                    "Old line: {old_line}\n"
                                    "Replacing {old_element} with"
                                    "{new_element}".format(
                                        old_line=old_line,
                                        old_element=l_element.value[1:],
                                        new_element=scan_code_with_offset_hex
                                    )
                                )
                                print("New line: {}\n".format(line))

                processed_lines.append(line)

        except LexerError as err:
            print(err)
            print("{0} {1}:tokenize -> {2}:{3}".format(
                ERROR,
                self.__class__.__name__,
                kll_file.path,
                err.place[0],
            ))

        # Set HID Mapping in context
        kll_file.context.hid_mapping = self.layout_mgr.get_layout(hid_mapping_name)

        # Applying the offsets to the kll objets, if appropriate
        if apply_offsets:
            new_data = os.linesep.join(processed_lines)

            kll_file.data = new_data
            kll_file.lines = processed_lines

    def determine_scancode_offsets(self):
        # Sanity check the min/max codes
        assert (len(self.min_scan_code) is len(self.max_scan_code))

        # Doing the actual work
        self.interconnect_scancode_offsets = []
        previous_max_offset = 0
        for scancode_offset_for_id in self.max_scan_code:
            self.interconnect_scancode_offsets.append(previous_max_offset)
            previous_max_offset += scancode_offset_for_id
        self.interconnect_scancode_offsets.append(previous_max_offset)

        if self.preprocessor_debug:
            print("Scancode offsets: {0}".format(self.interconnect_scancode_offsets))

    def import_data_from_disk(self, kll_files):
        for kll_file in kll_files:
            kll_file.read()

    def export_data_to_disk(self, kll_files):
        paths = []
        for kll_file in kll_files:
            paths.append(kll_file.path)

        common_path = os.path.commonprefix(paths)

        for kll_file in kll_files:
            # Outputting the file to disk, with a different filename
            file_prefix = os.path.dirname(kll_file.path)
            file_prefix = file_prefix.replace(common_path, "")
            file_prefix = file_prefix.replace("\\", "_")
            file_prefix = file_prefix.replace("/", "_")

            base_filename = kll_file.filename()

            # Handle multiple dots across multiple versions of Python 3
            splits = base_filename.split(".")
            extension = splits[-1]
            filename = splits[0:-1]

            processed_filename = "{prefix}@{filename}_processed.{extension}".format(
                prefix=file_prefix,
                filename=filename,
                extension=extension
            )

            if self.preprocessor_debug:
                print("Processed filename: %s" % processed_filename)

            output_filename = '{processed_dir}/{filename}'.format(
                processed_dir=self.processed_save_path,
                filename=processed_filename
            )
            kll_file.write(output_filename, self.preprocessor_debug)
            kll_file.path = output_filename

    def gather_scancode_offsets(self, kll_files):
        self.most_recent_connect_id = 0
        for kll_file in kll_files:
            self.process_connect_ids(kll_file, apply_offsets=False)

    def apply_scancode_offsets(self, kll_files):
        self.most_recent_connect_id = 0
        for kll_file in kll_files:
            self.process_connect_ids(kll_file, apply_offsets=True)

    def process(self):
        '''
        Preprocessor Execution
        '''
        self._status = 'Running'

        # Determine colorization setting
        self.color = self.control.stage('CompilerConfigurationStage').color

        # Acquire thread pool
        pool = self.control.stage('CompilerConfigurationStage').pool

        # Build list of layouts
        #self.layout_mgr = Layouts(layout_path='/home/hyatt/Source/layouts')
        self.layout_mgr = Layouts()
        self.layout_list = self.layout_mgr.list_layouts()

        # TODO
        # Once the KLL Spec has preprocessor commands, there may be a risk of infinite/circular dependencies
        # Please add a non-invasive way to avoid/warn/stop in this case -HaaTa

        # First, since initial contexts have been populated, populate details
        # TODO
        # This step will change once preprocessor commands have been added

        # Simply, this just takes the imported file data (KLLFile) and puts it in the context container
        self.kll_files = self.control.stage('FileImportStage').kll_files

        self.import_data_from_disk(self.kll_files)
        self.gather_scancode_offsets(self.kll_files)
        self.determine_scancode_offsets()
        #self.apply_scancode_offsets(self.kll_files) # XXX (HaaTa) not necessary anymore
        self.export_data_to_disk(self.kll_files)

        if False in pool.map(self.seed_context, self.kll_files):
            self._status = 'Incomplete'
            return

        # Apply connect ids
        self.apply_connect_ids()

        # Next, tokenize and parser the preprocessor KLL commands.
        # NOTE: This may result in having to create more KLL Contexts and tokenize/parse again numerous times over
        # TODO
        if self.preprocessor_debug:
            print("Preprocessor determined Min ScanCodes: {0}".format(self.min_scan_code))
            print("Preprocessor determined Max ScanCodes: {0}".format(self.max_scan_code))
            print("Preprocessor determined ScanCode offsets: {0}".format(self.interconnect_scancode_offsets))
        self._status = 'Completed'


class OperationClassificationStage(Stage):
    '''
    Operation Classification Stage

    * Sorts operations by type based on operator
    * Tokenizes only operator pivots and left/right arguments
    * Further tokenization and parsing occurs at a later stage
    '''

    def __init__(self, control):
        '''
        Initialize operation classification stage
        '''
        super().__init__(control)

        self.tokenized_data = []
        self.contexts = []

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
        # Create new option group
        group = parser.add_argument_group('\033[1mOperation Classification Configuration\033[0m')

    def merge_tokens(self, token_list, token_type):
        '''
        Merge list of tokens into a single token

        @param token_list: List of tokens
        @param token_type: String name of token type
        '''
        # Initial token parameters
        ret_token = Token(token_type, '')

        # Set start/end positions of token
        ret_token.start = token_list[0].start
        ret_token.end = token_list[-1].end

        # Build token value
        for token in token_list:
            ret_token.value += token.value

        return ret_token

    def tokenize(self, kll_context):
        '''
        Tokenize a single string

        @param kll_context: KLL Context containing file data
        '''
        ret = True

        # Basic Tokens Spec
        spec = [
            ('Comment', (r' *#.*', )),
            ('Space', (r'[ \t]+', )),
            ('NewLine', (r'[\r\n]+', )),

            # Tokens that will be grouped together after tokenization
            # Ignored at this stage
            # This is required to isolate the Operator tags
            ('Misc', (r'r?[xyz]:[0-9]+(.[0-9]+)?', )),  # Position context
            ('Misc', (r'\([^\)]*\)', )),  # Parenthesis context
            ('Misc', (r'\[[^\]]*\]', )),  # Square bracket context
            ('Misc', (r'"[^"]*"', )),    # Double quote context
            ('Misc', (r"'[^']*'", )),    # Single quote context

            ('Operator', (r'=>|<=|i:\+|i:-|i::|i:|:\+|:-|::|:|=', )),
            ('EndOfLine', (r';', )),

            # Everything else to be ignored at this stage
            ('Misc', (r'.', )),          # Everything else
        ]

        # Tokens to filter out of the token stream
        #useless = [ 'Space', 'Comment' ]
        useless = ['Comment', 'NewLine']

        # Build tokenizer that appends unknown characters to Misc Token groups
        # NOTE: This is technically slower processing wise, but allows for multi-stage tokenization
        #       Which in turn allows for parsing and tokenization rules to be simplified
        tokenizer = make_tokenizer(spec)

        # Tokenize and filter out useless tokens
        try:
            tokens = [x for x in tokenizer(kll_context.data) if x.type not in useless]
        except LexerError as err:
            print(err)
            print("{0} {1}:tokenize -> {2}:{3}".format(
                ERROR,
                self.__class__.__name__,
                kll_context.parent.path,
                err.place[0],
            ))

        # Merge Misc tokens delimited by Operator and EndOfLine tokens
        kll_context.classification_token_data = []
        new_token = []
        last_operator = None
        for token in tokens:
            # Check for delimiter, append new_token if ready
            if token.type in ['EndOfLine', 'Operator']:
                # Determine the token type
                token_type = 'LOperatorData'
                if token.type == 'EndOfLine':
                    token_type = 'ROperatorData'

                # If this is a 'misplaced' operator, set as Misc
                if token_type == last_operator:
                    token.type = 'Misc'
                    new_token.append(token)
                    continue

                if len(new_token) > 0:
                    # Build new token
                    kll_context.classification_token_data.append(
                            self.merge_tokens(new_token, token_type)
                    )
                    new_token = []
                kll_context.classification_token_data.append(token)
                last_operator = token_type

            # Collect Misc tokens
            elif token.type in ['Misc', 'Space']:
                new_token.append(token)

            # Invalid token for this stage
            else:
                print("{0} Invalid token '{1}' for '{2}'".format(
                    ERROR,
                    token,
                    type(self).__name__,
                ))
                ret = False

        return ret

    def sort(self, kll_context):
        '''
        Sorts tokenized data into expressions
        LOperatorData + Operator + ROperatorData + EndOfLine

        @param kll_context: KLL Context, contains tokenized data
        '''
        ret = True

        def validate_token(token, token_type):
            '''
            Validate token

            @param token: Given token to validate
            @param token_type: Token type to validate against

            @return True if the token is correct
            '''
            ret = token.type == token_type

            # Error message
            if not ret:
                print("Expected: '{0}' got '{1}':{2} '{3}'".format(
                    token_type,
                    token.type,
                    token._pos_str(),
                    token.value,
                ))

            return ret

        tokens = kll_context.classification_token_data
        for index in range(0, len(tokens), 4):
            # Make sure enough tokens exist
            if index + 3 >= len(tokens):
                print("Not enough tokens left: {0}".format(tokens[index:]))
                print("Expected: LOperatorData, Operator, ROperatorData, EndOfLine")
                print("{0} {1}:sort -> {2}:{3}".format(
                    ERROR,
                    self.__class__.__name__,
                    kll_context.parent.path,
                    tokens[-1].start[0],
                ))
                ret = False
                break

            # Validate the tokens are what was expected
            ret = validate_token(tokens[index], 'LOperatorData') and ret
            ret = validate_token(tokens[index + 1], 'Operator') and ret
            ret = validate_token(tokens[index + 2], 'ROperatorData') and ret
            ret = validate_token(tokens[index + 3], 'EndOfLine') and ret

            # Append expression
            kll_context.expressions.append(
                expression.Expression(tokens[index], tokens[index + 1], tokens[index + 2], kll_context)
            )

        return ret

    def process(self):
        '''
        Compiler Configuration Processing
        '''
        self._status = 'Running'

        # Determine colorization setting
        self.color = self.control.stage('CompilerConfigurationStage').color

        # Acquire thread pool
        pool = self.control.stage('CompilerConfigurationStage').pool

        # Get list of KLLFiles
        kll_files = self.control.stage('FileImportStage').kll_files

        # Build list of contexts
        self.contexts = [kll_file.context for kll_file in kll_files]

        # Tokenize operators
        # TODO
        #      Once preprocessor includes are implemented use a second kll_files list
        #      This way processing doesn't have to be recursive for a few stages -HaaTa
        if False in pool.map(self.tokenize, self.contexts):
            self._status = 'Incomplete'
            return

        # Sort elements into expressions
        # LOperatorData + Operator + ROperatorData + EndOfLine
        if False in pool.map(self.sort, self.contexts):
            self._status = 'Incomplete'
            return

        self._status = 'Completed'


class OperationSpecificsStage(Stage):
    '''
    Operation Specifics Stage

    * For each sorted operation, tokenize and parse the left/right arguments
    * Data is stored with the operation, but no context is given to the data beyond the argument types
    '''

    def __init__(self, control):
        '''
        Initialize operation specifics stage
        '''
        super().__init__(control)

        self.parser_debug = False
        self.parser_token_debug = False
        self.token_debug = False

    def command_line_args(self, args):
        '''
        Group parser for command line arguments

        @param args: Name space of processed arguments
        '''
        self.parser_debug = args.parser_debug
        self.parser_token_debug = args.parser_token_debug
        self.token_debug = args.token_debug

        # Auto-set parser_debug if parser_token_debug is set
        if self.parser_token_debug:
            self.parser_debug = True

    def command_line_flags(self, parser):
        '''
        Group parser for command line options

        @param parser: argparse setup object
        '''
        # Create new option group
        group = parser.add_argument_group('\033[1mOperation Specifics Configuration\033[0m')

        # Optional Arguments
        group.add_argument('--parser-debug', action='store_true', default=self.parser_debug,
            help="Enable parser debug output.\n",
        )
        group.add_argument('--parser-token-debug', action='store_true', default=self.parser_token_debug,
            help="Enable parser-stage token debug output.\n",
        )
        group.add_argument('--token-debug', action='store_true', default=self.token_debug,
            help="Enable tokenization debug output.\n",
        )

    ## Tokenizers ##
    def tokenize_base(self, kll_expression, lspec, rspec):
        '''
        Base tokenization logic for this stage

        @param kll_expression: KLL expression to tokenize
        @param lspec: Regex tokenization spec for the left parameter
        @param rspec: Regex tokenization spec for the right parameter

        @return False if a LexerError was detected
        '''
        # Build tokenizers for lparam and rparam
        ltokenizer = make_tokenizer(lspec)
        rtokenizer = make_tokenizer(rspec)

        # Tokenize lparam and rparam
        # Ignore the generators, not useful in this case (i.e. use list())
        err_pos = []  # Error positions
        try:
            kll_expression.lparam_sub_tokens = list(ltokenizer(kll_expression.lparam_token.value))
            for token in kll_expression.lparam_sub_tokens:
                token.locale = kll_expression.context.hid_mapping
        except LexerError as err:
            # Determine place in constructed expression
            err_pos.append(err.place[1])
            print(type(err).__name__, err)

        try:
            kll_expression.rparam_sub_tokens = list(rtokenizer(kll_expression.rparam_token.value))
            for token in kll_expression.rparam_sub_tokens:
                token.locale = kll_expression.context.hid_mapping
        except LexerError as err:
            # Determine place in constructed expression
            err_pos.append(err.place[1] + kll_expression.rparam_start())
            print(type(err).__name__, err)

        # Display more information if any errors were detected
        if len(err_pos) > 0:
            print(kll_expression.point_chars(err_pos))
            return False

        return True

    def tokenize_name_association(self, kll_expression):
        '''
        Tokenize lparam and rparam in name association expressions
        <lparam> => <rparam>;
        '''

        # Define tokenization regex
        lspec = [
            ('Name', (r'[A-Za-z_][A-Za-z_0-9]*', )),
            ('Space', (r'[ \t]+', )),
        ]

        rspec = [
            ('Space', (r'[ \t]+', )),
            ('Parenthesis', (r'\(|\)', )),
            ('Operator', (r':', )),
            ('Comma', (r',', )),
            ('Name', (r'[A-Za-z_][A-Za-z_0-9]*', )),
            ('Number', (r'-?((0x[0-9a-fA-F]+)|(0|([1-9][0-9]*)))', )),
        ]

        # Tokenize, expression stores the result, status is returned
        return self.tokenize_base(kll_expression, lspec, rspec)

    def tokenize_data_association(self, kll_expression):
        '''
        Tokenize lparam and rparam in data association expressions
        <lparam> <= <rparam>;
        '''

        # Define tokenization regex
        lspec = [
            ('Space', (r'[ \t]+', )),

            ('ScanCode', (r'S((0x[0-9a-fA-F]+)|([0-9]+))', )),
            ('ScanCodeStart', (r'S\[', )),
            ('Pixel', (r'P((0x[0-9a-fA-F]+)|([0-9]+))', )),
            ('PixelStart', (r'P\[', )),
            ('Animation', (r'A"[^"]+"', )),
            ('AnimationStart', (r'A\[', )),
            ('CodeBegin', (r'\[', )),
            ('CodeEnd', (r'\]', )),
            ('Position', (r'r?[xyz]:-?[0-9]+(.[0-9]+)?', )),

            ('Comma', (r',', )),
            ('Number', (r'(0x[0-9a-fA-F]+)|(0|([1-9][0-9]*))', )),
            ('Dash', (r'-', )),
            ('Name', (r'[A-Za-z_][A-Za-z_0-9]*', )),
        ]

        rspec = [
            ('Space', (r'[ \t]+', )),

            ('Pixel', (r'P((0x[0-9a-fA-F]+)|([0-9]+))', )),
            ('PixelStart', (r'P\[', )),
            ('PixelLayer', (r'PL((0x[0-9a-fA-F]+)|([0-9]+))', )),
            ('PixelLayerStart', (r'PL\[', )),
            ('Animation', (r'A"[^"]+"', )),
            ('AnimationStart', (r'A\[', )),
            ('USBCode', (r'U(("[^"]+")|(0x[0-9a-fA-F]+)|([0-9]+))', )),
            ('USBCodeStart', (r'U\[', )),
            ('ScanCode', (r'S((0x[0-9a-fA-F]+)|([0-9]+))', )),
            ('ScanCodeStart', (r'S\[', )),
            ('CodeBegin', (r'\[', )),
            ('CodeEnd', (r'\]', )),
            ('Position', (r'r?[xyz]:-?[0-9]+(.[0-9]+)?', )),
            ('PixelOperator', (r'(\+:|-:|>>|<<)', )),
            ('RelCROperator', (r'[cr]:i[+-]?', )),
            ('ColRowOperator', (r'[cr]:', )),

            ('String', (r'"[^"]*"', )),

            ('Operator', (r':', )),
            ('Comma', (r',', )),
            ('Parenthesis', (r'\(|\)', )),
            ('Percent', (r'-?(0|([1-9][0-9]*))%', )),
            ('Number', (r'((0x[0-9a-fA-F]+)|(0|([1-9][0-9]*)))', )),
            ('Dash', (r'-', )),
            ('Plus', (r'\+', )),
            ('Name', (r'[A-Za-z_][A-Za-z_0-9]*', )),
        ]

        # Tokenize, expression stores the result, status is returned
        return self.tokenize_base(kll_expression, lspec, rspec)

    def tokenize_assignment(self, kll_expression):
        '''
        Tokenize lparam and rparam in assignment expressions
        <lparam> = <rparam>;
        '''

        # Define tokenization regex
        lspec = [
            ('Space', (r'[ \t]+', )),

            ('Number', (r'(0x[0-9a-fA-F]+)|(0|([1-9][0-9]*))', )),
            ('Name', (r'[A-Za-z_][A-Za-z_0-9]*', )),
            ('CodeBegin', (r'\[', )),
            ('CodeEnd', (r'\]', )),
        ]

        rspec = [
            ('Space', (r'[ \t]+', )),

            ('String', (r'"[^"]*"', )),
            ('SequenceString', (r"'[^']*'", )),
            ('Number', (r'(0x[0-9a-fA-F]+)|(0|([1-9][0-9]*))', )),
            ('Name', (r'[A-Za-z_][A-Za-z_0-9]*', )),
            ('VariableContents', (r'''[^"' ;:=>()]+''', )),
        ]

        # Tokenize, expression stores the result, status is returned
        return self.tokenize_base(kll_expression, lspec, rspec)

    def tokenize_mapping(self, kll_expression):
        '''
        Tokenize lparam and rparam in mapping expressions

        <lparam>  :  <rparam>; # Set mapping
        <lparam>  :+ <rparam>; # Mappping append
        <lparam>  :- <rparam>; # Mapping removal
        <lparam>  :: <rparam>; # Replace mapping (does nothing if nothing to replace)

        Isolated versions of mappings
        When expressions are evalutated during runtime, any non-isolated mapping expressions are cancelled
        <lparam> i:  <rparam>;
        <lparam> i:+ <rparam>;
        <lparam> i:- <rparam>;
        <lparam> i:: <rparam>;
        '''

        # Define tokenization regex
        lspec = [
            ('Space', (r'[ \t]+', )),

            ('USBCode', (r'U(("[^"]+")|(0x[0-9a-fA-F]+)|([0-9]+))', )),
            ('USBCodeStart', (r'U\[', )),
            ('ConsCode', (r'CONS(("[^"]+")|(0x[0-9a-fA-F]+)|([0-9]+))', )),
            ('ConsCodeStart', (r'CONS\[', )),
            ('SysCode', (r'SYS(("[^"]+")|(0x[0-9a-fA-F]+)|([0-9]+))', )),
            ('SysCodeStart', (r'SYS\[', )),
            ('ScanCode', (r'S((0x[0-9a-fA-F]+)|([0-9]+))', )),
            ('ScanCodeStart', (r'S\[', )),
            ('IndCode', (r'I(("[^"]+")|(0x[0-9a-fA-F]+)|([0-9]+))', )),
            ('IndicatorStart', (r'I\[', )),
            ('Pixel', (r'P((0x[0-9a-fA-F]+)|([0-9]+))', )),
            ('PixelStart', (r'P\[', )),
            ('Animation', (r'A"[^"]+"', )),
            ('AnimationStart', (r'A\[', )),
            ('LayerStart', (r'Layer(|Shift|Latch|Lock)\[', )),
            ('TriggerStart', (r'T\[', )),
            ('CodeBegin', (r'\[', )),
            ('CodeEnd', (r'\]', )),

            ('String', (r'"[^"]*"', )),
            ('SequenceStringL', (r"'[^']*'", )),

            ('Operator', (r':', )),
            ('Comma', (r',', )),
            ('Plus', (r'\+', )),
            ('Parenthesis', (r'\(|\)', )),
            ('Timing', (r'[0-9]+(.[0-9]+)?((s)|(ms)|(us)|(ns))', )),
            ('Number', (r'(0x[0-9a-fA-F]+)|(0|([1-9][0-9]*))', )),
            ('Dash', (r'-', )),
            ('Name', (r'[A-Za-z_][A-Za-z_0-9]*', )),
        ]

        rspec = [
            ('Space', (r'[ \t]+', )),

            ('USBCode', (r'U(("[^"]+")|(0x[0-9a-fA-F]+)|([0-9]+))', )),
            ('USBCodeStart', (r'U\[', )),
            ('ConsCode', (r'CONS(("[^"]+")|(0x[0-9a-fA-F]+)|([0-9]+))', )),
            ('ConsCodeStart', (r'CONS\[', )),
            ('SysCode', (r'SYS(("[^"]+")|(0x[0-9a-fA-F]+)|([0-9]+))', )),
            ('SysCodeStart', (r'SYS\[', )),
            ('ScanCode', (r'S((0x[0-9a-fA-F]+)|([0-9]+))', )),
            ('ScanCodeStart', (r'S\[', )),
            ('Pixel', (r'P((0x[0-9a-fA-F]+)|([0-9]+))', )),
            ('PixelStart', (r'P\[', )),
            ('PixelLayer', (r'PL((0x[0-9a-fA-F]+)|([0-9]+))', )),
            ('PixelLayerStart', (r'PL\[', )),
            ('Animation', (r'A"[^"]+"', )),
            ('AnimationStart', (r'A\[', )),
            ('LayerStart', (r'Layer(|Shift|Latch|Lock)\[', )),
            ('CodeBegin', (r'\[', )),
            ('CodeEnd', (r'\]', )),

            ('String', (r'"[^"]*"', )),
            ('SequenceStringR', (r"'[^']*'", )),

            ('None', (r'None', )),

            ('Operator', (r':', )),
            ('Comma', (r',', )),
            ('Plus', (r'\+', )),
            ('Parenthesis', (r'\(|\)', )),
            ('Timing', (r'[0-9]+(.[0-9]+)?((s)|(ms)|(us)|(ns))', )),
            ('Number', (r'((0x[0-9a-fA-F]+)|(0|([1-9][0-9]*)))', )),
            ('Dash', (r'-', )),
            ('Name', (r'[A-Za-z_][A-Za-z_0-9]*', )),
        ]

        # Tokenize, expression stores the result, status is returned
        return self.tokenize_base(kll_expression, lspec, rspec)

    ## Parsers ##
    def parse_base(self, kll_expression, parse_expression, quiet):
        '''
        Base parsing logic

        @param kll_expression: Expression being parsed, contains tokens
        @param parse_expression: Parse tree expression that understands the group of tokens
        @param quiet: Reduces verbosity, used when re-running an errored command in debug mode

        @return: False if parsing wasn't successful
        '''
        ret = True

        try:
            # Since the expressions have already been pre-organized, we only expect a single expression at a time
            ret = parse_expression.parse(kll_expression.final_tokens())

            # Parse intepretation error, more info is provided by the specific parse intepreter
            if not ret and not quiet:
                print(kll_expression.final_tokens())

        except NoParseError as err:
            if not quiet:
                print(kll_expression.final_tokens())
                print("\033[1;33m{0}\033[0m".format(err))
            ret = False
            raise

        return ret

    def parse_name_association(self, kll_expression, quiet=False):
        '''
        Parse name association expressions
        <lparam> => <rparam>;
        '''
        # Import parse elements/lambda functions
        from kll.common.parse import (
            comma,
            name,
            number,
            operator,
            parenthesis,
            unarg,
            Make,
        )

        # Name Association
        # <capability name> => <c function>;
        capability_arguments = name + skip(operator(':')) + number + skip(maybe(comma)) >> unarg(Make.capArg)
        capability_expression = name + skip(operator('=>')) + name + skip(parenthesis('(')) + many(capability_arguments) + skip(parenthesis(')')) >> unarg(kll_expression.capability)

        # Name Association
        # <define name> => <c define>;
        define_expression = name + skip(operator('=>')) + name >> unarg(kll_expression.define)

        # Top-level Parser
        expr = (
            capability_expression |
            define_expression
        )

        return self.parse_base(kll_expression, expr, quiet)

    def parse_data_association(self, kll_expression, quiet=False):
        '''
        Parse data association expressions
        <lparam> <= <rparam>;
        '''
        from kll.common.parse import (
            animation_def,
            animation_elem,
            animation_flattened,
            animation_modlist,
            comma,
            flatten,
            operator,
            pixel_elem,
            pixel_expanded,
            pixelmod_elem,
            position_list,
            triggerCode_outerList,
            unarg,
        )

        # Data Association
        # <animation>       <= <modifiers>;
        # <animation frame> <= <modifiers>;
        animation_expression = (animation_elem | animation_def) + skip(operator('<=')) + animation_modlist >> unarg(kll_expression.animation)
        animationFrame_expression = animation_flattened + skip(operator('<=')) + oneplus(pixelmod_elem + skip(maybe(comma))) >> unarg(kll_expression.animationFrame)

        # Data Association
        # <pixel> <= <position>;
        pixelPosition_expression = (pixel_expanded | pixel_elem) + skip(operator('<=')) + position_list >> unarg(kll_expression.pixelPosition)

        # Data Association
        # <scancode> <= <position>;
        scanCodePosition_expression = (triggerCode_outerList >> flatten >> flatten) + skip(operator('<=')) + position_list >> unarg(kll_expression.scanCodePosition)

        # Top-level Parser
        expr = (
            animation_expression |
            animationFrame_expression |
            pixelPosition_expression |
            scanCodePosition_expression
        )

        return self.parse_base(kll_expression, expr, quiet)

    def parse_assignment(self, kll_expression, quiet=False):
        '''
        Parse assignment expressions
        <lparam> = <rparam>;
        '''
        # Import parse elements/lambda functions
        from kll.common.parse import (
            code_begin,
            code_end,
            comma,
            content,
            dash,
            name,
            number,
            operator,
            string,
            unarg,
            unseqString,
        )

        # Assignment
        # <variable> = <variable contents>;
        variable_contents = name | content | string | number | comma | dash | unseqString
        variable_expression = name + skip(operator('=')) + oneplus(variable_contents) >> unarg(kll_expression.variable)

        # Array Assignment
        # <variable>[]        = <space> <separated> <list>;
        # <variable>[<index>] = <index element>;
        array_expression = name + skip(code_begin) + maybe(number) + skip(code_end) + skip(operator('=')) + oneplus(variable_contents) >> unarg(kll_expression.array)

        # Top-level Parser
        expr = (
            array_expression |
            variable_expression
        )

        return self.parse_base(kll_expression, expr, quiet)

    def parse_mapping(self, kll_expression, quiet=False):
        '''
        Parse mapping expressions

        <lparam>  :  <rparam>; # Set mapping
        <lparam>  :+ <rparam>; # Mappping append
        <lparam>  :- <rparam>; # Mapping removal
        <lparam>  :: <rparam>; # Replace mapping (does nothing if nothing to replace)

        Isolated versions of mappings
        When expressions are evalutated during runtime, any non-isolated mapping expressions are cancelled
        <lparam> i:  <rparam>;
        <lparam> i:+ <rparam>;
        <lparam> i:- <rparam>;
        <lparam> i:: <rparam>;
        '''
        # Import parse elements/lambda functions
        from kll.common.parse import (
            none,
            operator,
            pixelchan_elem,
            resultCode_outerList,
            scanCode_single,
            triggerCode_outerList,
            unarg,
        )

        # Mapping
        # <trigger> : <result>;
        operatorTriggerResult = operator(':') | operator(':+') | operator(':-') | operator('::') | operator('i:') | operator('i:+') | operator('i:-') | operator('i::')
        triggerCode_expression = triggerCode_outerList + operatorTriggerResult + resultCode_outerList >> unarg(kll_expression.triggerCode)

        # Data Association
        # <pixel chan> : <scanCode>;
        pixelChan_expression = pixelchan_elem + skip(operator(':')) + (scanCode_single | none) >> unarg(kll_expression.pixelChannels)

        # Top-level Parser
        expr = (
            triggerCode_expression |
            pixelChan_expression
        )

        return self.parse_base(kll_expression, expr, quiet)

    ## Processing ##
    def tokenize(self, kll_context):
        '''
        Tokenizes contents of both LOperatorData and ROperatorData
        LOperatorData and ROperatorData have different contexts, so tokenization can be simplified a bit

        @param context: KLL Context containing file data
        '''
        ret = True

        # Tokenizer map, each takes an expression argument
        tokenizers = {
            # Name association
            '=>': self.tokenize_name_association,
            # Data association
            '<=': self.tokenize_data_association,
            # Assignment
            '=': self.tokenize_assignment,
            # Mapping
            # All : based operators have the same structure
            # The only difference is the application context (handled in a later stage)
            ':': self.tokenize_mapping,
        }

        # Tokenize left and right parameters of the expression
        for kll_expression in kll_context.expressions:
            # Determine which parser to use
            token = kll_expression.operator_type()

            # If there was a problem tokenizing, display exprersion info
            if not tokenizers[token](kll_expression):
                ret = False
                print("{0} {1}:tokenize -> {2}:{3}".format(
                    ERROR,
                    self.__class__.__name__,
                    kll_context.parent.path,
                    kll_expression.lparam_token.start[0],
                ))

            # Debug Output
            # Displays each parsed expression on a single line
            # Includes <filename>:<line number>
            if self.token_debug:
                # Uncolorize if requested
                output = "\033[1m{0}\033[0m:\033[1;33m{1}\033[0m:\033[1;32m{2}\033[0m\033[1;36;41m>\033[0m {3}".format(
                    os.path.basename(kll_context.parent.path),
                    kll_expression.lparam_token.start[0],
                    kll_expression.__class__.__name__,
                    kll_expression.final_tokens(),
                )
                print(self.color and output or ansi_escape.sub('', output))

        return ret

    def parse(self, kll_context):
        '''
        Parse the fully tokenized expressions

        @param kll_context: KLL Context which has the fully tokenized expression list
        '''
        ret = True

        # Parser map of functions, each takes an expression argument
        parsers = {
            # Name association
            '=>': self.parse_name_association,
            # Data association
            '<=': self.parse_data_association,
            # Assignment
            '=': self.parse_assignment,
            # Mapping
            # All : based operators have the same structure
            # The only difference is the application context (handled in a later stage)
            ':': self.parse_mapping,
        }

        # Parse each expression to extract the data from it
        for kll_expression in kll_context.expressions:
            token = kll_expression.operator_type()

            # Assume failed, unless proven otherwise
            cur_ret = False

            # In some situations we don't want a parser trace, but only disable when we know
            parser_debug_ignore = False

            # If there was a problem parsing, display expression info
            # Catch any TypeErrors due to incorrect parsing rules
            try:
                cur_ret = parsers[token](kll_expression)

            # Unexpected token (user grammar error), sometimes might be a bug
            except NoParseError as err:
                import traceback

                traceback.print_tb(err.__traceback__)
                print(type(err).__name__, err)
                print("\033[1mBad kll expression, usually a syntax error.\033[0m")
                cur_ret = False

            # Invalid parsing rules, definitely a bug
            except TypeError as err:
                import traceback

                traceback.print_tb(err.__traceback__)
                print(type(err).__name__, err)
                print("\033[1mBad parsing rule, this is a bug!\033[0m")

            # Lookup error, invalid lookup
            except KeyError as err:
                import traceback

                print("".join(traceback.format_tb(err.__traceback__)[-1:]), end='')
                print("\033[1mInvalid dictionary lookup, check syntax.\033[0m")
                parser_debug_ignore = True

            # Parsing failed, show more error info
            if not cur_ret:
                ret = False

                # We don't always want a full trace of the parser
                if not parser_debug_ignore:
                    # StringIO stream from funcparserlib parser.py
                    # Command failed, run again, this time with verbose logging enabled
                    # Helps debug erroneous parsing expressions
                    parser_log = io.StringIO()

                    # This part is not thread-safe
                    # You must run with --jobs 1 to get 100% valid output
                    Parser_debug(True, parser_log)
                    try:
                        parsers[token](kll_expression, True)
                    except BaseException:
                        pass
                    Parser_debug(False)

                    # Display
                    print(parser_log.getvalue())

                    # Cleanup StringIO
                    parser_log.close()

                print("{0} {1}:parse -> {2}:{3}".format(
                    ERROR,
                    self.__class__.__name__,
                    kll_context.parent.path,
                    kll_expression.lparam_token.start[0],
                ))

            # Debug Output
            # Displays each parsed expression on a single line
            # Includes <filename>:<line number>
            if self.parser_debug:
                # Uncolorize if requested
                output = "\033[1m{0}\033[0m:\033[1;33m{1}\033[0m:\033[1;32m{2}\033[0m:\033[1;35m{3}\033[1;36;41m>\033[0m {4}".format(
                    os.path.basename(kll_context.parent.path),
                    kll_expression.lparam_token.start[0],
                    kll_expression.__class__.__name__,
                    kll_expression.type,
                    kll_expression
                )
                print(self.color and output or ansi_escape.sub('', output))

            if self.parser_token_debug:
                # Uncolorize if requested
                output = "\t\033[1;4mTokens\033[0m\033[1;36m:\033[0m {0}".format(
                    [(t.type, t.value) for t in kll_expression.final_tokens()]
                )
                print(self.color and output or ansi_escape.sub('', output))

        return ret

    def process(self):
        '''
        Compiler Configuration Processing
        '''
        self._status = 'Running'

        # Determine colorization setting
        self.color = self.control.stage('CompilerConfigurationStage').color

        # Acquire thread pool
        pool = self.control.stage('CompilerConfigurationStage').pool

        # Get list of KLL contexts
        contexts = self.control.stage('OperationClassificationStage').contexts

        # Tokenize operators
        if False in pool.map(self.tokenize, contexts):
            self._status = 'Incomplete'
            return

        # Parse operators
        if False in pool.map(self.parse, contexts):
            self._status = 'Incomplete'
            return

        self._status = 'Completed'


class OperationOrganizationStage(Stage):
    '''
    Operation Organization Stage

    * Using the type of each operation, apply the KLL Context to each operation
    * This results in various datastructures being populated based upon the context and type of operation
    * Each Context instance (distinct Context of the same type), remain separate
    '''

    def __init__(self, control):
        '''
        Initialize configuration variables
        '''
        super().__init__(control)

        self.operation_organization_debug = False
        self.operation_organization_display = False

    def command_line_args(self, args):
        '''
        Group parser for command line arguments

        @param args: Name space of processed arguments
        '''
        self.operation_organization_debug = args.operation_organization_debug
        self.operation_organization_display = args.operation_organization_display

    def command_line_flags(self, parser):
        '''
        Group parser for command line options

        @param parser: argparse setup object
        '''
        # Create new option group
        group = parser.add_argument_group('\033[1mOperation Organization Configuration\033[0m')

        # Optional Arguments
        group.add_argument(
            '--operation-organization-debug',
            action='store_true',
            default=self.operation_organization_debug,
            help="Enable operation organization debug output.\n",
        )
        group.add_argument(
            '--operation-organization-display',
            action='store_true',
            default=self.operation_organization_display,
            help="Show datastructure of each context after filling.\n",
        )

    def organize(self, kll_context):
        '''
        Organize each set of expressions on a context level

        The full layout organization occurs over multiple stages, this is the first one
        '''
        # Add each of the expressions to the organization data structure
        try:
            for kll_expression in kll_context.expressions:
                # Debug output
                if self.operation_organization_debug:
                    # Uncolorize if requested
                    output = "\033[1m{0}\033[0m:\033[1;33m{1}\033[0m:\033[1;32m{2}\033[0m:\033[1;35m{3}\033[1;36;41m>\033[0m {4}".format(
                        os.path.basename(kll_context.parent.path),
                        kll_expression.lparam_token.start[0],
                        kll_expression.__class__.__name__,
                        kll_expression.type,
                        kll_expression
                    )
                    print(self.color and output or ansi_escape.sub('', output))

                # Set connect_id for expression
                kll_expression.connect_id = kll_context.connect_id

                # Add expression
                kll_context.organization.add_expression(
                    kll_expression,
                    (self.operation_organization_debug, self.color)
                )

        except Exception as err:
            import traceback

            traceback.print_tb(err.__traceback__)
            print(type(err).__name__, err)
            print("Could not add/modify kll expression in context datastructure.")
            return False

        return True

    def process(self):
        '''
        Operation Organization Stage Processing
        '''
        self._status = 'Running'

        # Determine colorization setting
        self.color = self.control.stage('CompilerConfigurationStage').color

        # Acquire thread pool
        pool = self.control.stage('CompilerConfigurationStage').pool

        # Get list of KLL contexts
        contexts = self.control.stage('OperationClassificationStage').contexts

        # Add expressions from contexts to context datastructures
        if False in pool.map(self.organize, contexts):
            self._status = 'Incomplete'
            return

        # Show result of filling datastructure
        if self.operation_organization_display:
            for kll_context in contexts:
                # Uncolorize if requested
                output = "\033[1m{0}\033[0m:\033[1;33m{1}\033[0m".format(
                        os.path.basename(kll_context.parent.path),
                        kll_context.__class__.__name__
                )
                print(self.color and output or ansi_escape.sub('', output))

                # Display Table
                for store in kll_context.organization.stores():
                    # Uncolorize if requested
                    output = "\t\033[1;4;32m{0}\033[0m".format(
                            store.__class__.__name__
                    )
                    print(self.color and output or ansi_escape.sub('', output))
                    print(self.color and store or ansi_escape.sub('', store), end="")

        self._status = 'Completed'


class DataOrganizationStage(Stage):
    '''
    Data Organization Stage

    * Using the constructed Context datastructures, merge contexts of the same type together
    * Precedence/priority is defined by the order each Context was included on the command line
    * May include datastructure data optimizations
    '''

    def __init__(self, control):
        '''
        Initialize configuration variables
        '''
        super().__init__(control)

        self.data_organization_debug = False
        self.data_organization_display = False
        self.contexts = None

    def command_line_args(self, args):
        '''
        Group parser for command line arguments

        @param args: Name space of processed arguments
        '''
        self.data_organization_debug = args.data_organization_debug
        self.data_organization_display = args.data_organization_display

    def command_line_flags(self, parser):
        '''
        Group parser for command line options

        @param parser: argparse setup object
        '''
        # Create new option group
        group = parser.add_argument_group('\033[1mData Organization Configuration\033[0m')

        # Optional Arguments
        group.add_argument(
            '--data-organization-debug',
            action='store_true',
            default=self.data_organization_debug,
            help="Show debug info from data organization stage.\n",
        )
        group.add_argument(
            '--data-organization-display',
            action='store_true',
            default=self.data_organization_display,
            help="Show datastructure of each context after merging.\n",
        )

    def sort_contexts(self, contexts):
        '''
        Returns a dictionary of list of sorted 'like' contexts

        This is used to group the contexts that need merging
        '''
        lists = {}

        for kll_context in contexts:
            name = kll_context.__class__.__name__

            # PartialMapContext's are sorted by name *and* layer number
            if name == "PartialMapContext":
                name = "{0}{1}".format(name, kll_context.layer)

            # Add new list if no elements yet
            if name not in lists.keys():
                lists[name] = [kll_context]
            else:
                lists[name].append(kll_context)

        if self.data_organization_debug:
            output = "\033[1mContext Organization\033[0m"
            for key, val in sorted(lists.items()):
                output += "\n{}".format(key)
                for elem in val:
                    output += "\n\t{} - {}".format(elem.layer_info(), elem.kll_files)
            print(self.color and output or ansi_escape.sub('', output))

        return lists

    def organize(self, kll_context):
        '''
        Symbolically merge all like Contexts

        The full layout organization occurs over multiple stages, this is the second stage
        '''
        # Lookup context name
        context_name = "{0}".format(kll_context[0].__class__.__name__)

        # PartialMapContext's are sorted by name *and* layer number
        if context_name == "PartialMapContext":
            context_name = "{0}{1}".format(context_name, kll_context[0].layer)

        # Initialize merge context as the first one
        self.contexts[context_name] = context.MergeContext(kll_context[0])

        # Indicate when a context is skipped as there is only one
        if self.data_organization_debug:
            if len(kll_context) < 2:
                output = "\033[1;33mSkipping\033[0m\033[1m:\033[1;32m{0}\033[0m".format(
                    context_name
                )
                print(self.color and output or ansi_escape.sub('', output))
                return True

        # The incoming list is ordered
        # Merge in each of the contexts symbolically
        for next_context in kll_context[1:]:
            try:
                if self.data_organization_debug:
                    output = "\033[1m=== Merging ===\033[0m {1} into {0}".format(self.contexts[context_name].kll_files, next_context.kll_files)
                    print(self.color and output or ansi_escape.sub('', output))

                self.contexts[context_name].merge(
                    next_context,
                    context_name,
                    (self.data_organization_debug, self.color)
                )

            except Exception as err:
                import traceback

                traceback.print_tb(err.__traceback__)
                print(type(err).__name__, err)
                print("Could not merge '{0}' into '{1}' context.".format(
                    os.path.basename(next_context.parent.path),
                    context_name
                ))
                return False

        # After merging contexts, update Context information.
        # If a BaseMap, apply modifier to each of the expressions.
        # This is used by emitter to decide whether the expression can be filtered out.
        if context_name == 'BaseMapContext':
            for key, expr in self.contexts['BaseMapContext'].organization.mapping_data.data.items():
                # Only applys to MapExpressions
                if isinstance(expr[0], expression.MapExpression):
                    expr[0].base_map = True

        return True

    def process(self):
        '''
        Data Organization Stage Processing
        '''
        self._status = 'Running'

        # Determine colorization setting
        self.color = self.control.stage('CompilerConfigurationStage').color

        # Acquire thread pool
        pool = self.control.stage('CompilerConfigurationStage').pool

        # Get list of KLL contexts
        contexts = self.control.stage('OperationClassificationStage').contexts

        # Get sorted list of KLL contexts
        sorted_contexts = self.sort_contexts(contexts)
        self.contexts = {}

        # Add expressions from contexts to context datastructures
        if False in pool.map(self.organize, sorted_contexts.values()):
            self._status = 'Incomplete'
            return

        # Show result of filling datastructure
        if self.data_organization_display:
            for key, kll_context in self.contexts.items():
                # Uncolorize if requested
                output = "\033[1;33m{0}\033[0m:\033[1m{1}\033[0m".format(
                    key,
                    kll_context.paths(),
                )
                print(self.color and output or ansi_escape.sub('', output))

                # Display Table
                for store in kll_context.organization.stores():
                    # Uncolorize if requested
                    output = "\t\033[1;4;32m{0}\033[0m".format(
                        store.__class__.__name__
                    )
                    print(self.color and output or ansi_escape.sub('', output))
                    print(self.color and store or ansi_escape.sub('', store), end="")

        self._status = 'Completed'


class DataFinalizationStage(Stage):
    '''
    Data Finalization Stage

    * Using the merged Context datastructures, apply the Configuration and BaseMap contexts to the higher
    level DefaultMap and PartialMap Contexts
    * First BaseMap is applied on top of Configuration
    * Next, DefaultMap is applied on top of (Configuration+BaseMap) as well as the PartialMaps
    * May include datastructure data optimizations
    '''

    def __init__(self, control):
        '''
        Initialize configuration variables
        '''
        super().__init__(control)

        self.data_finalization_debug = False
        self.data_finalization_display = False
        self.base_context = None
        self.default_context = None
        self.partial_contexts = None
        self.full_context = None
        self.context_list = None
        self.layer_contexts = None

    def command_line_args(self, args):
        '''
        Group parser for command line arguments

        @param args: Name space of processed arguments
        '''
        self.data_finalization_debug = args.data_finalization_debug
        self.data_finalization_display = args.data_finalization_display

    def command_line_flags(self, parser):
        '''
        Group parser for command line options

        @param parser: argparse setup object
        '''
        # Create new option group
        group = parser.add_argument_group('\033[1mData Organization Configuration\033[0m')

        # Optional Arguments
        group.add_argument(
            '--data-finalization-debug',
            action='store_true',
            default=self.data_finalization_debug,
            help="Show debug info from data finalization stage.\n",
        )
        group.add_argument(
            '--data-finalization-display',
            action='store_true',
            default=self.data_finalization_display,
            help="Show datastructure of each context after merging.\n",
        )

    def process(self):
        '''
        Data Organization Stage Processing
        '''
        self._status = 'Running'

        # Determine colorization setting
        self.color = self.control.stage('CompilerConfigurationStage').color

        # Get context silos
        contexts = self.control.stage('DataOrganizationStage').contexts
        self._status = 'Incomplete'

        # Context list
        self.context_list = []

        # Depending on the calling order, we may need to use a GenericContext or ConfigurationContext as the base
        # Default to ConfigurationContext first
        if 'ConfigurationContext' in contexts.keys():
            self.base_context = context.MergeContext(contexts['ConfigurationContext'])

            # If we still have GenericContexts around, merge them on top of the ConfigurationContext
            if 'GenericContext' in contexts.keys():
                self.base_context.merge(
                    contexts['GenericContext'],
                    'GenericContext',
                    (self.data_finalization_debug, self.color)
                )

        # Otherwise, just use a GenericContext
        elif 'GenericContext' in contexts.keys():
            self.base_context = context.MergeContext(contexts['GenericContext'])

        # Fail otherwise, you *must* have a GenericContext or ConfigurationContext
        else:
            print("{0} Missing a 'GenericContext' and/or 'ConfigurationContext'.".format(ERROR))
            self._status = 'Incomplete'
            return

        # Next use the BaseMapContext and overlay on ConfigurationContext
        # This serves as the basis for the next two merges
        if 'BaseMapContext' in contexts.keys():
            self.base_context.merge(
                contexts['BaseMapContext'],
                'BaseMapContext',
                (self.data_finalization_debug, self.color)
            )
            self.context_list.append(('BaseMapContext', self.base_context))

        # Then use the DefaultMapContext as the default keyboard mapping
        self.default_context = context.MergeContext(self.base_context)
        if 'DefaultMapContext' in contexts.keys():
            self.default_context.merge(
                contexts['DefaultMapContext'],
                'DefaultMapContext',
                (self.data_finalization_debug, self.color)
            )
            self.context_list.append(('DefaultMapContext', self.default_context))

        # For convenience build a fully merged dataset
        # This is usually only required for variables
        self.full_context = context.MergeContext(self.default_context)

        # Finally setup each of the PartialMapContext groups
        # Build list of PartialMapContexts and sort by layer before iterating over
        self.partial_contexts = []
        partial_context_list = [
            (item[1].layer, item[1])
            for item in contexts.items()
            if 'PartialMapContext' in item[0]
        ]
        for layer, partial in sorted(partial_context_list, key=lambda x: x[0]):
            # Start with base context
            self.partial_contexts.append(context.MergeContext(self.base_context))

            # Merge in layer
            self.partial_contexts[layer].merge(
                partial,
                'PartialMapContext',
                (self.data_finalization_debug, self.color)
            )

            # Add to context list
            self.context_list.append(('PartialMapContext{0}'.format(layer), self.default_context))

            # Add each partial to the full_context as well
            self.full_context.merge(
                partial,
                'PartialMapContext',
                (self.data_finalization_debug, self.color)
            )

        # Build layer context list
        # Each index of the list corresponds to the keyboard layer
        self.layer_contexts = [self.default_context]
        self.layer_contexts.extend(self.partial_contexts)

        # Show result of filling datastructure
        if self.data_finalization_display:
            for key, kll_context in self.context_list:
                # Uncolorize if requested
                output = "*\033[1;33m{0}\033[0m:\033[1m{1}\033[0m".format(
                    key,
                    kll_context.paths(),
                )
                print(self.color and output or ansi_escape.sub('', output))

                # Display Table
                for store in kll_context.organization.stores():
                    # Uncolorize if requested
                    output = "\t\033[1;4;32m{0}\033[0m".format(
                        store.__class__.__name__
                    )
                    print(self.color and output or ansi_escape.sub('', output))
                    print(self.color and store or ansi_escape.sub('', store), end="")

        self._status = 'Completed'


class DataAnalysisStage(Stage):
    '''
    Data Analysis Stage

    * Using the completed Context datastructures, do additional analysis that may be required for Code Generation
    '''

    def __init__(self, control):
        '''
        Initialize configuration variables
        '''
        super().__init__(control)

        self.data_analysis_debug = False
        self.data_analysis_display = False

        self.trigger_index = []
        self.result_index = []
        self.trigger_index_lookup = dict()
        self.trigger_index_reduced_lookup = dict()
        self.result_index_lookup = dict()
        self.result_index = []
        self.trigger_lists = []

        # NOTE Interconnect offsets are determined in the preprocessor stage
        self.max_scan_code = []
        self.min_scan_code = []

        self.rotation_map = dict()

        self.interconnect_scancode_offsets = []
        self.interconnect_pixel_offsets = []

        self.scancode_positions = dict()
        self.pixel_positions = dict()
        self.pixel_display_mapping = []
        self.pixel_display_params = dict()

        self.animation_settings = dict()
        self.animation_settings_orig = dict()
        self.animation_settings_list = []
        self.animation_uid_lookup = dict()

        self.partial_contexts = None
        self.layer_contexts = None
        self.full_context = None

    def command_line_args(self, args):
        '''
        Group parser for command line arguments

        @param args: Name space of processed arguments
        '''
        self.data_analysis_debug = args.data_analysis_debug
        self.data_analysis_display = args.data_analysis_display

    def command_line_flags(self, parser):
        '''
        Group parser for command line options

        @param parser: argparse setup object
        '''
        # Create new option group
        group = parser.add_argument_group('\033[1mData Analysis Configuration\033[0m')

        # Optional Arguments
        group.add_argument(
            '--data-analysis-debug',
            action='store_true',
            default=self.data_analysis_debug,
            help="Show debug info from data analysis stage.\n",
        )
        group.add_argument(
            '--data-analysis-display',
            action='store_true',
            default=self.data_analysis_display,
            help="Show results of data analysis.\n",
        )

    def reduction(self):
        '''
        Builds a new reduced_contexts list

        For each of the layers, evaluate triggers into ScanCodes (USBCode to ScanCodes)
        (all other triggers don't require reductions)
        '''
        self.reduced_contexts = []

        if self.data_analysis_debug:
            print("\033[1m--- Analysis Reduction ---\033[0m")

        for index, layer in enumerate(self.layer_contexts):
            if self.data_analysis_debug:
                print("\033[1m ++ Layer {0} ++\033[0m".format(index))
            reduced = context.MergeContext(layer)
            reduced.reduction(debug=self.data_analysis_debug)
            self.reduced_contexts.append(reduced)

        # Filter out BaseMap specific expressions
        if self.data_analysis_debug:
            print("\033[1m == BaseMap Cleanup ==\033[0m")

        # Skip DefaultLayer (0) as there is nothing to cleanup
        for index, layer in enumerate(self.reduced_contexts[1:]):
            if self.data_analysis_debug:
                print("\033[1m ++ Layer {0} ++\033[0m".format(index + 1))
            layer.cleanup((self.data_analysis_debug, self.color))
            if self.data_analysis_debug:
                print(layer.organization.mapping_data)

    def generate_mapping_indices(self):
        '''
        For each trigger:result pair generate a unique index

        The triggers and results are first sorted alphabetically
        '''
        if self.data_analysis_debug or self.data_analysis_display:
            print("\033[1m--- Mapping Indices ---\033[0m")

        # Build uniq dictionary of map expressions
        # Only reduce true duplicates (identical kll expressions) initially
        expressions = dict()
        # Gather list of expressions
        for index, layer in enumerate(self.reduced_contexts):
            # Set initial min/max ScanCode
            self.min_scan_code.append(0xFFFF)
            self.max_scan_code.append(0)

            # Add each expression in layer to overall dictionary lookup for command reduction
            for key, elem in layer.organization.mapping_data.data.items():
                # Add each of the expressions (usually just one)
                # Before adding the expression, adjust the scancode using the connect_id offset
                for sub_expr in elem:
                    scancode_offset = self.interconnect_scancode_offsets[sub_expr.connect_id]
                    sub_expr.add_trigger_uid_offset(scancode_offset)
                    expressions[sub_expr.kllify()] = sub_expr

                # We only need to use the first expression, as the triggers are all the same
                # Determine min ScanCode of each trigger expression
                min_uid = elem[0].min_trigger_uid()
                if min_uid < self.min_scan_code[index]:
                    self.min_scan_code[index] = min_uid

                # Determine max ScanCode of each trigger expression
                max_uid = elem[0].max_trigger_uid()
                if max_uid > self.max_scan_code[index]:
                    self.max_scan_code[index] = max_uid

            # Unset min_scan_code if not set
            if self.min_scan_code[index] == 0xFFFF and self.max_scan_code[index] == 0:
                self.min_scan_code[index] = 0

        # Sort expressions by trigger and result, there may be *duplicate* triggers however don't reduce yet
        # we need the trigger->result and result->trigger mappings still
        trigger_sorted = dict()
        trigger_sorted_reduced = dict()
        result_sorted = dict()
        for key, elem in expressions.items():
            # Trigger Sorting (we don't use trigger_str() here as it would cause reduction)
            trig_key = key
            if trig_key not in trigger_sorted.keys():
                trigger_sorted[trig_key] = [elem]
            else:
                trigger_sorted[trig_key].append(elem)

            # Trigger Sorting, reduced dictionary for trigger guides (i.e. we want reduction)
            trig_key = elem.trigger_str()
            if trig_key not in trigger_sorted_reduced.keys():
                trigger_sorted_reduced[trig_key] = [elem]
            else:
                trigger_sorted_reduced[trig_key].append(elem)

            # Result Sorting
            res_key = elem.result_str()
            if res_key not in result_sorted.keys():
                result_sorted[res_key] = [elem]
            else:
                result_sorted[res_key].append(elem)

        # Debug info
        if self.data_analysis_debug or self.data_analysis_display:
            print("\033[1mMin ScanCode\033[0m: {0}".format(self.min_scan_code))
            print("\033[1mMax ScanCode\033[0m: {0}".format(self.max_scan_code))

        # Build indices
        self.trigger_index = [elem for key, elem in sorted(trigger_sorted.items(), key=lambda x: x[1][0].sort_trigger())]
        self.trigger_index_reduced = [elem for key, elem in sorted(trigger_sorted_reduced.items(), key=lambda x: x[1][0].sort_trigger())]
        self.result_index = [elem for key, elem in sorted(result_sorted.items(), key=lambda x: x[1][0].sort_result())]

        # Build index lookup
        # trigger_index_lookup has a full lookup so we don't lose information
        self.trigger_index_lookup = {name[0].kllify(): index for index, name in enumerate(self.trigger_index)}
        self.trigger_index_reduced_lookup = {name[0].sort_trigger(): index for index, name in enumerate(self.trigger_index_reduced)}
        self.result_index_lookup = {name[0].sort_result(): index for index, name in enumerate(self.result_index)}

    def generate_map_offset_table(self):
        '''
        Generates list of offsets for each of the interconnect ids
        '''
        if self.data_analysis_debug or self.data_analysis_display:
            print("\033[1m--- Map Offsets ---\033[0m")
            print("Scan Code Offsets: {0}".format(self.interconnect_scancode_offsets))
            print("Pixel Id Offsets:  {0}".format(self.interconnect_pixel_offsets))

        # FIXME Should this be removed entirely?
        return
        print("{0} This functionality is handled by the preprocessor".format(ERROR))

        maxscancode = {}
        maxpixelid = {}
        for index, layer in enumerate(self.reduced_contexts):
            # Find the max scancode of each the layers
            # A max scancode for each of the interconnect ids found
            for key, value in layer.organization.maxscancode().items():
                if key not in maxscancode.keys() or maxscancode[key] < value:
                    maxscancode[key] = value

            # Find the max pixel id for each of the interconnect ids found
            for key, value in layer.organization.maxpixelid().items():
                if key not in maxpixelid.keys() or maxpixelid[key] < value:
                    maxpixelid[key] = value

        # Build scancode list of offsets
        self.interconnect_scancode_offsets = []
        cumulative = 0
        if len(maxscancode.keys()) > 0:
            for index in range(max(maxscancode.keys()) + 1):
                # Set offset, then add max to cumulative
                self.interconnect_scancode_offsets.append(cumulative)
                cumulative += maxscancode[index]

        # Build pixel id list of offsets
        self.interconnect_pixel_offsets = []
        cumulative = 0
        if len(maxpixelid.keys()) > 0:
            for index in range(max(maxpixelid.keys()) + 1):
                # Set offset, then add max to cumulative
                self.interconnect_pixel_offsets.append(cumulative)
                cumulative += maxscancode[index]

        if self.data_analysis_debug:
            print("\033[1m--- Map Offsets ---\033[0m")
            print("Scan Code Offsets: {0}".format(self.interconnect_scancode_offsets))
            print("Pixel Id Offsets:  {0}".format(self.interconnect_pixel_offsets))

    def generate_trigger_lists(self):
        '''
        Generate Trigger Lists per layer using the index lists
        '''
        if self.data_analysis_debug or self.data_analysis_display:
            print("\033[1m--- Trigger Lists ---\033[0m")

        # Iterate through each of the layers (starting from 0/Default)
        # Generate the trigger list for each of the ScanCodes
        # A trigger list is a list of all possible trigger macros that may be initiated by a ScanCode
        for index, layer in enumerate(self.reduced_contexts):
            # Initialize trigger list by max index size
            self.trigger_lists.append([None] * (self.max_scan_code[index] + 1))

            # Iterate over each expression
            for key, elem in layer.organization.mapping_data.data.items():
                # Each trigger, may have multiple results
                for sub_expr in elem:
                    # Get list of ids from expression
                    for identifier in sub_expr.trigger_id_list():
                        # If animation, set the uid first by doing a uid lookup
                        if identifier.type in ['Animation']:
                            identifier.uid = self.animation_uid_lookup[identifier.name]

                        # Append each uid to Trigger List
                        if identifier.type in ['Animation', 'IndCode', 'GenericTrigger', 'Layer', 'LayerLock', 'LayerShift', 'LayerLatch', 'ScanCode']:
                            # In order to uniquely identify each trigger, using full kll expression as lookup
                            trigger_index = self.trigger_index_lookup[sub_expr.kllify()]

                            # Initialize trigger list if None
                            if self.trigger_lists[index][identifier.get_uid()] is None:
                                self.trigger_lists[index][identifier.get_uid()] = [trigger_index]

                            # Append to trigger list, only if trigger not already added
                            elif trigger_index not in self.trigger_lists[index][identifier.get_uid()]:
                                self.trigger_lists[index][identifier.get_uid()].append(trigger_index)

            # Debug output
            if self.data_analysis_debug or self.data_analysis_display:
                print("\033[1mTrigger List\033[0m: {0} {1}".format(index, self.trigger_lists[index]))

    def generate_rotation_ranges(self):
        '''
        Generate Rotation Ranges

        Using the reduced contexts determine the uids of the rotation triggers used.
        And calculate the size of the rotation (so KLL knowns where the wrap-around occurs)

        Currently only used for Generic Trigger 21
        T[21,0](0) : <result>;
        T[21,0](1) : <result>;
        T[21,0](2) : <result>; # uid 0, range 0..2
        T[21,3](6) : <result>; # uid 3, range 0..6

        We don't need to worry about capabilities doing triggers that don't exist.
        Those will be ignored at runtime.
        '''
        # Iterate over each layer
        for layer in self.reduced_contexts:
            # Iterate over each expression
            for key, elem in layer.organization.mapping_data.data.items():
                # Each trigger, may have multiple results
                for sub_expr in elem:
                    # Get list of ids from expression
                    for identifier in sub_expr.trigger_id_list():
                        # Determine if GenericTrigger
                        if identifier.type in ['GenericTrigger'] and identifier.idcode == 21:
                            # If uid not in rotation_map, add it
                            if identifier.uid not in self.rotation_map.keys():
                                self.rotation_map[identifier.uid] = 0

                            # If there is no parameter raise an error
                            if len(identifier.parameters) != 1:
                                self._status = 'Incomplete'
                                print("{} Rotation trigger must have 1 parameter e.g. T[21,1](3): {}".format(
                                    ERROR,
                                    elem,
                                ))
                                continue

                            # Set the maximum rotation value
                            if identifier.parameters[0].state > self.rotation_map[identifier.uid]:
                                self.rotation_map[identifier.uid] = identifier.parameters[0].state

    def generate_pixel_display_mapping(self):
        '''
        Generate Pixel Display Mapping

        First generate a position dictionary of all pixels using Pixel Index addresses and x,y,z positions

        Build a 2-dimensinoal mapping of all Pixels.
        Use UnitSize, ColumnSize and RowSize to determine pixel fit.
        * Build list of all pixels in a rows/columns
        * Find min/max x/y to determine size of grid
        * Use UnitSize to determine where to place each Pixel
        * Error if we cannot fit all Pixels
        '''
        # Query the scancode and pixels positions
        scancode_physical = self.full_context.query('DataAssociationExpression', 'ScanCodePosition')
        pixel_physical = self.full_context.query('DataAssociationExpression', 'PixelPosition')
        pixel_indices = self.full_context.query('MapExpression', 'PixelChannel')

        pixel_indices_filtered = list(filter(lambda x: not isinstance(x.position, list), pixel_indices.data.values()))
        physical = scancode_physical.data.copy()
        physical.update(pixel_physical.data)

        positions = dict()
        scancode_positions = dict()
        for key, item in physical.items():
            entry = dict()
            # Acquire each dimension
            entry['x'] = item.association[0].x
            entry['y'] = item.association[0].y
            entry['z'] = item.association[0].z

            # Not every pixel has a scancode mapping
            scancode_uid = None

            # Check each dimension, set to 0 if None
            for k in entry.keys():
                if entry[k] is None:
                    entry[k] = 0.0
                else:
                    entry[k] = float(entry[k])

            # Query Pixel index
            uid = item.association[0].uid
            if isinstance(uid, id.PixelAddressId):
                uid = uid.index

            # Use the ScanCode to perform a pixel uid lookup
            else:
                # Filter list, looking for ScanCode uid
                lookup = list(filter(lambda x: x.position.uid == uid, pixel_indices_filtered))
                scancode_uid = uid

                # TODO (HaaTa) Make sure this is a valid ScanCode

                # Also add a scancode_position entry (if this is a scancode)
                scancode_positions[scancode_uid] = copy.copy(entry)

                # Then lookup the pixel uid
                if len(lookup) > 0:
                    uid = lookup[0].pixel.uid.index

                    # Also add a PixelId if one is found to the scancode_position entry
                    scancode_positions[scancode_uid]['PixelId'] = uid

            positions[uid] = copy.copy(entry)

            # Only add ScanCode if one was found
            if scancode_uid is not None:
                positions[uid]['ScanCode'] = scancode_uid

        # Having a full list of Physical Positions is useful during code generation
        self.pixel_positions = positions
        self.scancode_positions = scancode_positions

        # Lookup Pixel Display Mapping parameters
        variables = self.full_context.query('AssignmentExpression', 'Variable')
        try:
            unit_size = float(variables.data['Pixel_DisplayMapping_UnitSize'].value)
            column_size = int(variables.data['Pixel_DisplayMapping_ColumnSize'].value)
            row_size = int(variables.data['Pixel_DisplayMapping_RowSize'].value)
            column_direction = int(variables.data['Pixel_DisplayMapping_ColumnDirection'].value)
            row_direction = int(variables.data['Pixel_DisplayMapping_RowDirection'].value)
        except KeyError:
            unit_size = 1
            column_size = 20
            row_size = 20
            column_direction = 1
            row_direction = 1

        # Determine the min/max x/y for defining the mapping bounds
        minval = {'x': 0, 'y': 0}
        maxval = {'x': 0, 'y': 0}
        for key, item in positions.items():
            for val in ['x', 'y']:
                if item[val] > maxval[val]:
                    maxval[val] = item[val]
                if item[val] < minval[val]:
                    minval[val] = item[val]

        # Calculate grid parameters
        height_val = maxval['y'] - minval['y']
        width_val = maxval['x'] - minval['x']
        height = int(round(height_val / unit_size * column_size)) + 1
        width = int(round(width_val / unit_size * row_size)) + 1
        height_offset = minval['y'] * -1
        width_offset = minval['x'] * -1

        # Set parameters
        self.pixel_display_params['Columns'] = width
        self.pixel_display_params['Rows'] = height

        # Define grid
        self.pixel_display_mapping = [[0 for x in range(width)] for y in range(height)]

        # Place each of the pixels within the x,y mapping
        # Display an error if any pixel is overwritten (i.e. replacing non-0 value)
        for key, item in positions.items():
            # Calculate the percentage position in the grid
            x_percent = ((item['x'] + width_offset) / width_val)
            y_percent = ((item['y'] + height_offset) / height_val)

            # Direction
            if column_direction == -1:
                y_percent = 1 - y_percent
            if row_direction == -1:
                x_percent = 1 - x_percent

            # Determine the exact position
            x = x_percent * (width - 1)
            y = y_percent * (height - 1)

            # First check with rounding
            x_round = int(round(x))
            y_round = int(round(y))

            # Make sure we don't overwrite another pixel
            if self.pixel_display_mapping[y_round][x_round] == 0:
                self.pixel_display_mapping[y_round][x_round] = key
            # Error out
            # XXX We should try additional fitting locations -HaaTa
            else:
                print("{0} Cannot fit:".format(WARNING),
                    key, item, x_round, y_round, self.pixel_display_mapping[y_round][x_round]
                )

        # Debug info
        if self.data_analysis_debug:
            for row in self.pixel_display_mapping:
                print(row)

    def find_animation_result(self, result_expr):
        '''
        Returns list of animation results

        The string'ified version of the object is unique.
        Only return a reduced list of objects.
        '''
        animation_dict = {}
        #print( result_expr )
        for seq in result_expr:
            for combo in seq:
                for elem in combo:
                    if isinstance(elem, id.AnimationId):
                        animation_dict["{0}".format(elem)] = elem
        # Just return the values
        return animation_dict.values()

    def generate_animation_settings(self):
        '''
        Generate Animation Settings

        This function reconciles default and used animation settings.
        Default settings are used to simplify used animation results.
        Meaning that you don't have to remember to define the correct interpolation algorithm every time.
        Each permutation of animation settings is stored (along with the defaults even if not used directly).

        A reduction is done such that only the minimum number of settings entries are created.

        animation_settings stores the key => settings lookup
        animation_settings_list stores the order of the settings (using the keys)
        '''
        # Setup defaults
        animations = self.full_context.query('DataAssociationExpression', 'Animation')
        default_animations = {}
        for key, animation in sorted(animations.data.items()):
            str_name = "{0}({1})".format(key, animation.value)
            self.animation_settings[str_name] = animation.value
            self.animation_settings_list.append(str_name)
            default_animations[key] = animation.value

        val_list = []
        for layer in self.layer_contexts:
            map_expressions = layer.query('MapExpression')
            for expr_type in map_expressions:
                for key, expr in map_expressions[expr_type].data.items():
                    if isinstance(expr, list):
                        for elem in expr:
                            val_list += self.find_animation_result(elem.results)

        # Reduce settings using defaults and determine which are variants needing new settings entries
        for val in sorted(frozenset(val_list), key=lambda x: x.__repr__()):
            mod_default_list = []

            # Lookup defaults
            lookup_name = "A[{0}]".format(val.name)
            str_name = "{0}".format(val)
            found = False
            for name in default_animations.keys():
                if lookup_name == name:
                    mod_default_list = default_animations[name].modifiers
                    found = True
            # Otherwise just add it, if there isn't a default
            if not found:
                self.animation_settings[str_name] = val
                self.animation_settings_orig[str_name] = val
                self.animation_settings_list.append(str_name)
                continue

            # Update settings with defaults
            new_setting = copy.deepcopy(val)
            for setting in mod_default_list:
                found = False
                for mod in new_setting.modifiers:
                    if mod.name == setting.name:
                        found = True
                if not found:
                    new_setting.replace(setting)

            # Add update setting
            self.animation_settings[str_name] = new_setting
            self.animation_settings_orig[str_name] = val

            # Make sure we haven't added this setting to the list already
            if str_name not in self.animation_settings_list:
                self.animation_settings_list.append(str_name)

        # Build uid lookup for each of the animations
        count = 0
        for key, animation in sorted(animations.data.items()):
            self.animation_uid_lookup[animation.association.name] = count
            count += 1

    def analyze(self):
        '''
        Analyze the set of configured contexts
        '''
        # Reduce Contexts
        # Convert all trigger USBCodes to ScanCodes
        self.reduction()

        # Show result of filling datastructure
        if self.data_analysis_display:
            for key, kll_context in enumerate(self.reduced_contexts):
                # Uncolorize if requested
                output = "*\033[1;33mLayer{0}\033[0m:\033[1m{1}\033[0m".format(
                    key,
                    kll_context.paths(),
                )
                print(self.color and output or ansi_escape.sub('', output))

                # Display Table
                for store in kll_context.organization.stores():
                    # Uncolorize if requested
                    output = "\t\033[1;4;32m{0}\033[0m".format(
                        store.__class__.__name__
                    )
                    print(self.color and output or ansi_escape.sub('', output))
                    print(self.color and store or ansi_escape.sub('', store), end="")

        # Generate 2D Pixel Display Mapping
        self.generate_pixel_display_mapping()

        # Generate Animation Settings List
        self.generate_animation_settings()

        # Generate Offset Table
        # This is needed for interconnect devices
        self.generate_map_offset_table()

        # Generate Indices
        # Assigns a sequential index (starting from 0) for each map expresssion
        self.generate_mapping_indices()

        # Generate Trigger Lists
        self.generate_trigger_lists()

        # Generate Rotation Ranges
        self.generate_rotation_ranges()

    def process(self):
        '''
        Data Analysis Stage Processing
        '''
        self._status = 'Running'

        self.max_scan_code = self.control.stage('PreprocessorStage').max_scan_code
        self.min_scan_code = self.control.stage('PreprocessorStage').min_scan_code

        self.interconnect_scancode_offsets = self.control.stage('PreprocessorStage').interconnect_scancode_offsets

        # Determine colorization setting
        self.color = self.control.stage('CompilerConfigurationStage').color

        # Acquire list of contexts
        self.layer_contexts = self.control.stage('DataFinalizationStage').layer_contexts
        self.partial_contexts = self.control.stage('DataFinalizationStage').partial_contexts
        self.full_context = self.control.stage('DataFinalizationStage').full_context

        # Analyze set of contexts
        self.analyze()

        # Return if status has changed
        if self._status != 'Running':
            return

        self._status = 'Completed'


class CodeGenerationStage(Stage):
    '''
    Code Generation Stage

    * Generates code for the given firmware backend
    * Backend is selected in the Compiler Configuration Stage
    * Uses the specified emitter to generate the code
    '''

    def __init__(self, control):
        '''
        Initialize configuration variables
        '''
        super().__init__(control)

    def command_line_args(self, args):
        '''
        Group parser for command line arguments

        @param args: Name space of processed arguments
        '''
        self.control.stage('CompilerConfigurationStage').emitters.command_line_args(args)

    def command_line_flags(self, parser):
        '''
        Group parser for command line options

        @param parser: argparse setup object
        '''
        # Create new option group
        group = parser.add_argument_group('\033[1mCode Generation Configuration\033[0m')

        # Create options groups for each of the Emitters
        self.control.stage('CompilerConfigurationStage').emitters.command_line_flags(parser)

    def process(self):
        '''
        Data Organization Stage Processing
        '''
        self._status = 'Running'

        # Determine colorization setting
        self.color = self.control.stage('CompilerConfigurationStage').color

        # Get Emitter object
        self.emitter = self.control.stage('CompilerConfigurationStage').emitters.emitter(
            self.control.stage('CompilerConfigurationStage').emitter
        )

        # Call Emitter
        self.emitter.process()

        # Generate Outputs using Emitter
        self.emitter.output()

        # Check Emitter status
        if self.emitter.check():
            self._status = 'Completed'
        else:
            self._status = 'Incomplete'


class ReportGenerationStage(Stage):
    '''
    Report Generation Stage

    * Using the datastructures and analyzed data, generate a compiler report
    * TODO
    '''
