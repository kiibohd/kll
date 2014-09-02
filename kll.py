#!/usr/bin/env python3
# KLL Compiler
# Keyboard Layout Langauge
#
# Copyright (C) 2014 by Jacob Alexander
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
import io
import os
import re
import sys
import token
import importlib

from tokenize import generate_tokens
from re       import VERBOSE
from pprint   import pformat

from kll_lib.hid_dict   import *
from kll_lib.containers import *

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

def processCommandLineArgs():
	# Setup argument processor
	pArgs = argparse.ArgumentParser(
	        usage="%(prog)s [options] <file1>...",
	        description="Generates .h file state tables and pointer indices from KLL .kll files.",
	        epilog="Example: {0} TODO".format( os.path.basename( sys.argv[0] ) ),
	        formatter_class=argparse.RawTextHelpFormatter,
	        add_help=False,
)

	# Positional Arguments
	pArgs.add_argument( 'files', type=str, nargs='+',
		help=argparse.SUPPRESS ) # Suppressed help output, because Python output is verbosely ugly

	# Optional Arguments
	pArgs.add_argument( '-b', '--backend', type=str, default="kiibohd",
		help="Specify target backend for the KLL compiler.\n"
		"Default: kiibohd" )
	pArgs.add_argument( '-p', '--partial', type=str, nargs='+', action='append',
		help="Specify .kll files to generate partial map, multiple files per flag.\n"
		"Each -p defines another partial map.\n"
		"Base .kll files (that define the scan code maps) must be defined for each partial map." )
	pArgs.add_argument( '-t', '--template', type=str, default="templateKeymap.h",
		help="Specify template used to generate the keymap.\n"
		"Default: templateKeymap.h" )
	pArgs.add_argument( '-o', '--output', type=str, default="templateKeymap.h",
		help="Specify output file. Writes to current working directory by default.\n"
		"Default: generatedKeymap.h" )
	pArgs.add_argument( '-h', '--help', action="help",
		help="This message." )

	# Process Arguments
	args = pArgs.parse_args()

	# Parameters
	defaultFiles = args.files
	partialFileSets = args.partial
	if partialFileSets is None:
		partialFileSets = [[]]

	# Check file existance
	for filename in defaultFiles:
		if not os.path.isfile( filename ):
			print ( "{0} {1} does not exist...".format( ERROR, filename ) )
			sys.exit( 1 )

	for partial in partialFileSets:
		for filename in partial:
			if not os.path.isfile( filename ):
				print ( "{0} {1} does not exist...".format( ERROR, filename ) )
				sys.exit( 1 )

	return (defaultFiles, partialFileSets, args.backend, args.template, args.output)



### Tokenizer ###

def tokenize( string ):
	"""str -> Sequence(Token)"""

	# Basic Tokens Spec
	specs = [
		( 'Comment',          ( r' *#.*', ) ),
		( 'Space',            ( r'[ \t\r\n]+', ) ),
		( 'USBCode',          ( r'U(("[^"]+")|(0x[0-9a-fA-F]+)|([0-9]+))', ) ),
		( 'USBCodeStart',     ( r'U\[', ) ),
		( 'ScanCode',         ( r'S((0x[0-9a-fA-F]+)|([0-9]+))', ) ),
		( 'ScanCodeStart',    ( r'S\[', ) ),
		( 'CodeEnd',          ( r'\]', ) ),
		( 'String',           ( r'"[^"]*"', VERBOSE ) ),
		( 'SequenceString',   ( r"'[^']*'", ) ),
		( 'Comma',            ( r',', ) ),
		( 'Dash',             ( r'-', ) ),
		( 'Plus',             ( r'\+', ) ),
		( 'Operator',         ( r'=>|:|=', ) ),
		( 'Parenthesis',      ( r'\(|\)', ) ),
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
scanCode_map      = [ None ] * 0xFF # Define 8 bit address width
usbCode_map       = [ None ] * 0xFF # Define 8 bit address width
variable_dict     = dict()
capabilities_dict = Capabilities()


 ## Parsing Functions

def make_scanCode( token ):
	scanCode = int( token[1:], 0 )
	# Check size, to make sure it's valid
	if scanCode > 0xFF:
		print ( "{0} ScanCode value {1} is larger than 255".format( ERROR, scanCode ) )
		raise
	return scanCode

def make_usbCode( token ):
	# If first character is a U, strip
	if token[0] == "U":
		token = token[1:]

	# If using string representation of USB Code, do lookup, case-insensitive
	if '"' in token:
		try:
			usbCode = kll_hid_lookup_dictionary[ token[1:-1].upper() ]
		except LookupError as err:
			print ( "{0} {1} is an invalid USB Code Lookup...".format( ERROR, err ) )
			raise
	else:
		usbCode = int( token, 0 )

	# Check size, to make sure it's valid
	if usbCode > 0xFF:
		print ( "{0} USBCode value {1} is larger than 255".format( ERROR, usbCode ) )
		raise
	return usbCode

def make_seqString( token ):
	# Shifted Characters, and amount to move by to get non-shifted version
	# US ANSI
	shiftCharacters = (
		( "ABCDEFGHIJKLMNOPQRSTUVWXYZ", 0x20 ),
		( "+",       0x12 ),
		( "&(",      0x11 ),
		( "!#$%<>",  0x10 ),
		( "*",       0x0E ),
		( ")",       0x07 ),
		( '"',       0x05 ),
		( ":",       0x01 ),
		( "^",      -0x10 ),
		( "_",      -0x18 ),
		( "{}|",    -0x1E ),
		( "~",      -0x20 ),
		( "@",      -0x32 ),
		( "?",      -0x38 ),
	)

	listOfLists = []
	shiftKey = kll_hid_lookup_dictionary["SHIFT"]

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
		usbCode = kll_hid_lookup_dictionary[ processedChar.upper() ]

		# Create Combo for this character, add shift key if shifted
		charCombo = []
		if shiftCombo:
			charCombo = [ [ shiftKey ] ]
		charCombo.append( [ usbCode ] )

		# Add to list of lists
		listOfLists.append( charCombo )

	return listOfLists

def make_string( token ):
	return token[1:-1]

def make_number( token ):
	return int( token, 0 )

  # Range can go from high to low or low to high
def make_scanCode_range( rangeVals ):
	start = rangeVals[0]
	end   = rangeVals[1]

	# Swap start, end if start is greater than end
	if start > end:
		start, end = end, start

	# Iterate from start to end, and generate the range
	return list( range( start, end + 1 ) )

  # Range can go from high to low or low to high
  # Warn on 0-9 (as this does not do what one would expect) TODO
  # Lookup USB HID tags and convert to a number
def make_usbCode_range( rangeVals ):
	# Check if already integers
	if isinstance( rangeVals[0], int ):
		start = rangeVals[0]
	else:
		start = make_usbCode( rangeVals[0] )

	if isinstance( rangeVals[1], int ):
		end = rangeVals[1]
	else:
		end = make_usbCode( rangeVals[1] )

	# Swap start, end if start is greater than end
	if start > end:
		start, end = end, start

	# Iterate from start to end, and generate the range
	return list( range( start, end + 1 ) )
	pass


 ## Base Rules

const       = lambda x: lambda _: x
unarg       = lambda f: lambda x: f(*x)
flatten     = lambda list: sum( list, [] )

tokenValue  = lambda x: x.value
tokenType   = lambda t: some( lambda x: x.type == t ) >> tokenValue
operator    = lambda s: a( Token( 'Operator', s ) ) >> tokenValue
parenthesis = lambda s: a( Token( 'Parenthesis', s ) ) >> tokenValue
eol         = a( Token( 'EndOfLine', ';' ) )

def listElem( item ):
	return [ item ]

  # Flatten only the top layer (list of lists of ...)
def oneLayerFlatten( items ):
	mainList = []
	for sublist in items:
		for item in sublist:
			mainList.append( item )

	return mainList

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
				break

	return expandedSequences


 ## Evaluation Rules

def eval_scanCode( trigger, result ):
	# Convert to lists of lists of lists to tuples of tuples of tuples
	trigger = tuple( tuple( tuple( sequence ) for sequence in variant ) for variant in trigger )
	result  = tuple( tuple( tuple( sequence ) for sequence in variant ) for variant in result )

	# Add to the base scanCode map, overwrite if already defined
#	if scanCode_map[ trigger ] != None:
#		print ( "ScanCodeMap - Replacing '{0}' with '{1}' -> {2}".format( scanCode_map[ trigger ], result, trigger ) )
#	scanCode_map[ trigger ] = result

def eval_usbCode( trigger, result ):
	# Check if trigger is list

	# Add to the base usbCode map, overwrite if already defined
	if usbCode_map[ trigger ] != None:
		print ( "USBCodeMap - Replacing '{0}' with '{1}' -> {2}".format( usbCode_map[ trigger ], result, trigger ) )
	usbCode_map[ trigger ] = result
	print ( trigger )

def eval_variable( name, content ):
	# Content might be a concatenation of multiple data types, convert everything into a single string
	assigned_content = ""
	for item in content:
		assigned_content += str( item )

	variable_dict[ name ] = assigned_content

def eval_capability( name, function, args ):
	capabilities_dict[ name ] = [ function, args ]

map_scanCode   = unarg( eval_scanCode )
map_usbCode    = unarg( eval_usbCode )

set_variable   = unarg( eval_variable )
set_capability = unarg( eval_capability )


 ## Sub Rules

usbCode   = tokenType('USBCode') >> make_usbCode
scanCode  = tokenType('ScanCode') >> make_scanCode
name      = tokenType('Name')
number    = tokenType('Number') >> make_number
comma     = tokenType('Comma')
dash      = tokenType('Dash')
plus      = tokenType('Plus')
content   = tokenType('VariableContents')
string    = tokenType('String') >> make_string
unString  = tokenType('String') # When the double quotes are still needed for internal processing
seqString = tokenType('SequenceString') >> make_seqString

  # Code variants
code_end = tokenType('CodeEnd')

  # Scan Codes
scanCode_start     = tokenType('ScanCodeStart')
scanCode_range     = number + skip( dash ) + number >> make_scanCode_range
scanCode_listElem  = number >> listElem
scanCode_innerList = oneplus( ( scanCode_range | scanCode_listElem ) + skip( maybe( comma ) ) ) >> flatten
scanCode_expanded  = skip( scanCode_start ) + scanCode_innerList + skip( code_end )
scanCode_elem      = scanCode >> listElem
scanCode_combo     = oneplus( ( scanCode_expanded | scanCode_elem ) + skip( maybe( plus ) ) )
scanCode_sequence  = oneplus( scanCode_combo + skip( maybe( comma ) ) )

  # USB Codes
usbCode_start       = tokenType('USBCodeStart')
usbCode_range       = ( number | unString ) + skip( dash ) + ( number | unString ) >> make_usbCode_range
usbCode_listElemTag = unString >> make_usbCode
usbCode_listElem    = ( number | usbCode_listElemTag ) >> listElem
usbCode_innerList   = oneplus( ( usbCode_range | usbCode_listElem ) + skip( maybe( comma ) ) ) >> flatten
usbCode_expanded    = skip( usbCode_start ) + usbCode_innerList + skip( code_end )
usbCode_elem        = usbCode >> listElem
usbCode_combo       = oneplus( ( usbCode_expanded | usbCode_elem ) + skip( maybe( plus ) ) ) >> listElem
usbCode_sequence    = oneplus( ( usbCode_combo | seqString ) + skip( maybe( comma ) ) ) >> oneLayerFlatten

  # Capabilities
capFunc_arguments = number + skip( maybe( comma ) )
capFunc_elem      = name + skip( parenthesis('(') ) + many( capFunc_arguments ) + skip( parenthesis(')') ) >> listElem
capFunc_combo     = oneplus( ( usbCode_expanded | usbCode_elem | capFunc_elem ) + skip( maybe( plus ) ) ) >> listElem
capFunc_sequence  = oneplus( ( capFunc_combo | seqString ) + skip( maybe( comma ) ) ) >> oneLayerFlatten

  # Trigger / Result Codes
triggerCode_outerList    = scanCode_sequence >> optionExpansion
triggerUSBCode_outerList = usbCode_sequence >> optionExpansion
resultCode_outerList     = capFunc_sequence >> optionExpansion


 ## Main Rules

#| <variable> = <variable contents>;
variable_contents   = name | content | string | number | comma | dash
variable_expression = name + skip( operator('=') ) + oneplus( variable_contents ) + skip( eol ) >> set_variable

#| <capability name> => <c function>;
capability_arguments  = name + skip( operator(':') ) + number + skip( maybe( comma ) )
capability_expression = name + skip( operator('=>') ) + name + skip( parenthesis('(') ) + many( capability_arguments ) + skip( parenthesis(')') ) + skip( eol ) >> set_capability

#| <trigger> : <result>;
scanCode_expression = triggerCode_outerList + skip( operator(':') ) + resultCode_outerList + skip( eol ) >> map_scanCode
usbCode_expression  = triggerUSBCode_outerList + skip( operator(':') ) + resultCode_outerList + skip( eol ) #>> map_usbCode

def parse( tokenSequence ):
	"""Sequence(Token) -> object"""

	# Top-level Parser
	expression = scanCode_expression | usbCode_expression | variable_expression | capability_expression

	kll_text = many( expression )
	kll_file = maybe( kll_text ) + skip( finished )

	return kll_file.parse( tokenSequence )



### Main Entry Point ###

if __name__ == '__main__':
	(defaultFiles, partialFileSets, backend_name, template, output) = processCommandLineArgs()

	# Load backend module
	global backend
	backend_import = importlib.import_module( "backends.{0}".format( backend_name ) )
	backend = backend_import.Backend( template )

	#TODO Move elsewhere
	for filename in defaultFiles:
		with open( filename ) as file:
			data = file.read()

			tokenSequence = tokenize( data )
			print ( pformat( tokenSequence ) )
			tree = parse( tokenSequence )
			#print ( tree )
			#print ( scanCode_map )
			#print ( usbCode_map )
			print ( variable_dict )
			print ( capabilities_dict )

	# TODO Move
	backend.process( capabilities_dict )

	# Successful Execution
	sys.exit( 0 )

