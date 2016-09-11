#!/usr/bin/env python3
'''
KLL Data Organization
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

import copy
import re



### Decorators ###

## Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'

ansi_escape = re.compile(r'\x1b[^m]*m')



### Classes ###

class Data:
	'''
	Base class for KLL datastructures
	'''
	# Debug output formatters
	debug_output = {
		'add' : "\t\033[1;42;37m++\033[0m\033[1mADD KEY\033[1;42;37m++\033[0m \033[1m<==\033[0m {0}",
		'app' : "\t\033[1;45;37m**\033[0m\033[1mAPP KEY\033[1;45;37m**\033[0m \033[1m<==\033[0m {0}",
		'mod' : "\t\033[1;44;37m##\033[0m\033[1mMOD KEY\033[1;44;37m##\033[0m \033[1m<==\033[0m {0}",
		'rem' : "\t\033[1;41;37m--\033[0m\033[1mREM KEY\033[1;41;37m--\033[0m \033[1m<==\033[0m {0}",
		'drp' : "\t\033[1;43;37m@@\033[0m\033[1mDRP KEY\033[1;43;37m@@\033[0m \033[1m<==\033[0m {0}",
		'dup' : "\t\033[1;46;37m!!\033[0m\033[1mDUP KEY\033[1;46;37m!!\033[0m \033[1m<==\033[0m {0}",
	}

	def __init__( self, parent ):
		'''
		Initialize datastructure

		@param parent: Parent organization, used to query data from other datastructures
		'''
		self.data = {}
		self.parent = parent

	def add_expression( self, expression, debug ):
		'''
		Add expression to data structure

		May have multiple keys to add for a given expression

		@param expression: KLL Expression (fully tokenized and parsed)
		@param debug:      Enable debug output
		'''
		# Lookup unique keys for expression
		keys = expression.unique_keys()

		# Add/Modify expressions in datastructure
		for key, uniq_expr in keys:
			# Check which operation we are trying to do, add or modify
			if debug[0]:
				if key in self.data.keys():
					output = self.debug_output['mod'].format( key )
				else:
					output = self.debug_output['add'].format( key )
				print( debug[1] and output or ansi_escape.sub( '', output ) )

			self.data[ key ] = uniq_expr

	def merge( self, merge_in, debug ):
		'''
		Merge in the given datastructure to this datastructure

		This datastructure serves as the base.

		@param merge_in: Data structure from another organization to merge into this one
		@param debug:    Enable debug out
		'''
		# The default case is just to add the expression in directly
		for key, kll_expression in merge_in.data.items():
			# Display key:expression being merged in
			if debug[0]:
				output = merge_in.elem_str( key, True )
				print( debug[1] and output or ansi_escape.sub( '', output ), end="" )

			self.add_expression( kll_expression, debug )

	def reduction( self ):
		'''
		Simplifies datastructure

		Most of the datastructures don't have a reduction. Just do nothing in this case.
		'''
		pass

	def elem_str( self, key, single=False ):
		'''
		Debug output for a single element

		@param key:    Index to datastructure
		@param single: Setting to True will bold the key
		'''
		if single:
			return "\033[1;33m{0: <20}\033[0m \033[1;36;41m>\033[0m {1}\n".format( key, self.data[ key ] )
		else:
			return "{0: <20} \033[1;36;41m>\033[0m {1}\n".format( key, self.data[ key ] )

	def __repr__( self ):
		output = ""

		# Display sorted list of keys, along with the internal value
		for key in sorted( self.data ):
			output += self.elem_str( key )

		return output


class MappingData( Data ):
	'''
	KLL datastructure for data mapping

	ScanCode  trigger -> result
	USBCode   trigger -> result
	Animation trigger -> result
	'''
	def add_expression( self, expression, debug ):
		'''
		Add expression to data structure

		May have multiple keys to add for a given expression

		Map expressions insert into the datastructure according to their operator.

		+Operators+
		:   Add/Modify
		:+  Append
		:-  Remove
		::  Lazy Add/Modify

		i:  Add/Modify
		i:+ Append
		i:- Remove
		i:: Lazy Add/Modify

		The i or isolation operators are stored separately from the main ones.
		Each key is pre-pended with an i

		The :: or lazy operators act just like : operators, except that they will be ignore if the evaluation
		merge cannot resolve a ScanCode.

		@param expression: KLL Expression (fully tokenized and parsed)
		@param debug:      Enable debug output
		'''
		# Lookup unique keys for expression
		keys = expression.unique_keys()

		# Add/Modify expressions in datastructure
		for key, uniq_expr in keys:
			# Determine which the expression operator
			operator = expression.operator

			# Except for the : operator, all others have delayed action
			# Meaning, they change behaviour depending on how Contexts are merged
			# This means we can't simplify yet
			# In addition, :+ and :- are stackable, which means each key has a list of expressions
			# We append the operator to differentiate between the different types of delayed operations
			key = "{0}{1}".format( operator, key )

			# Determine if key exists already
			exists = key in self.data.keys()

			# Add/Modify
			if operator in [':', '::', 'i:', 'i::']:
				debug_tag = exists and 'mod' or 'add'

			# Append/Remove
			else:
				# Check to make sure we haven't already appended expression
				# Use the string representation to do the comparison (general purpose)
				if exists and "{0}".format( uniq_expr ) in [ "{0}".format( elem ) for elem in self.data[ key ] ]:
					debug_tag = 'dup'

				# Append
				elif operator in [':+', 'i:+']:
					debug_tag = 'app'

				# Remove
				else:
					debug_tag = 'rem'

			# Debug output
			if debug[0]:
				output = self.debug_output[ debug_tag ].format( key )
				print( debug[1] and output or ansi_escape.sub( '', output ) )

			# Don't append if a duplicate
			if debug_tag == 'dup':
				continue

			# Append, rather than replace
			if operator in [':+', ':-', 'i:+', 'i:-']:
				if exists:
					self.data[ key ].append( uniq_expr )

				# Create initial list
				else:
					self.data[ key ] = [ uniq_expr ]
			else:
				self.data[ key ] = [ uniq_expr ]

	def set_interconnect_id( self, interconnect_id, triggers ):
		'''
		Traverses the sequence of combo of identifiers to set the interconnect_id
		'''
		for sequence in triggers:
			for combo in sequence:
				for identifier in combo:
					identifier.interconnect_id = interconnect_id

	def merge( self, merge_in, debug ):
		'''
		Merge in the given datastructure to this datastructure

		This datastructure serves as the base.

		Map expressions merge differently than insertions.

		+Operators+
		:   Add/Modify       - Replace
		:+  Append           - Add
		:-  Remove           - Remove
		::  Lazy Add/Modify  - Replace if found, otherwise drop

		i:  Add/Modify       - Replace
		i:+ Append           - Add
		i:- Remove           - Remove
		i:: Lazy Add/Modify  - Replace if found, otherwise drop

		@param merge_in: Data structure from another organization to merge into this one
		@param debug:    Enable debug out
		'''
		# Check what the current interconnectId is
		# If not set, we set to 0 (default)
		# We use this to calculate the scancode during the DataAnalysisStage
		interconnect_id = 0
		if 'interconnectId' in self.parent.variable_data.data.keys():
			interconnect_id = self.parent.variable_data.data['interconnectId']

		# Sort different types of keys
		cur_keys = merge_in.data.keys()

		# Lazy Set ::
		lazy_keys = [ key for key in cur_keys if key[0:2] == '::' or key[0:3] == 'i::' ]
		cur_keys = list( set( cur_keys ) - set( lazy_keys ) )

		# Append :+
		append_keys = [ key for key in cur_keys if key[0:2] == ':+' or key[0:3] == 'i:+' ]
		cur_keys = list( set( cur_keys ) - set( append_keys ) )

		# Remove :-
		remove_keys = [ key for key in cur_keys if key[0:2] == ':-' or key[0:3] == 'i:-' ]
		cur_keys = list( set( cur_keys ) - set( remove_keys ) )

		# Set :
		# Everything left is just a set
		set_keys = cur_keys


		# First process the :: (or lazy) operators
		# We need to read into this datastructure and apply those first
		# Otherwise we may get undesired behaviour
		for key in lazy_keys:
			# Display key:expression being merged in
			if debug[0]:
				output = merge_in.elem_str( key, True )
				print( debug[1] and output or ansi_escape.sub( '', output ), end="" )

			# Construct target key
			target_key = key[0] == 'i' and "i{0}".format( key[2:] ) or key[1:]

			# If target key exists, replace
			if target_key in self.data.keys():
				debug_tag = 'mod'
			else:
				debug_tag = 'drp'

			# Debug output
			if debug[0]:
				output = self.debug_output[ debug_tag ].format( key )
				print( debug[1] and output or ansi_escape.sub( '', output ) )

			# Only replace
			if debug_tag == 'mod':
				self.data[ target_key ] = merge_in.data[ key ]

		# Then apply : assignment operators
		for key in set_keys:
			# Display key:expression being merged in
			if debug[0]:
				output = merge_in.elem_str( key, True )
				print( debug[1] and output or ansi_escape.sub( '', output ), end="" )

			# Construct target key
			target_key = key

			# Indicate if add or modify
			if target_key in self.data.keys():
				debug_tag = 'mod'
			else:
				debug_tag = 'add'

			# Debug output
			if debug[0]:
				output = self.debug_output[ debug_tag ].format( key )
				print( debug[1] and output or ansi_escape.sub( '', output ) )

			# Set into new datastructure regardless
			self.data[ target_key ] = merge_in.data[ key ]

			# Only the : is used to set ScanCodes
			# We need to set the interconnect_id just in case the base context has it set
			# and in turn influence the new context as well
			# This must be done during the merge
			for elem in self.data[ target_key ]:
				if elem.type == 'ScanCode':
					self.set_interconnect_id( interconnect_id, elem.triggers )

		# Now apply append operations
		for key in append_keys:
			# Display key:expression being merged in
			if debug[0]:
				output = merge_in.elem_str( key, True )
				print( debug[1] and output or ansi_escape.sub( '', output ), end="" )

			# Construct target key
			target_key = key[0] == 'i' and "i:{0}".format( key[3:] ) or ":{0}".format( key[2:] )

			# Alwyays appending
			debug_tag = 'app'

			# Debug output
			if debug[0]:
				output = self.debug_output[ debug_tag ].format( key )
				print( debug[1] and output or ansi_escape.sub( '', output ) )

			# Extend list if it exists
			if target_key in self.data.keys():
				self.data[ target_key ].extend( merge_in.data[ key ] )
			else:
				self.data[ target_key ] = merge_in.data[ key ]

		# Finally apply removal operations to this datastructure
		# If the target removal doesn't exist, ignore silently (show debug message)
		for key in remove_keys:
			# Display key:expression being merged in
			if debug[0]:
				output = merge_in.elem_str( key, True )
				print( debug[1] and output or ansi_escape.sub( '', output ), end="" )

			# Construct target key
			target_key = key[0] == 'i' and "i:{0}".format( key[3:] ) or ":{0}".format( key[2:] )

			# Drop right away if target datastructure doesn't have target key
			if target_key not in self.data.keys():
				debug_tag = 'drp'

				# Debug output
				if debug[0]:
					output = self.debug_output[ debug_tag ].format( key )
					print( debug[1] and output or ansi_escape.sub( '', output ) )

				continue

			# Compare expressions to be removed with the current set
			# Use strings to compare
			remove_expressions = [ "{0}".format( expr ) for expr in merge_in.data[ key ] ]
			current_expressions = [ ( "{0}".format( expr ), expr ) for expr in self.data[ target_key ] ]
			for string, expr in current_expressions:
				debug_tag = 'drp'

				# Check if an expression matches
				if string in remove_expressions:
					debug_tag = 'rem'

				# Debug output
				if debug[0]:
					output = self.debug_output[ debug_tag ].format( key )
					print( debug[1] and output or ansi_escape.sub( '', output ) )

				# Remove if found
				if debug_tag == 'rem':
					self.data[ target_key ] = [ value for value in self.data.values() if value != expr ]

	def reduction( self ):
		'''
		Simplifies datastructure

		Used to replace all trigger HIDCode(USBCode)s with ScanCodes

		NOTE: Make sure to create a new MergeContext before calling this as you lose data and prior context
		'''
		scan_code_lookup = {}

		# Build dictionary of single ScanCodes first
		for key, expr in self.data.items():
			if expr[0].elems()[0] == 1 and expr[0].triggers[0][0][0].type == 'ScanCode':
				scan_code_lookup[ key ] = expr

		# Using this dictionary, replace all the trigger USB codes
		new_data = copy.copy( scan_code_lookup )

		# 1) Single USB Codes trigger results will replace the original ScanCode result
		# 2) 

		#TODO
		#print("YAY")
		#print( scan_code_lookup )


class AnimationData( Data ):
	'''
	KLL datastructure for Animation configuration

	Animation -> modifiers
	'''


class AnimationFrameData( Data ):
	'''
	KLL datastructure for Animation Frame configuration

	Animation -> Pixel Settings
	'''


class CapabilityData( Data ):
	'''
	KLL datastructure for Capability mapping

	Capability -> C Function/Identifier
	'''


class DefineData( Data ):
	'''
	KLL datastructure for Define mapping

	Variable -> C Define/Identifier
	'''


class PixelChannelData( Data ):
	'''
	KLL datastructure for Pixel Channel mapping

	Pixel -> Channels
	'''


class PixelPositionData( Data ):
	'''
	KLL datastructure for Pixel Position mapping

	Pixel -> Physical Location
	'''


class ScanCodePositionData( Data ):
	'''
	KLL datastructure for ScanCode Position mapping

	ScanCode -> Physical Location
	'''


class VariableData( Data ):
	'''
	KLL datastructure for Variables and Arrays

	Variable -> Data
	Array    -> Data
	'''


class Organization:
	'''
	Container class for KLL datastructures

	The purpose of these datastructures is to symbolically store at first, and slowly solve/deduplicate expressions.
	Since the order in which the merges occurs matters, this involves a number of intermediate steps.
	'''

	def __init__( self ):
		'''
		Intialize data structure
		'''
		# Setup each of the internal sub-datastructures
		self.animation_data          = AnimationData( self )
		self.animation_frame_data    = AnimationFrameData( self )
		self.capability_data         = CapabilityData( self )
		self.define_data             = DefineData( self )
		self.mapping_data            = MappingData( self )
		self.pixel_channel_data      = PixelChannelData( self )
		self.pixel_position_data     = PixelPositionData( self )
		self.scan_code_position_data = ScanCodePositionData( self )
		self.variable_data           = VariableData( self )

		# Expression to Datastructure mapping
		self.data_mapping = {
			'AssignmentExpression' : {
				'Array'    : self.variable_data,
				'Variable' : self.variable_data,
			},
			'DataAssociationExpression' : {
				'Animation'        : self.animation_data,
				'AnimationFrame'   : self.animation_frame_data,
				'PixelPosition'    : self.pixel_position_data,
				'ScanCodePosition' : self.scan_code_position_data,
			},
			'MapExpression' : {
				'ScanCode'     : self.mapping_data,
				'USBCode'      : self.mapping_data,
				'Animation'    : self.mapping_data,
				'PixelChannel' : self.pixel_channel_data,
			},
			'NameAssociationExpression' : {
				'Capability' : self.capability_data,
				'Define'     : self.define_data,
			},
		}

	def stores( self ):
		'''
		Returns list of sub-datastructures
		'''
		return [
			self.animation_data,
			self.animation_frame_data,
			self.capability_data,
			self.define_data,
			self.mapping_data,
			self.pixel_channel_data,
			self.pixel_position_data,
			self.scan_code_position_data,
			self.variable_data,
		]

	def add_expression( self, expression, debug ):
		'''
		Add expression to datastructure

		Will automatically determine which type of expression and place in the relevant store

		@param expression: KLL Expression (fully tokenized and parsed)
		@param debug:      Enable debug output
		'''
		# Determine type of of Expression
		expression_type = expression.__class__.__name__

		# Determine Expression Subtype
		expression_subtype = expression.type

		# Locate datastructure
		data = self.data_mapping[ expression_type ][ expression_subtype ]

		# Debug output
		if debug[0]:
			output = "\t\033[4m{0}\033[0m".format( data.__class__.__name__ )
			print( debug[1] and output or ansi_escape.sub( '', output ) )

		# Add expression to determined datastructure
		data.add_expression( expression, debug )

	def merge( self, merge_in, debug ):
		'''
		Merge in the given organization to this organization

		This organization serves as the base.

		@param merge_in: Organization to merge into this one
		@param debug:    Enable debug out
		'''
		# Merge each of the sub-datastructures
		for this, that in zip( self.stores(), merge_in.stores() ):
			this.merge( that, debug )

	def reduction( self ):
		'''
		Simplifies datastructure

		NOTE: This will remove data, therefore, context is lost
		'''
		for store in self.stores():
			store.reduction()

	def __repr__( self ):
		return "{0}".format( self.stores() )

