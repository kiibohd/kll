#!/bin/bash
# Specific combinations of .kll files for testing kiibohd controller code
# Jacob Alexander 2017-2018
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

# Simple test
simple_test() {
	local TEST_PATH=${OUT_PATH}/simple
	mkdir -p ${TEST_PATH}
	echo "${FUNCNAME[0]}"
	cmd ../kll \
		--config \
		${CONTROLLER}/Scan/Devices/MatrixARM/capabilities.kll \
		${CONTROLLER}/Macro/PartialMap/capabilities.kll \
		${CONTROLLER}/Output/USB/capabilities.kll \
		--base \
		${CONTROLLER}/Scan/Infinity_60/scancode_map.kll \
		${CONTROLLER}/kll/examples/nonetest.kll \
		--default \
		${CONTROLLER}/kll/layouts/stdFuncMap.kll \
		--emitter kiibohd \
		--def-template ${CONTROLLER}/kll/templates/kiibohdDefs.h \
		--map-template ${CONTROLLER}/kll/templates/kiibohdKeymap.h \
		--pixel-template ${CONTROLLER}/kll/templates/kiibohdPixelmap.c \
		--def-output ${TEST_PATH}/kll_defs.h \
		--map-output ${TEST_PATH}/generatedKeymap.h \
		--pixel-output ${TEST_PATH}/generatedPixelmap.c \
		--json-output ${TEST_PATH}/kll.json ${@}
}

# Multiple Function1 test (WhiteFox)
func1_test() {
	local TEST_PATH=${OUT_PATH}/function1
	mkdir -p ${TEST_PATH}
	echo "${FUNCNAME[0]}"
	cmd ../kll \
		--config \
		${CONTROLLER}/Scan/Devices/ISSILed/capabilities.kll \
		${CONTROLLER}/Scan/Devices/MatrixARM/capabilities.kll \
		${CONTROLLER}/Macro/PartialMap/capabilities.kll \
		${CONTROLLER}/Macro/PixelMap/capabilities.kll \
		${CONTROLLER}/Output/HID-IO/capabilities.kll \
		${CONTROLLER}/Output/USB/capabilities.kll \
		--base \
		${CONTROLLER}/Scan/WhiteFox/scancode_map.kll \
		${CONTROLLER}/Scan/WhiteFox/scancode_map.truefox.kll \
		--default \
		${CONTROLLER}/kll/layouts/tab_function.kll \
		${CONTROLLER}/kll/layouts/stdFuncMap.kll \
		--partial \
		${CONTROLLER}/kll/layouts/whitefox/whitefox.kll \
		${CONTROLLER}/kll/layouts/stdFuncMap.kll \
		--emitter kiibohd \
		--def-template ${CONTROLLER}/kll/templates/kiibohdDefs.h \
		--map-template ${CONTROLLER}/kll/templates/kiibohdKeymap.h \
		--pixel-template ${CONTROLLER}/kll/templates/kiibohdPixelmap.c \
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
		${CONTROLLER}/Scan/Devices/ISSILed/capabilities.kll \
		${CONTROLLER}/Scan/Devices/MatrixARM/capabilities.kll \
		${CONTROLLER}/Scan/Devices/PortSwap/capabilities.kll \
		${CONTROLLER}/Scan/Devices/UARTConnect/capabilities.kll \
		${CONTROLLER}/Macro/PartialMap/capabilities.kll \
		${CONTROLLER}/Macro/PixelMap/capabilities.kll \
		${CONTROLLER}/Output/HID-IO/capabilities.kll \
		${CONTROLLER}/Output/USB/capabilities.kll \
		--base \
		${CONTROLLER}/Scan/K-Type/scancode_map.kll \
		--default \
		${CONTROLLER}/kll/layouts/animation_test.kll \
		${CONTROLLER}/kll/layouts/stdFuncMap.kll \
		--partial \
		${CONTROLLER}/kll/layouts/k-type/unset_v1.kll \
		${CONTROLLER}/kll/layouts/k-type/rainbow_wipe.kll \
		--partial \
		${CONTROLLER}/kll/layouts/k-type/unset_v1.kll \
		${CONTROLLER}/kll/layouts/k-type/color_painter.kll \
		--emitter kiibohd \
		--def-template ${CONTROLLER}/kll/templates/kiibohdDefs.h \
		--map-template ${CONTROLLER}/kll/templates/kiibohdKeymap.h \
		--pixel-template ${CONTROLLER}/kll/templates/kiibohdPixelmap.c \
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
		${CONTROLLER}/Scan/Devices/ISSILed/capabilities.kll \
		${CONTROLLER}/Scan/Devices/MatrixARM/capabilities.kll \
		${CONTROLLER}/Scan/Devices/STLcd/capabilities.kll \
		${CONTROLLER}/Scan/Devices/UARTConnect/capabilities.kll \
		${CONTROLLER}/Macro/PartialMap/capabilities.kll \
		${CONTROLLER}/Macro/PixelMap/capabilities.kll \
		${CONTROLLER}/Output/HID-IO/capabilities.kll \
		${CONTROLLER}/Output/USB/capabilities.kll \
		--base \
		${CONTROLLER}/Scan/Infinity_Ergodox/scancode_map.kll \
		${CONTROLLER}/Scan/Infinity_Ergodox/leftHand.kll \
		${CONTROLLER}/Scan/Infinity_Ergodox/slave1.kll \
		${CONTROLLER}/Scan/Infinity_Ergodox/rightHand.kll \
		${CONTROLLER}/kll/examples/nonetest.kll \
		--default \
		${CONTROLLER}/kll/layouts/infinity_ergodox/mdergo1Overlay.kll \
		${CONTROLLER}/kll/layouts/infinity_ergodox/lcdFuncMap.kll \
		--partial \
		${CONTROLLER}/kll/layouts/infinity_ergodox/iced_func.kll \
		${CONTROLLER}/kll/layouts/infinity_ergodox/mdergo1Overlay.kll \
		${CONTROLLER}/kll/layouts/infinity_ergodox/lcdFuncMap.kll \
		--partial \
		${CONTROLLER}/kll/layouts/infinity_ergodox/iced_numpad.kll \
		--emitter kiibohd \
		--def-template ${CONTROLLER}/kll/templates/kiibohdDefs.h \
		--map-template ${CONTROLLER}/kll/templates/kiibohdKeymap.h \
		--pixel-template ${CONTROLLER}/kll/templates/kiibohdPixelmap.c \
		--def-output ${TEST_PATH}/kll_defs.h \
		--map-output ${TEST_PATH}/generatedKeymap.h \
		--pixel-output ${TEST_PATH}/generatedPixelmap.c \
		--json-output ${TEST_PATH}/kll.json ${@}
}

# klltest.kll
klltest_test() {
	local TEST_PATH=${OUT_PATH}/klltest
	mkdir -p ${TEST_PATH}
	echo "${FUNCNAME[0]}"
	cmd ../kll \
		--config \
		${CONTROLLER}/Scan/Devices/MatrixARM/capabilities.kll \
		${CONTROLLER}/Macro/PartialMap/capabilities.kll \
		${CONTROLLER}/Output/USB/capabilities.kll \
		--base \
		${CONTROLLER}/Scan/Infinity_60/scancode_map.kll \
		--default \
		${CONTROLLER}/kll/layouts/klltest.kll \
		--emitter kll \
		--target-dir ${TEST_PATH} \
		${@}
	cmd ../kll \
		--config \
		${CONTROLLER}/Scan/Devices/MatrixARM/capabilities.kll \
		${CONTROLLER}/Macro/PartialMap/capabilities.kll \
		${CONTROLLER}/Output/USB/capabilities.kll \
		--base \
		${CONTROLLER}/Scan/Infinity_60/scancode_map.kll \
		--default \
		${CONTROLLER}/kll/layouts/klltest.kll \
		--emitter kiibohd \
		--def-template ${CONTROLLER}/kll/templates/kiibohdDefs.h \
		--map-template ${CONTROLLER}/kll/templates/kiibohdKeymap.h \
		--pixel-template ${CONTROLLER}/kll/templates/kiibohdPixelmap.c \
		--def-output ${TEST_PATH}/kll_defs.h \
		--map-output ${TEST_PATH}/generatedKeymap.h \
		--pixel-output ${TEST_PATH}/generatedPixelmap.c \
		--json-output ${TEST_PATH}/kll.json ${@}
}


simple_test ${@}
func1_test ${@}
add_test ${@}
interconnect_test ${@}
klltest_test ${@}


## Tests complete


result
exit $?

