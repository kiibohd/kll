#!/usr/bin/env python3
'''
KLL Context Definitions
* Generic (auto-detected)
* Configuration
* BaseMap
* DefaultMap
* PartialMap
'''

# Copyright (C) 2016-2018 by Jacob Alexander
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
import os

import kll.common.organization as organization



### Decorators ###

# Print Decorator Variables
ERROR = '\033[5;1;31mERROR\033[0m:'
WARNING = '\033[5;1;33mWARNING\033[0m:'



### Classes ###

class Context:
    '''
    Base KLL Context Class
    '''

    def __init__(self):
        '''
        Context initialization
        '''
        # Each context may have one or more included kll files
        # And each of these files will have at least 1 Context
        self.kll_files = []

        # File data assigned to each context
        # This info is populated during the PreprocessorStage
        self.lines = []
        self.data = ""
        self.parent = None

        # Tokenized data sets
        self.classification_token_data = []
        self.expressions = []

        # Organized Expression Datastructure
        self.organization = organization.Organization(self)

        # Layer Information (unset, unless a PartialMapContext)
        self.layer = None

        # Connect Id information (unset, but usually initialized)
        self.connect_id = None

        # HID Mapping object
        self.hid_mapping = None

    def __repr__(self):
        # Build list of all the info
        return "(kll_files={}, hid_mapping={}, lines={}, data='''{}''')".format(
            self.kll_files,
            self.hid_mapping,
            self.lines,
            self.data,
        )

    def layer_info(self):
        '''
        Returns a text string indicating which layer this is
        '''
        if self.layer is None:
            return "0"

        return "{}".format(self.layer + 1)

    def initial_context(self, lines, data, parent):
        '''
        Used in the PreprocessorStage to update the initial line and kll file data

        @param lines:  Data split per line
        @param data:   Entire context in a single string
        @param parent: Parent node, always a KLLFile
        '''
        self.lines = lines
        self.data = data
        self.parent = parent
        self.connect_id = parent.connect_id

    def query(self, kll_expression, kll_type=None):
        '''
        Query

        Returns a dictionary of the specified property.
        Most queries should use this.

        See organization.py:Organization for property_type details.

        @param kll_expression: String name of expression type
        @param kll_type: String name of the expression sub-type
                         If set to None, return all

        @return: context_name: (dictionary)
        '''
        if kll_type is None:
            return self.organization.data_mapping[kll_expression]
        return self.organization.data_mapping[kll_expression][kll_type]


class GenericContext(Context):
    '''
    Generic KLL Context Class
    '''


class ConfigurationContext(Context):
    '''
    Configuration KLL Context Class
    '''


class BaseMapContext(Context):
    '''
    Base Map KLL Context Class
    '''


class DefaultMapContext(Context):
    '''
    Default Map KLL Context Class
    '''


class PartialMapContext(Context):
    '''
    Partial Map KLL Context Class
    '''

    def __init__(self, layer):
        '''
        Partial Map Layer Context Initialization

        @param: Layer associated with Partial Map
        '''
        super().__init__()

        self.layer = layer


class MergeContext(Context):
    '''
    Container class for a merged Context

    Has references to the original contexts merged in
    '''

    def __init__(self, base_context):
        '''
        Initialize the MergeContext with the base context
        Another MergeContext can be used as the base_context

        @param base_context: Context used to seed the MergeContext
        '''
        super().__init__()

        # Setup list of kll_files
        self.kll_files = base_context.kll_files

        # Transfer layer, whenever merging in, we'll use the new layer identifier
        self.layer = base_context.layer

        # List of context, in the order of merging, starting from the base
        self.contexts = [base_context]

        # Copy the base context Organization into the MergeContext
        self.organization = copy.copy(base_context.organization)
        self.organization.parent = self

        # Set the layer if the base is a PartialMapContext
        if base_context.__class__.__name__ == 'PartialMapContext':
            self.layer = base_context.layer

    def merge(self, merge_in, map_type, debug):
        '''
        Merge in context

        Another MergeContext can be merged into a MergeContext

        @param merge_in: Context to merge in to this one
        @param map_type: Used for map specific merges (e.g. BaseMap reductions)
        @param debug:    Enable debug out
        '''
        # Extend list of kll_files
        self.kll_files.extend(merge_in.kll_files)

        # Use merge_in layer identifier as the master (most likely to be correct)
        self.layer = merge_in.layer

        # Append to context list
        self.contexts.append(merge_in)

        # Merge context
        self.organization.merge(
            merge_in.organization,
            map_type,
            debug
        )

        # Set the layer if the base is a PartialMapContext
        if merge_in.__class__.__name__ == 'PartialMapContext':
            self.layer = merge_in.layer

    def cleanup(self, debug=False):
        '''
        Post-processing step for merges that may need to remove some data in the organization.
        Mainly used for dropping BaseMapContext expressions after generating a PartialMapContext.
        '''
        self.organization.cleanup(debug)

    def reduction(self, debug=False):
        '''
        Simplifies datastructure

        NOTE: This will remove data, therefore, context is lost
        '''
        self.organization.reduction(debug)

    def paths(self):
        '''
        Returns list of file paths used to generate this context
        '''
        file_paths = []

        for kll_context in self.contexts:
            # If context is a MergeContext then we have to recursively search
            if kll_context.__class__.__name__ is 'MergeContext':
                file_paths.extend(kll_context.paths())
            else:
                file_paths.append(kll_context.parent.path)

        return file_paths

    def files(self):
        '''
        Short form list of file paths used to generate this context
        '''
        file_paths = []
        for file_path in self.paths():
            file_paths.append(os.path.basename(file_path))

        return file_paths

    def __repr__(self):
        return "(kll_files={0}, organization={1})".format(
            self.files(),
            self.organization,
        )

    def query_contexts(self, kll_expression, kll_type):
        '''
        Context Query

        Returns a list of tuples (dictionary, kll_context) doing a deep search to the context leaf nodes.
        This results in pre-merge data and is useful for querying information about files used during compilation.

        See organization.py:Organization for property_type details.

        @param kll_expression: String name of expression type
        @param kll_type: String name of the expression sub-type

        @return: context_name: (dictionary, kll_context)
        '''
        # Build list of leaf contexts
        leaf_contexts = []
        for kll_context in self.contexts:
            # Recursively search if necessary
            if kll_context.__class__.__name__ == 'MergeContext':
                leaf_contexts.extend(
                    kll_context.query_contexts(
                        kll_expression, kll_type))
            else:
                leaf_contexts.append((
                    kll_context.query(
                        kll_expression,
                        kll_type
                    ),
                    kll_context
                ))

        return leaf_contexts
