#!/usr/bin/env python3
'''
KLL Kiibohd .h File Emitter
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

import re
import sys

from datetime import date

from common.emitter import Emitter, TextEmitter
from common.hid_dict import kll_hid_lookup_dictionary



### Decorators ###

## Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'



### Classes ###

class Kiibohd( Emitter, TextEmitter ):
	'''
	Kiibohd .h file emitter for KLL
	'''

	# List of required capabilities
	requiredCapabilities = {
		'CONS' : 'consCtrlOut',
		'NONE' : 'noneOut',
		'SYS'  : 'sysCtrlOut',
		'USB'  : 'usbKeyOut',
	}

	def __init__( self, control ):
		'''
		Emitter initialization

		@param control: ControlStage object, used to access data from other stages
		'''
		Emitter.__init__( self, control )
		TextEmitter.__init__( self )

		# Defaults
		self.map_template   = "templates/kiibohdKeymap.h"
		self.pixel_template = "templates/kiibohdPixelmap.c"
		self.def_template   = "templates/kiibohdDefs.h"
		self.map_output     = "generatedKeymap.h"
		self.pixel_output   = "generatedPixelmap.c"
		self.def_output     = "kll_defs.h"

		self.fill_dict = {}

	def command_line_args( self, args ):
		'''
		Group parser for command line arguments

		@param args: Name space of processed arguments
		'''
		self.def_template = args.def_template
		self.map_template = args.map_template
		self.pixel_template = args.pixel_template
		self.def_output = args.def_output
		self.map_output = args.map_output
		self.pixel_output = args.pixel_output

	def command_line_flags( self, parser ):
		'''
		Group parser for command line options

		@param parser: argparse setup object
		'''
		# Create new option group
		group = parser.add_argument_group('\033[1mKiibohd Emitter Configuration\033[0m')

		group.add_argument( '--def-template', type=str, default=self.def_template,
			help="Specify KLL define .h file template.\n"
			"\033[1mDefault\033[0m: {0}\n".format( self.def_template )
		)
		group.add_argument( '--map-template', type=str, default=self.map_template,
			help="Specify KLL map .h file template.\n"
			"\033[1mDefault\033[0m: {0}\n".format( self.map_template )
		)
		group.add_argument( '--pixel-template', type=str, default=self.pixel_template,
			help="Specify KLL pixel map .c file template.\n"
			"\033[1mDefault\033[0m: {0}\n".format( self.pixel_template )
		)
		group.add_argument( '--def-output', type=str, default=self.def_output,
			help="Specify KLL define .h file output.\n"
			"\033[1mDefault\033[0m: {0}\n".format( self.def_output )
		)
		group.add_argument( '--map-output', type=str, default=self.map_output,
			help="Specify KLL map .h file output.\n"
			"\033[1mDefault\033[0m: {0}\n".format( self.map_output )
		)
		group.add_argument( '--pixel-output', type=str, default=self.pixel_output,
			help="Specify KLL map .h file output.\n"
			"\033[1mDefault\033[0m: {0}\n".format( self.pixel_output )
		)

	def output( self ):
		'''
		Final Stage of Emitter

		Generate desired outputs from templates
		'''
		# Load define template and generate
		self.load_template( self.def_template )
		self.generate( self.def_output )

		# Load keymap template and generate
		self.load_template( self.map_template )
		self.generate( self.map_output )

		# Load pixelmap template and generate
		self.load_template( self.pixel_template )
		self.generate( self.pixel_output )

	def process( self ):
		'''
		Emitter Processing

		Takes KLL datastructures and Analysis results then populates the fill_dict
		The fill_dict is used populate the template files.
		'''
		# Acquire Datastructures
		early_contexts = self.control.stage('DataOrganizationStage').contexts
		base_context = self.control.stage('DataFinalizationStage').base_context
		default_context = self.control.stage('DataFinalizationStage').default_context
		partial_contexts = self.control.stage('DataFinalizationStage').partial_contexts
		full_context = self.control.stage('DataFinalizationStage').full_context


		# Build string list of compiler arguments
		compilerArgs = ""
		for arg in sys.argv:
			if "--" in arg or ".py" in arg:
				compilerArgs += "//    {0}\n".format( arg )
			else:
				compilerArgs += "//      {0}\n".format( arg )


		# Build a string of modified files, if any
		gitChangesStr = "\n"
		if len( self.control.git_changes ) > 0:
			for gitFile in self.control.git_changes:
				gitChangesStr += "//    {0}\n".format( gitFile )
		else:
			gitChangesStr = "    None\n"


		# Prepare BaseLayout and Layer Info
		configLayoutInfo = ""
		if 'ConfigurationContext' in early_contexts.keys():
			contexts = early_contexts['ConfigurationContext'].query_contexts( 'AssignmentExpression', 'Array' )
			for sub in contexts:
				name = sub[0].data['Name'].value
				configLayoutInfo += "//    {0}\n//      {1}\n".format( name, sub[1].parent.path )

		genericLayoutInfo = ""
		if 'GenericContext' in early_contexts.keys():
			contexts = early_contexts['GenericContext'].query_contexts( 'AssignmentExpression', 'Array' )
			for sub in contexts:
				name = sub[0].data['Name'].value
				genericLayoutInfo += "//    {0}\n//      {1}\n".format( name, sub[1].parent.path )

		baseLayoutInfo = ""
		if 'BaseMapContext' in early_contexts.keys():
			contexts = early_contexts['BaseMapContext'].query_contexts( 'AssignmentExpression', 'Array' )
			for sub in contexts:
				name = sub[0].data['Name'].value
				baseLayoutInfo += "//    {0}\n//      {1}\n".format( name, sub[1].parent.path )

		defaultLayerInfo = ""
		if 'DefaultMapContext' in early_contexts.keys():
			contexts = early_contexts['DefaultMapContext'].query_contexts( 'AssignmentExpression', 'Array' )
			for sub in contexts:
				name = sub[0].data['Name'].value
				defaultLayerInfo += "//    {0}\n//      {1}\n".format( name, sub[1].parent.path )

		partialLayersInfo = ""
		partial_context_list = [
			( item[1].layer, item[0] )
			for item in early_contexts.items()
			if 'PartialMapContext' in item[0]
		]
		for layer, tag in sorted( partial_context_list, key=lambda x: x[0] ):
			partialLayersInfo += "//    Layer {0}\n".format( layer + 1 )
			contexts = early_contexts[ tag ].query_contexts( 'AssignmentExpression', 'Array' )
			for sub in contexts:
				name = sub[0].data['Name'].value
				partialLayersInfo += "//     {0}\n//       {1}\n".format( name, sub[1].parent.path )


		## Information ##
		self.fill_dict['Information']  = "// This file was generated by the kll compiler, DO NOT EDIT.\n"
		self.fill_dict['Information'] += "// Generation Date:    {0}\n".format( date.today() )
		self.fill_dict['Information'] += "// KLL Emitter:        {0}\n".format(
			self.control.stage('CompilerConfigurationStage').emitter
		)
		self.fill_dict['Information'] += "// KLL Version:        {0}\n".format( self.control.version )
		self.fill_dict['Information'] += "// KLL Git Changes:{0}".format( gitChangesStr )
		self.fill_dict['Information'] += "// Compiler arguments:\n{0}".format( compilerArgs )
		self.fill_dict['Information'] += "//\n"
		self.fill_dict['Information'] += "// - Configuration File -\n{0}".format( configLayoutInfo )
		self.fill_dict['Information'] += "// - Generic Files -\n{0}".format( genericLayoutInfo )
		self.fill_dict['Information'] += "// - Base Layer -\n{0}".format( baseLayoutInfo )
		self.fill_dict['Information'] += "// - Default Layer -\n{0}".format( defaultLayerInfo )
		self.fill_dict['Information'] += "// - Partial Layers -\n{0}".format( partialLayersInfo )


		## Defines ##
		self.fill_dict['Defines'] = ""

		# Iterate through defines and lookup the variables
		defines = full_context.query( 'NameAssociationExpression', 'Define' )
		variables = full_context.query( 'AssignmentExpression', 'Variable' )
		for dkey, dvalue in sorted( defines.data.items() ):
			if dvalue.name in variables.data.keys():
				self.fill_dict['Defines'] += "\n#define {0} {1}".format(
					dvalue.association,
					variables.data[ dvalue.name ].value.replace( '\n', ' \\\n' ),
				)
			else:
				print( "{0} '{1}' not defined...".format( WARNING, dvalue.name ) )


		## Capabilities ##
		self.fill_dict['CapabilitiesFuncDecl'] = ""
		self.fill_dict['CapabilitiesList'] = "const Capability CapabilitiesList[] = {\n"
		self.fill_dict['CapabilitiesIndices'] = "typedef enum CapabilityIndex {\n"

		# Keys are pre-sorted
		capabilities = full_context.query( 'NameAssociationExpression', 'Capability' )
		for dkey, dvalue in sorted( capabilities.data.items() ):
			funcName = dvalue.association.name
			argByteWidth = dvalue.association.total_arg_bytes()

			self.fill_dict['CapabilitiesList'] += "\t{{ {0}, {1} }},\n".format( funcName, argByteWidth )
			self.fill_dict['CapabilitiesFuncDecl'] += \
				"void {0}( uint8_t state, uint8_t stateType, uint8_t *args );\n".format( funcName )
			self.fill_dict['CapabilitiesIndices'] += "\t{0}_index,\n".format( funcName )

		self.fill_dict['CapabilitiesList'] += "};"
		self.fill_dict['CapabilitiesIndices'] += "} CapabilityIndex;"
		return


		## Results Macros ##
		self.fill_dict['ResultMacros'] = ""

		# Iterate through each of the result macros
		for result in range( 0, len( macros.resultsIndexSorted ) ):
			self.fill_dict['ResultMacros'] += "Guide_RM( {0} ) = {{ ".format( result )

			# Add the result macro capability index guide (including capability arguments)
			# See kiibohd controller Macros/PartialMap/kll.h for exact formatting details
			for sequence in range( 0, len( macros.resultsIndexSorted[ result ] ) ):
				# If the sequence is longer than 1, prepend a sequence spacer
				# Needed for USB behaviour, otherwise, repeated keys will not work
				if sequence > 0:
					# <single element>, <usbCodeSend capability>, <USB Code 0x00>
					self.fill_dict['ResultMacros'] += "1, {0}, 0x00, ".format( capabilities.getIndex( self.capabilityLookup('USB') ) )

				# For each combo in the sequence, add the length of the combo
				self.fill_dict['ResultMacros'] += "{0}, ".format( len( macros.resultsIndexSorted[ result ][ sequence ] ) )

				# For each combo, add each of the capabilities used and their arguments
				for combo in range( 0, len( macros.resultsIndexSorted[ result ][ sequence ] ) ):
					resultItem = macros.resultsIndexSorted[ result ][ sequence ][ combo ]

					# Add the capability index
					self.fill_dict['ResultMacros'] += "{0}, ".format( capabilities.getIndex( resultItem[0] ) )

					# Add each of the arguments of the capability
					for arg in range( 0, len( resultItem[1] ) ):
						# Special cases
						if isinstance( resultItem[1][ arg ], str ):
							# If this is a CONSUMER_ element, needs to be split into 2 elements
							# AC_ and AL_ are other sections of consumer control
							if re.match( r'^(CONSUMER|AC|AL)_', resultItem[1][ arg ] ):
								tag = resultItem[1][ arg ].split( '_', 1 )[1]
								if '_' in tag:
									tag = tag.replace( '_', '' )
								try:
									lookupNum = kll_hid_lookup_dictionary['ConsCode'][ tag ][1]
								except KeyError as err:
									print ( "{0} {1} Consumer HID kll bug...please report.".format( ERROR, err ) )
									raise
								byteForm = lookupNum.to_bytes( 2, byteorder='little' ) # XXX Yes, little endian from how the uC structs work
								self.fill_dict['ResultMacros'] += "{0}, {1}, ".format( *byteForm )
								continue

							# None, fall-through disable
							elif resultItem[0] is self.capabilityLookup('NONE'):
								continue

						self.fill_dict['ResultMacros'] += "{0}, ".format( resultItem[1][ arg ] )

			# If sequence is longer than 1, append a sequence spacer at the end of the sequence
			# Required by USB to end at sequence without holding the key down
			if len( macros.resultsIndexSorted[ result ] ) > 1:
				# <single element>, <usbCodeSend capability>, <USB Code 0x00>
				self.fill_dict['ResultMacros'] += "1, {0}, 0x00, ".format( capabilities.getIndex( self.capabilityLookup('USB') ) )

			# Add list ending 0 and end of list
			self.fill_dict['ResultMacros'] += "0 };\n"
		self.fill_dict['ResultMacros'] = self.fill_dict['ResultMacros'][:-1] # Remove last newline


		## Result Macro List ##
		self.fill_dict['ResultMacroList'] = "const ResultMacro ResultMacroList[] = {\n"

		# Iterate through each of the result macros
		for result in range( 0, len( macros.resultsIndexSorted ) ):
			self.fill_dict['ResultMacroList'] += "\tDefine_RM( {0} ),\n".format( result )
		self.fill_dict['ResultMacroList'] += "};"


		## Result Macro Record ##
		self.fill_dict['ResultMacroRecord'] = "ResultMacroRecord ResultMacroRecordList[ ResultMacroNum ];"


		## Trigger Macros ##
		self.fill_dict['TriggerMacros'] = ""

		# Iterate through each of the trigger macros
		for trigger in range( 0, len( macros.triggersIndexSorted ) ):
			self.fill_dict['TriggerMacros'] += "Guide_TM( {0} ) = {{ ".format( trigger )

			# Add the trigger macro scan code guide
			# See kiibohd controller Macros/PartialMap/kll.h for exact formatting details
			for sequence in range( 0, len( macros.triggersIndexSorted[ trigger ][0] ) ):
				# For each combo in the sequence, add the length of the combo
				self.fill_dict['TriggerMacros'] += "{0}, ".format( len( macros.triggersIndexSorted[ trigger ][0][ sequence ] ) )

				# For each combo, add the key type, key state and scan code
				for combo in range( 0, len( macros.triggersIndexSorted[ trigger ][0][ sequence ] ) ):
					triggerItemId = macros.triggersIndexSorted[ trigger ][0][ sequence ][ combo ]

					# Lookup triggerItem in ScanCodeStore
					triggerItemObj = macros.scanCodeStore[ triggerItemId ]
					triggerItem = triggerItemObj.offset( macros.interconnectOffset )

					# TODO Add support for Analog keys
					# TODO Add support for LED states
					self.fill_dict['TriggerMacros'] += "0x00, 0x01, 0x{0:02X}, ".format( triggerItem )

			# Add list ending 0 and end of list
			self.fill_dict['TriggerMacros'] += "0 };\n"
		self.fill_dict['TriggerMacros'] = self.fill_dict['TriggerMacros'][ :-1 ] # Remove last newline


		## Trigger Macro List ##
		self.fill_dict['TriggerMacroList'] = "const TriggerMacro TriggerMacroList[] = {\n"

		# Iterate through each of the trigger macros
		for trigger in range( 0, len( macros.triggersIndexSorted ) ):
			# Use TriggerMacro Index, and the corresponding ResultMacro Index
			self.fill_dict['TriggerMacroList'] += "\tDefine_TM( {0}, {1} ),\n".format( trigger, macros.triggersIndexSorted[ trigger ][1] )
		self.fill_dict['TriggerMacroList'] += "};"


		## Trigger Macro Record ##
		self.fill_dict['TriggerMacroRecord'] = "TriggerMacroRecord TriggerMacroRecordList[ TriggerMacroNum ];"


		## Max Scan Code ##
		self.fill_dict['MaxScanCode'] = "#define MaxScanCode 0x{0:X}".format( macros.overallMaxScanCode )


		## Interconnect ScanCode Offset List ##
		self.fill_dict['ScanCodeInterconnectOffsetList'] = "const uint8_t InterconnectOffsetList[] = {\n"
		for offset in range( 0, len( macros.interconnectOffset ) ):
			self.fill_dict['ScanCodeInterconnectOffsetList'] += "\t0x{0:02X},\n".format( macros.interconnectOffset[ offset ] )
		self.fill_dict['ScanCodeInterconnectOffsetList'] += "};"


		## Max Interconnect Nodes ##
		self.fill_dict['InterconnectNodeMax'] = "#define InterconnectNodeMax 0x{0:X}\n".format( len( macros.interconnectOffset ) )


		## Default Layer and Default Layer Scan Map ##
		self.fill_dict['DefaultLayerTriggerList'] = ""
		self.fill_dict['DefaultLayerScanMap'] = "const nat_ptr_t *default_scanMap[] = {\n"

		# Iterate over triggerList and generate a C trigger array for the default map and default map array
		for triggerList in range( macros.firstScanCode[0], len( macros.triggerList[0] ) ):
			# Generate ScanCode index and triggerList length
			self.fill_dict['DefaultLayerTriggerList'] += "Define_TL( default, 0x{0:02X} ) = {{ {1}".format( triggerList, len( macros.triggerList[0][ triggerList ] ) )

			# Add scanCode trigger list to Default Layer Scan Map
			self.fill_dict['DefaultLayerScanMap'] += "default_tl_0x{0:02X}, ".format( triggerList )

			# Add each item of the trigger list
			for triggerItem in macros.triggerList[0][ triggerList ]:
				self.fill_dict['DefaultLayerTriggerList'] += ", {0}".format( triggerItem )

			self.fill_dict['DefaultLayerTriggerList'] += " };\n"
		self.fill_dict['DefaultLayerTriggerList'] = self.fill_dict['DefaultLayerTriggerList'][:-1] # Remove last newline
		self.fill_dict['DefaultLayerScanMap'] = self.fill_dict['DefaultLayerScanMap'][:-2] # Remove last comma and space
		self.fill_dict['DefaultLayerScanMap'] += "\n};"


		## Partial Layers and Partial Layer Scan Maps ##
		self.fill_dict['PartialLayerTriggerLists'] = ""
		self.fill_dict['PartialLayerScanMaps'] = ""

		# Iterate over each of the layers, excluding the default layer
		for layer in range( 1, len( macros.triggerList ) ):
			# Prepare each layer
			self.fill_dict['PartialLayerScanMaps'] += "// Partial Layer {0}\n".format( layer )
			self.fill_dict['PartialLayerScanMaps'] += "const nat_ptr_t *layer{0}_scanMap[] = {{\n".format( layer )
			self.fill_dict['PartialLayerTriggerLists'] += "// Partial Layer {0}\n".format( layer )

			# Iterate over triggerList and generate a C trigger array for the layer
			for triggerList in range( macros.firstScanCode[ layer ], len( macros.triggerList[ layer ] ) ):
				# Generate ScanCode index and triggerList length
				self.fill_dict['PartialLayerTriggerLists'] += "Define_TL( layer{0}, 0x{1:02X} ) = {{ {2}".format( layer, triggerList, len( macros.triggerList[ layer ][ triggerList ] ) )

				# Add scanCode trigger list to Default Layer Scan Map
				self.fill_dict['PartialLayerScanMaps'] += "layer{0}_tl_0x{1:02X}, ".format( layer, triggerList )

				# Add each item of the trigger list
				for trigger in macros.triggerList[ layer ][ triggerList ]:
					self.fill_dict['PartialLayerTriggerLists'] += ", {0}".format( trigger )

				self.fill_dict['PartialLayerTriggerLists'] += " };\n"
			self.fill_dict['PartialLayerTriggerLists'] += "\n"
			self.fill_dict['PartialLayerScanMaps'] = self.fill_dict['PartialLayerScanMaps'][:-2] # Remove last comma and space
			self.fill_dict['PartialLayerScanMaps'] += "\n};\n\n"
		self.fill_dict['PartialLayerTriggerLists'] = self.fill_dict['PartialLayerTriggerLists'][:-2] # Remove last 2 newlines
		self.fill_dict['PartialLayerScanMaps'] = self.fill_dict['PartialLayerScanMaps'][:-2] # Remove last 2 newlines


		## Layer Index List ##
		self.fill_dict['LayerIndexList'] = "const Layer LayerIndex[] = {\n"

		# Iterate over each layer, adding it to the list
		for layer in range( 0, len( macros.triggerList ) ):
			# Lookup first scancode in map
			firstScanCode = macros.firstScanCode[ layer ]

			# Generate stacked name
			stackName = ""
			if '*NameStack' in variables.layerVariables[ layer ].keys():
				for name in range( 0, len( variables.layerVariables[ layer ]['*NameStack'] ) ):
					stackName += "{0} + ".format( variables.layerVariables[ layer ]['*NameStack'][ name ] )
				stackName = stackName[:-3]

			# Default map is a special case, always the first index
			if layer == 0:
				self.fill_dict['LayerIndexList'] += '\tLayer_IN( default_scanMap, "D: {1}", 0x{0:02X} ),\n'.format( firstScanCode, stackName )
			else:
				self.fill_dict['LayerIndexList'] += '\tLayer_IN( layer{0}_scanMap, "{0}: {2}", 0x{1:02X} ),\n'.format( layer, firstScanCode, stackName )
		self.fill_dict['LayerIndexList'] += "};"


		## Layer State ##
		self.fill_dict['LayerState'] = "uint8_t LayerState[ LayerNum ];"

