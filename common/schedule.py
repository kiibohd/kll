#!/usr/bin/env python3
'''
KLL Schedule Containers
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



### Decorators ###

## Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'



### Classes ###

class Time:
	'''
	Time parameter
	'''
	def __init__( self, time, unit ):
		self.time = time
		self.unit = unit

	def __repr__( self ):
		return "{0}{1}".format( self.time, self.unit )


class Schedule:
	'''
	Identifier schedule
	Each schedule may have multiple parameters configuring how the element is scheduled

	Used for trigger and result elements
	'''
	def __init__( self ):
		self.parameters = None

	def setSchedule( self, parameters ):
		'''
		Applies given list of Schedule Parameters to Schedule

		None signifies an undefined schedule which allows free-form scheduling
		at either a later stage or at the convenience of the device firmware/driver

		If schedule is already set, do not overwrite, expressions are read inside->out
		'''
		# Ignore if already set
		if self.parameters is not None:
			return

		self.parameters = parameters

	def strSchedule( self, kll=False ):
		'''
		__repr__ of Schedule when multiple inheritance is used
		'''
		output = ""
		if self.parameters is not None:
			for index, param in enumerate( self.parameters ):
				if index > 0:
					output += ","
				output += "{0}".format( param.kllify() )
		return output

	def kllify( self ):
		'''
		KLL representation of object
		'''
		return self.strSchedule( kll=True )

	def __repr__( self ):
		return self.strSchedule()


class ScheduleParam:
	'''
	Schedule parameter

	In the case of a Timing parameter, the base type is unknown and must be inferred later
	'''
	def __init__( self, state, timing=None ):
		self.state = state
		self.timing = timing

		# Mutate class into the desired type
		if self.state in ['P', 'H', 'R', 'O', 'UP', 'UR']:
			self.__class__ = ButtonScheduleParam
		elif self.state in ['A', 'On', 'D', 'Off']:
			self.__class__ = IndicatorScheduleParam
		elif self.state is None and self.timing is not None:
			pass
		else:
			print( "{0} Invalid ScheduleParam state '{1}'".format( ERROR, self.state ) )

	def setTiming( self, timing ):
		'''
		Set parameter timing
		'''
		self.timing = timing

	def kllify( self ):
		'''
		KLL representation of ScheduleParam object
		'''
		output = ""
		if self.state is None and self.timing is not None:
			output += "{0}".format( self.timing )
		return output

	def __repr__( self ):
		output = ""
		if self.state is None and self.timing is not None:
			output += "{0}".format( self.timing )
		else:
			output += "??"
			print( "{0} Unknown ScheduleParam state '{1}'".format( ERROR, self.state ) )
		return output


class ButtonScheduleParam( ScheduleParam ):
	'''
	Button Schedule Parameter

	Accepts:
	P  - Press
	H  - Hold
	R  - Release
	O  - Off
	UP - Unique Press
	UR - Unique Release

	Timing specifiers are valid.
	Validity of specifiers are context dependent, and may error at a later stage, or be stripped altogether
	'''
	def __repr__( self ):
		output = "{0}".format( self.state )
		if self.timing is not None:
			output += ":{0}".format( self.timing )
		return output

	def kllify( self ):
		'''
		KLL representation of object
		'''
		return "{0}".format( self )


class AnalogScheduleParam( ScheduleParam ):
	'''
	Analog Schedule Parameter

	Accepts:
	Value from 0 to 100, indicating a percentage pressed

	XXX: Might be useful to accept decimal percentages
	'''
	def __init__( self, state ):
		self.state = state

	def __repr__( self ):
		return "Analog({0})".format( self.state )

	def kllify( self ):
		'''
		KLL representation of object
		'''
		return "{0}".format( self.state )


class IndicatorScheduleParam( ScheduleParam ):
	'''
	Indicator Schedule Parameter

	Accepts:
	A   - Activate
	On
	D   - Deactivate
	Off

	Timing specifiers are valid.
	Validity of specifiers are context dependent, and may error at a later stage, or be stripped altogether
	'''
	def __repr__( self ):
		output = "{0}".format( self.state )
		if self.timing is not None:
			output += ":{0}".format( self.timing )
		return output

	def kllify( self ):
		'''
		KLL representation of object
		'''
		return "{0}".format( self )

