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
rm -rf ${SCRIPT_DIR}/generated


# Args used for each of the tests
ARGS="--emitter kll --target-dir ${SCRIPT_DIR}/generated"
FAIL_ARGS="--emitter kll --target-dir ${SCRIPT_DIR}/generated --token-debug --parser-token-debug --operation-organization-display --data-organization-display --data-finalization-display"

# Files to check syntax on
FILES=(
	examples/assignment.kll
)


## Tests


cmds "./kll" "${ARGS}" "${FAIL_ARGS}" ${FILES[@]}
cmd diff --color=always ${SCRIPT_DIR}/cmp_assignment/final.kll ${SCRIPT_DIR}/generated/final.kll


## Tests complete


result
exit $?

