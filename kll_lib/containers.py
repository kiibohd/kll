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
		for arg in self.capabilities[ name ][1]:
			totalBytes += int( arg[1] )

		return totalBytes

	# Name of the capability function
	def funcName( self, name ):
		return self.capabilities[ name ][0]


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

	def __repr__( self ):
		return "{0}".format( self.macros )

	def setLayer( self, layer ):
		self.layer = layer

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

	# Return a list of ScanCode triggers with the given USB Code trigger
	def lookupUSBCodes( self, usbCode ):
		scanCodeList = []

		# Scan current layer for USB Codes
		for macro in self.macros[ self.layer ].keys():
			if usbCode == self.macros[ self.layer ][ macro ]:
				scanCodeList.append( macro )

		return scanCodeList

