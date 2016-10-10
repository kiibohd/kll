#!/bin/bash
# Use example .kll files to check syntax compatibility
# Does not generate code, so resulting datastructures do not necessarily need to functino
# Jacob Alexander 2016
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Common functions
source ${SCRIPT_DIR}/common.bash

# Start in kll top-level directory
cd ${SCRIPT_DIR}/..


# Args used for each of the tests
ARGS="--emitter none --data-finalization-display"
FAIL_ARGS="--emitter none --token-debug --parser-token-debug --operation-organization-display --data-organization-display --data-finalization-display"

# Files to check syntax on
FILES=(
	examples/assignment.kll
	examples/capabilitiesExample.kll
	examples/colemak.kll
	examples/defaultMapExample.kll
	examples/example.kll
	examples/hhkbpro2.kll
	examples/leds.kll
	examples/mapping.kll
	examples/md1Map.kll
	examples/simple1.kll
	examples/simple2.kll
	examples/simpleExample.kll
	examples/state_scheduling.kll
)


## Tests


cmds "./kll" "${ARGS}" "${FAIL_ARGS}" ${FILES[@]}


## Tests complete


result
exit $?

