#!/usr/bin/env python3
'''
KLL Kiibohd .h/.c File Emitter
'''

# Copyright (C) 2016-2019 by Jacob Alexander
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
import sys
import math

from datetime import date

from kll.common.emitter import JsonEmitter, Emitter, TextEmitter
from kll.common.id import (
    AnimationId,
    CapId,
    HIDId,
    LayerId,
    NoneId,
    ScanCodeId,
    TriggerId,
    UTF8Id
)

from layouts.emitter import basic_c_defines



### Decorators ###

# Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'



### Classes ###

class Kiibohd(Emitter, TextEmitter, JsonEmitter):
    '''
    Kiibohd .h file emitter for KLL
    '''

    # List of required capabilities
    required_capabilities = {
        'A': 'animationIndex',
        'CONS': 'consCtrlOut',
        'NONE': 'noneOut',
        'SYS': 'sysCtrlOut',
        'USB': 'usbKeyOut',
        'Layer': 'layerShift',
        'LayerShift': 'layerShift',
        'LayerLatch': 'layerLatch',
        'LayerLock': 'layerLock',
    }

    # List of optional capabilities
    # If any of these are used, and not available, the compiler will fail
    optional_capabilities = {
        'UTF8State': 'unicode_state',
        'UTF8Text': 'unicode_text',
    }

    # Code to capability mapping
    code_to_capability = {
        'Animation': 'animationIndex',
        'Capability': None,
        'ConsCode': 'consCtrlOut',
        'Layer': 'layerShift',
        'LayerShift': 'layerShift',
        'LayerLatch': 'layerLatch',
        'LayerLock': 'layerLock',
        'None': 'none',
        'ScanCode': None,
        'SysCode': 'sysCtrlOut',
        'USBCode': 'usbKeyOut',
    }

    # Optional required capabilities
    # Used mostly for animationIndex
    optional_required_capabilities = [
        'A',
    ]

    def __init__(self, control):
        '''
        Emitter initialization

        @param control: ControlStage object, used to access data from other stages
        '''
        Emitter.__init__(self, control)
        TextEmitter.__init__(self)
        JsonEmitter.__init__(self)

        # Script directory (relative location to default templates)
        kll_module_dir = os.path.abspath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..')
        )
        template_dir = os.path.join(kll_module_dir, 'templates')

        # Defaults
        self.map_template = os.path.join(template_dir, "kiibohdKeymap.h")
        self.hid_template = os.path.join(template_dir, "kiibohd_usb_hid.h")
        self.pixel_template = os.path.join(template_dir, "kiibohdPixelmap.c")
        self.def_template = os.path.join(template_dir, "kiibohdDefs.h")
        self.map_output = "generatedKeymap.h"
        self.hid_output = "usb_hid.h"
        self.pixel_output = "generatedPixelmap.c"
        self.def_output = "kll_defs.h"
        self.json_output = "kll.json"
        self.kiibohd_debug = False
        self.enable_capv2 = False

        # Convenience
        self.capabilities = None
        self.capabilities_index = dict()

        self.use_pixel_map = False  # Default to disabling PixelMap (auto-enables if needed)

        # Signal erroring due to an issue
        # We may not want to exit immediately as we could find other potential issues that need fixing
        self.error_exit = False

        # Fill dictionary
        self.fill_dict = {}

        # USB Code Lookup for header emitter
        self.usb_code_lookup = None
        self.usb_c_defines = None

        # UTF-8 String List
        self.utf8_strings = dict()

    def command_line_args(self, args):
        '''
        Group parser for command line arguments

        @param args: Name space of processed arguments
        '''
        self.def_template = args.def_template
        self.map_template = args.map_template
        self.hid_template = args.hid_template
        self.pixel_template = args.pixel_template
        self.def_output = args.def_output
        self.map_output = args.map_output
        self.hid_output = args.hid_output
        self.pixel_output = args.pixel_output
        self.json_output = args.json_output
        self.kiibohd_debug = args.kiibohd_debug
        self.enable_capv2 = args.enable_capv2

    def command_line_flags(self, parser):
        '''
        Group parser for command line options

        @param parser: argparse setup object
        '''
        # Create new option group
        group = parser.add_argument_group('\033[1mKiibohd Emitter Configuration\033[0m')

        group.add_argument('--def-template', type=str, default=self.def_template,
            help="Specify KLL define .h file template.\n"
            "\033[1mDefault\033[0m: {0}\n".format(self.def_template)
        )
        group.add_argument('--map-template', type=str, default=self.map_template,
            help="Specify KLL map .h file template.\n"
            "\033[1mDefault\033[0m: {0}\n".format(self.map_template)
        )
        group.add_argument('--hid-template', type=str, default=self.hid_template,
            help="Specify USB HID Lookup .h file template.\n"
            "\033[1mDefault\033[0m: {0}\n".format(self.hid_template)
        )
        group.add_argument('--pixel-template', type=str, default=self.pixel_template,
            help="Specify KLL pixel map .c file template.\n"
            "\033[1mDefault\033[0m: {0}\n".format(self.pixel_template)
        )
        group.add_argument('--def-output', type=str, default=self.def_output,
            help="Specify KLL define .h file output.\n"
            "\033[1mDefault\033[0m: {0}\n".format(self.def_output)
        )
        group.add_argument('--map-output', type=str, default=self.map_output,
            help="Specify KLL map .h file output.\n"
            "\033[1mDefault\033[0m: {0}\n".format(self.map_output)
        )
        group.add_argument('--hid-output', type=str, default=self.hid_output,
            help="Specify USB HID Lookup .h file output.\n"
            "\033[1mDefault\033[0m: {0}\n".format(self.hid_output)
        )
        group.add_argument('--pixel-output', type=str, default=self.pixel_output,
            help="Specify KLL map .h file output.\n"
            "\033[1mDefault\033[0m: {0}\n".format(self.pixel_output)
        )
        group.add_argument('--json-output', type=str, default=self.json_output,
            help="Specify json output file for settings dictionary.\n"
            "\033[1mDefault\033[0m: {0}\n".format(self.json_output)
        )
        group.add_argument(
            '--kiibohd-debug',
            action='store_true',
            default=self.kiibohd_debug,
            help="Show debug info from kiibohd emitter.",
        )
        group.add_argument(
            '--enable-capv2',
            action='store_true',
            default=self.enable_capv2,
            help="Enable v2 of capabilities (requires firmware support).",
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

        Generate desired outputs from templates
        '''
        if self.kiibohd_debug:
            print("-- Generating --")
            print(os.path.abspath(self.def_output))
            print(os.path.abspath(self.map_output))
            print(os.path.abspath(self.hid_output))
            if self.use_pixel_map:
                print(os.path.abspath(self.pixel_output))
            print(os.path.abspath(self.json_output))

        # Load define template and generate
        self.load_template(self.def_template)
        self.generate(self.def_output)

        # Load keymap template and generate
        self.load_template(self.map_template)
        self.generate(self.map_output)

        # Load hid lookup template and generate
        self.load_template(self.hid_template)
        self.generate(self.hid_output)

        # Load pixelmap template and generate
        if self.use_pixel_map:
            self.load_template(self.pixel_template)
            self.generate(self.pixel_output)

        # Remove file if it exists, and create an empty file
        else:
            open(self.pixel_output, 'w').close()

        # Generate Json Output
        self.generate_json(self.json_output)

        # Make sure files were generated
        self.check_file(self.def_output)
        self.check_file(self.map_output)
        if self.use_pixel_map:
            self.check_file(self.pixel_output)
        self.check_file(self.json_output)

    def byte_split(self, number, total_bytes):
        '''
        Converts and integer number into a defined length list of byte sized integers

        Used to convert a large number into 8 bit chunks so it can fit inside a C byte array.
        Little endian byte order is used.
        '''
        # If negative, used signed mode
        # In general we output unsigned, but in some cases we need a negative
        # For these cases each context can handle the signed integers
        negative = number < 0 and True or False

        # XXX Yes, little endian from how the uC structs work
        byte_form = number.to_bytes(
            total_bytes,
            byteorder='little',
            signed=negative,
        )
        # Convert into a list of strings
        return ["{0}".format(int(byte)) for byte in byte_form]

    def result_combo_conversion(self, schedule_list, combo=None):
        '''
        Converts a result combo (list of Ids) to the C array string format

        @param combo: List of Ids/capabilities
        @return: C array string format
        '''
        # Lookup default_schedule
        default_schedule = None
        for index, key in enumerate(sorted(schedule_list.keys())):
            if key == "":
                default_schedule = index
                break

        # If result_elem is None, assume 0-length USB code
        if combo is None:
            # <single element>, <usbCodeSend capability>, <schedule>, <USB Code 0x00>
            return "1, {0}, {1}, 0x00".format(
                self.capabilities_index[self.required_capabilities['USB']],
                default_schedule,
            )

        # Determine length of combo
        output = "{0}".format(len(combo))

        # Iterate over each trigger identifier
        for index, identifier in enumerate(combo):
            # Lookup capability index
            cap = "/* XXX INVALID XXX */"
            schedule = "/* XXX INVALID SCHEDULE XXX*/"

            schedule_key = identifier.strSchedule()
            for index, key in enumerate(sorted(schedule_list.keys())):
                if key == schedule_key:
                    schedule = index
                    break

            # HIDId
            if isinstance(identifier, HIDId):
                # Lookup capability index
                cap_index = self.capabilities_index[self.required_capabilities[identifier.second_type]]
                cap_arg = ""

                # Check for a split argument (e.g. Consumer codes)
                if identifier.width() > 1:
                    cap_arg = ", ".join(
                            self.byte_split(identifier.get_uid(), identifier.width())
                    )

                # Do not lookup hid define if USB Keycode and >= 0xF0
                # These are unofficial HID codes, report error
                elif identifier.second_type == 'USB' and identifier.get_uid() >= 0xF0:
                    print("{0} '{1}' Invalid USB HID code, missing FuncMap layout (e.g. stdFuncMap, lcdFuncMap)".format(
                            ERROR,
                            identifier
                    ))
                    cap_arg = "/* XXX INVALID {0} */".format(identifier)
                    self.error_exit = True

                # Otherwise use the C define instead of the number (increases readability)
                else:
                    try:
                        cap_arg = self.usb_code_lookup[identifier.type][identifier.get_hex_str()]
                    except KeyError as err:
                        print("{0} {1} HID lookup kll bug...please report.".format(ERROR, err))
                        self.error_exit = True

                cap = "{0}, {1}, {2}".format(cap_index, schedule, cap_arg)

            # None - Is instance of CapId, so has to be first
            elif isinstance(identifier, NoneId):
                # <single element>, <usbCodeSend capability>, <USB Code 0x00>
                return "1, {0}, {1}, 0x00".format(
                    self.capabilities_index[self.required_capabilities['USB']],
                    schedule,
                )

            # Capability
            elif isinstance(identifier, CapId):
                # Lookup capability index
                cap_index = self.capabilities_index[identifier.name]

                # Check if we need to add arguments to capability
                if identifier.total_arg_bytes(self.capabilities.data) > 0:
                    cap_lookup = self.capabilities.data[identifier.name].association
                    cap = "{0}, {1}".format(
                        cap_index,
                        schedule,
                    )
                    for arg, lookup in zip(identifier.arg_list, cap_lookup.arg_list):
                        cap += ", "
                        cap += ", ".join(self.byte_split(arg.value, lookup.width))

                # Otherwise, no arguments necessary
                else:
                    cap = "{0}, {1}".format(
                        cap_index,
                        schedule,
                    )

            # AnimationId
            elif isinstance(identifier, AnimationId):
                # Lookup capability index
                cap_index = self.capabilities_index[self.required_capabilities[identifier.second_type]]
                cap_arg = ""

                # Lookup animation setting index
                settings_index = 0
                lookup_id = "{0}".format(identifier)
                animation_settings_list = self.control.stage('DataAnalysisStage').animation_settings_list
                if lookup_id not in animation_settings_list:
                    print("{0} Unknown animation '{1}'".format(ERROR, lookup_id))
                    self.error_exit = True
                else:
                    settings_index = animation_settings_list.index(lookup_id)

                # Check for a split argument (e.g. Consumer codes)
                if identifier.width() > 1:
                    cap_arg = ", ".join(
                            self.byte_split(settings_index, identifier.width())
                    )

                cap = "{0}, {1}, {2}".format(cap_index, schedule, cap_arg)

            # LayerId
            elif isinstance(identifier, LayerId):
                # Lookup capabilityIndex
                cap_index = self.capabilities_index[self.required_capabilities[identifier.type]]
                cap_arg = ""
                layer_number = identifier.uid

                # Check for a split argument (e.g. Consumer codes)
                if identifier.width() > 1:
                    cap_arg = ", ".join(
                            self.byte_split(layer_number, identifier.width())
                    )

                cap = "{0}, {1}, {2}".format(cap_index, schedule, cap_arg)

            # UTF8Id
            elif isinstance(identifier, UTF8Id):
                # Lookup capabilityIndex
                if self.optional_capabilities[identifier.type] not in self.capabilities_index.keys():
                    self.error_exit = True
                    print("{0} Optional capability '{1}' for '{2}' was used and is missing!".format(
                        ERROR,
                        identifier.type,
                        'UTF8Id',
                    ))
                    return ""

                cap_index = self.capabilities_index[self.optional_capabilities[identifier.type]]
                cap_arg = ""
                string_number = self.utf8_strings[identifier.uid]

                # Check for a split argument (e.g. Consumer codes)
                if identifier.width() > 1:
                    cap_arg = ", ".join(
                            self.byte_split(string_number, identifier.width())
                    )

                cap = "{0}, {1}".format(cap_index, cap_arg)

            # Unknown/Invalid Id
            else:
                print("{0} Unknown identifier({1}) -> {2}".format(
                    ERROR,
                    identifier.__class__.__name__,
                    identifier,
                ))
                self.error_exit = True

            # Generate identifier string for element of the combo
            output += ", {0}".format(
                    cap,
            )

        return output

    def layer_type_lookup(self, layer_type):
        '''
        Lookup enumeration name for layer type

        Returns an empty string if unknown

        @param layer_type: Type of layer
        @return: Enum name for layer type
        '''
        output = ""
        if layer_type == 'LayerShift':
            output = " | ScheduleType_Shift"
        elif layer_type == 'LayerLatch':
            output = " | ScheduleType_Latch"
        elif layer_type == 'LayerLock':
            output = " | ScheduleType_Lock"

        return output

    def schedule_param_lookup(self, param, freq, parent):
        '''
        Convert schedule to schedule lookup id

        .time = <time>, .state = <schedule>
        .time = <time>, .analog = <level>
        .time = <time>, .index = <index>
        @param param:  Schedule element to do lookup on
        @param freq:   CPU frequency to calculate ticks at
        @param parent: Parent element, used to determine if this is a Layer event
        '''
        output = ""

        # If state is set, add parameter
        if param.state is not None or param == 0:
            # Analog
            if param.isAnalog():
                output += ".analog = {}".format(param.scheduleLookup())
            elif param.isIndex():
                output += ".index = {}".format(param.scheduleLookup())
            else:
                output += ".state = "
                output += "ScheduleType_{}".format(param.scheduleLookup()[1])
                output += self.layer_type_lookup(parent.type)

            output += ", "
        # If state is not set, set as a generic
        else:
            output += ".state = ScheduleType_Gen, "

        # Ignore unused param
        if param.timing is not None:
            ms, ticks = param.timing.to_ms_ticks(freq)
            time = "{{ {}, {} }}".format(int(ms), int(ticks))

            output += ".time = {}, ".format(time)

        return output

    def trigger_combo_conversion(self, schedule_list, combo):
        '''
        Converts a trigger combo (list of Ids) to the C array string format

        @param combo: List of Ids/capabilities
        @return: C array string format
        '''

        # Determine length of combo
        output = "{0}".format(len(combo))

        # Iterate over each trigger identifier
        for index, identifier in enumerate(combo):
            # Construct trigger combo
            trigger = "/* XXX INVALID XXX */"

            # TODO Add support for Analog keys
            # TODO Add support for non-press states
            uid = identifier.get_uid()
            trigger_type = "/* XXX INVALID TYPE XXX */"

            schedule_key = identifier.strSchedule()
            state = "/* XXX INVALID STATE INDEX */"
            for index, key in enumerate(sorted(schedule_list.keys())):
                if key == schedule_key:
                    state = index
                    break

            no_error = False
            # ScanCodeId
            if isinstance(identifier, ScanCodeId):
                no_error = True

                # Determine the type and adjust uid
                if uid < 256:
                    trigger_type = "TriggerType_Switch1"

                elif uid < 512:
                    trigger_type = "TriggerType_Switch2"
                    uid -= 256

                elif uid < 768:
                    trigger_type = "TriggerType_Switch3"
                    uid -= 512

                elif uid < 1024:
                    trigger_type = "TriggerType_Switch4"
                    uid -= 768

                else:
                    no_error = False

            # LayerId
            elif isinstance(identifier, LayerId):
                no_error = True

                # Determine the type and adjust uid
                if uid < 256:
                    trigger_type = "TriggerType_Layer1"

                elif uid < 512:
                    trigger_type = "TriggerType_Layer2"
                    uid -= 256

                elif uid < 768:
                    trigger_type = "TriggerType_Layer3"
                    uid -= 512

                elif uid < 1024:
                    trigger_type = "TriggerType_Layer4"
                    uid -= 768

                else:
                    no_error = False

            # AnimationId
            elif isinstance(identifier, AnimationId):
                no_error = True

                # Retrieve uid of animation
                animation_uid_lookup = self.control.stage('DataAnalysisStage').animation_uid_lookup
                uid = animation_uid_lookup[identifier.name]

                # Determine the type and adjust uid
                if uid < 256:
                    trigger_type = "TriggerType_Animation1"

                elif uid < 512:
                    trigger_type = "TriggerType_Animation2"
                    uid -= 256

                elif uid < 768:
                    trigger_type = "TriggerType_Animation3"
                    uid -= 512

                elif uid < 1024:
                    trigger_type = "TriggerType_Animation4"
                    uid -= 768

                else:
                    no_error = False

            # IndCode HIDId
            elif isinstance(identifier, HIDId) and identifier.type == 'IndCode':
                no_error = True

                # Determine the type and adjust uid
                if uid < 256:
                    trigger_type = "TriggerType_LED1"

                else:
                    no_error = False

            # TriggerId
            elif isinstance(identifier, TriggerId):
                no_error = True

                # No need to decode as a TriggerId has all the necessary information ready
                trigger_type = identifier.idcode

                # However, for the types that are known, use the full name
                lookup = {
                    0x00: 'TriggerType_Switch1',
                    0x01: 'TriggerType_Switch2',
                    0x02: 'TriggerType_Switch3',
                    0x03: 'TriggerType_Switch4',
                    0x04: 'TriggerType_LED1',
                    0x05: 'TriggerType_Analog1',
                    0x06: 'TriggerType_Analog2',
                    0x07: 'TriggerType_Analog3',
                    0x08: 'TriggerType_Analog4',
                    0x09: 'TriggerType_Layer1',
                    0x0A: 'TriggerType_Layer2',
                    0x0B: 'TriggerType_Layer3',
                    0x0C: 'TriggerType_Layer4',
                    0x0D: 'TriggerType_Animation1',
                    0x0E: 'TriggerType_Animation2',
                    0x0F: 'TriggerType_Animation3',
                    0x10: 'TriggerType_Animation4',
                    0x11: 'TriggerType_Sleep1',
                    0x12: 'TriggerType_Resume1',
                    0x13: 'TriggerType_Inactive1',
                    0x14: 'TriggerType_Active1',
                    0x15: 'TriggerType_Rotation1',
                    0xFF: 'TriggerType_Debug',
                }
                if trigger_type in lookup.keys():
                    trigger_type = lookup[trigger_type]

                uid = identifier.uid

            # Unknown/Invalid Id
            else:
                print("{0} Unknown identifier -> {1}".format(ERROR, identifier))
                self.error_exit = True

            # Set trigger if there wasn't an error
            if no_error:
                # <type>, <state>, <uid>
                trigger = "{0}, {1}, 0x{2:02X}".format(trigger_type, state, uid)

            # Generate identifier string for element of the combo
            output += ", {0}".format(
                    trigger,
            )

        return output

    def animation_frameset(self, name, aniframe):
        '''
        Generates an animation frame set, and may also generate filler frames if necessary

        @param name:     Name for animation
        @param aniframe: Animation frame data
        '''
        # Frame set header
        self.fill_dict['AnimationFrames'] += "//// {0} Animation Frame Set ////\n".format(
            name
        )
        self.fill_dict['AnimationFrames'] += "const uint8_t *{0}_frames[] = {{".format(
            name
        )

        # Generate entry for each of the frames (even blank inbetweens)
        for index in range(1, aniframe + 1):
            self.fill_dict['AnimationFrames'] += "\n\t{0}_frame{1},".format(
                name,
                index
            )
        self.fill_dict['AnimationFrames'] += "\n\t0\n};\n\n\n"

    def animation_modifier_set(self, animation, name):
        '''
        Check if false or None and set to 0, otherwise as argument

        name is the name of the animation modifier
        '''
        modifier = animation.getModifier(name)

        # Simple modifier
        simple_mods = ['pos', 'loops', 'framedelay', 'divmask', 'frame']
        if name in simple_mods:
            if not modifier or modifier is None:
                return 0
            return modifier

        if name == 'pfunc':
            if not modifier or modifier is None or modifier == 'off':
                return 0
            if modifier.arg == 'interp':
                return 1
            print("{0} '{1}:{2}' is unsupported".format(WARNING, name, modifier))
            return 0

        if name == 'ffunc':
            if not modifier or modifier is None or modifier == 'off':
                return 0
            print("{0} '{1}:{2}' is unsupported".format(WARNING, name, modifier))
            return 0

        if name == 'replace':
            if not modifier or modifier is None or modifier.arg == 'stack':
                return 0
            if modifier.arg == 'basic':
                return 1
            if modifier.arg == 'all':
                return 2
            if modifier.arg == 'state':
                return 3
            if modifier.arg == 'clear':
                return 4
            if modifier.arg == 'clearactive':
                return 5
            print("{0} '{1}:{2}' is unsupported".format(WARNING, name, modifier))
            return 0

        print("{0} '{1}:{2}' is unsupported".format(WARNING, name, modifier))
        return 0

    def animation_settings_entry(self, animation, animation_name, count, additional=False):
        '''
        Build an animation settings string entry
        '''
        # For each animation index store the default settings
        # <triggerguide> - Set to 1 if start in default settings
        a_start = 1
        a_pause = 1
        a_stop = 1
        a_single = 1
        if not animation.getModifier('start'):
            a_start = 0
        if not animation.getModifier('pause'):
            a_pause = 0
        if not animation.getModifier('stop'):
            a_stop = 0
        if not animation.getModifier('single'):
            a_single = 0
        # <index>        - Animation id (Animation__<name>)
        a_name = animation_name
        # <pos>          - Frame position
        a_pos = self.animation_modifier_set(animation, 'pos')
        # <subpos>       - Sub frame position
        a_subpos = 0
        # <loops>        - Number of loops, set to 0 for infinite
        a_loops = self.animation_modifier_set(animation, 'loops')
        if animation.getModifier('loop'):
            a_loops = 0
        # <framedelay>   - Frame delay
        a_framedelay = self.animation_modifier_set(animation, 'framedelay')
        # <frameoption>  - Frame option
        a_frameoption = []
        # <framestretch> - frameoption Frame stretch
        if animation.getModifier('framestretch'):
            a_frameoption.append("PixelFrameOption_FrameStretch")
        # <ffunc>        - Frame function index
        a_ffunc = self.animation_modifier_set(animation, 'ffunc')
        # <pfunc>        - Pixel function index
        a_pfunc = self.animation_modifier_set(animation, 'pfunc')
        # <replace>      - Replacement mode
        a_replace = self.animation_modifier_set(animation, 'replace')
        # <state>        - Animation play state (defaults to Paused if not set)
        if a_pause == 1:
            a_state = "AnimationPlayState_Pause"
        elif a_stop == 1:
            a_state = "AnimationPlayState_Stop"
        elif a_single == 1:
            a_state = "AnimationPlayState_Single"
        elif a_start == 1:
            a_state = "AnimationPlayState_Start"
        else:
            a_state = "AnimationPlayState_Pause"

        # Determine what to set a_frameoption
        a_frameoption_str = "PixelFrameOption_None"
        for option in a_frameoption:
            if a_frameoption_str == "PixelFrameOption_None":
                a_frameoption_str = option
            else:
                a_frameoption_str += " | {}".format(option)

        # Do not set a_initial if this is an additional (non-default) animation settings entry
        a_initial = 1
        if additional:
            a_initial = 0

        # Add autostart flag if this animation has the start flag and is an initial animation
        if a_initial == 1 and a_start == 1:
            a_state += " | AnimationPlayState_AutoStart"

        return "\n\t{{ (TriggerMacro*){2}, {3}, /*{0} {1}*/\n\t\t{4}, {5}, {6}, {7}, {8}, {9}, {10}, {11}, {12}}},".format(
            count,
            animation,
            # AnimationStackElement
            a_initial,
            a_name,
            a_pos,
            a_subpos,
            a_loops,
            a_framedelay,
            a_frameoption_str,
            a_ffunc,
            a_pfunc,
            a_replace,
            a_state,
        )

    def generateGammaTable(self, gamma=2.2):
        '''
        Generate an 8-bit gamma table

        Based off of a suggestion: https://github.com/kiibohd/controller/issues/255

        TODO (HaaTa): Handle non-8bit as well
        '''
        max_in = 255
        max_out = 255
        return [round(math.pow(i/max_in, gamma) * max_out) for i in range(0,max_in+1) ]

    def process(self):
        '''
        Emitter Processing

        Takes KLL datastructures and Analysis results then populates the fill_dict
        The fill_dict is used populate the template files.
        '''
        # Acquire Datastructures
        early_contexts = self.control.stage('DataOrganizationStage').contexts
        full_context = self.control.stage('DataFinalizationStage').full_context

        reduced_contexts = self.control.stage('DataAnalysisStage').reduced_contexts  # Default + Partial

        trigger_index = self.control.stage('DataAnalysisStage').trigger_index
        trigger_index_reduced = self.control.stage('DataAnalysisStage').trigger_index_reduced
        result_index = self.control.stage('DataAnalysisStage').result_index
        trigger_index_reduced_lookup = self.control.stage('DataAnalysisStage').trigger_index_reduced_lookup
        trigger_index_lookup = self.control.stage('DataAnalysisStage').trigger_index_lookup
        result_index_lookup = self.control.stage('DataAnalysisStage').result_index_lookup
        min_scan_code = self.control.stage('DataAnalysisStage').min_scan_code
        max_scan_code = self.control.stage('DataAnalysisStage').max_scan_code
        trigger_lists = self.control.stage('DataAnalysisStage').trigger_lists
        interconnect_scancode_offsets = self.control.stage('DataAnalysisStage').interconnect_scancode_offsets
        interconnect_pixel_offsets = self.control.stage('DataAnalysisStage').interconnect_pixel_offsets

        rotation_map = self.control.stage('DataAnalysisStage').rotation_map
        schedule_list = self.control.stage('DataAnalysisStage').schedule_list

        scancode_positions = self.control.stage('DataAnalysisStage').scancode_positions
        pixel_positions = self.control.stage('DataAnalysisStage').pixel_positions
        pixel_display_mapping = self.control.stage('DataAnalysisStage').pixel_display_mapping
        pixel_display_params = self.control.stage('DataAnalysisStage').pixel_display_params

        animation_settings = self.control.stage('DataAnalysisStage').animation_settings
        animation_settings_orig = self.control.stage('DataAnalysisStage').animation_settings_orig
        animation_settings_list = self.control.stage('DataAnalysisStage').animation_settings_list
        animation_uid_lookup = self.control.stage('DataAnalysisStage').animation_uid_lookup

        utf8_strings = self.control.stage('DataAnalysisStage').utf8_strings
        self.utf8_strings = utf8_strings

        # Build full list of C-Defines
        layout_mgr = self.control.stage('PreprocessorStage').layout_mgr
        self.usb_c_defines = basic_c_defines(layout_mgr.get_layout('default'))
        self.usb_code_lookup = {
            'USBCode': dict([(t[1], t[0]) for t in self.usb_c_defines[0]]),
            'IndCode': dict([(t[1], t[0]) for t in self.usb_c_defines[1]]),
            'SysCode': dict([(t[1], t[0]) for t in self.usb_c_defines[2]]),
            'ConsCode': dict([(t[1], t[0]) for t in self.usb_c_defines[3]]),
        }

        # Setup json datastructures
        animation_id_json = dict()
        animation_settings_json = dict()
        animation_settings_index_json = []
        pixel_id_json = dict()
        scancode_json = dict()
        capabilities_json = dict()
        defines_json = dict()
        layers_json = dict()

        # Build string list of compiler arguments
        compilerArgs = ""
        for arg in sys.argv:
            if "--" in arg or ".py" in arg:
                compilerArgs += "//    {0}\n".format(arg)
            else:
                compilerArgs += "//      {0}\n".format(arg)

        # Build a string of modified files, if any
        gitChangesStr = "\n"
        if len(self.control.git_changes) > 0:
            for gitFile in self.control.git_changes:
                gitChangesStr += "//    {0}\n".format(gitFile)
        else:
            gitChangesStr = "    None\n"

        def get_context_name(context_type, contexts=None):
            '''
            Retrieve context names and paths

            @param context_type: Name of context type

            @return: List of name and context paths
            '''
            if contexts is None:
                contexts = early_contexts[context_type].query_contexts('AssignmentExpression', 'Array')
            output = []
            for sub in contexts:
                name = "None"
                if 'Name' in sub[0].data.keys():
                    name = sub[0].data['Name'].value
                else:
                    print("{0} 'Name' field missing from '{1}' context".format(WARNING, context_type))
                path = sub[1].parent.path
                output.append((name, path))
            return output

        # Prepare BaseLayout and Layer Info
        configLayoutInfo = ""
        if 'ConfigurationContext' in early_contexts.keys():
            for pair in get_context_name('ConfigurationContext'):
                configLayoutInfo += "//    {0}\n//      {1}\n".format(pair[0], pair[1])

        genericLayoutInfo = ""
        if 'GenericContext' in early_contexts.keys():
            for pair in get_context_name('GenericContext'):
                genericLayoutInfo += "//    {0}\n//      {1}\n".format(pair[0], pair[1])

        baseLayoutInfo = ""
        if 'BaseMapContext' in early_contexts.keys():
            for pair in get_context_name('BaseMapContext'):
                baseLayoutInfo += "//    {0}\n//      {1}\n".format(pair[0], pair[1])

        defaultLayerInfo = ""
        if 'DefaultMapContext' in early_contexts.keys():
            for pair in get_context_name('DefaultMapContext'):
                defaultLayerInfo += "//    {0}\n//      {1}\n".format(pair[0], pair[1])

        partialLayersInfo = ""
        partial_context_list = [
                (item[1].layer, item[0])
                for item in early_contexts.items()
                if 'PartialMapContext' in item[0]
        ]
        for layer, tag in sorted(partial_context_list, key=lambda x: x[0]):
            partialLayersInfo += "//    Layer {0}\n".format(layer + 1)
            contexts = early_contexts[tag].query_contexts('AssignmentExpression', 'Array')
            for pair in get_context_name('PartialMapContext', contexts):
                partialLayersInfo += "//     {0}\n//       {1}\n".format(pair[0], pair[1])

        ## Information ##
        self.fill_dict['Information'] = "// This file was generated by the kll compiler, DO NOT EDIT.\n"
        self.fill_dict['Information'] += "// Generation Date:    {0}\n".format(date.today())
        self.fill_dict['Information'] += "// KLL Emitter:        {0}\n".format(
                self.control.stage('CompilerConfigurationStage').emitter
        )
        self.fill_dict['Information'] += "// KLL Version:        {0}\n".format(self.control.version)
        self.fill_dict['Information'] += "// KLL Git Changes:{0}".format(gitChangesStr)
        self.fill_dict['Information'] += "// Compiler arguments:\n{0}".format(compilerArgs)
        self.fill_dict['Information'] += "//\n"
        self.fill_dict['Information'] += "// - Configuration File -\n{0}".format(configLayoutInfo)
        self.fill_dict['Information'] += "// - Generic Files -\n{0}".format(genericLayoutInfo)
        self.fill_dict['Information'] += "// - Base Layer -\n{0}".format(baseLayoutInfo)
        self.fill_dict['Information'] += "// - Default Layer -\n{0}".format(defaultLayerInfo)
        self.fill_dict['Information'] += "// - Partial Layers -\n{0}".format(partialLayersInfo)

        ## Defines ##
        self.fill_dict['Defines'] = ""

        # Iterate through defines and lookup the variables
        defines = full_context.query('NameAssociationExpression', 'Define')
        variables = full_context.query('AssignmentExpression', 'Variable')
        for dkey, dvalue in sorted(defines.data.items()):
            if dvalue.name in variables.data.keys():
                # TODO Handle arrays
                if not isinstance(variables.data[dvalue.name].value, list):
                    value = variables.data[dvalue.name].value.replace('\n', ' \\\n')
                    self.fill_dict['Defines'] += "\n#define {0} {1}".format(
                        dvalue.association,
                        value,
                    )
                    defines_json[dvalue.name] = {
                        'name' : dvalue.association,
                        'value' : value,
                    }
            else:
                print("{0} '{1}' not defined...".format(WARNING, dvalue.name))

        ## Schedules ##
        # Make sure CPU_Frequency variable is set
        cpu_freq = 0
        cpu_freq = int(variables.data['CPU_Frequency'].value) if 'CPU_Frequency' in variables.data else 0
        if 'CPU_Frequency' not in variables.data:
            print("{} 'CPU_Frequency' should be set, and should be the same value as F_CPU".format(WARNING))

        self.fill_dict['StateScheduleParams'] = ""
        self.fill_dict['StateSchedules'] = "const ScheduleLookup ScheduleLookupTable = {\n"
        self.fill_dict['StateSchedules'] += "\t.count = {},\n".format(len(schedule_list))
        self.fill_dict['StateSchedules'] += "\t.schedule = {\n"
        schedule_index = 0
        for key, value in sorted(schedule_list.items()):
            # Build schedule parameter list
            self.fill_dict['StateScheduleParams'] += "const ScheduleParam schedule{}_elems[] = {{ ".format(
                schedule_index
            )
            num_schedules = 0
            if value.parameters is not None:
                for elem in value.parameters:
                    self.fill_dict['StateScheduleParams'] += "{{ {}}}, ".format(self.schedule_param_lookup(elem, cpu_freq, value))
                num_schedules = len(value.parameters)
            # Generic trigger
            else:
                output_schedule = "ScheduleType_Gen{}".format(self.layer_type_lookup(value.type))
                self.fill_dict['StateScheduleParams'] += "{{ .state = {}, }}, ".format(output_schedule)
                num_schedules = 1
            self.fill_dict['StateScheduleParams'] += "};\n"

            # Build schedule
            self.fill_dict['StateSchedules'] += "\t\t{{ (ScheduleParam*)schedule{0}_elems, {1} }}, // {2}\n".format(
                schedule_index,
                num_schedules,
                key == "" and "Generic" or key
            )

            schedule_index += 1
        self.fill_dict['StateSchedules'] += "\t}\n};\n"
        if len(schedule_list) > 255:
            print("{} KLL compiler does not yet support more than 255 different state schedules, please file a bug!".format(
                ERROR
            ))

        ## Capabilities ##
        self.fill_dict['CapabilitiesFuncDecl'] = ""
        self.fill_dict['CapabilitiesList'] = "const Capability CapabilitiesList[] = {\n"
        self.fill_dict['CapabilitiesIndices'] = "typedef enum CapabilityIndex {\n"

        # Sorted by C Function name
        self.capabilities = full_context.query('NameAssociationExpression', 'Capability')
        self.capabilities_index = dict()
        count = 0
        safe_capabilities = [
            # PartialMap
            "layerState",
            "layerLatch",
            "layerLock",
            "layerShift",
            "layerRotate",
            "testThreadSafe",
            # USB
            "consCtrlOut",
            "noneOut",
            "sysCtrlOut",
            "usbKeyOut",
            "mouseOut",
            "mouseWheelOut",
            "flashMode",
        ]
        for dkey, dvalue in sorted(self.capabilities.data.items(), key=lambda x: x[1].association.name):
            funcName = dvalue.association.name
            argByteWidth = dvalue.association.total_arg_bytes()
            features = "CapabilityFeature_Safe" if dkey in safe_capabilities else "CapabilityFeature_None"

            self.fill_dict['CapabilitiesList'] += "\t/* {3} {4} */\n\t{{ {0}, {1}, {2} }},\n".format(
                funcName,
                argByteWidth,
                features,
                count,
                dkey,
            )
            if self.enable_capv2:
                self.fill_dict['CapabilitiesFuncDecl'] += \
                    "void {0}( TriggerMacro *trigger, uint16_t state, uint8_t stateType, uint8_t *args );\n".format(funcName)
            else:
                self.fill_dict['CapabilitiesFuncDecl'] += \
                    "void {0}( TriggerMacro *trigger, uint8_t state, uint8_t stateType, uint8_t *args );\n".format(funcName)
            self.fill_dict['CapabilitiesIndices'] += "\t{0}_index,\n".format(funcName)

            # Add to json
            capabilities_json[dkey] = {
                'args_count' : len(dvalue.association.arg_list),
                'args' : [],
                'name' : funcName,
                'index' : count,
                'features' : features,
            }
            for arg in dvalue.association.arg_list:
                capabilities_json[dkey]['args'].append({
                    'name' : arg.name,
                    'width' : arg.width,
                })

            # Generate index for result lookup
            self.capabilities_index[dkey] = count
            count += 1

        self.fill_dict['CapabilitiesList'] += "};"
        self.fill_dict['CapabilitiesIndices'] += "} CapabilityIndex;"

        # Validate that we have the required capabilities
        for key, elem in self.required_capabilities.items():
            if elem not in self.capabilities_index.keys():
                if key not in self.optional_required_capabilities:
                    self.error_exit = True
                    print("{0} Required capability '{1}' for '{2}' is missing!".format(
                        ERROR,
                        elem,
                        key,
                    ))

        ## Results Macros ##
        self.fill_dict['ResultMacros'] = ""

        # Iterate through each of the indexed result macros
        # This is the full set of result macros, layers are handled separately
        for index, result in enumerate(result_index):
            self.fill_dict['ResultMacros'] += "Guide_RM( {0} ) = {{ ".format(index)

            # Add the result macro capability index guide (including capability arguments)
            # See kiibohd controller Macros/PartialMap/kll.h for exact formatting details
            for seq_index, sequence in enumerate(result[0].results):
                # If the sequence is longer than 1, prepend a sequence spacer
                # Needed for USB behaviour, otherwise, repeated keys will not work
                if seq_index > 0:
                    # <single element>, <usbCodeSend capability>, <USB Code 0x00>
                    self.fill_dict['ResultMacros'] += "{0}, ".format(self.result_combo_conversion(schedule_list))

                # Iterate over each combo (element of the sequence)
                for com_index, combo in enumerate(sequence):
                    # Convert capability and arguments to output spring
                    self.fill_dict['ResultMacros'] += "{0}, ".format(self.result_combo_conversion(schedule_list, combo))

            # If sequence is longer than 1, append a sequence spacer at the end of the sequence
            # Required by USB to end at sequence without holding the key down
            if len(result[0].results[0]) > 1:
                # <single element>, <usbCodeSend capability>, <USB Code 0x00>
                self.fill_dict['ResultMacros'] += "{0}, ".format(self.result_combo_conversion(schedule_list))

            # Add list ending 0 and end of list
            self.fill_dict['ResultMacros'] += "0 }}; // {0}\n".format(
                result[0].result_str()
            )
        self.fill_dict['ResultMacros'] = self.fill_dict['ResultMacros'][:-1]  # Remove last newline

        ## Result Macro List ##
        self.fill_dict['ResultMacroList'] = "const ResultMacro ResultMacroList[] = {\n"

        # Iterate through each of the result macros
        for index, result in enumerate(result_index):
            # Include debug string for each result macro
            self.fill_dict['ResultMacroList'] += "\tDefine_RM( {0} ), // {1}\n".format(
                index,
                result[0].result_str()
            )
        self.fill_dict['ResultMacroList'] += "};"

        ## Trigger Macros ##
        self.fill_dict['TriggerMacros'] = ""

        # Iterate through each of the trigger macros
        for index, trigger in enumerate(trigger_index_reduced):
            self.fill_dict['TriggerMacros'] += "Guide_TM( {0} ) = {{ ".format(index)

            # Add the trigger macro scan code guide
            # See kiibohd controller Macros/PartialMap/kll.h for exact formatting details
            for seq_index, sequence in enumerate(trigger[0].triggers):

                # Iterate over each combo (element of the sequence)
                for com_index, combo in enumerate(sequence):
                    # Convert each combo into an array of bytes
                    self.fill_dict['TriggerMacros'] += "{0}, ".format(
                        self.trigger_combo_conversion(schedule_list, combo)
                    )

            # Add list ending 0 and end of list
            self.fill_dict['TriggerMacros'] += "0 }}; // {0}\n".format(
                trigger[0].trigger_str()
            )
        self.fill_dict['TriggerMacros'] = self.fill_dict['TriggerMacros'][:-1]  # Remove last newline

        ## Trigger Macro List ##
        self.fill_dict['TriggerMacroList'] = "const TriggerMacro TriggerMacroList[] = {\n"

        # Iterate through each of the trigger macros
        for index, trigger in enumerate(trigger_index):
            # Check if this is an isolated expression
            macro_type = 'TriggerMacroType_Default'
            if trigger[0].isolated:
                macro_type = 'TriggerMacroType_Isolated'

            # Use TriggerMacro Index, and the corresponding ResultMacro Index, including debug string
            self.fill_dict['TriggerMacroList'] += "\t/* {3} */ Define_TM( {0}, {1}, {4} ), // {2}\n".format(
                trigger_index_reduced_lookup[trigger[0].sort_trigger()],
                result_index_lookup[trigger[0].sort_result()],
                trigger[0],
                index,
                macro_type,
            )
        self.fill_dict['TriggerMacroList'] += "};"

        ## Trigger Macro Record ##
        self.fill_dict['TriggerMacroRecord'] = "TriggerMacroRecord TriggerMacroRecordList[ TriggerMacroNum ];"

        ## Max Scan Code ##
        self.fill_dict['MaxScanCode'] = "#define MaxScanCode 0x{0:X}".format(max(max_scan_code))

        ## Interconnect ScanCode Offset List ##
        self.fill_dict['ScanCodeInterconnectOffsetList'] = "const uint8_t InterconnectOffsetList[] = {\n"
        for index, offset in enumerate(interconnect_scancode_offsets):
            self.fill_dict['ScanCodeInterconnectOffsetList'] += "\t0x{0:02X},\n".format(
                offset
            )
        self.fill_dict['ScanCodeInterconnectOffsetList'] += "};"

        ## Max Interconnect Nodes ##
        self.fill_dict['InterconnectNodeMax'] = "#define InterconnectNodeMax 0x{0:X}\n".format(
            len(interconnect_scancode_offsets)
        )

        ## Default Layer and Default Layer Scan Map ##
        self.fill_dict['DefaultLayerTriggerList'] = ""
        self.fill_dict['DefaultLayerScanMap'] = "const nat_ptr_t *default_scanMap[] = { \n"

        # Iterate over triggerList and generate a C trigger array for the default map and default map array
        for index, trigger_list in enumerate(trigger_lists[0][min_scan_code[0]:]):
            trigger_list_len = 0
            if trigger_list is not None:
                trigger_list_len = len(trigger_list)

            # Generate ScanCode index and triggerList length
            self.fill_dict['DefaultLayerTriggerList'] += "Define_TL( default, 0x{0:02X} ) = {{ {1}".format(
                index,
                trigger_list_len
            )

            # Add scanCode trigger list to Default Layer Scan Map
            self.fill_dict['DefaultLayerScanMap'] += "default_tl_0x{0:02X}, ".format(index)

            # Add each item of the trigger list
            if trigger_list_len > 0:
                for trigger_code in trigger_list:
                    self.fill_dict['DefaultLayerTriggerList'] += ", {0}".format(trigger_code)

            self.fill_dict['DefaultLayerTriggerList'] += " };\n"
        self.fill_dict['DefaultLayerTriggerList'] = self.fill_dict['DefaultLayerTriggerList'][:-1]  # Remove last newline
        self.fill_dict['DefaultLayerScanMap'] = self.fill_dict['DefaultLayerScanMap'][:-2]  # Remove last comma and space
        self.fill_dict['DefaultLayerScanMap'] += "\n};"

        ## Partial Layers and Partial Layer Scan Maps ##
        self.fill_dict['PartialLayerTriggerLists'] = ""
        self.fill_dict['PartialLayerScanMaps'] = ""

        # Iterate over each of the layers, excluding the default layer
        for lay_index, layer in enumerate(trigger_lists):
            # Skip first layer (already done)
            if lay_index == 0:
                continue

            # Prepare each layer
            self.fill_dict['PartialLayerScanMaps'] += "// Partial Layer {0}\n".format(lay_index)
            self.fill_dict['PartialLayerScanMaps'] += "const nat_ptr_t *layer{0}_scanMap[] = {{ \n".format(lay_index)
            self.fill_dict['PartialLayerTriggerLists'] += "// Partial Layer {0}\n".format(lay_index)

            # Iterate over triggerList and generate a C trigger array for the layer
            for trig_index, trigger_list in enumerate(layer[min_scan_code[lay_index]:max_scan_code[lay_index] + 1]):
                # Generate ScanCode index and layer
                self.fill_dict['PartialLayerTriggerLists'] += \
                    "Define_TL( layer{0}, 0x{1:02X} ) = {{".format(
                            lay_index,
                            trig_index,
                )

                # TriggerList length
                if trigger_list is not None:
                    self.fill_dict['PartialLayerTriggerLists'] += " {0}".format(
                        len(trigger_list)
                    )

                # Blank trigger (Dropped), zero length
                else:
                    self.fill_dict['PartialLayerTriggerLists'] += " 0"

                # Add scanCode trigger list to Default Layer Scan Map
                self.fill_dict['PartialLayerScanMaps'] += "layer{0}_tl_0x{1:02X}, ".format(
                    lay_index,
                    trig_index,
                )

                # Add each item of the trigger list
                if trigger_list is not None:
                    for trigger_code in trigger_list:
                        self.fill_dict['PartialLayerTriggerLists'] += ", {0}".format(
                            trigger_code
                        )

                self.fill_dict['PartialLayerTriggerLists'] += " };\n"
            self.fill_dict['PartialLayerTriggerLists'] += "\n"
            self.fill_dict['PartialLayerScanMaps'] = self.fill_dict['PartialLayerScanMaps'][:-2]  # Remove last comma and space
            self.fill_dict['PartialLayerScanMaps'] += "\n};\n\n"
        self.fill_dict['PartialLayerTriggerLists'] = self.fill_dict['PartialLayerTriggerLists'][:-2]  # Remove last 2 newlines
        self.fill_dict['PartialLayerScanMaps'] = self.fill_dict['PartialLayerScanMaps'][:-2]  # Remove last 2 newlines

        ## Layer Index List ##
        self.fill_dict['LayerIndexList'] = "const Layer LayerIndex[] = {\n"

        # Iterate over each layer, adding it to the list
        for layer, layer_context in enumerate(reduced_contexts):
            # Generate stacked name (ignore capabilities.kll and scancode_map.kll)
            stack_name = ""
            for name in layer_context.files():
                if name not in ["capabilities.kll", "scancode_map.kll"]:
                    stack_name += "{0} + ".format(name)

            # Apply default name if using standard layout
            if stack_name == "":
                stack_name = "StandardLayer"
            else:
                stack_name = stack_name[:-3]

            # Default map is a special case, always the first index
            if layer == 0:
                self.fill_dict['LayerIndexList'] += '\tLayer_IN( default_scanMap, "D: {1}", 0x{0:02X} ),\n'.format(min_scan_code[layer], stack_name)
            else:
                self.fill_dict['LayerIndexList'] += '\tLayer_IN( layer{0}_scanMap, "{0}: {2}", 0x{1:02X} ),\n'.format(layer, min_scan_code[layer], stack_name)
        self.fill_dict['LayerIndexList'] += "};"

        ## Layer State ##
        self.fill_dict['LayerState'] = "LayerStateType LayerState[ LayerNum ];"

        ## Layers JSON ##
        # Layer 0 is the default map
        # Layer 1+ are the partial maps
        for layer, layer_context in enumerate(reduced_contexts):
            layer_info = dict()
            for key, mapped_trigger in sorted(layer_context.organization.mapping_data.data.items()):
                layer_info[key] = {
                    'trigger' : mapped_trigger[0].triggersSequenceOfCombosOfIds(),
                    'result' : mapped_trigger[0].resultsSequenceOfCombosOfIds(),
                    'kll' : mapped_trigger[0].kllify()
                }
            layers_json[layer] = layer_info

        ## PixelId Physical Positions ##
        for key, entry in sorted(pixel_positions.items()):
            # Add physical pixel positions and ScanCode (if available) to json
            pixel_id_json.setdefault(key, dict()).update(entry)

        ## ScanCode Physical Positions ##
        for key, entry in sorted(scancode_positions.items()):
            # Add physical scancode positions and PixelId (if available) to json
            scancode_json.setdefault(key, dict()).update(entry)

        ## Rotation Trigger Parameters
        max_rotations = 0
        if rotation_map.keys():
            max_rotations = max(rotation_map.keys())
        self.fill_dict['RotationParameters'] = 'const uint8_t Rotation_MaxParameter[] = {\n'
        cur_rotation = 0
        for key, entry in sorted(rotation_map.items()):
            # Make sure that we also fill in 0 for any non-existent rotations
            while cur_rotation != key:
                self.fill_dict['RotationParameters'] += '\t{}, // {}\n'.format(
                    0,
                    cur_rotation,
                )
                cur_rotation += 1
            self.fill_dict['RotationParameters'] += '\t{}, // {}\n'.format(
                entry,
                key,
            )
            cur_rotation += 1
        self.fill_dict['RotationParameters'] += '};'

        ## Pixel Buffer Setup ##
        # Only add sections if Pixel Buffer is defined
        self.use_pixel_map = 'Pixel_Buffer_Size' in defines.data.keys()
        self.fill_dict['AnimationList'] = ""
        if self.use_pixel_map:
            self.fill_dict['PixelBufferSetup'] = "PixelBuf Pixel_Buffers[] = {\n"

            # Lookup number of buffers
            bufsize = len(variables.data[defines.data['Pixel_Buffer_Size'].name].value)
            for index in range(bufsize):
                self.fill_dict['PixelBufferSetup'] += "\tPixelBufElem( {0}, {1}, {2}, {3} ),\n".format(
                    variables.data[defines.data['Pixel_Buffer_Length'].name].value[index],
                    variables.data[defines.data['Pixel_Buffer_Width'].name].value[index],
                    variables.data[defines.data['Pixel_Buffer_Size'].name].value[index],
                    variables.data[defines.data['Pixel_Buffer_Buffer'].name].value[index],
                )
            self.fill_dict['PixelBufferSetup'] += "};"

            # Compute total number of channels
            totalchannels = "{0} + {1}".format(
                variables.data[defines.data['Pixel_Buffer_Length'].name].value[bufsize - 1],
                variables.data[defines.data['Pixel_Buffer_Size'].name].value[bufsize - 1],
            )

            # Only include if defined
            # XXX (HaaTa) This has to be done to make sure KLL compiler is still compatible with older KLL files
            if 'LED_Buffer_Size' in variables.data.keys():
                self.fill_dict['PixelBufferSetup'] += "\nPixelBuf LED_Buffers[] = {\n"

                # Lookup number of buffers (LED)
                ledbufsize = len(variables.data[defines.data['LED_Buffer_Size'].name].value)
                for index in range(ledbufsize):
                    self.fill_dict['PixelBufferSetup'] += "\tPixelBufElem( {0}, {1}, {2}, {3} ),\n".format(
                        variables.data[defines.data['LED_Buffer_Length'].name].value[index],
                        variables.data[defines.data['LED_Buffer_Width'].name].value[index],
                        variables.data[defines.data['LED_Buffer_Size'].name].value[index],
                        variables.data[defines.data['LED_Buffer_Buffer'].name].value[index],
                    )
                self.fill_dict['PixelBufferSetup'] += "};"

                # Add LED fade group(s)
                self.fill_dict['PixelFadeConfig'] = ""
                ledgroupsize = len(variables.data[defines.data['KLL_LED_FadeGroup'].name].value)
                for index in range(ledgroupsize):
                    self.fill_dict['PixelFadeConfig'] += "const uint16_t Pixel_LED_DefaultFadeGroup{}[] = {{\n".format(
                        index
                    )
                    data = variables.data[defines.data['KLL_LED_FadeGroup'].name].value[index]
                    if data != "":
                        self.fill_dict['PixelFadeConfig'] += "\t{}\n".format(data)
                    self.fill_dict['PixelFadeConfig'] += "};\n"

                self.fill_dict['PixelFadeConfig'] += "const PixelLEDGroupEntry Pixel_LED_DefaultFadeGroups[] = {\n"
                for index in range(ledgroupsize):
                    # Count number of elements
                    data = variables.data[defines.data['KLL_LED_FadeGroup'].name].value[index]
                    count = len(data.split(','))
                    if data == "":
                        count = 0

                    self.fill_dict['PixelFadeConfig'] += "\t{{ {}, Pixel_LED_DefaultFadeGroup{} }},\n".format(
                        count,
                        index,
                    )
                self.fill_dict['PixelFadeConfig'] += "};\n"

                # Add fade periods
                self.fill_dict['PixelFadeConfig'] += "const PixelPeriodConfig Pixel_LED_FadePeriods[16] = {\n"
                periodgroupsize = len(variables.data[defines.data['KLL_LED_FadePeriod'].name].value)
                for index in range(periodgroupsize):
                    # Construct array
                    self.fill_dict['PixelFadeConfig'] += "\t{}, // {}\n".format(
                        variables.data[defines.data['KLL_LED_FadePeriod'].name].value[index],
                        index,
                    )
                self.fill_dict['PixelFadeConfig'] += "};\n"

                # Add profile brightnesses
                self.fill_dict['PixelFadeConfig'] += "const uint8_t Pixel_LED_FadeBrightness[4] = {\n"
                if 'KLL_LED_FadeBrightness' in variables.data.keys():
                    fadebrightnesssize = len(variables.data[defines.data['KLL_LED_FadeBrightness'].name].value)
                    for index in range(fadebrightnesssize):
                        # Construct array
                        self.fill_dict['PixelFadeConfig'] += "\t{}, // {}\n".format(
                            variables.data[defines.data['KLL_LED_FadeBrightness'].name].value[index],
                            index,
                        )
                self.fill_dict['PixelFadeConfig'] += "};\n"

                def fade_default_config(name):
                    fadeconfigsize = len(variables.data[defines.data[name].name].value)
                    self.fill_dict['PixelFadeConfig'] += "\t{ "
                    for index in range(fadeconfigsize):
                        self.fill_dict['PixelFadeConfig'] += "{}, ".format(
                            variables.data[defines.data[name].name].value[index]
                        )
                    self.fill_dict['PixelFadeConfig'] += "}}, // {}\n".format(name)

                # Add fade configs
                self.fill_dict['PixelFadeConfig'] += "const uint8_t Pixel_LED_FadePeriod_Defaults[4][4] = {\n"
                fade_default_config('KLL_LED_FadeDefaultConfig0')
                fade_default_config('KLL_LED_FadeDefaultConfig1')
                fade_default_config('KLL_LED_FadeDefaultConfig2')
                fade_default_config('KLL_LED_FadeDefaultConfig3')
                self.fill_dict['PixelFadeConfig'] += "};"

                # Compute total number of channels (LED)
                totalchannels = "{0} + {1}".format(
                    variables.data[defines.data['LED_Buffer_Length'].name].value[ledbufsize - 1],
                    variables.data[defines.data['LED_Buffer_Size'].name].value[ledbufsize - 1],
                )

            ## Pixel Mapping ##
            pixel_indices = full_context.query('MapExpression', 'PixelChannel')

            self.fill_dict['PixelMapping'] = "const PixelElement Pixel_Mapping[] = {\n"

            last_uid = 0
            for key, item in sorted(pixel_indices.data.items(), key=lambda x: x[1].pixel.uid.index):
                last_uid += 1
                # If last_uid isn't directly before, insert placeholder(s)
                while last_uid != item.pixel.uid.index:
                    self.fill_dict['PixelMapping'] += "\tPixel_Blank(), // {0}\n".format(last_uid)
                    last_uid += 1

                # Lookup width and number of channels
                width = item.pixel.channels[0].width
                channels = len(item.pixel.channels)
                self.fill_dict['PixelMapping'] += "\t{{ {0}, {1}, {{".format(width, channels)

                # Iterate over the channels (assuming same width)
                for ch in range(channels):
                    # Add comma if not first channel
                    if ch != 0:
                        self.fill_dict['PixelMapping'] += ","
                    self.fill_dict['PixelMapping'] += "{0}".format(item.pixel.channels[ch].uid)
                self.fill_dict['PixelMapping'] += "}} }}, // {0}\n".format(key)

            totalpixels = last_uid
            self.fill_dict['PixelMapping'] += "};"

            ## ScanCode to Pixel Mapping ##
            self.fill_dict['ScanCodeToPixelMapping'] = "const uint16_t Pixel_ScanCodeToPixel[] = {\n"
            self.fill_dict['ScanCodeToDisplayMapping'] = "const uint16_t Pixel_ScanCodeToDisplay[] = {\n"

            # Add row, column of Pixel to json (mirror lookup to Scan Code Positions as well)
            for y, elem in enumerate(pixel_display_mapping):
                for x, pixelid in enumerate(elem):
                    entry = {'Row': y, 'Col': x}
                    pixel_uid = pixelid + 1
                    pixel_id_json.setdefault(pixel_uid, dict()).update(entry)

                    if 'ScanCode' in pixel_id_json[pixel_uid].keys():
                        scancode_uid = pixel_id_json[pixel_uid]['ScanCode']
                        scancode_json[scancode_uid].update(entry)

            # Only deal with pixels mapped to ScanCodes
            last_scancode = 0
            pixel_items = {key:elem for key, elem in pixel_indices.data.items() if not isinstance(elem.position, list)}
            for key, item in sorted(pixel_items.items(), key=lambda x: x[1].position.uid):
                last_scancode += 1

                # Add ScanCodeToPixelMapping entry
                # Add ScanCodeToDisplayMapping entry
                while item.position.uid != last_scancode and item.position.uid >= last_scancode:
                    # Fill in unused scancodes
                    self.fill_dict['ScanCodeToPixelMapping'] += "\t/*{0}*/ 0,\n".format(last_scancode)
                    self.fill_dict['ScanCodeToDisplayMapping'] += "\t/*__,__ {0}*/ 0,\n".format(last_scancode)
                    last_scancode += 1

                self.fill_dict['ScanCodeToPixelMapping'] += "\t/*{0}*/ {1}, // {2}\n".format(
                    last_scancode,
                    item.pixel.uid.index,
                    key
                )

                # Find Pixel_DisplayMapping offset
                offset_row = 0
                offset_col = 0
                offset = 0
                for y_list in pixel_display_mapping:
                    for x_item in y_list:
                        if x_item == item.pixel.uid.index:
                            offset = offset_row * pixel_display_params['Columns'] + offset_col
                            break
                        offset_col += 1

                    # Offset found
                    if offset != 0:
                        break
                    offset_row += 1
                    offset_col = 0

                self.fill_dict['ScanCodeToDisplayMapping'] += "\t/*{3: >2},{4: >2} {0}*/ {1}, // {2}\n".format(
                    last_scancode,
                    offset,
                    key,
                    offset_col,
                    offset_row,
                )
            max_pixel_to_scancode = last_scancode
            self.fill_dict['ScanCodeToPixelMapping'] += "};"
            self.fill_dict['ScanCodeToDisplayMapping'] += "};"

            ## Pixel Display Mapping ##
            self.fill_dict['PixelDisplayMapping'] = "const uint16_t Pixel_DisplayMapping[] = {\n"
            for y_list in pixel_display_mapping:
                self.fill_dict['PixelDisplayMapping'] += \
                        ",".join("{0: >3}".format(x) for x in y_list) + ",\n"
            self.fill_dict['PixelDisplayMapping'] += "};"

            ## Gamma Table Generation ##
            gamma = float(variables.data['LEDGamma'].value) if 'LEDGamma' in variables.data else 1.0
            self.fill_dict['GammaTable'] = "const uint8_t gamma_table[] = {\n" \
                                            + ", ".join([str(i) for i in self.generateGammaTable(gamma)]) \
                                            + "\n};"

            ## Animations ##
            # TODO - Use reduced_contexts and generate per-layer (naming gets tricky)
            #        Currently using full_context which is not as configurable
            self.fill_dict['Animations'] = "const uint8_t **Pixel_Animations[] = {"
            self.fill_dict['AnimationSettings'] = "const AnimationStackElement Pixel_AnimationSettings[] = {"
            self.fill_dict['AnimationList'] = ""
            animations = full_context.query('DataAssociationExpression', 'Animation')
            count = 0
            for key, animation in sorted(animations.data.items()):
                # Lookup uid
                uid = animation_uid_lookup[animation.association.name]

                # Name each frame collection
                self.fill_dict['Animations'] += "\n\t/*{0}*/ {1}_frames,".format(
                    uid,
                    animation.association.name,
                )

                # Add animation name to list
                animation_name = "Animation__{0}".format(
                    animation.association.name
                )
                self.fill_dict['AnimationList'] += "\n#define {0} {1}".format(
                    animation_name,
                    uid,
                )

                # Map index to name (json)
                animation_id_json[animation.association.name] = uid

                # Animation Settings Index JSON entry
                animation_entry_json = animation.association.json()
                animation_entry_json.update(animation.value.json())
                animation_settings_index_json.append(animation_entry_json)

                # Generate animation settings string entry
                self.fill_dict['AnimationSettings'] += self.animation_settings_entry(
                    animation.value,
                    animation_name,
                    uid,
                    additional=False,
                )
                count += 1
            self.fill_dict['Animations'] += "\n};"

            # Additional Animation Settings
            self.fill_dict['AnimationSettings'] += "\n\n\t/* Additional Settings */\n"
            while count < len(animation_settings_list):
                animation = animation_settings[animation_settings_list[count]]
                animation_orig = animation_settings_orig[animation_settings_list[count]]
                animation_name = "Animation__{0}".format(
                    animation.name
                )

                # Animation Settings JSON entry
                animation_settings_json["{}".format(animation_orig)] = count

                # Animation Settings Index JSON entry
                animation_settings_index_json.append(animation.json())

                # Generate animation settings string entry
                self.fill_dict['AnimationSettings'] += self.animation_settings_entry(
                    animation,
                    animation_name,
                    count,
                    additional=True,
                )
                count += 1
            self.fill_dict['AnimationSettings'] += "\n};"

            ## Animation Frames ##
            # TODO - Use reduced_contexts and generate per-layer (naming gets tricky)
            #        Currently using full_context which is not as configurable
            self.fill_dict['AnimationFrames'] = ""
            animation_frames = full_context.query('DataAssociationExpression', 'AnimationFrame')
            prev_aniframe_name = ""
            prev_aniframe = 0
            for key, aniframe in sorted(animation_frames.data.items(), key=lambda x: (x[1].association[0].name, x[1].association[0].index)):
                aniframeid = aniframe.association[0]
                aniframedata = aniframe.value
                name = aniframeid.name

                # Generate frame-set
                if prev_aniframe_name != "" and name != prev_aniframe_name:
                    self.animation_frameset(prev_aniframe_name, prev_aniframe)

                    # Reset frame count
                    prev_aniframe = 0

                # Fill in frames if necessary
                while aniframeid.index > prev_aniframe + 1:
                    prev_aniframe += 1
                    self.fill_dict['AnimationFrames'] += "const uint8_t {0}_frame{1}[] = {{ PixelAddressType_End }};\n\n".format(
                        name,
                        prev_aniframe
                    )
                prev_aniframe_name = name

                # Address type lookup for frames
                # See Macros/PixelMap/pixel.h for list of types
                address_type = {
                    'PixelAddressId_Index': 'PixelAddressType_Index',
                    'PixelAddressId_Rect': 'PixelAddressType_Rect',
                    'PixelAddressId_ColumnFill': 'PixelAddressType_ColumnFill',
                    'PixelAddressId_RowFill': 'PixelAddressType_RowFill',
                    'PixelAddressId_ScanCode': 'PixelAddressType_ScanCode',
                    'PixelAddressId_RelativeRect': 'PixelAddressType_RelativeRect',
                    'PixelAddressId_RelativeColumnFill': 'PixelAddressType_RelativeColumnFill',
                    'PixelAddressId_RelativeRowFill': 'PixelAddressType_RelativeRowFill',
                }

                # Frame information
                self.fill_dict['AnimationFrames'] += "// {0}".format(
                    aniframe.kllify()
                )

                # Generate frame
                self.fill_dict['AnimationFrames'] += "\nconst uint8_t {0}_frame{1}[] = {{".format(
                    name,
                    aniframeid.index
                )

                # There may be multiple Ids per frame actions (must be expanded)
                for sub_aniframedata in aniframedata:
                    for elem in sub_aniframedata:
                        # TODO Determine widths (possibly do checks at an earlier stage to validate)

                        if isinstance(elem, list):
                            elem = elem[0]

                        # Select pixel address type
                        self.fill_dict['AnimationFrames'] += "\n\t{0},".format(
                            address_type[elem.uid.inferred_type()]
                        )

                        # For each channel select a pixel address
                        channels = elem.uid.uid_set()
                        channel_str = "/* UNKNOWN CHANNEL {0} */".format(len(channels))
                        if len(channels) == 1:
                            channel_str = " /*{0}*/{1},".format(
                                channels[0],
                                ",".join(self.byte_split(channels[0], 4))
                            )
                        elif len(channels) == 2:
                            channel_str = ""
                            for index, ch in enumerate(channels):
                                value = 0

                                # Convert to pixelmap position as we defined a percentage
                                if isinstance(ch, float):
                                    # Calculate percentage of displaymap
                                    if index == 0:
                                        value = (pixel_display_params['Columns'] - 1) * ch
                                    elif index == 1:
                                        value = (pixel_display_params['Rows'] - 1) * ch

                                    value = int(round(value))

                                # No value, set to 0
                                elif ch is None:
                                    value = 0

                                # Otherwise it's an integer
                                else:
                                    value = int(ch)

                                channel_str += " /*{0}*/{1},".format(
                                    ch, ",".join(self.byte_split(value, 2)),
                                )
                        self.fill_dict['AnimationFrames'] += channel_str

                        # For each channel, select an operator and value
                        for pixelmod in elem.modifiers:
                            # Set operator type
                            channel_str = " PixelChange_{0},".format(
                                pixelmod.operator_type()
                            )

                            # Set channel value
                            # TODO Support non-8bit values
                            channel_str += " {0},".format(pixelmod.value)

                            self.fill_dict['AnimationFrames'] += channel_str
                self.fill_dict['AnimationFrames'] += "\n\tPixelAddressType_End\n};\n\n"

                # Set frame number, for next frame evaluation
                prev_aniframe = aniframeid.index

            # Last frame set
            if prev_aniframe_name != "":
                self.animation_frameset(prev_aniframe_name, prev_aniframe)

        ## LED Buffer Struct ##
        if 'LED_BufferStruct' in variables.data.keys():
            self.fill_dict['LEDBufferStruct'] = variables.data['LED_BufferStruct'].value
        else:
            self.fill_dict['LEDBufferStruct'] = ""

        ## ScanCode Physical Positions ##
        scancode_physical = full_context.query('DataAssociationExpression', 'ScanCodePosition')
        self.fill_dict['KeyPositions'] = "const Position Key_Positions[] = {\n"
        for key, item in sorted(scancode_physical.data.items(), key=lambda x: x[1].association[0].get_uid()):
            entry = dict()
            # Acquire each dimension
            entry['x'] = item.association[0].x
            entry['y'] = item.association[0].y
            entry['z'] = item.association[0].z
            entry['rx'] = item.association[0].rx
            entry['ry'] = item.association[0].ry
            entry['rz'] = item.association[0].rz

            # Check each dimension, set to 0 if None
            for k in entry.keys():
                if entry[k] is None:
                    entry[k] = 0.0
                else:
                    entry[k] = float(entry[k])

            # Generate PositionEntry
            self.fill_dict['KeyPositions'] += "\tPositionEntry( {0}, {1}, {2}, {3}, {4}, {5} ), // {6}\n".format(
                entry['x'],
                entry['y'],
                entry['z'],
                entry['rx'],
                entry['ry'],
                entry['rz'],
                item,
            )
        self.fill_dict['KeyPositions'] += "};"

        ## UTF-8 ##
        self.fill_dict['UTF8Data'] = "const char* UTF8_Strings[] = {\n"
        for key, item in utf8_strings.items():
            # Remove surrounding b'mytext' -> mytext and encode into utf-8
            output_str = '{}'.format(key.encode('utf-8'))[2:-1]
            self.fill_dict['UTF8Data'] += '\t"{}",\n'.format(output_str)
        self.fill_dict['UTF8Data'] += "};"

        ## KLL Defines ##
        self.fill_dict['KLLDefines'] = ""
        self.fill_dict['KLLDefines'] += "#define CapabilitiesNum_KLL {0}\n".format(len(self.capabilities_index))
        self.fill_dict['KLLDefines'] += "#define LayerNum_KLL {0}\n".format(len(reduced_contexts))
        self.fill_dict['KLLDefines'] += "#define ResultMacroNum_KLL {0}\n".format(len(result_index))
        self.fill_dict['KLLDefines'] += "#define TriggerMacroNum_KLL {0}\n".format(len(trigger_index))
        self.fill_dict['KLLDefines'] += "#define MaxScanCode_KLL {0}\n".format(max(max_scan_code))
        self.fill_dict['KLLDefines'] += "#define RotationNum_KLL {0}\n".format(max_rotations)
        self.fill_dict['KLLDefines'] += "#define UTF8StringsNum_KLL {0}\n".format(len(utf8_strings))
        self.fill_dict['KLLDefines'] += "#define ScheduleNum_KLL {0}\n".format(len(schedule_list))

        # Only add defines if Pixel Buffer is defined
        if self.use_pixel_map:
            self.fill_dict['KLLDefines'] += "#define Pixel_BuffersLen_KLL {0}\n".format(bufsize)
            self.fill_dict['KLLDefines'] += "#define Pixel_TotalChannels_KLL {0}\n".format(totalchannels)
            self.fill_dict['KLLDefines'] += "#define Pixel_TotalPixels_KLL {0}\n".format(totalpixels)
            self.fill_dict['KLLDefines'] += "#define Pixel_DisplayMapping_Cols_KLL {0}\n".format(
                pixel_display_params['Columns']
            )
            self.fill_dict['KLLDefines'] += "#define Pixel_DisplayMapping_Rows_KLL {0}\n".format(
                pixel_display_params['Rows']
            )
            self.fill_dict['KLLDefines'] += "#define Pixel_AnimationSettingsNum_KLL {0}\n".format(
                len(animation_settings_list)
            )
            self.fill_dict['KLLDefines'] += "#define AnimationNum_KLL {0}\n".format(len(animations.data))
            self.fill_dict['KLLDefines'] += "#define MaxPixelToScanCode_KLL {0}\n".format(max_pixel_to_scancode)
        else:
            self.fill_dict['KLLDefines'] += "#define AnimationNum_KLL 0\n"

        ## Define Validation ##
        if 'stateWordSize' in variables.data.keys():
            index_uint_t_size = int(variables.data['stateWordSize'].value)
            total_index = max(len(trigger_index), len(result_index))
            if total_index > 2 ** index_uint_t_size:
                print("{} 'stateWordSize = {}' is not large enough! {} > {}".format(
                    ERROR,
                    index_uint_t_size,
                    total_index,
                    2 ** index_uint_t_size,
                ))
                self.error_exit = True

        ## Generate USB HID Lookup ##
        self.fill_dict['USBCDefineKeyboardMapping'] = ''
        for pair in self.usb_c_defines[0]:
            self.fill_dict['USBCDefineKeyboardMapping'] += "#define {} {}\n".format(*pair)

        self.fill_dict['USBCDefineLEDMapping'] = ''
        for pair in self.usb_c_defines[1]:
            self.fill_dict['USBCDefineLEDMapping'] += "#define {} {}\n".format(*pair)

        self.fill_dict['USBCDefineSystemControlMapping'] = ''
        for pair in self.usb_c_defines[2]:
            self.fill_dict['USBCDefineSystemControlMapping'] += "#define {} {}\n".format(*pair)

        self.fill_dict['USBCDefineConsumerControlMapping'] = ''
        for pair in self.usb_c_defines[3]:
            self.fill_dict['USBCDefineConsumerControlMapping'] += "#define {} {}\n".format(*pair)

        ## Finish up JSON datastructures
        # TODO Testing
        # - Run trigger
        #   1) Validate result (will need infra per capability)
        #   2) Hook into animation testing?
        # - Trigger Types
        #   1) Switch
        #   2) HID LED
        #   3) Layer
        #   4) Animation
        #   5) Analog
        self.json_dict['AnimationIds'] = animation_id_json
        self.json_dict['AnimationSettings'] = animation_settings_json
        self.json_dict['AnimationSettingsIndex'] = animation_settings_index_json
        self.json_dict['PixelIds'] = pixel_id_json
        self.json_dict['ScanCodes'] = scancode_json
        self.json_dict['Capabilities'] = capabilities_json
        self.json_dict['Defines'] = defines_json
        self.json_dict['Layers'] = layers_json
        self.json_dict['CodeLookup'] = self.code_to_capability

