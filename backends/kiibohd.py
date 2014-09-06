#!/usr/bin/env python3
# KLL Compiler - Kiibohd Backend
#
# Backend code generator for the Kiibohd Controller firmware.
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

import os
import sys
import re

# Modifying Python Path, which is dumb, but the only way to import up one directory...
sys.path.append( os.path.expanduser('..') )

from kll_lib.containers import *


### Decorators ###

 ## Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'



### Classes ###

class Backend:
	# Initializes backend
	# Looks for template file and builds list of fill tags
	def __init__( self, templatePath ):
		# Does template exist?
		if not os.path.isfile( templatePath ):
			print ( "{0} '{1}' does not exist...".format( ERROR, templatePath ) )
			sys.exit( 1 )

		self.templatePath = templatePath
		self.fill_dict = dict()

		# Generate list of fill tags
		self.tagList = []
		with open( templatePath, 'r' ) as openFile:
			for line in openFile:
				match = re.findall( '<\|([^|>]+)\|>', line )
				for item in match:
					self.tagList.append( item )


	# USB Code Capability Name
	def usbCodeCapability( self ):
		return "usbKeyOut";


	# Processes content for fill tags and does any needed dataset calculations
	def process( self, capabilities ):
		## Capabilities ##
		self.fill_dict['CapabilitiesList'] = "const Capability CapabilitiesList[] = {\n"

		# Keys are pre-sorted
		for key in capabilities.keys():
			funcName = capabilities.funcName( key )
			argByteWidth = capabilities.totalArgBytes( key )
			self.fill_dict['CapabilitiesList'] += "\t{{ {0}, {1} }},\n".format( funcName, argByteWidth )

		self.fill_dict['CapabilitiesList'] += "};"

		print( self.fill_dict['CapabilitiesList'] )


	# Generates the output keymap with fill tags filled
	def generate( self, filepath ):
		print("My path: {0}".format( filepath) )

