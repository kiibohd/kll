#!/usr/bin/env python3
# KLL Compiler
# Keyboard Layout Langauge
#
# Copyright (C) 2014-2016 by Jacob Alexander
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

import argparse
import importlib
import io
import os
import re
import sys
import token

from pprint   import pformat
from re       import VERBOSE
from tokenize import generate_tokens

from kll_lib.containers import *
from kll_lib.hid_dict   import *

from funcparserlib.lexer  import make_tokenizer, Token, LexerError
from funcparserlib.parser import (some, a, many, oneplus, skip, finished, maybe, skip, forward_decl, NoParseError)



### Decorators ###

 ## Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'


 ## Python Text Formatting Fixer...
 ##  Because the creators of Python are averse to proper capitalization.
textFormatter_lookup = {
	"usage: "            : "Usage: ",
	"optional arguments" : "Optional Arguments",
}

def textFormatter_gettext( s ):
	return textFormatter_lookup.get( s, s )

argparse._ = textFormatter_gettext



### Argument Parsing ###

def checkFileExists( filename ):
	if not os.path.isfile( filename ):
		print ( "{0} {1} does not exist...".format( ERROR, filename ) )
		sys.exit( 1 )

def processCommandLineArgs():
	# Setup argument processor
	pArgs = argparse.ArgumentParser(
		usage="%(prog)s [options] <file1>...",
		description="Generates .h file state tables and pointer indices from KLL .kll files.",
		epilog="Example: {0} mykeyboard.kll -d colemak.kll -p hhkbpro2.kll -p symbols.kll".format( os.path.basename( sys.argv[0] ) ),
		formatter_class=argparse.RawTextHelpFormatter,
		add_help=False,
	)

	# Positional Arguments
	pArgs.add_argument( 'files', type=str, nargs='+',
		help=argparse.SUPPRESS ) # Suppressed help output, because Python output is verbosely ugly

	# Optional Arguments
	pArgs.add_argument( '-b', '--backend', type=str, default="kiibohd",
		help="Specify target backend for the KLL compiler.\n"
		"Default: kiibohd\n"
		"Options: kiibohd" )
	pArgs.add_argument( '-d', '--default', type=str, nargs='+',
		help="Specify .kll files to layer on top of the default map to create a combined map." )
	pArgs.add_argument( '-p', '--partial', type=str, nargs='+', action='append',
		help="Specify .kll files to generate partial map, multiple files per flag.\n"
		"Each -p defines another partial map.\n"
		"Base .kll files (that define the scan code maps) must be defined for each partial map." )
	pArgs.add_argument( '-t', '--templates', type=str, nargs='+',
		help="Specify template used to generate the keymap.\n"
		"Default: <backend specific>" )
	pArgs.add_argument( '-o', '--outputs', type=str, nargs='+',
		help="Specify output file. Writes to current working directory by default.\n"
		"Default: <backend specific>" )
	pArgs.add_argument( '-h', '--help', action="help",
		help="This message." )

	# Process Arguments
	args = pArgs.parse_args()

	# Parameters
	baseFiles = args.files
	defaultFiles = args.default
	partialFileSets = args.partial
	if defaultFiles is None:
		defaultFiles = []
	if partialFileSets is None:
		partialFileSets = [[]]

	# Check file existance
	for filename in baseFiles:
		checkFileExists( filename )

	for filename in defaultFiles:
		checkFileExists( filename )

	for partial in partialFileSets:
		for filename in partial:
			checkFileExists( filename )

	return (baseFiles, defaultFiles, partialFileSets, args.backend, args.templates, args.outputs)



### Tokenizer ###

def tokenize( string ):
	"""str -> Sequence(Token)"""

	# Basic Tokens Spec
	specs = [
		( 'Comment',          ( r' *#.*', ) ),
		( 'Space',            ( r'[ \t\r\n]+', ) ),
		( 'USBCode',          ( r'U(("[^"]+")|(0x[0-9a-fA-F]+)|([0-9]+))', ) ),
		( 'USBCodeStart',     ( r'U\[', ) ),
		( 'ConsCode',         ( r'CONS(("[^"]+")|(0x[0-9a-fA-F]+)|([0-9]+))', ) ),
		( 'ConsCodeStart',    ( r'CONS\[', ) ),
		( 'SysCode',          ( r'SYS(("[^"]+")|(0x[0-9a-fA-F]+)|([0-9]+))', ) ),
		( 'SysCodeStart',     ( r'SYS\[', ) ),
		( 'ScanCode',         ( r'S((0x[0-9a-fA-F]+)|([0-9]+))', ) ),
		( 'ScanCodeStart',    ( r'S\[', ) ),
		( 'Indicator',        ( r'I(("[^"]+")|(0x[0-9a-fA-F]+)|([0-9]+))', ) ),
		( 'IndicatorStart',   ( r'I\[', ) ),
		( 'Pixel',            ( r'P"[^"]+"', ) ),
		( 'PixelStart',       ( r'P\[', ) ),
		( 'PixelLayer',       ( r'PL"[^"]+"', ) ),
		( 'PixelLayerStart',  ( r'PL\[', ) ),
		( 'Animation',        ( r'A"[^"]+"', ) ),
		( 'AnimationStart',   ( r'A\[', ) ),
		( 'CodeBegin',        ( r'\[', ) ),
		( 'CodeEnd',          ( r'\]', ) ),
		( 'Position',         ( r'r?[xyz]:[0-9]+(.[0-9]+)?', ) ),
		( 'String',           ( r'"[^"]*"', ) ),
		( 'SequenceString',   ( r"'[^']*'", ) ),
		( 'PixelOperator',    ( r'(\+:|-:|>>|<<)', ) ),
		( 'Operator',         ( r'=>|<=|:\+|:-|::|:|=', ) ),
		( 'Comma',            ( r',', ) ),
		( 'Dash',             ( r'-', ) ),
		( 'Plus',             ( r'\+', ) ),
		( 'Parenthesis',      ( r'\(|\)', ) ),
		( 'None',             ( r'None', ) ),
		( 'Timing',           ( r'[0-9]+(.[0-9]+)?((s)|(ms)|(us))', ) ),
		( 'Number',           ( r'-?(0x[0-9a-fA-F]+)|(0|([1-9][0-9]*))', VERBOSE ) ),
		( 'Name',             ( r'[A-Za-z_][A-Za-z_0-9]*', ) ),
		( 'VariableContents', ( r'''[^"' ;:=>()]+''', ) ),
		( 'EndOfLine',        ( r';', ) ),
	]

	# Tokens to filter out of the token stream
	useless = ['Space', 'Comment']

	tokens = make_tokenizer( specs )
	return [x for x in tokens( string ) if x.type not in useless]



### Parsing ###

 ## Map Arrays
macros_map        = Macros()
variables_dict    = Variables()
capabilities_dict = Capabilities()


 ## Parsing Functions

class Make:
	def scanCode( token ):
		scanCode = int( token[1:], 0 )
		# Check size, to make sure it's valid
		# XXX Add better check that takes symbolic names into account (i.e. U"Latch5")
		#if scanCode > 0xFF:
		#	print ( "{0} ScanCode value {1} is larger than 255".format( ERROR, scanCode ) )
		#	raise
		return scanCode

	def hidCode( type, token ):
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
			if type == 'USBCode' and token[0] == 'USB' or type == 'SysCode' and token[0] == 'SYS' or type == 'ConsCode' and token[0] == 'CONS':
				hidCode = token[1]
			# Convert
			else:
				hidCode = int( token, 0 )

		# Check size if a USB Code, to make sure it's valid
		# XXX Add better check that takes symbolic names into account (i.e. U"Latch5")
		#if type == 'USBCode' and hidCode > 0xFF:
		#	print ( "{0} USBCode value {1} is larger than 255".format( ERROR, hidCode ) )
		#	raise

		# Return a tuple, identifying which type it is
		if type == 'USBCode':
			return Make.usbCode_number( hidCode )
		elif type == 'ConsCode':
			return Make.consCode_number( hidCode )
		elif type == 'SysCode':
			return Make.sysCode_number( hidCode )
		elif type == 'IndCode':
			return Make.indCode_number( hidCode )

		print ( "{0} Unknown HID Specifier '{1}'".format( ERROR, type ) )
		raise

	def usbCode( token ):
		return Make.hidCode( 'USBCode', token )

	def consCode( token ):
		return Make.hidCode( 'ConsCode', token )

	def sysCode( token ):
		return Make.hidCode( 'SysCode', token )

	def indCode( token ):
		return Make.hidCode( 'IndCode', token )

	def animation( token ):
		# TODO
		print( token )
		return "NULL"

	def animationCapability( token ):
		# TODO
		print( token )
		return "DIS"

	def pixelCapability( token ):
		# TODO
		print( token )
		return "DAT"

	def pixel( token ):
		# TODO
		print( token )
		return "PNULL"

	def pixelLayer( token ):
		# TODO
		print( token )
		return "PLNULL"

	def pixelchans( token ):
		# Create dictionary list
		channel_widths = []
		for elem in token:
			channel_widths.append( {
				'chan'  : elem[0],
				'width' : elem[1],
			} )
		print(channel_widths)
		return channel_widths

	def pixelchan_elem( token ):
		channel_config = {
			'pixels' : token[0],
			'chans' : token[1],
		}
		return channel_config

	def pixelmods( token ):
		# TODO
		print( token )
		return "PMOD"

	def pixellayer( token ):
		# TODO
		print( token )
		return "PL"

	def position( token ):
		return token.split(':')

	def hidCode_number( type, token ):
		lookup = {
			'ConsCode' : 'CONS',
			'SysCode'  : 'SYS',
			'USBCode'  : 'USB',
			'IndCode'  : 'LED',
		}
		return ( lookup[ type ], token )

	def usbCode_number( token ):
		return Make.hidCode_number( 'USBCode', token )

	def consCode_number( token ):
		return Make.hidCode_number( 'ConsCode', token )

	def sysCode_number( token ):
		return Make.hidCode_number( 'SysCode', token )

	def indCode_number( token ):
		return Make.hidCode_number( 'IndCode', token )

	   # Replace key-word with None specifier (which indicates a noneOut capability)
	def none( token ):
		return [[[('NONE', 0)]]]

	def seqString( token ):
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
			usbCode = kll_hid_lookup_dictionary['USBCode'][ processedChar.upper() ]

			# Create Combo for this character, add shift key if shifted
			charCombo = []
			if shiftCombo:
				charCombo = [ [ shiftKey ] ]
			charCombo.append( [ usbCode ] )

			# Add to list of lists
			listOfLists.append( charCombo )

		return listOfLists

	def string( token ):
		return token[1:-1]

	def unseqString( token ):
		return token[1:-1]

	def number( token ):
		return int( token, 0 )

	def timing( token ):
		# Find ms, us, or s
		if 'ms' in token:
			unit = 'ms'
			num = token.split('m')[0]
			print (token.split('m'))
		elif 'us' in token:
			unit = 'us'
			num = token.split('u')[0]
		elif 's' in token:
			unit = 's'
			num = token.split('s')[0]
		else:
			print ( "{0} cannot find timing unit in token '{1}'".format( ERROR, token ) )
			return "NULL"

		print ( num, unit )
		ret = {
			'time' : float( num ),
			'unit' : unit,
		}
		return ret

	def specifierState( values ):
		# TODO
		print ( values )
		return "SPECSTATE"

	def specifierAnalog( value ):
		# TODO
		print( value )
		return "SPECANALOG"

	def specifierUnroll( value ):
		# TODO
		print( value )
		return [ value[0] ]

	  # Range can go from high to low or low to high
	def scanCode_range( rangeVals ):
		start = rangeVals[0]
		end   = rangeVals[1]

		# Swap start, end if start is greater than end
		if start > end:
			start, end = end, start

		# Iterate from start to end, and generate the range
		return list( range( start, end + 1 ) )

	  # Range can go from high to low or low to high
	  # Warn on 0-9 for USBCodes (as this does not do what one would expect) TODO
	  # Lookup USB HID tags and convert to a number
	def hidCode_range( type, rangeVals ):
		# Check if already integers
		if isinstance( rangeVals[0], int ):
			start = rangeVals[0]
		else:
			start = Make.hidCode( type, rangeVals[0] )[1]

		if isinstance( rangeVals[1], int ):
			end = rangeVals[1]
		else:
			end = Make.hidCode( type, rangeVals[1] )[1]

		# Swap start, end if start is greater than end
		if start > end:
			start, end = end, start

		# Iterate from start to end, and generate the range
		listRange = list( range( start, end + 1 ) )

		# Convert each item in the list to a tuple
		for item in range( len( listRange ) ):
			listRange[ item ] = Make.hidCode_number( type, listRange[ item ] )
		return listRange

	def usbCode_range( rangeVals ):
		return Make.hidCode_range( 'USBCode', rangeVals )

	def sysCode_range( rangeVals ):
		return Make.hidCode_range( 'SysCode', rangeVals )

	def consCode_range( rangeVals ):
		return Make.hidCode_range( 'ConsCode', rangeVals )

	def indCode_range( rangeVals ):
		return Make.hidCode_range( 'IndCode', rangeVals )

	def range( rangeVals ):
		# TODO
		print (rangeVals)
		return ""


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

def listElem( item ):
	return [ item ]

def listToTuple( items ):
	return tuple( items )

  # Flatten only the top layer (list of lists of ...)
def oneLayerFlatten( items ):
	mainList = []
	for sublist in items:
		for item in sublist:
			mainList.append( item )

	return mainList

  # Capability arguments may need to be expanded (e.g. 1 16 bit argument needs to be 2 8 bit arguments for the state machine)
def capArgExpander( items ):
	newArgs = []
	# For each defined argument in the capability definition
	for arg in range( 0, len( capabilities_dict[ items[0] ][1] ) ):
		argLen = capabilities_dict[ items[0] ][1][ arg ][1]
		num = items[1][ arg ]
		byteForm = num.to_bytes( argLen, byteorder='little' ) # XXX Yes, little endian from how the uC structs work

		# For each sub-argument, split into byte-sized chunks
		for byte in range( 0, argLen ):
			newArgs.append( byteForm[ byte ] )

	return tuple( [ items[0], tuple( newArgs ) ] )

  # Expand ranges of values in the 3rd dimension of the list, to a list of 2nd lists
  # i.e. [ sequence, [ combo, [ range ] ] ] --> [ [ sequence, [ combo ] ], <option 2>, <option 3> ]
def optionExpansion( sequences ):
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
		position = 0

		# Traverse sequence of combos to generate permuation
		for sequence in sequences:
			expandedSequences[ -1 ].append( [] )
			for combo in sequence:
				expandedSequences[ -1 ][ -1 ].append( combo[ curLeafList[ position ] ] )
				position += 1

		# Increment combination tracker
		for leaf in range( 0, len( curLeafList ) ):
			curLeafList[ leaf ] += 1

			# Reset this position, increment next position (if it exists), then stop
			if curLeafList[ leaf ] >= maxLeafList[ leaf ]:
				curLeafList[ leaf ] = 0
				if leaf + 1 < len( curLeafList ):
					curLeafList[ leaf + 1 ] += 1

	return expandedSequences


# Converts USB Codes into Capabilities
# These are tuples (<type>, <integer>)
def hidCodeToCapability( items ):
	# Items already converted to variants using optionExpansion
	for variant in range( 0, len( items ) ):
		# Sequence of Combos
		for sequence in range( 0, len( items[ variant ] ) ):
			for combo in range( 0, len( items[ variant ][ sequence ] ) ):
				if items[ variant ][ sequence ][ combo ][0] in backend.requiredCapabilities.keys():
					try:
						# Use backend capability name and a single argument
						items[ variant ][ sequence ][ combo ] = tuple(
							[ backend.capabilityLookup( items[ variant ][ sequence ][ combo ][0] ),
							tuple( [ hid_lookup_dictionary[ items[ variant ][ sequence ][ combo ] ] ] ) ]
						)
					except KeyError:
						print ( "{0} {1} is an invalid HID lookup value".format( ERROR, items[ variant ][ sequence ][ combo ] ) )
						sys.exit( 1 )
	return items


# Convert tuple of tuples to list of lists
def listit( t ):
	return list( map( listit, t ) ) if isinstance( t, ( list, tuple ) ) else t

# Convert list of lists to tuple of tuples
def tupleit( t ):
	return tuple( map( tupleit, t ) ) if isinstance( t, ( tuple, list ) ) else t


 ## Evaluation Rules

class Eval:
	def scanCode( triggers, operator, results ):
		print ( triggers, operator, results )
		# Convert to lists of lists of lists to tuples of tuples of tuples
		# Tuples are non-mutable, and can be used has index items
		triggers = tuple( tuple( tuple( sequence ) for sequence in variant ) for variant in triggers )
		results  = tuple( tuple( tuple( sequence ) for sequence in variant ) for variant in results )

		# Lookup interconnect id (Current file scope)
		# Default to 0 if not specified
		if 'ConnectId' not in variables_dict.overallVariables.keys():
			id_num = 0
		else:
			id_num = int( variables_dict.overallVariables['ConnectId'] )

		# Iterate over all combinations of triggers and results
		for sequence in triggers:
			# Convert tuple of tuples to list of lists so each element can be modified
			trigger = listit( sequence )

			# Create ScanCode entries for trigger
			for seq_index, combo in enumerate( sequence ):
				for com_index, scancode in enumerate( combo ):
					trigger[ seq_index ][ com_index ] = macros_map.scanCodeStore.append( ScanCode( scancode, id_num ) )

			# Convert back to a tuple of tuples
			trigger = tupleit( trigger )

			for result in results:
				# Append Case
				if operator == ":+":
					macros_map.appendScanCode( trigger, result )

				# Remove Case
				elif operator == ":-":
					macros_map.removeScanCode( trigger, result )

				# Replace Case
				# Soft Replace Case is the same for Scan Codes
				elif operator == ":" or operator == "::":
					macros_map.replaceScanCode( trigger, result )

	def usbCode( triggers, operator, results ):
		# TODO
		return
		# Convert to lists of lists of lists to tuples of tuples of tuples
		# Tuples are non-mutable, and can be used has index items
		triggers = tuple( tuple( tuple( sequence ) for sequence in variant ) for variant in triggers )
		results  = tuple( tuple( tuple( sequence ) for sequence in variant ) for variant in results )

		# Iterate over all combinations of triggers and results
		for trigger in triggers:
			scanCodes = macros_map.lookupUSBCodes( trigger )
			for scanCode in scanCodes:
				for result in results:
					# Soft Replace needs additional checking to see if replacement is necessary
					if operator == "::" and not macros_map.softReplaceCheck( scanCode ):
						continue

					# Cache assignment until file finishes processing
					macros_map.cacheAssignment( operator, scanCode, result )

	def variable( name, content ):
		# Content might be a concatenation of multiple data types, convert everything into a single string
		assigned_content = ""
		for item in content:
			assigned_content += str( item )

		variables_dict.assignVariable( name, assigned_content )

	def capability( name, function, args ):
		capabilities_dict[ name ] = [ function, args ]

	def define( name, cdefine_name ):
		variables_dict.defines[ name ] = cdefine_name

	def scanCodePosition( scanCode, positions ):
		print (scanCode)
		# Re-organize position lists into a dictionary first
		pos_dict = dict()
		for pos in positions:
			pos_dict[ pos[0] ] = pos[1]
		print (pos_dict)

		# TODO Create datastructure for positions

	def pixelPosition( pixel, position ):
		# TODO
		print (pixel, position)

	def pixelChannels( channel, scanCode ):
		# TODO
		print (channel, scanCode )

	def animation( animation, modifiers ):
		# TODO
		print( animation, modifiers )

	def animationFrame( animation, frame, modifiers ):
		# TODO
		print( frame, modifiers )

	def animationTrigger( animation, operator, results ):
		# TODO
		print ( animation, operator, results )

	def animationTriggerFrame( animation, frame, operator, results ):
		# TODO
		print ( animation, frame, operator, results )

	def array( name, index, content ):
		# TODO
		print (name, index, content)

class Map:
	scanCode              = unarg( Eval.scanCode )
	usbCode               = unarg( Eval.usbCode )
	animationTrigger      = unarg( Eval.animationTrigger )
	animationTriggerFrame = unarg( Eval.animationTriggerFrame )

class Set:
	animation        = unarg( Eval.animation )
	animationFrame   = unarg( Eval.animationFrame )
	array            = unarg( Eval.array )
	capability       = unarg( Eval.capability )
	define           = unarg( Eval.define )
	pixelChannels    = unarg( Eval.pixelChannels )
	pixelPosition    = unarg( Eval.pixelPosition )
	scanCodePosition = unarg( Eval.scanCodePosition )
	variable         = unarg( Eval.variable )


 ## Sub Rules

usbCode       = tokenType('USBCode') >> Make.usbCode
scanCode      = tokenType('ScanCode') >> Make.scanCode
consCode      = tokenType('ConsCode') >> Make.consCode
sysCode       = tokenType('SysCode') >> Make.sysCode
indCode       = tokenType('Indicator') >> Make.indCode
animation     = tokenType('Animation') >> Make.animation
pixel         = tokenType('Pixel') >> Make.pixel
pixelLayer    = tokenType('PixelLayer') >> Make.pixelLayer
none          = tokenType('None') >> Make.none
position      = tokenType('Position') >> Make.position
name          = tokenType('Name')
number        = tokenType('Number') >> Make.number
timing        = tokenType('Timing') >> Make.timing
comma         = tokenType('Comma')
dash          = tokenType('Dash')
plus          = tokenType('Plus')
content       = tokenType('VariableContents')
string        = tokenType('String') >> Make.string
unString      = tokenType('String') # When the double quotes are still needed for internal processing
seqString     = tokenType('SequenceString') >> Make.seqString
unseqString   = tokenType('SequenceString') >> Make.unseqString # For use with variables
pixelOperator = tokenType('PixelOperator')

  # Code variants
code_begin = tokenType('CodeBegin')
code_end   = tokenType('CodeEnd')

  # Specifier
specifier_state  = ( name + skip( operator(':') ) + timing ) | ( name + skip( operator(':') ) + timing ) | timing | name >> Make.specifierState
specifier_analog = number >> Make.specifierAnalog
specifier_list   = skip( parenthesis('(') ) + many( ( specifier_state | specifier_analog ) + skip( maybe( comma ) ) ) + skip( parenthesis(')') )

  # Scan Codes
scanCode_start     = tokenType('ScanCodeStart')
scanCode_range     = number + skip( dash ) + number >> Make.scanCode_range
scanCode_listElem  = number >> listElem
scanCode_specifier = ( scanCode_range | scanCode_listElem ) + maybe( specifier_list ) >> Make.specifierUnroll >> flatten
scanCode_innerList = many( scanCode_specifier + skip( maybe( comma ) ) ) >> flatten
scanCode_expanded  = skip( scanCode_start ) + scanCode_innerList + skip( code_end )
scanCode_elem      = scanCode + maybe( specifier_list ) >> Make.specifierUnroll >> listElem
scanCode_combo     = oneplus( ( scanCode_expanded | scanCode_elem ) + skip( maybe( plus ) ) )
scanCode_sequence  = oneplus( scanCode_combo + skip( maybe( comma ) ) )

  # Cons Codes
consCode_start       = tokenType('ConsCodeStart')
consCode_number      = number >> Make.consCode_number
consCode_range       = ( consCode_number | unString ) + skip( dash ) + ( number | unString ) >> Make.consCode_range
consCode_listElemTag = unString >> Make.consCode
consCode_listElem    = ( consCode_number | consCode_listElemTag ) >> listElem
consCode_specifier   = ( consCode_range | consCode_listElem ) + maybe( specifier_list ) >> Make.specifierUnroll >> flatten
consCode_innerList   = oneplus( consCode_specifier + skip( maybe( comma ) ) ) >> flatten
consCode_expanded    = skip( consCode_start ) + consCode_innerList + skip( code_end )
consCode_elem        = consCode + maybe( specifier_list ) >> Make.specifierUnroll >> listElem

  # Sys Codes
sysCode_start       = tokenType('SysCodeStart')
sysCode_number      = number >> Make.sysCode_number
sysCode_range       = ( sysCode_number | unString ) + skip( dash ) + ( number | unString ) >> Make.sysCode_range
sysCode_listElemTag = unString >> Make.sysCode
sysCode_listElem    = ( sysCode_number | sysCode_listElemTag ) >> listElem
sysCode_specifier   = ( sysCode_range | sysCode_listElem ) + maybe( specifier_list ) >> Make.specifierUnroll >> flatten
sysCode_innerList   = oneplus( sysCode_specifier + skip( maybe( comma ) ) ) >> flatten
sysCode_expanded    = skip( sysCode_start ) + sysCode_innerList + skip( code_end )
sysCode_elem        = sysCode + maybe( specifier_list ) >> Make.specifierUnroll >> listElem

  # Indicator Codes
indCode_start       = tokenType('IndicatorStart')
indCode_number      = number >> Make.indCode_number
indCode_range       = ( indCode_number | unString ) + skip( dash ) + ( number | unString ) >> Make.indCode_range
indCode_listElemTag = unString >> Make.indCode
indCode_listElem    = ( indCode_number | indCode_listElemTag ) >> listElem
indCode_specifier   = ( indCode_range | indCode_listElem ) + maybe( specifier_list ) >> Make.specifierUnroll >> flatten
indCode_innerList   = oneplus( indCode_specifier + skip( maybe( comma ) ) ) >> flatten
indCode_expanded    = skip( indCode_start ) + indCode_innerList + skip( code_end )
indCode_elem        = indCode + maybe( specifier_list ) >> Make.specifierUnroll >> listElem

  # USB Codes
usbCode_start       = tokenType('USBCodeStart')
usbCode_number      = number >> Make.usbCode_number
usbCode_range       = ( usbCode_number | unString ) + skip( dash ) + ( number | unString ) >> Make.usbCode_range
usbCode_listElemTag = unString >> Make.usbCode
usbCode_listElem    = ( usbCode_number | usbCode_listElemTag ) >> listElem
usbCode_specifier   = ( usbCode_range | usbCode_listElem ) + maybe( specifier_list ) >> Make.specifierUnroll >> flatten
usbCode_innerList   = oneplus( usbCode_specifier + skip( maybe( comma ) ) ) >> flatten
usbCode_expanded    = skip( usbCode_start ) + usbCode_innerList + skip( code_end )
usbCode_elem        = usbCode + maybe( specifier_list ) >> Make.specifierUnroll >> listElem

  # HID Codes
hidCode_elem        = usbCode_expanded | usbCode_elem | sysCode_expanded | sysCode_elem | consCode_expanded | consCode_elem | indCode_expanded | indCode_elem

usbCode_combo       = oneplus( hidCode_elem + skip( maybe( plus ) ) ) >> listElem
usbCode_sequence    = oneplus( ( usbCode_combo | seqString ) + skip( maybe( comma ) ) ) >> oneLayerFlatten

  # Pixels
pixel_start       = tokenType('PixelStart')
pixel_number      = number
pixel_range       = ( pixel_number ) + skip( dash ) + ( number ) >> Make.range
pixel_listElem    = pixel_number >> listElem
pixel_innerList   = many( ( pixel_range | pixel_listElem ) + skip( maybe( comma ) ) )
pixel_expanded    = skip( pixel_start ) + pixel_innerList + skip( code_end )
pixel_elem        = pixel >> listElem

  # Pixel Layer
pixellayer_start    = tokenType('PixelLayerStart')
pixellayer_number   = number
pixellayer_expanded = skip( pixellayer_start ) + pixellayer_number + skip( code_end )
pixellayer_elem     = pixelLayer >> listElem

  # Pixel Channels
pixelchan_chans = many( number + skip( operator(':') ) + number + skip( maybe( comma ) ) ) >> Make.pixelchans
pixelchan_elem  = ( pixel_expanded | pixel_elem ) + skip( parenthesis('(') ) + pixelchan_chans + skip( parenthesis(')') ) >> Make.pixelchan_elem

  # Pixel Mods
pixelmod_mods  = many( maybe( pixelOperator | plus | dash ) + number + skip( maybe( comma ) ) ) >> Make.pixelmods
pixelmod_layer = ( pixellayer_expanded | pixellayer_elem ) >> Make.pixellayer
pixelmod_elem  = ( pixel_expanded | pixel_elem | pixelmod_layer ) + skip( parenthesis('(') ) + pixelmod_mods + skip( parenthesis(')') )

  # Pixel Capability
pixel_capability = pixelmod_elem >> Make.pixelCapability

  # Animations
animation_start       = tokenType('AnimationStart')
animation_name        = name
animation_frame_range = ( number ) + skip( dash ) + ( number ) >> Make.range
animation_name_frame  = many( ( number | animation_frame_range ) + skip( maybe( comma ) ) )
animation_def         = skip( animation_start ) + animation_name + skip( code_end )
animation_expanded    = skip( animation_start ) + animation_name + skip( comma ) + animation_name_frame + skip( code_end )
animation_elem        = animation >> listElem

  # Animation Modifier
animation_modifier = many( ( name | number ) + maybe( skip( operator(':') ) + number ) + skip( maybe( comma ) ) )

  # Animation Capability
animation_capability = ( animation_def | animation_elem ) + maybe( skip( parenthesis('(') + animation_modifier + skip( parenthesis(')') ) ) ) >> Make.animationCapability

  # Capabilities
capFunc_arguments = many( number + skip( maybe( comma ) ) ) >> listToTuple
capFunc_elem      = name + skip( parenthesis('(') ) + capFunc_arguments + skip( parenthesis(')') ) >> capArgExpander >> listElem
capFunc_combo     = oneplus( ( hidCode_elem | capFunc_elem | animation_capability | pixel_capability ) + skip( maybe( plus ) ) ) >> listElem
capFunc_sequence  = oneplus( ( capFunc_combo | seqString ) + skip( maybe( comma ) ) ) >> oneLayerFlatten

  # Trigger / Result Codes
triggerCode_outerList    = scanCode_sequence >> optionExpansion
triggerUSBCode_outerList = usbCode_sequence >> optionExpansion >> hidCodeToCapability
resultCode_outerList     = ( ( capFunc_sequence >> optionExpansion ) | none ) >> hidCodeToCapability

  # Positions
position_list = oneplus( position + skip( maybe( comma ) ) )


 ## Main Rules

#| Assignment
#| <variable> = <variable contents>;
variable_contents   = name | content | string | number | comma | dash | unseqString
variable_expression = name + skip( operator('=') ) + oneplus( variable_contents ) + skip( eol ) >> Set.variable

#| Array Assignment
#| <variable>[]        = <space> <separated> <list>;
#| <variable>[<index>] = <index element>;
array_expression = name + skip( code_begin ) + maybe( number ) + skip( code_end ) + skip( operator('=') ) + oneplus( variable_contents ) + skip( eol ) >> Set.array

#| Name Association
#| <capability name> => <c function>;
capability_arguments  = name + skip( operator(':') ) + number + skip( maybe( comma ) )
capability_expression = name + skip( operator('=>') ) + name + skip( parenthesis('(') ) + many( capability_arguments ) + skip( parenthesis(')') ) + skip( eol ) >> Set.capability

#| Name Association
#| <define name> => <c define>;
define_expression = name + skip( operator('=>') ) + name + skip( eol ) >> Set.define

#| Data Association
#| <animation>       <= <modifiers>;
#| <animation frame> <= <modifiers>;
animation_expression      = ( animation_elem | animation_def ) + skip( operator('<=') ) + animation_modifier + skip( eol ) >> Set.animation
animationFrame_expression = animation_expanded + skip( operator('<=') ) + many( pixelmod_elem + skip( maybe( comma ) ) ) + skip( eol ) >> Set.animationFrame

#| Data Association
#| <pixel> <= <position>;
pixelPosition_expression = ( pixel_expanded | pixel_elem ) + skip( operator('<=') ) + position_list + skip( eol ) >> Set.pixelPosition

#| Data Association
#| <pixel chan> <= <scanCode>;
pixelChan_expression = pixelchan_elem + skip( operator(':') ) + ( scanCode_expanded | scanCode_elem | none ) + skip( eol ) >> Set.pixelChannels

#| Data Association
#| <scancode> <= <position>;
scanCodePosition_expression = triggerCode_outerList + skip( operator('<=') ) + position_list + skip( eol ) >> Set.scanCodePosition

#| Mapping
#| <trigger> : <result>;
operatorTriggerResult    = operator(':') | operator(':+') | operator(':-') | operator('::')
scanCode_expression      = triggerCode_outerList + operatorTriggerResult + resultCode_outerList + skip( eol ) >> Map.scanCode
usbCode_expression       = triggerUSBCode_outerList + operatorTriggerResult + resultCode_outerList + skip( eol ) >> Map.usbCode
animation_trigger        = ( animation_elem | animation_def ) + operatorTriggerResult + resultCode_outerList + skip( eol ) >> Map.animationTrigger
animation_triggerFrame   = animation_expanded + operatorTriggerResult + resultCode_outerList + skip( eol ) >> Map.animationTriggerFrame

def parse( tokenSequence ):
	"""Sequence(Token) -> object"""

	# Top-level Parser
	expression = (
		scanCode_expression |
		scanCodePosition_expression |
		usbCode_expression |
		animation_trigger |
		animation_triggerFrame |
		pixelPosition_expression |
		pixelChan_expression |
		animation_expression |
		animationFrame_expression |
		array_expression |
		variable_expression |
		capability_expression |
		define_expression
	)

	kll_text = many( expression )
	kll_file = maybe( kll_text ) + skip( finished )

	return kll_file.parse( tokenSequence )



def processKLLFile( filename ):
	with open( filename ) as file:
		data = file.read()
		try:
			tokenSequence = tokenize( data )
		except LexerError as err:
			print ( "{0} Tokenization error in '{1}' - {2}".format( ERROR, filename, err ) )
			sys.exit( 1 )
		#print ( pformat( tokenSequence ) ) # Display tokenization
		try:
			tree = parse( tokenSequence )
		except (NoParseError, KeyError) as err:
			print ( "{0} Parsing error in '{1}' - {2}".format( ERROR, filename, err ) )
			sys.exit( 1 )


### Misc Utility Functions ###

def gitRevision( kllPath ):
	import subprocess

	# Change the path to where kll.py is
	origPath = os.getcwd()
	os.chdir( kllPath )

	# Just in case git can't be found
	try:
		# Get hash of the latest git commit
		revision = subprocess.check_output( ['git', 'rev-parse', 'HEAD'] ).decode()[:-1]

		# Get list of files that have changed since the commit
		changed = subprocess.check_output( ['git', 'diff-index', '--name-only', 'HEAD', '--'] ).decode().splitlines()
	except:
		revision = "<no git>"
		changed = []

	# Change back to the old working directory
	os.chdir( origPath )

	return revision, changed


### Main Entry Point ###

if __name__ == '__main__':
	(baseFiles, defaultFiles, partialFileSets, backend_name, templates, outputs) = processCommandLineArgs()

	# Look up git information on the compiler
	gitRev, gitChanges = gitRevision( os.path.dirname( os.path.realpath( __file__ ) ) )

	# Load backend module
	global backend
	backend_import = importlib.import_module( "backends.{0}".format( backend_name ) )
	backend = backend_import.Backend( templates )

	# Process base layout files
	for filename in baseFiles:
		variables_dict.setCurrentFile( filename )
		processKLLFile( filename )
	macros_map.completeBaseLayout() # Indicates to macros_map that the base layout is complete
	variables_dict.baseLayoutFinished()

	# Default combined layer
	for filename in defaultFiles:
		variables_dict.setCurrentFile( filename )
		processKLLFile( filename )
		# Apply assignment cache, see 5.1.2 USB Codes for why this is necessary
		macros_map.replayCachedAssignments()

	# Iterate through additional layers
	for partial in partialFileSets:
		# Increment layer for each -p option
		macros_map.addLayer()
		variables_dict.incrementLayer() # DefaultLayer is layer 0

		# Iterate and process each of the file in the layer
		for filename in partial:
			variables_dict.setCurrentFile( filename )
			processKLLFile( filename )
			# Apply assignment cache, see 5.1.2 USB Codes for why this is necessary
			macros_map.replayCachedAssignments()
		# Remove un-marked keys to complete the partial layer
		macros_map.removeUnmarked()

	# Do macro correlation and transformation
	macros_map.generate()

	# Process needed templating variables using backend
	backend.process(
		capabilities_dict,
		macros_map,
		variables_dict,
		gitRev,
		gitChanges
	)

	# Generate output file using template and backend
	backend.generate( outputs )

	# Successful Execution
	sys.exit( 0 )

