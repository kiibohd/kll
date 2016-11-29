#!/bin/bash
# Use example .kll files to check basic kll processing
# Does a diff comparison with a pre-generated file for validation
# Jacob Alexander 2016
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Common functions
source ${SCRIPT_DIR}/common.bash

# Start in kll top-level directory
cd ${SCRIPT_DIR}/..

# Cleanup previously generated files
rm -rf ${SCRIPT_DIR}/generated_regen*


# Args used for each of the tests
ARGS="--emitter kll --output-debug"
LAST_ARG=" --target-dir ${SCRIPT_DIR}/generated_regen/"
FAIL_ARGS="--emitter kll --token-debug --parser-token-debug --operation-organization-display --data-organization-display --data-finalization-display"
FAIL_ARGS=""

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


cmds_extra "./kll" "${ARGS}" "${FAIL_ARGS}" "${LAST_ARG}" ${FILES[@]}

for file in ${FILES[@]}; do
	base=$(basename ${file})
	cmd diff ${SCRIPT_DIR}/cmp_regen/${base%.*}_final.kll ${SCRIPT_DIR}/generated_regen/${base%.*}/final.kll
done


## Tests complete


result
exit $?

