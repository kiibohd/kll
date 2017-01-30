/* Copyright (C) 2016-2017 by Jacob Alexander
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


// ----- Includes -----

// Compiler Includes
#include <stdint.h>

// KLL Includes
#include <kll_defs.h>

// Project Includes
#include <pixel.h>



// LED Buffer Struct
<|LEDBufferStruct|>


// Buffer list
<|PixelBufferSetup|>


// Pixel Mapping
<|PixelMapping|>


// Pixel Display Mapping
// TODO This table should be generated based off the physical x,y,z positions of each of the pixels
// TODO type should be determined by Pixel_TotalPixels
<|PixelDisplayMapping|>


// Animation Frames and Framesets
//  uint8_t *<animation>_frames[] = { <animation>_frame<num>, ... }
<|AnimationFrames|>
// Index of animations
//  uint8_t *Pixel_Animations[] = { <animation>_frames, ... }
<|Animations|>


// ScanCode to Pixel Mapping
<|ScanCodeToPixelMapping|>


// ScanCode to Display Mapping
<|ScanCodeToDisplayMapping|>

