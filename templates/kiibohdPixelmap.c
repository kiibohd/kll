/* Copyright (C) 2016 by Jacob Alexander
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



// TODO Generate properly
#define ISSI_Chips_define 4
#define LED_BufferLength 144
typedef struct LED_Buffer {
	uint16_t i2c_addr;
	uint16_t reg_addr;
	uint16_t buffer[LED_BufferLength];
} LED_Buffer;
extern LED_Buffer LED_pageBuffer[ ISSI_Chips_define ];


// Buffer list
<|PixelBufferSetup|>


// Pixel Mapping
<|PixelMapping|>


// Pixel Display Mapping
// TODO This table should be generated based off the physical x,y,z positions of each of the pixels
// TODO type should be determined by Pixel_TotalPixels
// Notes:
// - Single rows, we ignore the space between the F row and the Number row
// - 0.5 key spacing between the columns, in the case where multiple leds should be in the column, one is shifted to the right
//#define Pixel_DisplayMapping_Cols 38
//#define Pixel_DisplayMapping_Rows 6
<|PixelDisplayMapping|>
const uint8_t Pixel_DisplayMapping[] = {
 97,  1,  0, 98,  0,  2, 99,  3,  0,  4,100,  5,  0,101,  6,102,  7,  0,  8,103,  9,104,  0, 10,105, 11,  0, 12,106, 13,  0,107, 14,108, 15,  0, 16,109,
128, 17,  0, 18,  0, 19,  0, 20,  0, 21,  0, 22,  0, 23,  0, 24,  0, 25,  0, 26,  0, 27,  0, 28,  0, 29,  0,  0, 30,  0,  0,  0, 31,  0, 32,  0, 33,110,
127, 34,  0,  0, 35,  0, 36,  0, 37,  0, 38,  0, 39,  0, 40,  0, 41,  0, 42,  0, 43,  0, 44,  0, 45,  0, 46,  0,  0, 47,  0,  0, 48,  0, 49,  0, 50,111,
  0,  0, 51,  0,  0, 52,  0, 53,  0, 54,  0, 55,  0, 56,  0, 57,  0, 58,  0, 59,  0, 60,  0, 61,  0, 62,  0,  0, 63,  0,  0,  0,  0,  0,  0,  0,  0,  0,
126,  0, 64,  0,  0,  0, 65,  0, 66,  0, 67,  0, 68,  0, 69,  0, 70,  0, 71,  0, 72,  0, 73,  0, 74,  0,  0,  0, 75,  0,  0,  0,  0,  0, 76,  0,  0,112,
125, 77,  0,124, 78,  0, 79,123,  0,122,  0,  0,  0,121, 80,  0,120,  0,  0,119,  0, 81,118,  0, 82,117, 83,  0,116, 84,  0,115, 85,114, 86,  0, 87,113,
};

// Frame of led changes
//  const uint8_t <animation>_frame<num>[] = { PixelMod, ... }
#define s2bs(n) (n & 0xFF), (n >> 8)
#define w2bs(n) (n & 0xFF), (n & 0xFF00) >> 8, (n & 0xFF0000) >> 16, (n & 0xFF000000) >> 24
#define Pixel_ModRGB(pixel,change,color) PixelAddressType_Index, w2bs(pixel), PixelChange_##change, color
#define Pixel_ModRGBCol(col,change,color) PixelAddressType_ColumnFill, s2bs(col), s2bs(0), PixelChange_##change, color
#define Pixel_ModRGB_(pixel,change,r,g,b) PixelAddressType_Index, w2bs(pixel), PixelChange_##change, r, g, b
#define Pixel_ModRGBScan(scanCode,change,color) PixelAddressType_ScanCode, w2bs(scanCode), PixelChange_##change, color
const uint8_t testani_frame0[] = {
	Pixel_ModRGB_(0, Set, 30, 70, 120),
	PixelAddressType_End,
};
const uint8_t testani_frame1[] = {
	Pixel_ModRGB_(0, Set, 0, 0, 0),
	PixelAddressType_End,
};
const uint8_t testani_frame2[] = {
	Pixel_ModRGB_(0, Set, 60, 90, 140),
	PixelAddressType_End,
};

// Temp convenience colours
#define RGB_HalfRed      127,0,0
#define RGB_Red          255,0,0
#define RGB_RedOrange    255,64,0
#define RGB_Orange       255,127,0
#define RGB_OrangeYellow 255,191,0
#define RGB_Yellow       255,255,0
#define RGB_YellowGreen  127,255,0
#define RGB_Green        0,255,0
#define RGB_GreenBlue    0,127,127
#define RGB_Blue         0,0,255
#define RGB_BlueIndigo   38,0,193
#define RGB_Indigo       75,0,130
#define RGB_IndigoViolet 101,0,193
#define RGB_Violet       127,0,255
#define RGB_HalfViolet   64,0,127

#define RGB_White        255,255,255
#define RGB_Black        0,0,0

#define RGB_MD_Blue      0x00,0xAE,0xDA


const uint8_t rainbow_inter_frame0[] = {
	Pixel_ModRGBCol(0, Set, RGB_Green),
	Pixel_ModRGBCol(9, Set, RGB_Yellow),
	Pixel_ModRGBCol(19, Set, RGB_Red),
	Pixel_ModRGBCol(28, Set, RGB_Violet),
	Pixel_ModRGBCol(37, Set, RGB_Blue),
	0,
};

const uint8_t clear_pixels_frame0[] = {
	Pixel_ModRGBScan(17, Set, RGB_Black),
	Pixel_ModRGBScan(18, Set, RGB_Black),
	Pixel_ModRGBScan(19, Set, RGB_Black),
	Pixel_ModRGBScan(20, Set, RGB_Black),
	Pixel_ModRGBScan(21, Set, RGB_Black),
	0,
};


// Index of frames for animations
//  uint8_t *<animation>_frames[] = { <animation>_frame<num>, ... }
const uint8_t *testani_frames[] = {
	testani_frame0,
	testani_frame1,
	testani_frame2,
	0,
};


// Rainbox (interpolation) frame index
const uint8_t *rainbow_inter_frames[] = {
	rainbow_inter_frame0,
	0,
};


// Pixel Clear test
const uint8_t *clear_pixels_frames[] = {
	clear_pixels_frame0,
	0,
};


const uint8_t md_blue_frame0[] = {
	Pixel_ModRGBCol(0, Set, RGB_MD_Blue),
	Pixel_ModRGBCol(37, Set, RGB_MD_Blue),
	0,
};


const uint8_t *md_blue_frames[] = {
	md_blue_frame0,
	0,
};


// Index of animations
//  uint8_t *Pixel_Animations[] = { <animation>_frames, ... }
<|Animations|>
const uint8_t **Pixel_Animations[] = {
	testani_frames,
	rainbow_inter_frames,
	clear_pixels_frames,
	md_blue_frames,
};


// ScanCode to Pixel Mapping
<|ScanCodeToPixelMapping|>

