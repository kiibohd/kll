#!/usr/bin/env python3
'''
KLL Parsing Expressions

This file contains various parsing rules and processors used by funcparserlib for KLL

REMEMBER: When editing parser BNF-like expressions, order matters. Specifically lexer tokens and parser |
'''

# Parser doesn't play nice with linters, disable some checks
# pylint: disable=no-self-argument, too-many-public-methods, no-self-use, bad-builtin

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

from common.hid_dict import kll_hid_lookup_dictionary

from common.id import (
	AnimationId, AnimationFrameId,
	CapArgId, CapId,
	HIDId,
	NoneId,
	PixelAddressId, PixelId, PixelLayerId,
	ScanCodeId
)
from common.modifier import AnimationModifierList
from common.schedule import AnalogScheduleParam, ScheduleParam, Time

from funcparserlib.lexer  import Token
from funcparserlib.parser import (some, a, many, oneplus, skip, maybe)




### Decorators ###

## Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'



### Classes ###

## Parsing Functions

class Make:
	'''
	Collection of parse string interpreters
	'''

	def scanCode( token ):
		'''
		Converts a raw scan code string into an ScanCodeId /w integer

		S0x10 -> 16
		'''
		if isinstance( token, int ):
			return ScanCodeId( token )
		else:
			return ScanCodeId( int( token[1:], 0 ) )

	def hidCode( type, token ):
		'''
		Convert a given raw hid token string to an integer /w a type

		U"Enter" -> USB, Enter(0x28)
		'''
		# If already converted to a HIDId, just return
		if isinstance( token, HIDId ):
			return token

		# If first character is a U or I, strip
		if token[0] == "U" or token[0] == "I":
			token = token[1:]
		# CONS specifier
		elif 'CONS' in token:
			token = token[4:]
		# SYS specifier
		elif 'SYS' in token:
			token = token[3:]

		# If using string representation of USB Code, do lookup, case-insensitive
		if '"' in token:
			try:
				hidCode = kll_hid_lookup_dictionary[ type ][ token[1:-1].upper() ][1]
			except LookupError as err:
				print ( "{0} {1} is an invalid USB HID Code Lookup...".format( ERROR, err ) )
				raise
		else:
			# Already tokenized
			if (
				type == 'USBCode' and token[0] == 'USB'
				or
				type == 'SysCode' and token[0] == 'SYS'
				or
				type == 'ConsCode' and token[0] == 'CONS'
				or
				type == 'IndCode' and token[0] == 'IND'
			):
				hidCode = token[1]
			# Convert
			else:
				hidCode = int( token, 0 )

		return HIDId( type, hidCode )


	def usbCode( token ):
		'''
		Convert a given raw USB Keyboard hid token string to an integer /w a type

		U"Enter" -> USB, Enter(0x28)
		'''
		return Make.hidCode( 'USBCode', token )

	def consCode( token ):
		'''
		Convert a given raw Consumer Control hid token string to an integer /w a type
		'''
		return Make.hidCode( 'ConsCode', token )

	def sysCode( token ):
		'''
		Convert a given raw System Control hid token string to an integer /w a type
		'''
		return Make.hidCode( 'SysCode', token )

	def indCode( token ):
		'''
		Convert a given raw Indicator hid token string to an integer /w a type
		'''
		return Make.hidCode( 'IndCode', token )

	def animation( name ):
		'''
		Converts a raw animation value into an AnimationId /w name

		A"myname" -> myname
		'''
		if name[0] == "A":
			return AnimationId( name[2:-1] )
		else:
			return AnimationId( name )

	def animationTrigger( animation, frame_indices ):
		'''
		Generate either an AnimationId or an AnimationFrameId

		frame_indices indicate that this is an AnimationFrameId
		'''
		trigger_list = []
		# AnimationFrameId
		if len( frame_indices ) > 0:
			for index in frame_indices:
				trigger_list.append( [ [ AnimationFrameId( animation, index ) ] ] )
		# AnimationId
		else:
			trigger_list.append( [ [ AnimationId( animation ) ] ] )

		return trigger_list

	def animationCapability( animation, modifiers ):
		'''
		Apply modifiers to AnimationId
		'''
		if modifiers is not None:
			animation.setModifiers( modifiers )
		return [ animation ]

	def animationModlist( modifiers ):
		'''
		Build an AnimationModifierList

		Only used for animation data association
		'''
		modlist = AnimationModifierList()
		modlist.setModifiers( modifiers )
		return modlist

	def pixelCapability( pixels, modifiers ):
		'''
		Apply modifiers to list of pixels/pixellists

		Results in a combination of pixel capabilities
		'''
		pixelcap_list = []
		for pixel in pixels:
			pixel.setModifiers( modifiers )
			pixelcap_list.append( pixel )
		return pixelcap_list

	def pixel( token ):
		'''
		Converts a raw pixel value into a PixelId /w integer

		P0x3 -> 3
		'''
		if isinstance( token, int ):
			return PixelId( token )
		else:
			return PixelId( int( token[1:], 0 ) )

	def pixel_list( pixel_list ):
		'''
		Converts a list a numbers into a list of PixelIds
		'''
		pixels = []
		for pixel in pixel_list:
			pixels.append( PixelId( pixel ) )
		return pixels

	def pixelLayer( token ):
		'''
		Converts a raw pixel layer value into a PixelLayerId /w integer

		PL0x3 -> 3
		'''
		if isinstance( token, int ):
			return PixelLayerId( token )
		else:
			return PixelLayerId( int( token[2:], 0 ) )

	def pixelLayer_list( layer_list ):
		'''
		Converts a list a numbers into a list of PixelLayerIds
		'''
		layers = []
		for layer in layer_list:
			layers.append( PixelLayerId( layer ) )
		return layers

	def pixelchan( pixel_list, chans ):
		'''
		Apply channels to PixelId

		Only one pixel at a time can be mapped, hence pixel_list[0]
		'''
		pixel = pixel_list[0]
		pixel.setChannels( chans )
		return pixel

	def pixelmod( pixels, modifiers ):
		'''
		Apply modifiers to list of pixels/pixellists

		Results in a combination of pixel capabilities
		'''
		pixelcap_list = []
		for pixel in pixels:
			# Convert HIDIds into PixelIds
			if isinstance( pixel, HIDId ) or isinstance( pixel, ScanCodeId ):
				pixel = PixelId( pixel )
			pixel.setModifiers( modifiers )
			pixelcap_list.append( pixel )
		return pixelcap_list

	def pixel_address( elems ) :
		'''
		Parse pixel positioning for row/column addressing

		@param elems:  index list or (operator, value)

		40
		c:0
		c:30%
		r:i+30
		'''
		pixel_address_list = []

		# Index list
		if isinstance( elems, list ):
			# List of integers, possibly a range
			if isinstance( elems[0], int ):
				for elem in elems:
					pixel_address_list.append( PixelAddressId( index=elem ) )
			# Already ready to append
			elif isinstance( elems[0], PixelId ):
				pixel_address_list.append( elems[0] )

		# No value
		elif isinstance( elems, Token ):
			# Row
			if "r:i" in elems.name:
				pixel_address_list.append( PixelAddressId( relRow=0 ) )
			# Column
			if "c:i" in elems.name:
				pixel_address_list.append( PixelAddressId( relCol=0 ) )

		# Operator with value
		elif isinstance( elems[0], Token ):
			# Prepare address value
			value = elems[1]

			# Positioning
			if elems[0].type == "ColRowOperator":
				# Row
				if elems[0].name == "r:":
					pixel_address_list.append( PixelAddressId( row=value ) )
				# Column
				if elems[0].name == "c:":
					pixel_address_list.append( PixelAddressId( col=value ) )

			# Relative Positioning
			elif elems[0].type == "RelCROperator":
				if '-' in elems[0].name:
					value *= -1

				# Row
				if "r:i" in elems[0].name:
					pixel_address_list.append( PixelAddressId( relRow=value ) )
				# Column
				if "c:i" in elems[0].name:
					pixel_address_list.append( PixelAddressId( relCol=value ) )

		return pixel_address_list

	def pixel_address_merge( elems ):
		'''
		Merge pixel addresses together
		'''
		# Merge is only necessary if there is more than one element
		if len( elems ) > 1:
			for elem in elems[1:]:
				elems[0].merge( elem )

		return [ elems[0] ]

	def position( token ):
		'''
		Physical position split

		x:20 -> (x, 20)
		'''
		return token.split(':')

	def usbCode_number( token ):
		'''
		USB Keyboard HID Code lookup
		'''
		return HIDId( 'USBCode', token )

	def consCode_number( token ):
		'''
		Consumer Control HID Code lookup
		'''
		return HIDId( 'ConsCode', token )

	def sysCode_number( token ):
		'''
		System Control HID Code lookup
		'''
		return HIDId( 'SysCode', token )

	def indCode_number( token ):
		'''
		Indicator HID Code lookup
		'''
		return HIDId( 'IndCode', token )

	def none( token ):
		'''
		Replace key-word with NoneId specifier (which indicates a noneOut capability)
		'''
		return [[[NoneId()]]]

	def seqString( token ):
		'''
		Converts sequence string to a sequence of combinations

		'Ab' -> U"Shift" + U"A", U"B"
		'''
		# TODO - Add locale support

		# Shifted Characters, and amount to move by to get non-shifted version
		# US ANSI
		shiftCharacters = (
			( "ABCDEFGHIJKLMNOPQRSTUVWXYZ", 0x20 ),
			( "+",       0x12 ),
			( "&(",      0x11 ),
			( "!#$%",    0x10 ),
			( "*",       0x0E ),
			( ")",       0x07 ),
			( '"',       0x05 ),
			( ":",       0x01 ),
			( "@",      -0x0E ),
			( "<>?",    -0x10 ),
			( "~",      -0x1E ),
			( "{}|",    -0x20 ),
			( "^",      -0x28 ),
			( "_",      -0x32 ),
		)

		listOfLists = []
		shiftKey = kll_hid_lookup_dictionary['USBCode']["SHIFT"]

		# Creates a list of USB codes from the string: sequence (list) of combos (lists)
		for char in token[1:-1]:
			processedChar = char

			# Whether or not to create a combo for this sequence with a shift
			shiftCombo = False

			# Depending on the ASCII character, convert to single character or Shift + character
			for pair in shiftCharacters:
				if char in pair[0]:
					shiftCombo = True
					processedChar = chr( ord( char ) + pair[1] )
					break

			# Do KLL HID Lookup on non-shifted character
			# NOTE: Case-insensitive, which is why the shift must be pre-computed
			usb_code = kll_hid_lookup_dictionary['USBCode'][ processedChar.upper() ]

			# Create Combo for this character, add shift key if shifted
			charCombo = []
			if shiftCombo:
				charCombo = [ [ HIDId( 'USBCode', shiftKey[1] ) ] ]
			charCombo.append( [ HIDId( 'USBCode', usb_code[1] ) ] )

			# Add to list of lists
			listOfLists.append( charCombo )

		return listOfLists

	def string( token ):
		'''
		Converts a raw string to a Python string

		"this string" -> this string
		'''
		return token[1:-1]

	def unseqString( token ):
		'''
		Converts a raw sequence string to a Python string

		'this string' -> this string
		'''
		return token[1:-1]

	def number( token ):
		'''
		Convert string number to Python integer
		'''
		return int( token, 0 )

	def percent( token ):
		'''
		Convert string percent to Python float
		'''
		return int( token[:-1], 0 ) / 100.0

	def timing( token ):
		'''
		Convert raw timing parameter to integer time and determine units

		1ms -> 1, ms
		'''
		# Find ms, us, or s
		if 'ms' in token:
			unit = 'ms'
			num = token.split('m')[0]
		elif 'us' in token:
			unit = 'us'
			num = token.split('u')[0]
		elif 'ns' in token:
			unit = 'ns'
			num = token.split('n')[0]
		elif 's' in token:
			unit = 's'
			num = token.split('s')[0]
		else:
			print ( "{0} cannot find timing unit in token '{1}'".format( ERROR, token ) )

		return Time( float( num ), unit )

	def specifierTiming( timing ):
		'''
		When only timing is given, infer state at a later stage from the context of the mapping
		'''
		return ScheduleParam( None, timing )

	def specifierState( state, timing=None ):
		'''
		Generate a Schedule Parameter
		Automatically mutates itself into the correct object type
		'''
		return ScheduleParam( state, timing )

	def specifierAnalog( value ):
		'''
		Generate an Analog Schedule Parameter
		'''
		return AnalogScheduleParam( value )

	def specifierUnroll( identifier, schedule_params ):
		'''
		Unroll specifiers into the trigger/result identifier

		First, combine all Schedule Parameters into a Schedul
		Then attach Schedule to the identifier

		If the identifier is a list, then iterate through them
		and apply the schedule to each
		'''
		# Check if this is a list of identifiers
		if isinstance( identifier, list ):
			for ident in identifier:
				ident.setSchedule( schedule_params )
			return identifier
		else:
			identifier.setSchedule( schedule_params )

		return [ identifier ]


	# Range can go from high to low or low to high
	def scanCode_range( rangeVals ):
		'''
		Scan Code range expansion

		S[0x10-0x12] -> S0x10, S0x11, S0x12
		'''
		start = rangeVals[0]
		end   = rangeVals[1]

		# Swap start, end if start is greater than end
		if start > end:
			start, end = end, start

		# Iterate from start to end, and generate the range
		values = list( range( start, end + 1 ) )

		# Generate ScanCodeIds
		return [ ScanCodeId( v ) for v in values ]

	# Range can go from high to low or low to high
	# Warn on 0-9 for USBCodes (as this does not do what one would expect) TODO
	# Lookup USB HID tags and convert to a number
	def hidCode_range( type, rangeVals ):
		'''
		HID Code range expansion

		U["A"-"C"] -> U"A", U"B", U"C"
		'''

		# Check if already integers
		if isinstance( rangeVals[0], int ):
			start = rangeVals[0]
		else:
			start = Make.hidCode( type, rangeVals[0] ).uid

		if isinstance( rangeVals[1], int ):
			end = rangeVals[1]
		else:
			end = Make.hidCode( type, rangeVals[1] ).uid

		# Swap start, end if start is greater than end
		if start > end:
			start, end = end, start

		# Iterate from start to end, and generate the range
		listRange = list( range( start, end + 1 ) )

		# Convert each item in the list to a tuple
		for item in range( len( listRange ) ):
			listRange[ item ] = HIDId( type, listRange[ item ] )
		return listRange

	def usbCode_range( rangeVals ):
		'''
		USB Keyboard HID Code range expansion
		'''
		return Make.hidCode_range( 'USBCode', rangeVals )

	def sysCode_range( rangeVals ):
		'''
		System Control HID Code range expansion
		'''
		return Make.hidCode_range( 'SysCode', rangeVals )

	def consCode_range( rangeVals ):
		'''
		Consumer Control HID Code range expansion
		'''
		return Make.hidCode_range( 'ConsCode', rangeVals )

	def indCode_range( rangeVals ):
		'''
		Indicator HID Code range expansion
		'''
		return Make.hidCode_range( 'IndCode', rangeVals )

	def range( start, end ):
		'''
		Converts a start and end points of a range to a list of numbers

		Can go low to high or high to low
		'''
		# High to low
		if end < start:
			return list( range( end, start + 1 ) )

		# Low to high
		return list( range( start, end + 1 ) )

	def capArg( argument, width=None ):
		'''
		Converts a capability argument:width to a CapArgId

		If no width is specified, it is ignored
		'''
		return CapArgId( argument, width )

	def capUsage( name, arguments ):
		'''
		Converts a capability tuple, argument list to a CapId Usage
		'''
		return CapId( name, 'Usage', arguments )

	def debug( tokens ):
		'''
		Just prints tokens
		Used for debugging
		'''
		print( tokens )
		return tokens



### Rules ###

## Base Rules

const       = lambda x: lambda _: x
unarg       = lambda f: lambda x: f(*x)
flatten     = lambda list: sum( list, [] )

tokenValue  = lambda x: x.value
tokenType   = lambda t: some( lambda x: x.type == t ) >> tokenValue
operator    = lambda s: a( Token( 'Operator', s ) ) >> tokenValue
parenthesis = lambda s: a( Token( 'Parenthesis', s ) ) >> tokenValue
bracket     = lambda s: a( Token( 'Bracket', s ) ) >> tokenValue
eol         = a( Token( 'EndOfLine', ';' ) )

def maybeFlatten( items ):
	'''
	Iterate through top-level lists
	Flatten, only if the element is also a list

	[[1,2],3,[[4,5]]] -> [1,2,3,[4,5]]
	'''
	new_list = []
	for elem in items:
		# Flatten only if a list
		if isinstance( elem, list ):
			new_list.extend( elem )
		else:
			new_list.append( elem )
	return new_list

def listElem( item ):
	'''
	Convert to a list element
	'''
	return [ item ]

def listToTuple( items ):
	'''
	Convert list to a tuple
	'''
	return tuple( items )

def oneLayerFlatten( items ):
	'''
	Flatten only the top layer (list of lists of ...)
	'''
	mainList = []
	for sublist in items:
		for item in sublist:
			mainList.append( item )

	return mainList

def optionExpansion( sequences ):
	'''
	Expand ranges of values in the 3rd dimension of the list, to a list of 2nd lists

	i.e. [ sequence, [ combo, [ range ] ] ] --> [ [ sequence, [ combo ] ], <option 2>, <option 3> ]
	'''
	expandedSequences = []

	# Total number of combinations of the sequence of combos that needs to be generated
	totalCombinations = 1

	# List of leaf lists, with number of leaves
	maxLeafList = []

	# Traverse to the leaf nodes, and count the items in each leaf list
	for sequence in sequences:
		for combo in sequence:
			rangeLen = len( combo )
			totalCombinations *= rangeLen
			maxLeafList.append( rangeLen )

	# Counter list to keep track of which combination is being generated
	curLeafList = [0] * len( maxLeafList )

	# Generate a list of permuations of the sequence of combos
	for count in range( 0, totalCombinations ):
		expandedSequences.append( [] ) # Prepare list for adding the new combination
		pos = 0

		# Traverse sequence of combos to generate permuation
		for sequence in sequences:
			expandedSequences[ -1 ].append( [] )
			for combo in sequence:
				expandedSequences[ -1 ][ -1 ].append( combo[ curLeafList[ pos ] ] )
				pos += 1

		# Increment combination tracker
		for leaf in range( 0, len( curLeafList ) ):
			curLeafList[ leaf ] += 1

			# Reset this position, increment next position (if it exists), then stop
			if curLeafList[ leaf ] >= maxLeafList[ leaf ]:
				curLeafList[ leaf ] = 0
				if leaf + 1 < len( curLeafList ):
					curLeafList[ leaf + 1 ] += 1

	return expandedSequences

def listit( t ):
	'''
	Convert tuple of tuples to list of lists
	'''
	return list( map( listit, t ) ) if isinstance( t, ( list, tuple ) ) else t

def tupleit( t ):
	'''
	Convert list of lists to tuple of tuples
	'''
	return tuple( map( tupleit, t ) ) if isinstance( t, ( tuple, list ) ) else t


## Sub Rules

usbCode       = tokenType('USBCode') >> Make.usbCode
scanCode      = tokenType('ScanCode') >> Make.scanCode
consCode      = tokenType('ConsCode') >> Make.consCode
sysCode       = tokenType('SysCode') >> Make.sysCode
indCode       = tokenType('IndCode') >> Make.indCode
animation     = tokenType('Animation') >> Make.animation
pixel         = tokenType('Pixel') >> Make.pixel
pixelLayer    = tokenType('PixelLayer') >> Make.pixelLayer
none          = tokenType('None') >> Make.none
position      = tokenType('Position') >> Make.position

comma         = tokenType('Comma')
content       = tokenType('VariableContents')
dash          = tokenType('Dash')
name          = tokenType('Name')
number        = tokenType('Number') >> Make.number
percent       = tokenType('Percent') >> Make.percent
plus          = tokenType('Plus')
timing        = tokenType('Timing') >> Make.timing

string        = tokenType('String') >> Make.string
unString      = tokenType('String') # When the double quotes are still needed for internal processing
seqString     = tokenType('SequenceString') >> Make.seqString
unseqString   = tokenType('SequenceString') >> Make.unseqString # For use with variables

colRowOperator = lambda s: a( Token( 'ColRowOperator', s ) )
relCROperator  = lambda s: a( Token( 'RelCROperator', s ) )
pixelOperator  = tokenType('PixelOperator')

# Code variants
code_begin = tokenType('CodeBegin')
code_end   = tokenType('CodeEnd')

# Specifier
specifier_basic   = ( timing >> Make.specifierTiming ) | ( name >> Make.specifierState )
specifier_complex = ( name + skip( operator(':') ) + timing ) >> unarg( Make.specifierState )
specifier_state   = specifier_complex | specifier_basic
specifier_analog  = number >> Make.specifierAnalog
specifier_list    = skip( parenthesis('(') ) + many( ( specifier_state | specifier_analog ) + skip( maybe( comma ) ) ) + skip( parenthesis(')') )

# Scan Codes
scanCode_start       = tokenType('ScanCodeStart')
scanCode_range       = number + skip( dash ) + number >> Make.scanCode_range
scanCode_listElem    = number >> Make.scanCode
scanCode_specifier   = ( scanCode_range | scanCode_listElem ) + maybe( specifier_list ) >> unarg( Make.specifierUnroll )
scanCode_innerList   = many( scanCode_specifier + skip( maybe( comma ) ) ) >> flatten
scanCode_expanded    = skip( scanCode_start ) + scanCode_innerList + skip( code_end ) + maybe( specifier_list ) >> unarg( Make.specifierUnroll )
scanCode_elem        = scanCode + maybe( specifier_list ) >> unarg( Make.specifierUnroll )
scanCode_combo       = oneplus( ( scanCode_expanded | scanCode_elem ) + skip( maybe( plus ) ) )
scanCode_sequence    = oneplus( scanCode_combo + skip( maybe( comma ) ) )
scanCode_single      = ( skip( scanCode_start ) + scanCode_listElem + skip( code_end ) ) | scanCode
scanCode_il_nospec   = oneplus( ( scanCode_range | scanCode_listElem ) + skip( maybe( comma ) ) )
scanCode_nospecifier = skip( scanCode_start ) + scanCode_il_nospec + skip( code_end )

# Cons Codes
consCode_start       = tokenType('ConsCodeStart')
consCode_number      = number >> Make.consCode_number
consCode_range       = ( consCode_number | unString ) + skip( dash ) + ( number | unString ) >> Make.consCode_range
consCode_listElemTag = unString >> Make.consCode
consCode_listElem    = ( consCode_number | consCode_listElemTag )
consCode_specifier   = ( consCode_range | consCode_listElem ) + maybe( specifier_list ) >> unarg( Make.specifierUnroll )
consCode_innerList   = oneplus( consCode_specifier + skip( maybe( comma ) ) ) >> flatten
consCode_expanded    = skip( consCode_start ) + consCode_innerList + skip( code_end ) + maybe( specifier_list ) >> unarg( Make.specifierUnroll )
consCode_elem        = consCode + maybe( specifier_list ) >> unarg( Make.specifierUnroll )
consCode_il_nospec   = oneplus( ( consCode_range | consCode_listElem ) + skip( maybe( comma ) ) )
consCode_nospecifier = skip( consCode_start ) + consCode_il_nospec + skip( code_end )

# Sys Codes
sysCode_start       = tokenType('SysCodeStart')
sysCode_number      = number >> Make.sysCode_number
sysCode_range       = ( sysCode_number | unString ) + skip( dash ) + ( number | unString ) >> Make.sysCode_range
sysCode_listElemTag = unString >> Make.sysCode
sysCode_listElem    = ( sysCode_number | sysCode_listElemTag )
sysCode_specifier   = ( sysCode_range | sysCode_listElem ) + maybe( specifier_list ) >> unarg( Make.specifierUnroll )
sysCode_innerList   = oneplus( sysCode_specifier + skip( maybe( comma ) ) ) >> flatten
sysCode_expanded    = skip( sysCode_start ) + sysCode_innerList + skip( code_end ) + maybe( specifier_list ) >> unarg( Make.specifierUnroll )
sysCode_elem        = sysCode + maybe( specifier_list ) >> unarg( Make.specifierUnroll )
sysCode_il_nospec   = oneplus( ( sysCode_range | sysCode_listElem ) + skip( maybe( comma ) ) )
sysCode_nospecifier = skip( sysCode_start ) + sysCode_il_nospec + skip( code_end )

# Indicator Codes
indCode_start       = tokenType('IndicatorStart')
indCode_number      = number >> Make.indCode_number
indCode_range       = ( indCode_number | unString ) + skip( dash ) + ( number | unString ) >> Make.indCode_range
indCode_listElemTag = unString >> Make.indCode
indCode_listElem    = ( indCode_number | indCode_listElemTag )
indCode_specifier   = ( indCode_range | indCode_listElem ) + maybe( specifier_list ) >> unarg( Make.specifierUnroll )
indCode_innerList   = oneplus( indCode_specifier + skip( maybe( comma ) ) ) >> flatten
indCode_expanded    = skip( indCode_start ) + indCode_innerList + skip( code_end ) + maybe( specifier_list ) >> unarg( Make.specifierUnroll )
indCode_elem        = indCode + maybe( specifier_list ) >> unarg( Make.specifierUnroll )
indCode_il_nospec   = oneplus( ( indCode_range | indCode_listElem ) + skip( maybe( comma ) ) )
indCode_nospecifier = skip( indCode_start ) + indCode_il_nospec + skip( code_end )

# USB Codes
usbCode_start       = tokenType('USBCodeStart')
usbCode_number      = number >> Make.usbCode_number
usbCode_range       = ( usbCode_number | unString ) + skip( dash ) + ( number | unString ) >> Make.usbCode_range
usbCode_listElemTag = unString >> Make.usbCode
usbCode_listElem    = ( usbCode_number | usbCode_listElemTag )
usbCode_specifier   = ( usbCode_range | usbCode_listElem ) + maybe( specifier_list ) >> unarg( Make.specifierUnroll )
usbCode_il_nospec   = oneplus( ( usbCode_range | usbCode_listElem ) + skip( maybe( comma ) ) )
usbCode_nospecifier = skip( usbCode_start ) + usbCode_il_nospec + skip( code_end )
usbCode_innerList   = oneplus( usbCode_specifier + skip( maybe( comma ) ) ) >> flatten
usbCode_expanded    = skip( usbCode_start ) + usbCode_innerList + skip( code_end ) + maybe( specifier_list ) >> unarg( Make.specifierUnroll )
usbCode_elem        = usbCode + maybe( specifier_list ) >> unarg( Make.specifierUnroll )

# HID Codes
hidCode_elem        = usbCode_expanded | usbCode_elem | sysCode_expanded | sysCode_elem | consCode_expanded | consCode_elem | indCode_expanded | indCode_elem

usbCode_combo       = oneplus( hidCode_elem + skip( maybe( plus ) ) ) >> listElem
usbCode_sequence    = oneplus( ( usbCode_combo | seqString ) + skip( maybe( comma ) ) ) >> oneLayerFlatten

# Pixels
pixel_start       = tokenType('PixelStart')
pixel_range       = ( number ) + skip( dash ) + ( number ) >> unarg( Make.range ) >> Make.pixel_address
pixel_listElem    = number >> listElem >> Make.pixel_address
pixel_pos         = ( colRowOperator('c:') | colRowOperator('r:') ) + ( number | percent ) >> Make.pixel_address
pixel_posRel      = ( relCROperator('c:i+') | relCROperator('c:i-') | relCROperator('r:i+') | relCROperator('r:i-') ) + ( number | percent ) >> Make.pixel_address
pixel_posRelHere  = ( relCROperator('c:i') | relCROperator('r:i') ) >> Make.pixel_address
pixel_posMerge    = oneplus( ( pixel_pos | pixel_posRel | pixel_posRelHere ) + skip( maybe( comma ) ) ) >> flatten >> Make.pixel_address_merge
pixel_innerList   = ( ( oneplus( ( pixel_range | pixel_listElem | pixel_posMerge ) + skip( maybe( comma ) ) ) >> flatten ) | ( pixel_posMerge ) ) >> Make.pixel_list
pixel_expanded    = skip( pixel_start ) + pixel_innerList + skip( code_end )
pixel_elem        = pixel >> listElem >> Make.pixel_address

# Pixel Layer
pixellayer_start     = tokenType('PixelLayerStart')
pixellayer_range     = ( number ) + skip( dash ) + ( number ) >> unarg( Make.range )
pixellayer_listElem  = number >> listElem
pixellayer_innerList = oneplus( ( pixellayer_range | pixellayer_listElem ) + skip( maybe( comma ) ) ) >> flatten >> Make.pixelLayer_list
pixellayer_expanded  = skip( pixellayer_start ) + pixellayer_innerList + skip( code_end )
pixellayer_elem      = pixelLayer >> listElem

# Pixel Channels
pixelchan_chans = many( number + skip( operator(':') ) + number + skip( maybe( comma ) ) )
pixelchan_elem  = ( ( pixel_expanded | pixel_elem ) + skip( parenthesis('(') ) + pixelchan_chans + skip( parenthesis(')') ) ) >> unarg( Make.pixelchan )

# HID Id for Pixel Mods
pixelmod_hid_elem = ( usbCode | sysCode | consCode | indCode | scanCode ) >> listElem
pixelmod_hid = pixelmod_hid_elem | usbCode_nospecifier | scanCode_nospecifier | consCode_nospecifier | sysCode_nospecifier | indCode_nospecifier

# Pixel Mods
pixelmod_modop = maybe( pixelOperator | plus | dash ) >> listElem
pixelmod_modva = number >> listElem
pixelmod_mods  = oneplus( ( pixelmod_modop + pixelmod_modva + skip( maybe( comma ) ) ) >> flatten )
pixelmod_layer = ( pixellayer_expanded | pixellayer_elem )
pixelmod_index = ( pixel_expanded | pixel_elem | pixelmod_hid | pixelmod_layer )
pixelmod_elem  = pixelmod_index + skip( parenthesis('(') ) + pixelmod_mods + skip( parenthesis(')') ) >> unarg( Make.pixelmod )

# Pixel Capability
pixel_capability = pixelmod_elem

# Animations
animation_start       = tokenType('AnimationStart')
animation_name        = name
animation_frame_range = ( number ) + skip( dash ) + ( number ) >> unarg( Make.range )
animation_name_frame  = many( ( animation_frame_range | number ) + skip( maybe( comma ) ) ) >> maybeFlatten
animation_def         = skip( animation_start ) + animation_name + skip( code_end ) >> Make.animation
animation_expanded    = skip( animation_start ) + animation_name + skip( maybe( comma ) ) + animation_name_frame + skip( code_end ) >> unarg( Make.animationTrigger )
animation_flattened   = animation_expanded >> flatten >> flatten
animation_elem        = animation

# Animation Modifier
animation_modifier = many( ( name | number ) + maybe( skip( operator(':') ) + number ) + skip( maybe( comma ) ) )
animation_modlist = animation_modifier >> Make.animationModlist

# Animation Capability
animation_capability = ( ( animation_def | animation_elem ) + maybe( skip( parenthesis('(') ) + animation_modifier + skip( parenthesis(')') ) ) ) >> unarg( Make.animationCapability )

# Capabilities
capFunc_argument  = number >> Make.capArg # TODO Allow for symbolic arguments, i.e. arrays and variables
capFunc_arguments = many( capFunc_argument + skip( maybe( comma ) ) )
capFunc_elem      = name + skip( parenthesis('(') ) + capFunc_arguments + skip( parenthesis(')') ) >> unarg( Make.capUsage ) >> listElem
capFunc_combo     = oneplus( ( hidCode_elem | capFunc_elem | animation_capability | pixel_capability ) + skip( maybe( plus ) ) ) >> listElem
capFunc_sequence  = oneplus( ( capFunc_combo | seqString ) + skip( maybe( comma ) ) ) >> oneLayerFlatten

# Trigger / Result Codes
triggerCode_outerList    = scanCode_sequence >> optionExpansion
triggerUSBCode_outerList = usbCode_sequence >> optionExpansion
resultCode_outerList     = ( ( capFunc_sequence >> optionExpansion ) | none )

# Positions
position_list = oneplus( position + skip( maybe( comma ) ) )

