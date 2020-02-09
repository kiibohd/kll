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

from collections import OrderedDict

from kll.common.emitter import JsonEmitter, Emitter



### Decorators ###

# Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'



### Classes ###

class Configurator(Emitter, JsonEmitter):
    '''
    Create a layout file for the configurator
    '''

    def __init__(self, control):
        '''
        Emitter initialization

        @param control: ControlStage object, used to access data from other stages
        '''
        Emitter.__init__(self, control)
        JsonEmitter.__init__(self)

        self.output_file = "configurator.json"

    def command_line_args(self, args):
        '''
        Group parser for command line arguments

        @param args: Name space of processed arguments
        '''

        self.output_file = args.configurator_output

    def command_line_flags(self, parser):
        '''
        Group parser for command line options

        @param parser: argparse setup object
        '''

        # Create new option group
        group = parser.add_argument_group('\033[1mInternal State Emitter Configuration\033[0m')

        group.add_argument('--configurator-output', type=str, default=self.output_file,
            help="Specify generated configurator layout output.\n"
            "\033[1mDefault\033[0m: {0}\n".format(self.output_file)
        )

    def check_file(self, filepath):
        '''
        Check file, make sure it exists

        @param filepath: File path

        @returns: True if path exists
        '''
        if not os.path.isfile(filepath):
            print("{} Did not generate: {}".format(
                ERROR,
                os.path.abspath(filepath),
            ))

    def output(self):
        '''
        Final Stage of Emitter

        Write json file
        '''

        # Generate Json Output
        self.generate_json(self.output_file)

        # Make sure files were generated
        self.check_file(self.output_file)


    def process(self):
        '''
        Emitter Processing

        Generate json
        '''

        scancode_positions = self.control.stage('DataAnalysisStage').scancode_positions
        pixel_positions = self.control.stage('DataAnalysisStage').pixel_positions
        pixel_display_params = self.control.stage('DataAnalysisStage').pixel_display_params
        trigger_index_reduced = self.control.stage('DataAnalysisStage').trigger_index_reduced
        full_context = self.control.stage('DataFinalizationStage').full_context
        animations = full_context.query('DataAssociationExpression', 'Animation')
        #animation_settings = self.control.stage('DataAnalysisStage').animation_settings

        mappings = {}
        key_w = 4
        key_h = 4

        header_json = {}
        matrix_json = []
        leds_json = []
        custom_json = {} # TODO
        animation_json = {}
        macro_json = {} # TODO

        import datetime
        header_json['Name'] = 'Kiibohd' # TODO
        header_json['Variant'] = 'standard' # TODO
        header_json['Layout'] = 'Standard' # TODO
        header_json['Base'] = 'Standard' # TODO
        header_json['Version'] = '0.1.0'
        header_json['Author'] = ''
        header_json['KLL'] = self.control.short_version
        header_json['Date'] = datetime.datetime.today().strftime('%Y-%m-%d')
        header_json['Generator'] = 'Kll Emitter'

        for trigger in trigger_index_reduced:
            for (layer, expr) in enumerate(trigger):
                trigger = str(expr.triggers[0][0][0])
                result = expr.results[0][0][0]

                from kll.common.id import HIDId
                if isinstance(result, HIDId):
                    result = result.name().upper()
                else:
                    result = "#:{}".format(str(result))

                action = {
                    'key': result,
                    'label': result,
                }
                if not trigger in mappings:
                    mappings[trigger] = {}
                mappings[trigger][str(layer)] = action

        for id in sorted(scancode_positions.keys()):
            switch = scancode_positions[id]
            item = OrderedDict()
            item['code'] = "0x{:02X}".format(id)
            item['x'] = int(switch['x'] / pixel_display_params['UnitSize']) * key_w # FIXME
            item['y'] = int((-switch['y']+0) / pixel_display_params['UnitSize']) * key_h # FIXME
            item['w'] = None
            item['h'] = None
            item['layers'] = mappings.get("S{:03}".format(id), {})
            matrix_json.append(item)

        for id in sorted(pixel_positions.keys()):
            pixel = pixel_positions[id]
            item = OrderedDict()
            item['id'] = id
            if 'ScanCode' in pixel:
                item['scanCode'] = "0x{:02X}".format(pixel['ScanCode'])
            item['x'] = pixel['x']
            item['y'] = -pixel['y'] + 0 # Avoid -0
            leds_json.append(item)

        for key, association in animations.data.items():
            name = key.replace("A[", "").replace("]", "")
            animation_settings = str(association.value)
            animation_json[name] = {
                'type': 'custom',
                'settings': animation_settings,
                'frames': [], # TODO
            }

        self.json_dict['header'] = header_json
        self.json_dict['matrix'] = matrix_json
        self.json_dict['leds'] = leds_json
        self.json_dict['custom'] = custom_json
        self.json_dict['animations'] = animation_json
        self.json_dict['macros'] = macro_json
