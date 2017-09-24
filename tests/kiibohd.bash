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

# Multiple Function1 test
FUNC1_TEST=${OUT_PATH}/function1
mkdir -p ${FUNC1_TEST}
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
	--partial \
	test_controller/kll/layouts/whitefox/whitefox.kll \
	test_controller/kll/layouts/stdFuncMap.kll \
	--emitter kiibohd \
	--def-template test_controller/kll/templates/kiibohdDefs.h \
	--map-template test_controller/kll/templates/kiibohdKeymap.h \
	--pixel-template test_controller/kll/templates/kiibohdPixelmap.c \
	--def-output ${FUNC1_TEST}/kll_defs.h \
	--map-output ${FUNC1_TEST}/generatedKeymap.h \
	--pixel-output ${FUNC1_TEST}/generatedPixelmap.c \
	--json-output ${FUNC1_TEST}/kll.json


## Tests complete


result
exit $?

