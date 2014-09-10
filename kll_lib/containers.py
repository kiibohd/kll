#!/usr/bin/env python3
# KLL Compiler Containers
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

import copy



### Decorators ###

 ## Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'



### Parsing ###

 ## Containers
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
		if not self.baseLayout is None:
			del self.layerLayoutMarkers[ self.layer ][ trigger ]

	# Return a list of ScanCode triggers with the given USB Code trigger
	def lookupUSBCodes( self, usbCode ):
		scanCodeList = []

		# Scan current layer for USB Codes
		for macro in self.macros[ self.layer ].keys():
			if usbCode in self.macros[ self.layer ][ macro ]:
				scanCodeList.append( macro )

		return scanCodeList

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
			elif item[0] == ":":
				self.replaceScanCode( item[1], item[2] )

		# Clear assignment cache
		self.assignmentCache = []

	# Generate/Correlate Layers
	def generate( self ):
		self.generateIndices()
		self.sortIndexLists()
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
						for combo in sequence:
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

		# Determine overall maxScanCode
		self.overallMaxScanCode = 0x00
		for maxVal in self.maxScanCode:
			if maxVal > self.overallMaxScanCode:
				self.overallMaxScanCode = maxVal

