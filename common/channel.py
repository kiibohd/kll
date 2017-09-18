#!/usr/bin/env python3
'''
KLL Channel Containers
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



### Decorators ###

# Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'



### Classes ###

class Channel:
    '''
    Pixel Channel Container
    '''

    def __init__(self, uid, width):
        self.uid = uid
        self.width = width

    def __repr__(self):
        return "{0}:{1}".format(self.uid, self.width)


class ChannelList:
    '''
    Pixel Channel List Container
    '''

    def __init__(self):
        self.channels = []

    def setChannels(self, channel_list):
        '''
        Apply channels to Pixel
        '''
        for channel in channel_list:
            self.channels.append(Channel(channel[0], channel[1]))

    def strChannels(self):
        '''
        __repr__ of Channel when multiple inheritance is used
        '''
        output = ""
        for index, channel in enumerate(self.channels):
            if index > 0:
                output += ","
            output += "{0}".format(channel)

        return output

    def __repr__(self):
        return self.strChannels()
