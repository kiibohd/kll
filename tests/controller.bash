#!/bin/bash
# Run through I:C keyboards to validate kll compiler usage.
# Jacob Alexander 2017
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Common functions
source ${SCRIPT_DIR}/common.bash

# Start in kll top-level directory
cd ${SCRIPT_DIR}/..

CONTROLLER=test_controller


## Tests

# Check for latest controller, clone/update if necessary
if [ -e "${SCRIPT_DIR}/${CONTROLLER}/main.c" ]; then
	cd ${SCRIPT_DIR}/${CONTROLLER}
	git pull --rebase origin master
else
	cd ${SCRIPT_DIR}
	git clone https://github.com/kiibohd/controller.git ${CONTROLLER}
	cd ${SCRIPT_DIR}/${CONTROLLER}
fi

# Symlink this kll to it
ln -sf -T ${SCRIPT_DIR}/.. kll
cd Keyboards

# Run kll_regen targets
# TODO On failures, run debug targets
export CMakeExtraBuildArgs='-- kll_regen'
cmd ./ergodox.bash
cmd ./infinity.bash
cmd ./infinity_led.bash
cmd ./k-type.bash
cmd ./whitefox.bash


## Tests complete

result
exit $?

