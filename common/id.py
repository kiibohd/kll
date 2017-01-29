#!/usr/bin/env python3
'''
KLL Id Containers
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

from common.hid_dict import hid_lookup_dictionary

from common.channel  import ChannelList
from common.modifier import AnimationModifierList, PixelModifierList
from common.position import Position
from common.schedule import Schedule

from funcparserlib.parser import NoParseError



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

	def kllify( self ):
		'''
		Returns KLL version of the Id

		In most cases we can just the string representation of the object
		'''
		return "{0}".format( self )


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

	kll_types = {
		'USBCode'  : 'U',
		'SysCode'  : 'SYS',
		'ConsCode' : 'CONS',
		'IndCode'  : 'IND',
	}

	type_width = {
		'USBCode'  : 1,
		'SysCode'  : 1,
		'ConsCode' : 2,
		'IndCode'  : 1,
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

		# Set kll type
		self.kll_type = self.kll_types[ self.type ]

		# TODO Validate uid to make sure it's in the lookup dictionary
		# TODO Validate HID specifier
		#print ( "{0} Unknown HID Specifier '{1}'".format( ERROR, type ) )
		#raise

	def width( self ):
		'''
		Returns the bit width of the HIDId

		This is the maximum number of bytes required for each type of HIDId as per the USB spec.
		Generally this is just 1 byte, however, Consumer elements (ConsCode) requires 2 bytes.
		'''
		return self.type_width[ self.type ]

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

	def kllify( self ):
		'''
		Returns KLL version of the Id
		'''
		schedule = self.strSchedule()
		if len( schedule ) > 0:
			schedule = "({0})".format( schedule )

		output = "{0}{1:#05x}{2}".format( self.kll_type, self.uid, schedule )
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

	def inferred_type( self ):
		'''
		Always returns ScanCode (simplifies code when mixed with PixelAddressId)
		'''
		return 'PixelAddressId_ScanCode'

	def uid_set( self ):
		'''
		Returns a tuple of uids, always a single element for ScanCodeId
		'''
		return tuple([ self.uid ])

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

	def kllify( self ):
		'''
		Returns KLL version of the Id
		'''
		schedule = self.strSchedule()
		if len( schedule ) > 0:
			schedule = "({0})".format( schedule )

		output = "S{0:#05x}{1}".format( self.uid, schedule )

		# Position enabled
		if self.isPositionSet():
			output += " <= {0}".format( self.strPosition() )
		return output


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

	def kllify( self ):
		'''
		Returns KLL version of the Id
		'''
		return "A[{0}, {1}]".format( self.name, self.index )


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

	def unique_key( self, kll=False ):
		'''
		Returns the key string used for datastructure sorting

		@param kll: Kll output format mode
		'''
		if isinstance( self.uid, HIDId ) or isinstance( self.uid, ScanCodeId ):
			if kll:
				return "{0}".format( self.uid.kllify() )
			return "P[{0}]".format( self.uid )

		if isinstance( self.uid, PixelAddressId ):
			if kll:
				return "P[{0}]".format( self.uid.kllify() )
			return "P[{0}]".format( self.uid )

		if kll:
			return "P{0:#05x}".format( self.uid )

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

	def kllify( self ):
		'''
		KLL syntax compatible output for Pixel object
		'''
		# Positions are a special case
		if self.positionSet():
			return "{0} <= {1}".format( self.unique_key( kll=True ), self.strPosition() )

		extra = ""
		if len( self.modifiers ) > 0:
			extra += "({0})".format( self.strModifiers() )
		if len( self.channels ) > 0:
			extra += "({0})".format( self.strChannels() )
		return "{0}{1}".format( self.unique_key( kll=True ), extra )


class PixelAddressId( Id ):
	'''
	Pixel address identifier container class
	'''
	def __init__( self, index=None, col=None, row=None, relCol=None, relRow=None ):
		Id.__init__( self )

		# Check to make sure index, col or row is set
		if index is None and col is None and row is None and relRow is None and relCol is None:
			print ( "{0} index, col or row must be set".format( ERROR ) )

		self.index = index
		self.col = col
		self.row = row
		self.relCol = relCol
		self.relRow = relRow

		self.type = 'PixelAddress'

	def inferred_type( self ):
		'''
		Determine which PixelAddressType based on set values
		'''

		if self.index is not None:
			return 'PixelAddressId_Index'
		if self.col is not None and self.row is None:
			return 'PixelAddressId_ColumnFill'
		if self.col is None and self.row is not None:
			return 'PixelAddressId_RowFill'
		if self.col is not None and self.row is not None:
			return 'PixelAddressId_Rect'
		if self.relCol is not None and self.relRow is None:
			return 'PixelAddressId_RelativeColumnFill'
		if self.relCol is None and self.relRow is not None:
			return 'PixelAddressId_RelativeRowFill'
		if self.relCol is not None and self.relRow is not None:
			return 'PixelAddressId_RelativeRect'

		print( "{0} Unknown PixelAddressId, this is a bug!".format( ERROR ) )
		return "<UNKNOWN PixelAddressId>"

	def uid_set( self ):
		'''
		Returns a tuple of uids, depends on what has been set.
		'''
		if self.index is not None:
			return tuple([ self.index ])
		if self.col is not None and self.row is None:
			return tuple([ self.col, self.row ])
		if self.col is None and self.row is not None:
			return tuple([ self.col, self.row ])
		if self.col is not None and self.row is not None:
			return tuple([ self.col, self.row ])
		if self.relCol is not None and self.relRow is None:
			return tuple([ self.relCol, self.relRow ])
		if self.relCol is None and self.relRow is not None:
			return tuple([ self.relCol, self.relRow ])
		if self.relCol is not None and self.relRow is not None:
			return tuple([ self.relCol, self.relRow ])

		print( "{0} Unknown uid set, this is a bug!".format( ERROR ) )
		return "<UNKNOWN uid set"

	def merge( self, address ):
		'''
		Merge in a PixelAddressId

		Will error-out instead of overwriting

		@param address: PixelAddressId object to merge in
		'''
		# Make sure we are either index or col/row
		if not self.index is None or not address.index is None:
			print( "{0} Cannot merge into index PixelAddressIds".format( ERROR ) )
			raise NoParseError

		# Make sure we don't overwrite
		if not self.col is None and not address.col is None:
			print( "{0} Duplicate column fields '{1}' '{2}'".format( ERROR, self, address ) )
			raise NoParseError
		if not self.row is None and not address.row is None:
			print( "{0} Duplicate row fields '{1}' '{2}'".format( ERROR, self, address ) )
			raise NoParseError

		# Merge over values
		if not address.col is None:
			self.col = address.col
		if not address.row is None:
			self.row = address.row
		if not address.relCol is None:
			self.relCol = address.relCol
		if not address.relRow is None:
			self.relRow = address.relRow

	def valueStr( self, value ):
		'''
		Prepare numerical value based on type

		@param value: Float or Integer position

		@return: String
		'''
		output = ""

		# Check if float
		if isinstance( value, float ):
			output += "{0}%".format( value * 100 )
		else:
			output += "{0}".format( value )

		return output

	def outputStrList( self ):
		'''
		List of string items used for __repr__ and kllify

		@returns: List of strings
		'''
		output = []

		# Construct representation
		if not self.index is None:
			output.append( "{0}".format( self.valueStr( self.index ) ) )
		if not self.row is None:
			cur_out = "r:{0}".format( self.valueStr( self.row ) )
			output.append( cur_out )
		if not self.col is None:
			cur_out = "c:{0}".format( self.valueStr( self.col ) )
			output.append( cur_out )
		if not self.relRow is None:
			cur_out = "r:i"
			cur_out += self.relRow >= 0 and "+" or ""
			cur_out += "{0}".format( self.valueStr( self.relRow ) )
			output.append( cur_out )
		if not self.relCol is None:
			cur_out = "c:i"
			cur_out += self.relCol >= 0 and "+" or ""
			cur_out += "{0}".format( self.valueStr( self.relCol ) )
			output.append( cur_out )

		return output

	def __repr__( self ):
		return "{0}".format( self.outputStrList() )

	def kllify( self ):
		'''
		KLL syntax compatible output for PixelAddress object
		'''
		return ",".join( self.outputStrList() )


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

	def total_arg_bytes( self, capabilities_dict=None ):
		'''
		Calculate the total number of bytes needed for the args

		@param capabilities_dict: Dictionary of capabilities used, just in case no widths have been assigned

		return: Number of bytes
		'''
		# Zero if no args
		total_bytes = 0
		for index, arg in enumerate( self.arg_list ):
			# Lookup actual width if necessary (wasn't set explicitly)
			if capabilities_dict is not None and arg.width is None:
				total_bytes += capabilities_dict[ self.name ].association.arg_list[ index ].width

			# Otherwise use the set width
			else:
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

