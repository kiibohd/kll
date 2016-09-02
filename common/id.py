#!/usr/bin/env python3
'''
KLL Id Containers
'''

# Copyright (C) 2016 by Jacob Alexander
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

from common.hid_dict import hid_lookup_dictionary

from common.channel  import ChannelList
from common.modifier import AnimationModifierList, PixelModifierList
from common.position import Position
from common.schedule import Schedule



### Decorators ###

## Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'



### Classes ###

class Id:
	'''
	Base container class for various KLL types
	'''
	def __init__( self ):
		self.type = None
		self.uid = None


class HIDId( Id, Schedule ):
	'''
	HID/USB identifier container class
	'''
	secondary_types = {
		'USBCode'  : 'USB',
		'SysCode'  : 'SYS',
		'ConsCode' : 'CONS',
		'IndCode'  : 'IND',
	}

	def __init__( self, type, uid ):
		'''
		@param type: String type of the Id
		@param uid:  Unique integer identifier for the Id
		'''
		Id.__init__( self )
		Schedule.__init__( self )
		self.type = type
		self.uid = uid

		# Set secondary type
		self.second_type = self.secondary_types[ self.type ]

		# TODO Validate uid to make sure it's in the lookup dictionary
		# TODO Validate HID specifier
		#print ( "{0} Unknown HID Specifier '{1}'".format( ERROR, type ) )
		#raise

	def __repr__( self ):
		'''
		Use string name instead of integer, easier to debug
		'''
		uid = hid_lookup_dictionary[ ( self.second_type, self.uid ) ]
		schedule = self.strSchedule()
		if len( schedule ) > 0:
			schedule = "({0})".format( schedule )

		output = 'HID({0})"{1}"{2}'.format( self.type, uid, schedule )
		return output


class ScanCodeId( Id, Schedule, Position ):
	'''
	Scan Code identifier container class
	'''

	def __init__( self, uid ):
		Id.__init__( self )
		Schedule.__init__( self )
		Position.__init__( self )
		self.type = 'ScanCode'
		self.uid = uid

		# By default, interconnect_id of 0
		# Will be set during the merge process if it needs to change
		self.interconnect_id = 0

	def unique_key( self ):
		'''
		Returns the key string used for datastructure sorting
		'''
		# Positions are a special case
		if self.positionSet():
			return "P{0}".format( self.uid )

	def __repr__( self ):
		# Positions are a special case
		if self.positionSet():
			return "{0} <= {1}".format( self.unique_key(), self.strPosition() )

		schedule = self.strSchedule()
		if len( schedule ) > 0:
			return "S{0}({1})".format( self.uid, schedule )
		else:
			return "S{0}".format( self.uid )


class AnimationId( Id, AnimationModifierList ):
	'''
	Animation identifier container class
	'''
	name = None

	def __init__( self, name ):
		Id.__init__( self )
		AnimationModifierList.__init__( self )
		self.name = name
		self.type = 'Animation'

	def __repr__( self ):
		if len( self.modifiers ) > 0:
			return "A[{0}]({1})".format( self.name, self.strModifiers() )
		return "A[{0}]".format( self.name )


class AnimationFrameId( Id, AnimationModifierList ):
	'''
	Animation Frame identifier container class
	'''
	def __init__( self, name, index ):
		Id.__init__( self )
		AnimationModifierList.__init__( self )
		self.name = name
		self.index = index
		self.type = 'AnimationFrame'

	def __repr__( self ):
		return "AF[{0}, {1}]".format( self.name, self.index )


class PixelId( Id, Position, PixelModifierList, ChannelList ):
	'''
	Pixel identifier container class
	'''
	def __init__( self, uid ):
		Id.__init__( self )
		Position.__init__( self )
		PixelModifierList.__init__( self )
		ChannelList.__init__( self )
		self.uid = uid
		self.type = 'Pixel'

	def unique_key( self ):
		'''
		Returns the key string used for datastructure sorting
		'''
		return "P{0}".format( self.uid )

	def __repr__( self ):
		# Positions are a special case
		if self.positionSet():
			return "{0} <= {1}".format( self.unique_key(), self.strPosition() )

		extra = ""
		if len( self.modifiers ) > 0:
			extra += "({0})".format( self.strModifiers() )
		if len( self.channels ) > 0:
			extra += "({0})".format( self.strChannels() )
		return "{0}{1}".format( self.unique_key(), extra )


class PixelLayerId( Id, PixelModifierList ):
	'''
	Pixel Layer identifier container class
	'''
	def __init__( self, uid ):
		Id.__init__( self )
		PixelModifierList.__init__( self )
		self.uid = uid
		self.type = 'PixelLayer'

	def __repr__( self ):
		if len( self.modifiers ) > 0:
			return "PL{0}({1})".format( self.uid, self.strModifiers() )
		return "PL{0}".format( self.uid )


class CapId( Id ):
	'''
	Capability identifier
	'''
	def __init__( self, name, type, arg_list=[] ):
		'''
		@param name:     Name of capability
		@param type:     Type of capability definition, string
		@param arg_list: List of CapArgIds, empty list if there are none
		'''
		Id.__init__( self )
		self.name     = name
		self.type     = type
		self.arg_list = arg_list

	def __repr__( self ):
		# Generate prettified argument list
		arg_string = ""
		for arg in self.arg_list:
			arg_string += "{0},".format( arg )
		if len( arg_string ) > 0:
			arg_string = arg_string[:-1]

		return "{0}({1})".format( self.name, arg_string )

	def total_arg_bytes( self ):
		'''
		Calculate the total number of bytes needed for the args

		return: Number of bytes
		'''
		# Zero if no args
		total_bytes = 0
		for arg in self.arg_list:
			total_bytes += arg.width

		return total_bytes


class NoneId( CapId ):
	'''
	None identifier

	It's just a capability...that does nothing (instead of infering to do something else)
	'''
	def __init__( self ):
		super().__init__( 'None', 'None' )

	def __repr__( self ):
		return "None"


class CapArgId( Id ):
	'''
	Capability Argument identifier
	'''
	def __init__( self, name, width=None ):
		'''
		@param name:  Name of argument
		@param width: Byte-width of the argument, if None, this is not port of a capability definition
		'''
		Id.__init__( self )
		self.name = name
		self.width = width
		self.type = 'CapArg'

	def __repr__( self ):
		if self.width is None:
			return "{0}".format( self.name )
		else:
			return "{0}:{1}".format( self.name, self.width )

