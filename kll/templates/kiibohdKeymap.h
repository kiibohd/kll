/* Copyright (C) 2014-2018 by Jacob Alexander
 *
 * This file is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This file is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this file.  If not, see <http://www.gnu.org/licenses/>.
 */

<|Information|>


#pragma once

// ----- Includes -----

// KLL Include
#include <kll.h>



// ----- Capabilities -----

// Capability function declarations
<|CapabilitiesFuncDecl|>


// Indexed Capabilities Table
<|CapabilitiesList|>


// -- Result Macros

// Result Macro Guides
<|ResultMacros|>


// -- Result Macro List

// Indexed Table of Result Macros
<|ResultMacroList|>


// -- Trigger Macros

// Trigger Macro Guides
<|TriggerMacros|>


// -- Trigger Macro List

// Indexed Table of Trigger Macros
<|TriggerMacroList|>


// -- Trigger Macro Record List

// Keeps a record/state of each trigger macro
<|TriggerMacroRecord|>



// ----- Trigger Maps -----

// MaxScanCode
// - This is retrieved from the KLL configuration
// - Should be corollated with the max scan code in the scan module
// - Maximum value is 0x100 (0x0 to 0xFF)
// - Increasing it beyond the keyboard's capabilities is just a waste of ram...
#define MaxScanCode <|MaxScanCode|>

// -- Trigger Lists
//
// Index 0: # of triggers in list
// Index n: pointer to trigger macro - use tm() macro

// - Default Layer -
<|DefaultLayerTriggerList|>


// - Partial Layers -
<|PartialLayerTriggerLists|>


// -- ScanCode Offset Map
// Maps interconnect ids to scancode offsets
//
// Only used for keyboards with an interconnect
<|ScanCodeInterconnectOffsetList|>


// -- ScanCode Indexed Maps
// Maps to a trigger list of macro pointers
//                 _
// <scan code> -> |T|
//                |r| -> <trigger macro pointer 1>
//                |i|
//                |g| -> <trigger macro pointer 2>
//                |g|
//                |e| -> <trigger macro pointer 3>
//                |r|
//                |s| -> <trigger macro pointer n>
//                 -

// - Default Map for ScanCode Lookup -
<|DefaultLayerScanMap|>


// - Partial Layer ScanCode Lookup Maps -
<|PartialLayerScanMaps|>



// ----- Layer Index -----

// -- Layer Index List
//
// Index 0: Default map
// Index n: Additional layers
<|LayerIndexList|>


// - Layer State
<|LayerState|>



// ----- Rotation Parameters -----

// Each position represents the maximum rotation value for the index
<|RotationParameters|>



// ----- Key Positions -----

// -- Physical Key Positions
//
// Index 0: Key 1
// Each key has 6 dimensions
// x,y,z and rx,ry,rz (rotation)
// Units are in mm
<|KeyPositions|>

