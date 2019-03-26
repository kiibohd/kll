#!/usr/bin/env python3
'''
KLL Version Update Suggestions

This file contains suggestions when having to update KLL from one version to another.
Each of the breaking changes are list (and which version the breaking change is added).
If many breaking changes are present, then it is up to the user to combine all the changes.
'''

# Copyright (C) 2019 by Jacob Alexander
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

from packaging import version



### Database ###

suggestions = {
    '0.5.7.11': [
        "KLL now supports inverting the Layer Fade profile.",
        "This means when a layer is active, only the keys in that layer will show the active animation.",
        "It is used by default on Gemini Dusk and Dawn.",
        "",
        "To use, add the following to your KLL file:",
        "KLL_LED_FadeActiveLayerInvert = 1;",
        "KLL_LED_FadeBrightness[0] = 255;",
        "KLL_LED_FadeBrightness[1] = 255;",
        "KLL_LED_FadeBrightness[2] = 255;",
        "KLL_LED_FadeBrightness[3] = 0; # Sets unused LEDs to off",
        "Layer[1] : fade_layer_highlight(1); # Activates layer fade when layer is triggered",
        "Layer[2] : fade_layer_highlight(2); # Activates layer fade when layer is triggered",
    ],
    '0.5.7.8': [
        "KLL now supports fade profile brightness settings.",
        "A fade profile is a selection of LEDs associated to one of 4 groups:",
        " - Keys",
        " - Underglow",
        " - Indicators",
        " - Active Layer",
        "Fade profiles are used to apply a configurable dimming and brightening, on top of whatever animation may be set.",
        "0.5.7.8 adds support for the fade_control() which (among other things), can adjust brightness per-fade profile.",
        "The most useful application of this would be to dim the LEDs under keys, while leaving underglow and indicator LEDs on.",
        "",
        'U"B" : fade_control(0, 3, 20); # Increment brightness on fade profile 0 (keys) by 20',
        'U"C" : fade_control(1, 4, 10); # Decrement brightness on fade profile 1 (underglow) by 10',
        'KLL_LED_FadeBrightness[2] = 150; # Set default brightness of indicators to 150',
        "",
        "For more details, review the KLL definition file:",
        "https://github.com/kiibohd/controller/blob/ae7bf0b711dfba5e77451cd2f269032f929a8657/Macro/PixelMap/capabilities.kll#L89",
    ],
    '0.5.7.6': [
        "KLL now supports the replace:clearactive animation option.",
        "For example:",
        "A[my_animation] <= pfunc:interp, replace:clearactive, single;",
        'U"Q" : A[my_other_animation](replace:clearactive);',
        "",
        "The main use for clearactive is to clear any non-paused animations from the animation stack.",
        "While leaving any animations that are currently paused still on the stack.",
        "This means it's possible to save those animations to non-volatile memory (if your keyboard supports it).",
        "If you use replace:clear (as was the default before), when you save the current settings on your keyboard",
        "the keyboard won't understand the sequence of events in order to display the current LED colors.",
    ],
    '0.5.7.0': [
        "KLL now supports the single animation option.",
        "For example:"
        "A[my_animation] <= pfunc:interp, single;",
        'U"Q" : A[my_other_animation](single, pos:20); # Start animation at frame 20 and pause',
        "",
        "The single option starts an animation at the specified frame and pauses immediately after.",
        "This is useful when creating a list of colors to cycle through using a rotation.",
        "",
        "",
        "KLL now supports a basic gamma correction table.",
        "Gamma correction can be dynamically enabled using the gamma() function.",
        'U"A" : gamma(2); # Toggles gamma correction',
        "The gamma correction table is generated at compile time and can be configured using:",
        "LEDGamma = 2.2; # Default gamma correction",
        "",
        "For more details, review the KLL definition file:",
        "https://github.com/kiibohd/controller/blob/bce0073e5c31ce89ecc4122d5c1438a027809393/Macro/PixelMap/capabilities.kll",
    ],
    '0.5.6.0': [
        "KLL now supports fade profile groups.",
        "A fade profile is a selection of LEDs associated to one of 4 groups:"
        " - Keys",
        " - Underglow",
        " - Indicators",
        " - Active Layer",
        "Each fade profile may be given 4 fade periods:",
        " 0: Off to On",
        " 1: On",
        " 2: On to Off",
        " 3: Off",
        "There are 16 configurable periods in which start and end times may be set from 0 to 15.",
        "Setting start and end to 0, disables that period (no time is spent waiting/interpolating).",
        "Setting 1 waits for 1 frame, 2 -> 2 frames, 3 -> 4 frames, 4 -> 8 frames",
        "The equations are:",
        " .start == (1 << start) - 1",
        " .end   == (1 << end)",
        "Setting .start to a non-zero value will begin the interpolation starting at that frame brightness.",
        "",
        "Fade profiles can be set dynamically using fade_set() capability.",
        ' U"A" : fade_set(0, 2, 13); # On profile 0 (keys), set On to Off period to configuration 13',
        "The active layer fade can be started using the fade_layer_highlight() capability.",
        " Layer[1] : fade_layer_highlight(1);",
        "",
        "For more details, review the KLL definition file:",
        "https://github.com/kiibohd/controller/blob/2d7152e0576281abd2f4b1d094a5d778d9811aff/Macro/PixelMap/capabilities.kll",
    ],
}



### Classes ###

class Suggestions:
    '''
    Determines which suggestions to show
    '''
    def __init__(self, running_version, file_version):
        self.running_version = version.parse(running_version)
        self.file_version = version.parse(file_version)

    def show(self):
        '''
        Show relevant suggestions based on the requested versions
        '''
        sorted_keys = sorted([version.parse(suggestion) for suggestion in suggestions.keys() if version.parse(suggestion) > self.file_version])
        for key in sorted_keys:
            print("\033[1m === {} === \033[0m".format(key))
            for line in suggestions[str(key)]:
                print(line)
            print("")

