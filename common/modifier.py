#!/usr/bin/env python3
'''
KLL Modifier Containers
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

## Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'



### Classes ###

class AnimationModifier:
	'''
	Animation modification container class
	'''
	def __init__( self, name, value=None ):
		self.name = name
		self.value = value

	def __repr__( self ):
		if self.value is None:
			return "{0}".format( self.name )
		return "{0}:{1}".format( self.name, self.value )

	def kllify( self ):
		'''
		Returns KLL version of the Modifier

		In most cases we can just the string representation of the object
		'''
		return "{0}".format( self )


class AnimationModifierList:
	'''
	Animation modification container list class

	Contains a list of modifiers, the order does not matter
	'''
	def __init__( self ):
		self.modifiers = []

	def setModifiers( self, modifier_list ):
		'''
		Apply modifiers to Animation
		'''
		for modifier in modifier_list:
			self.modifiers.append( AnimationModifier( modifier[0], modifier[1] ) )

	def strModifiers( self ):
		'''
		__repr__ of Position when multiple inheritance is used
		'''
		output = ""
		for index, modifier in enumerate( self.modifiers ):
			if index > 0:
				output += ","
			output += "{0}".format( modifier )

		return output

	def __repr__( self ):
		return self.strModifiers()

	def kllify( self ):
		'''
		Returns KLL version of the ModifierList

		In most cases we can just the string representation of the object
		'''
		return "{0}".format( self )


class PixelModifier:
	'''
	Pixel modification container class
	'''
	def __init__( self, operator, value ):
		self.operator = operator
		self.value = value

	def __repr__( self ):
		if self.operator is None:
			return "{0}".format( self.value )
		return "{0}{1}".format( self.operator, self.value )

	def operator_type( self ):
		'''
		Returns operator type
		'''
		types = {
			None : 'Set',
			'+'  : 'Add',
			'-'  : 'Subtract',
			'+:' : 'NoRoll_Add',
			'-:' : 'NoRoll_Subtract',
			'<<' : 'LeftShift',
			'>>' : 'RightShift',
		}
		return types[ self.operator ]

	def kllify( self ):
		'''
		Returns KLL version of the PixelModifier

		In most cases we can just the string representation of the object
		'''
		return "{0}".format( self )


class PixelModifierList:
	'''
	Pixel modification container list class

	Contains a list of modifiers
	Index 0, corresponds to pixel 0
	'''
	def __init__( self ):
		self.modifiers = []

	def setModifiers( self, modifier_list ):
		'''
		Apply modifier to each pixel channel
		'''
		for modifier in modifier_list:
			self.modifiers.append( PixelModifier( modifier[0], modifier[1] ) )

	def strModifiers( self ):
		'''
		__repr__ of Position when multiple inheritance is used
		'''
		output = ""
		for index, modifier in enumerate( self.modifiers ):
			if index > 0:
				output += ","
			output += "{0}".format( modifier )

		return output

	def __repr__( self ):
		return self.strModifiers()

	def kllify( self ):
		'''
		Returns KLL version of the PixelModifierList

		In most cases we can just the string representation of the object
		'''
		return "{0}".format( self )

