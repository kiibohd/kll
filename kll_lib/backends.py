#!/usr/bin/env python3
# KLL Compiler - Kiibohd Backend
#
# Backend code generator classes
#
# Copyright (C) 2015 by Jacob Alexander
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

import os
import sys
import re


### Decorators ###

 ## Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'



### Classes ###

class BackendBase:
	# Default templates and output files
	templatePaths = []
	outputPaths = []

	# Initializes backend
	# Looks for template file and builds list of fill tags
	def __init__( self, templatePaths ):
		# Use defaults if no template is specified
		if templatePaths is not None:
			self.templatePaths = templatePaths

		self.fill_dict = dict()

		# Process each template and add to tagList
		self.tagList = []
		for templatePath in self.templatePaths:
			# Does template exist?
			if not os.path.isfile( templatePath ):
				print ( "{0} '{1}' does not exist...".format( ERROR, templatePath ) )
				sys.exit( 1 )

			# Generate list of fill tags
			with open( templatePath, 'r' ) as openFile:
				for line in openFile:
					match = re.findall( '<\|([^|>]+)\|>', line )
					for item in match:
						self.tagList.append( item )


	# USB Code Capability Name
	# XXX Make sure to override
	def usbCodeCapability( self ):
		return "my_capability";


	# Processes content for fill tags and does any needed dataset calculations
	# XXX Make sure to override
	def process( self, capabilities, macros, variables, gitRev, gitChanges ):
		print ( "{0} BackendBase 'process' function must be overridden".format( ERROR ) )
		sys.exit( 2 )


	# Generates the output keymap with fill tags filled
	def generate( self, outputPaths ):
		# Use default if not specified
		if outputPaths is None:
			outputPaths = self.outputPaths

		for templatePath, outputPath in zip( self.templatePaths, outputPaths ):
			# Process each line of the template, outputting to the target path
			with open( outputPath, 'w' ) as outputFile:
				with open( templatePath, 'r' ) as templateFile:
					for line in templateFile:
						# TODO Support multiple replacements per line
						# TODO Support replacement with other text inline
						match = re.findall( '<\|([^|>]+)\|>', line )

						# If match, replace with processed variable
						if match:
							outputFile.write( self.fill_dict[ match[ 0 ] ] )
							outputFile.write("\n")

						# Otherwise, just append template to output file
						else:
							outputFile.write( line )

