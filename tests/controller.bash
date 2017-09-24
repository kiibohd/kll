#!/bin/bash
# Run through I:C keyboards to validate kll compiler usage.
# Jacob Alexander 2017
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Common functions
source ${SCRIPT_DIR}/common.bash

# Start in kll top-level directory
cd ${SCRIPT_DIR}/..


## Tests

# Check for latest controller
git_setup
cd ${CONTROLLER}/Keyboards # CONTROLLER is set by git_setup

# Run kll_regen targets
export CMakeExtraBuildArgs='-- kll_regen'
export CMakeExtraArgs='-DCompilerOverride=host'
export ExtraBuildPath='.host_override'

cmd_cmake ./ergodox.bash      "" "-- kll_token kll_parser kll_debug kll_display"
cmd_cmake ./infinity.bash     "" "-- kll_token kll_parser kll_debug kll_display"
cmd_cmake ./infinity_led.bash "" "-- kll_token kll_parser kll_debug kll_display"
cmd_cmake ./k-type.bash       "" "-- kll_token kll_parser kll_debug kll_display"
cmd_cmake ./whitefox.bash     "" "-- kll_token kll_parser kll_debug kll_display"


## Tests complete

result
exit $?

