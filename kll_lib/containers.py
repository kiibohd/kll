#!/usr/bin/env python3
# KLL Compiler Containers
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

import copy



### Decorators ###

## Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'



### Parsing ###


## Containers

class ScanCode:
	# Container for ScanCodes
	#
	# scancode        - Non-interconnect adjusted scan code
	# interconnect_id - Unique id for the interconnect node
	def __init__( self, scancode, interconnect_id ):
		self.scancode = scancode
		self.interconnect_id = interconnect_id

	def __eq__( self, other ):
		return self.dict() == other.dict()

	def __repr__( self ):
		return repr( self.dict() )

	def dict( self ):
		return {
			'ScanCode' : self.scancode,
			'Id'       : self.interconnect_id,
		}

	# Calculate the actual scancode using the offset list
	def offset( self, offsetList ):
		if self.interconnect_id > 0:
			return self.scancode + offsetList[ self.interconnect_id - 1 ]
		else:
			return self.scancode


class ScanCodeStore:
	# Unique lookup for ScanCodes
	def __init__( self ):
		self.scancodes = []

	def __getitem__( self, name ):
		# First check if this is a ScanCode object
		if isinstance( name, ScanCode ):
			# Do a reverse lookup
			for idx, scancode in enumerate( self.scancodes ):
				if scancode == name:
					return idx

			# Could not find scancode
			return None

		# Return scancode using unique id
		return self.scancodes[ name ]

	# Attempt add ScanCode to list, return unique id
	def append( self, new_scancode ):
		# Iterate through list to make sure this is a unique ScanCode
		for idx, scancode in enumerate( self.scancodes ):
			if new_scancode == scancode:
				return idx

		# Unique entry, add to the list
		self.scancodes.append( new_scancode )

		return len( self.scancodes ) - 1


class Capabilities:
	# Container for capabilities dictionary and convenience functions
	def __init__( self ):
		self.capabilities = dict()

	def __getitem__( self, name ):
		return self.capabilities[ name ]

	def __setitem__( self, name, contents ):
		self.capabilities[ name ] = contents

	def __repr__( self ):
		return "Capabilities => {0}\nIndexed Capabilities => {1}".format( self.capabilities, sorted( self.capabilities, key = self.capabilities.get ) )


	# Total bytes needed to store arguments
	def totalArgBytes( self, name ):
		totalBytes = 0

		# Iterate over the arguments, summing the total bytes
		for arg in self.capabilities[ name ][ 1 ]:
			totalBytes += int( arg[ 1 ] )

		return totalBytes

	# Name of the capability function
	def funcName( self, name ):
		return self.capabilities[ name ][ 0 ]


	# Only valid while dictionary keys are not added/removed
	def getIndex( self, name ):
		return sorted( self.capabilities, key = self.capabilities.get ).index( name )

	def getName( self, index ):
		return sorted( self.capabilities, key = self.capabilities.get )[ index ]

	def keys( self ):
		return sorted( self.capabilities, key = self.capabilities.get )


class Macros:
	# Container for Trigger Macro : Result Macro correlation
	# Layer selection for generating TriggerLists
	#
	# Only convert USB Code list once all the ResultMacros have been accumulated (does a macro reduction; not reversible)
	# Two staged list for ResultMacros:
	#  1) USB Code/Non-converted (may contain capabilities)
	#  2) Capabilities
	def __init__( self ):
		# Default layer (0)
		self.layer = 0

		# Unique ScanCode Hash Id Lookup
		self.scanCodeStore = ScanCodeStore()

		# Macro Storage
		self.macros = [ dict() ]

		# Base Layout Storage
		self.baseLayout = None
		self.layerLayoutMarkers = []

		# Correlated Macro Data
		self.resultsIndex = dict()
		self.triggersIndex = dict()
		self.resultsIndexSorted = []
		self.triggersIndexSorted = []
		self.triggerList = []
		self.maxScanCode = []
		self.firstScanCode = []
		self.interconnectOffset = []

		# USBCode Assignment Cache
		self.assignmentCache = []

	def __repr__( self ):
		return "{0}".format( self.macros )

	def completeBaseLayout( self ):
		# Copy base layout for later use when creating partial layers and add marker
		self.baseLayout = copy.deepcopy( self.macros[ 0 ] )
		self.layerLayoutMarkers.append( copy.deepcopy( self.baseLayout ) ) # Not used for default layer, just simplifies coding

	def removeUnmarked( self ):
		# Remove all of the unmarked mappings from the partial layer
		for trigger in self.layerLayoutMarkers[ self.layer ].keys():
			del self.macros[ self.layer ][ trigger ]

	def addLayer( self ):
		# Increment layer count, and append another macros dictionary
		self.layer += 1
		self.macros.append( copy.deepcopy( self.baseLayout ) )

		# Add a layout marker for each layer
		self.layerLayoutMarkers.append( copy.deepcopy( self.baseLayout ) )

	# Use for ScanCode trigger macros
	def appendScanCode( self, trigger, result ):
		if not trigger in self.macros[ self.layer ]:
			self.replaceScanCode( trigger, result )
		else:
			self.macros[ self.layer ][ trigger ].append( result )

	# Remove the given trigger/result pair
	def removeScanCode( self, trigger, result ):
		# Remove all instances of the given trigger/result pair
		while result in self.macros[ self.layer ][ trigger ]:
			self.macros[ self.layer ][ trigger ].remove( result )

	# Replaces the given trigger with the given result
	# If multiple results for a given trigger, clear, then add
	def replaceScanCode( self, trigger, result ):
		self.macros[ self.layer ][ trigger ] = [ result ]

		# Mark layer scan code, so it won't be removed later
		# Also check to see if it hasn't already been removed before
		if not self.baseLayout is None and trigger in self.layerLayoutMarkers[ self.layer ]:
			del self.layerLayoutMarkers[ self.layer ][ trigger ]

	# Return a list of ScanCode triggers with the given USB Code trigger
	def lookupUSBCodes( self, usbCode ):
		scanCodeList = []

		# Scan current layer for USB Codes
		for macro in self.macros[ self.layer ].keys():
			if usbCode in self.macros[ self.layer ][ macro ]:
				scanCodeList.append( macro )

		if len(scanCodeList) == 0:
			if len(usbCode) > 1 or len(usbCode[0]) > 1:
				for combo in usbCode:
					comboCodes = list()
					for key in combo:
						scanCode = self.lookupUSBCodes(((key,),))
						comboCodes.append(scanCode[0][0][0])
					scanCodeList.append(tuple(code for code in comboCodes))
				scanCodeList = [tuple(scanCodeList)]

		return scanCodeList

	# Check whether we should do soft replacement
	def softReplaceCheck( self, scanCode ):
		# First check if not the default layer
		if self.layer == 0:
			return True

		# Check if current layer is set the same as the BaseMap
		if not self.baseLayout is None and scanCode in self.layerLayoutMarkers[ self.layer ]:
			return False

		# Otherwise, allow replacement
		return True

	# Cache USBCode Assignment
	def cacheAssignment( self, operator, scanCode, result ):
		self.assignmentCache.append( [ operator, scanCode, result ] )

	# Assign cached USBCode Assignments
	def replayCachedAssignments( self ):
		# Iterate over each item in the assignment cache
		for item in self.assignmentCache:
			# Check operator, and choose the specified assignment action
			# Append Case
			if item[0] == ":+":
				self.appendScanCode( item[1], item[2] )

			# Remove Case
			elif item[0] == ":-":
				self.removeScanCode( item[1], item[2] )

			# Replace Case
			elif item[0] == ":" or item[0] == "::":
				self.replaceScanCode( item[1], item[2] )

		# Clear assignment cache
		self.assignmentCache = []

	# Generate/Correlate Layers
	def generate( self ):
		self.generateIndices()
		self.sortIndexLists()
		self.generateOffsetTable()
		self.generateTriggerLists()

	# Generates Index of Results and Triggers
	def generateIndices( self ):
		# Iterate over every trigger result, and add to the resultsIndex and triggersIndex
		for layer in range( 0, len( self.macros ) ):
			for trigger in self.macros[ layer ].keys():
				# Each trigger has a list of results
				for result in self.macros[ layer ][ trigger ]:
					# Only add, with an index, if result hasn't been added yet
					if not result in self.resultsIndex:
						self.resultsIndex[ result ] = len( self.resultsIndex )

					# Then add a trigger for each result, if trigger hasn't been added yet
					triggerItem = tuple( [ trigger, self.resultsIndex[ result ] ] )
					if not triggerItem in self.triggersIndex:
						self.triggersIndex[ triggerItem ] = len( self.triggersIndex )

	# Sort Index Lists using the indices rather than triggers/results
	def sortIndexLists( self ):
		self.resultsIndexSorted = [ None ] * len( self.resultsIndex )
		# Iterate over the resultsIndex and sort by index
		for result in self.resultsIndex.keys():
			self.resultsIndexSorted[ self.resultsIndex[ result ] ] = result

		self.triggersIndexSorted = [ None ] * len( self.triggersIndex )
		# Iterate over the triggersIndex and sort by index
		for trigger in self.triggersIndex.keys():
			self.triggersIndexSorted[ self.triggersIndex[ trigger ] ] = trigger

	# Generates list of offsets for each of the interconnect ids
	def generateOffsetTable( self ):
		idMaxScanCode = [ 0 ]

		# Iterate over each layer to get list of max scancodes associated with each interconnect id
		for layer in range( 0, len( self.macros ) ):
			# Iterate through each trigger/sequence in the layer
			for sequence in self.macros[ layer ].keys():
				# Iterate over the trigger to locate the ScanCodes
				for combo in sequence:
					# Iterate over each scancode id in the combo
					for scancode_id in combo:
						# Lookup ScanCode
						scancode_obj = self.scanCodeStore[ scancode_id ]

						# Extend list if not large enough
						if scancode_obj.interconnect_id >= len( idMaxScanCode ):
							idMaxScanCode.extend( [ 0 ] * ( scancode_obj.interconnect_id - len( idMaxScanCode ) + 1 ) )

						# Determine if the max seen id for this interconnect id
						if scancode_obj.scancode > idMaxScanCode[ scancode_obj.interconnect_id ]:
							idMaxScanCode[ scancode_obj.interconnect_id ] = scancode_obj.scancode

		# Generate interconnect offsets
		self.interconnectOffset = [ idMaxScanCode[0] + 1 ]
		for index in range( 1, len( idMaxScanCode ) ):
			self.interconnectOffset.append( self.interconnectOffset[ index - 1 ] + idMaxScanCode[ index ] )

	# Generates Trigger Lists per layer using index lists
	def generateTriggerLists( self ):
		for layer in range( 0, len( self.macros ) ):
			# Set max scancode to 0xFF (255)
			# But keep track of the actual max scancode and reduce the list size
			self.triggerList.append( [ [] ] * 0xFF )
			self.maxScanCode.append( 0x00 )

			# Iterate through trigger macros to locate necessary ScanCodes and corresponding triggerIndex
			for trigger in self.macros[ layer ].keys():
				for variant in range( 0, len( self.macros[ layer ][ trigger ] ) ):
					# Identify result index
					resultIndex = self.resultsIndex[ self.macros[ layer ][ trigger ][ variant ] ]

					# Identify trigger index
					triggerIndex = self.triggersIndex[ tuple( [ trigger, resultIndex ] ) ]

					# Iterate over the trigger to locate the ScanCodes
					for sequence in trigger:
						for combo_id in sequence:
							combo = self.scanCodeStore[ combo_id ].offset( self.interconnectOffset )
							# Append triggerIndex for each found scanCode of the Trigger List
							# Do not re-add if triggerIndex is already in the Trigger List
							if not triggerIndex in self.triggerList[ layer ][ combo ]:
								# Append is working strangely with list pre-initialization
								# Doing a 0 check replacement instead -HaaTa
								if len( self.triggerList[ layer ][ combo ] ) == 0:
									self.triggerList[ layer ][ combo ] = [ triggerIndex ]
								else:
									self.triggerList[ layer ][ combo ].append( triggerIndex )

							# Look for max Scan Code
							if combo > self.maxScanCode[ layer ]:
								self.maxScanCode[ layer ] = combo

			# Shrink triggerList to actual max size
			self.triggerList[ layer ] = self.triggerList[ layer ][ : self.maxScanCode[ layer ] + 1 ]

			# Calculate first scan code for layer, useful for uC implementations trying to save RAM
			firstScanCode = 0
			for triggerList in range( 0, len( self.triggerList[ layer ] ) ):
				firstScanCode = triggerList

				# Break if triggerList has items
				if len( self.triggerList[ layer ][ triggerList ] ) > 0:
					break;
			self.firstScanCode.append( firstScanCode )

		# Determine overall maxScanCode
		self.overallMaxScanCode = 0x00
		for maxVal in self.maxScanCode:
			if maxVal > self.overallMaxScanCode:
				self.overallMaxScanCode = maxVal


class Variables:
	# Container for variables
	# Stores three sets of variables, the overall combined set, per layer, and per file
	def __init__( self ):
		# Dictionaries of variables
		self.baseLayout       = dict()
		self.fileVariables    = dict()
		self.layerVariables   = [ dict() ]
		self.overallVariables = dict()
		self.defines          = dict()

		self.currentFile = ""
		self.currentLayer = 0
		self.baseLayoutEnabled = True

	def baseLayoutFinished( self ):
		self.baseLayoutEnabled = False

	def setCurrentFile( self, name ):
		# Store using filename and current layer
		self.currentFile = name
		self.fileVariables[ name ] = dict()

		# If still processing BaseLayout
		if self.baseLayoutEnabled:
			if '*LayerFiles' in self.baseLayout.keys():
				self.baseLayout['*LayerFiles'] += [ name ]
			else:
				self.baseLayout['*LayerFiles'] = [ name ]
		# Set for the current layer
		else:
			if '*LayerFiles' in self.layerVariables[ self.currentLayer ].keys():
				self.layerVariables[ self.currentLayer ]['*LayerFiles'] += [ name ]
			else:
				self.layerVariables[ self.currentLayer ]['*LayerFiles'] = [ name ]

	def incrementLayer( self ):
		# Store using layer index
		self.currentLayer += 1
		self.layerVariables.append( dict() )

	def assignVariable( self, key, value ):
		# Overall set of variables
		self.overallVariables[ key ] = value

		# The Name variable is a special accumulation case
		if key == 'Name':
			# BaseLayout still being processed
			if self.baseLayoutEnabled:
				if '*NameStack' in self.baseLayout.keys():
					self.baseLayout['*NameStack'] += [ value ]
				else:
					self.baseLayout['*NameStack'] = [ value ]
			# Layers
			else:
				if '*NameStack' in self.layerVariables[ self.currentLayer ].keys():
					self.layerVariables[ self.currentLayer ]['*NameStack'] += [ value ]
				else:
					self.layerVariables[ self.currentLayer ]['*NameStack'] = [ value ]

		# If still processing BaseLayout
		if self.baseLayoutEnabled:
			self.baseLayout[ key ] = value
		# Set for the current layer
		else:
			self.layerVariables[ self.currentLayer ][ key ] = value

		# File context variables
		self.fileVariables[ self.currentFile ][ key ] = value

