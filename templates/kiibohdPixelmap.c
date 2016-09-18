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
#include <kll_defs.h.new.h>

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
//#define Pixel_BuffersLen 4
//#define Pixel_TotalChannels 576
PixelBuf Pixel_Buffers[] = {
	PixelBufElem( LED_BufferLength, 16, 0, LED_pageBuffer[0].buffer ),
	PixelBufElem( LED_BufferLength, 16, 144, LED_pageBuffer[1].buffer ),
	PixelBufElem( LED_BufferLength, 16, 288, LED_pageBuffer[2].buffer ),
	PixelBufElem( LED_BufferLength, 16, 432, LED_pageBuffer[3].buffer ),
};


// Pixel Mapping
//#define Pixel_TotalPixels 128 // TODO Generate
const PixelElement Pixel_Mapping[] = {
	// Function Row (1-16)
	Pixel_RGBChannel(0,33,49), // 1
	Pixel_RGBChannel(1,17,50), // 2
	Pixel_RGBChannel(2,18,34), // 3
	Pixel_RGBChannel(3,19,35), // 4
	Pixel_RGBChannel(4,20,36), // 5
	Pixel_RGBChannel(5,21,37), // 6
	Pixel_RGBChannel(6,22,38), // 7
	Pixel_RGBChannel(7,23,39), // 8
	Pixel_RGBChannel(128,112,96), // 9
	Pixel_RGBChannel(129,113,97), // 10
	Pixel_RGBChannel(130,114,98), // 11
	Pixel_RGBChannel(131,115,99), // 12
	Pixel_RGBChannel(132,116,100), // 13
	Pixel_RGBChannel(133,117,101), // 14
	Pixel_RGBChannel(134,118,85), // 15
	Pixel_RGBChannel(135,102,86), // 16

	// Number Row (17-33)
	Pixel_RGBChannel(8,41,57), // 17
	Pixel_RGBChannel(9,25,58), // 18
	Pixel_RGBChannel(10,26,42), // 19
	Pixel_RGBChannel(11,27,43), // 20
	Pixel_RGBChannel(12,28,44), // 21
	Pixel_RGBChannel(13,29,45), // 22
	Pixel_RGBChannel(14,30,46), // 23
	Pixel_RGBChannel(15,31,47), // 24
	Pixel_RGBChannel(136,120,104), // 25
	Pixel_RGBChannel(137,121,105), // 26
	Pixel_RGBChannel(138,122,106), // 27
	Pixel_RGBChannel(139,123,107), // 28
	Pixel_RGBChannel(140,124,108), // 29
	Pixel_RGBChannel(141,125,109), // 30
	Pixel_RGBChannel(142,126,93), // 31
	Pixel_RGBChannel(143,110,94), // 32
	Pixel_RGBChannel(144,177,193), // 33

	// Top Alpha Row (34-50)
	Pixel_RGBChannel(145,161,194), // 34
	Pixel_RGBChannel(146,162,178), // 35
	Pixel_RGBChannel(147,163,179), // 36
	Pixel_RGBChannel(148,164,180), // 37
	Pixel_RGBChannel(149,165,181), // 38
	Pixel_RGBChannel(150,166,182), // 39
	Pixel_RGBChannel(151,167,183), // 40
	Pixel_RGBChannel(272,256,240), // 41
	Pixel_RGBChannel(273,257,241), // 42
	Pixel_RGBChannel(274,258,242), // 43
	Pixel_RGBChannel(275,259,243), // 44
	Pixel_RGBChannel(276,260,244), // 45
	Pixel_RGBChannel(277,261,245), // 46
	Pixel_RGBChannel(278,262,229), // 47
	Pixel_RGBChannel(279,246,230), // 48
	Pixel_RGBChannel(152,185,201), // 49
	Pixel_RGBChannel(153,169,202), // 50

	// Mid Alpha Row (51-63)
	Pixel_RGBChannel(154,170,186), // 51
	Pixel_RGBChannel(155,171,187), // 52
	Pixel_RGBChannel(156,172,188), // 53
	Pixel_RGBChannel(157,173,189), // 54
	Pixel_RGBChannel(158,174,190), // 55
	Pixel_RGBChannel(159,175,191), // 56
	Pixel_RGBChannel(280,264,248), // 57
	Pixel_RGBChannel(281,265,249), // 58
	Pixel_RGBChannel(282,266,250), // 59
	Pixel_RGBChannel(283,267,251), // 60
	Pixel_RGBChannel(284,268,252), // 61
	Pixel_RGBChannel(285,269,253), // 62
	Pixel_RGBChannel(286,270,237), // 63

	// Low Alpha Row (64-76)
	Pixel_RGBChannel(287,254,238), // 64
	Pixel_RGBChannel(288,321,337), // 65
	Pixel_RGBChannel(289,305,338), // 66
	Pixel_RGBChannel(290,306,322), // 67
	Pixel_RGBChannel(291,307,323), // 68
	Pixel_RGBChannel(292,308,324), // 69
	Pixel_RGBChannel(293,309,325), // 70
	Pixel_RGBChannel(294,310,326), // 71
	Pixel_RGBChannel(295,311,327), // 72
	Pixel_RGBChannel(416,400,384), // 73
	Pixel_RGBChannel(417,401,385), // 74
	Pixel_RGBChannel(418,402,386), // 75
	Pixel_RGBChannel(419,403,387), // 76

	// Mod Row (77-87)
	Pixel_RGBChannel(420,404,388), // 77
	Pixel_RGBChannel(421,405,389), // 78
	Pixel_RGBChannel(422,406,373), // 79
	Pixel_RGBChannel(423,390,374), // 80
	Pixel_RGBChannel(296,329,345), // 81
	Pixel_RGBChannel(297,313,346), // 82
	Pixel_RGBChannel(298,314,330), // 83
	Pixel_RGBChannel(299,315,331), // 84
	Pixel_RGBChannel(300,316,332), // 85
	Pixel_RGBChannel(301,317,333), // 86
	Pixel_RGBChannel(302,318,334), // 87

	// Unused Pixels
	Pixel_Blank(), // 88
	Pixel_Blank(), // 89
	Pixel_Blank(), // 90
	Pixel_Blank(), // 91
	Pixel_Blank(), // 92
	Pixel_Blank(), // 93
	Pixel_Blank(), // 94
	Pixel_Blank(), // 95
	Pixel_Blank(), // 96

	/* Prototype 1 - K-Type
	Pixel_RGBChannel(303,319,335), // 88
	Pixel_RGBChannel(424,408,392), // 89
	Pixel_RGBChannel(425,409,393), // 90
	Pixel_RGBChannel(426,410,394), // 91
	Pixel_RGBChannel(427,411,395), // 92
	Pixel_RGBChannel(428,412,396), // 93
	Pixel_RGBChannel(429,413,397), // 94
	Pixel_RGBChannel(430,414,381), // 95
	*/

	// Underlighting
	Pixel_RGBChannel(432,465,481), // 97
	Pixel_RGBChannel(433,449,482), // 98
	Pixel_RGBChannel(434,450,466), // 99
	Pixel_RGBChannel(435,451,467), // 100
	Pixel_RGBChannel(436,452,468), // 101
	Pixel_RGBChannel(437,453,469), // 102
	Pixel_RGBChannel(438,454,470), // 103
	Pixel_RGBChannel(439,455,471), // 104
	Pixel_RGBChannel(560,544,528), // 105
	Pixel_RGBChannel(561,545,529), // 106
	Pixel_RGBChannel(562,546,530), // 107
	Pixel_RGBChannel(563,547,531), // 108
	Pixel_RGBChannel(564,548,532), // 109
	Pixel_RGBChannel(565,549,533), // 110
	Pixel_RGBChannel(566,550,517), // 111
	Pixel_RGBChannel(567,534,518), // 112
	Pixel_RGBChannel(440,473,489), // 113
	Pixel_RGBChannel(441,457,490), // 114
	Pixel_RGBChannel(442,458,474), // 115
	Pixel_RGBChannel(443,459,475), // 116
	Pixel_RGBChannel(444,460,476), // 117
	Pixel_RGBChannel(445,461,477), // 118
	Pixel_RGBChannel(446,462,478), // 119
	Pixel_RGBChannel(447,463,479), // 120
	Pixel_RGBChannel(568,552,536), // 121
	Pixel_RGBChannel(569,553,537), // 122
	Pixel_RGBChannel(570,554,538), // 123
	Pixel_RGBChannel(571,555,539), // 124
	Pixel_RGBChannel(572,556,540), // 125
	Pixel_RGBChannel(573,557,541), // 126
	Pixel_RGBChannel(574,558,525), // 127
	Pixel_RGBChannel(575,542,526), // 128
};

// Pixel Display Mapping
// TODO This table should be generated based off the physical x,y,z positions of each of the pixels
// TODO type should be determined by Pixel_TotalPixels
// Notes:
// - Single rows, we ignore the space between the F row and the Number row
// - 0.5 key spacing between the columns, in the case where multiple leds should be in the column, one is shifted to the right
//#define Pixel_DisplayMapping_Cols 38
//#define Pixel_DisplayMapping_Rows 6
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
#define Pixel_ModRGB(pixel,type,color) s2bs(pixel), PixelChange_##type, 1, color
#define Pixel_ModRGB_(pixel,type,r,g,b) pixel, PixelChange_##type, 1, r, g, b
const uint8_t testani_frame0[] = {
	Pixel_ModRGB_(0, Set, 30, 70, 120),
};
const uint8_t testani_frame1[] = {
	Pixel_ModRGB_(0, Set, 0, 0, 0),
};
const uint8_t testani_frame2[] = {
	Pixel_ModRGB_(0, Set, 60, 90, 140),
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


const uint8_t rainbow_inter_frame0[] = {
	Pixel_ModRGB(0, Set, RGB_Green),
	Pixel_ModRGB(5, Set, RGB_Yellow),
	Pixel_ModRGB(10, Set, RGB_Red),
	Pixel_ModRGB(15, Set, RGB_Violet),
	Pixel_ModRGB(20, Set, RGB_Blue),
};


// Index of frames for animations
//  uint8_t *<animation>_frames[] = { <animation>_frame<num>, ... }
const uint8_t *testani_frames[] = {
	testani_frame0,
	testani_frame1,
	testani_frame2,
};


// Rainbox (interpolation) frame index
const uint8_t *rainbow_inter_frames[] = {
	rainbow_inter_frame0,
};


// XXX Temp
uint16_t rainbow_pos = 0;


// Index of animations
//  uint8_t *Pixel_Animations[] = { <animation>_frames, ... }
const uint8_t **Pixel_Animations[] = {
	testani_frames,
};
