#!/bin/bash
# Specific combinations of .kll files for testing kiibohd controller code
# Jacob Alexander 2017
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Common functions
source ${SCRIPT_DIR}/common.bash

# Output path
OUT_PATH=${SCRIPT_DIR}/generated_kiibohd

# Cleanup previously generated files
rm -rf ${OUT_PATH}*

# Check for latest controller
git_setup

# Start in kll top-level directory
cd ${SCRIPT_DIR}


## Tests

# Multiple Function1 test (WhiteFox)
func1_test() {
	local TEST_PATH=${OUT_PATH}/function1
	mkdir -p ${TEST_PATH}
	echo "${FUNCNAME[0]}"
	cmd ../kll \
		--config \
		test_controller/Scan/Devices/ISSILed/capabilities.kll \
		test_controller/Scan/Devices/MatrixARM/capabilities.kll \
		test_controller/Macro/PartialMap/capabilities.kll \
		test_controller/Macro/PixelMap/capabilities.kll \
		test_controller/Output/HID-IO/capabilities.kll \
		test_controller/Output/pjrcUSB/capabilities.kll \
		--base \
		test_controller/Scan/WhiteFox/scancode_map.kll \
		test_controller/Scan/WhiteFox/scancode_map.truefox.kll \
		--default \
		test_controller/kll/layouts/tab_function.kll \
		test_controller/kll/layouts/stdFuncMap.kll \
		--partial \
		test_controller/kll/layouts/whitefox/whitefox.kll \
		test_controller/kll/layouts/stdFuncMap.kll \
		--emitter kiibohd \
		--def-template test_controller/kll/templates/kiibohdDefs.h \
		--map-template test_controller/kll/templates/kiibohdKeymap.h \
		--pixel-template test_controller/kll/templates/kiibohdPixelmap.c \
		--def-output ${TEST_PATH}/kll_defs.h \
		--map-output ${TEST_PATH}/generatedKeymap.h \
		--pixel-output ${TEST_PATH}/generatedPixelmap.c \
		--json-output ${TEST_PATH}/kll.json ${@}
}

# Basic K-Type Test
add_test() {
	local TEST_PATH=${OUT_PATH}/add
	mkdir -p ${TEST_PATH}
	echo "${FUNCNAME[0]}"
	cmd ../kll \
		--config \
		test_controller/Scan/Devices/ISSILed/capabilities.kll \
		test_controller/Scan/Devices/MatrixARM/capabilities.kll \
		test_controller/Scan/Devices/PortSwap/capabilities.kll \
		test_controller/Scan/Devices/UARTConnect/capabilities.kll \
		test_controller/Macro/PartialMap/capabilities.kll \
		test_controller/Macro/PixelMap/capabilities.kll \
		test_controller/Output/HID-IO/capabilities.kll \
		test_controller/Output/pjrcUSB/capabilities.kll \
		--base \
		test_controller/Scan/K-Type/scancode_map.kll \
		--default \
		test_controller/kll/layouts/animation_test.kll \
		test_controller/kll/layouts/stdFuncMap.kll \
		--partial \
		test_controller/kll/layouts/k-type/unset_v1.kll \
		test_controller/kll/layouts/k-type/rainbow_wipe.kll \
		--partial \
		test_controller/kll/layouts/k-type/unset_v1.kll \
		test_controller/kll/layouts/k-type/color_painter.kll \
		--emitter kiibohd \
		--def-template test_controller/kll/templates/kiibohdDefs.h \
		--map-template test_controller/kll/templates/kiibohdKeymap.h \
		--pixel-template test_controller/kll/templates/kiibohdPixelmap.c \
		--def-output ${TEST_PATH}/kll_defs.h \
		--map-output ${TEST_PATH}/generatedKeymap.h \
		--pixel-output ${TEST_PATH}/generatedPixelmap.c \
		--json-output ${TEST_PATH}/kll.json ${@}
}

# Interconnect Test
interconnect_test() {
	local TEST_PATH=${OUT_PATH}/interconnect
	mkdir -p ${TEST_PATH}
	echo "${FUNCNAME[0]}"

	cmd ../kll \
		--config \
		test_controller/Scan/Devices/ISSILed/capabilities.kll \
		test_controller/Scan/Devices/MatrixARM/capabilities.kll \
		test_controller/Scan/Devices/STLcd/capabilities.kll \
		test_controller/Scan/Devices/UARTConnect/capabilities.kll \
		test_controller/Macro/PartialMap/capabilities.kll \
		test_controller/Macro/PixelMap/capabilities.kll \
		test_controller/Output/HID-IO/capabilities.kll \
		test_controller/Output/pjrcUSB/capabilities.kll \
		--base \
		test_controller/Scan/Infinity_Ergodox/scancode_map.kll \
		test_controller/Scan/Infinity_Ergodox/leftHand.kll \
		test_controller/Scan/Infinity_Ergodox/slave1.kll \
		test_controller/Scan/Infinity_Ergodox/rightHand.kll \
		--default \
		test_controller/kll/layouts/infinity_ergodox/mdergo1Overlay.kll \
		test_controller/kll/layouts/infinity_ergodox/lcdFuncMap.kll \
		--partial \
		test_controller/kll/layouts/infinity_ergodox/iced_func.kll \
		--partial \
		test_controller/kll/layouts/infinity_ergodox/iced_numpad.kll \
		--emitter kiibohd \
		--def-template test_controller/kll/templates/kiibohdDefs.h \
		--map-template test_controller/kll/templates/kiibohdKeymap.h \
		--pixel-template test_controller/kll/templates/kiibohdPixelmap.c \
		--def-output ${TEST_PATH}/kll_defs.h \
		--map-output ${TEST_PATH}/generatedKeymap.h \
		--pixel-output ${TEST_PATH}/generatedPixelmap.c \
		--json-output ${TEST_PATH}/kll.json ${@}
}


func1_test ${@}
add_test ${@}
interconnect_test ${@}


## Tests complete


result
exit $?

