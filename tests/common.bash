#!/bin/bash
# Common functions for running kll unit tests
# Jacob Alexander 2016

PASSED=0
FAILED=0

# Results
result() {
	echo "--- Results ---"
	echo "${PASSED}/$((PASSED+FAILED))"
	if (( FAILED == 0 )); then
		return 0
	else
		return 1
	fi
}

# Runs a command, increments test passed/failed
# Args: Command
cmd() {
	# Run command
	echo "CMD: $@"
	$@
	local RET=$?

	# Check command
	if [[ ${RET} -ne 0 ]]; then
		((FAILED++))
	else
		((PASSED++))
	fi

	return ${RET}
}

# Run a command multiple times using an array of values
# Arg #1:  Base command
# Arg #2:  Static arguments
# Arg #3:  Static arguments to call when command fails (debug info)
# Arg #4+: Array of variations to swap into the command
cmds() {
	local BASE=${1}
	shift
	local STATIC=${1}
	shift
	local FAIL_STATIC=${1}
	shift
	local VARS=${@} # Rest of arguments

	# Base command
	echo "BASE CMD: ${BASE} ${STATIC}"

	# Iterate over variations
	for var in ${VARS[@]}; do
		cmd ${BASE} ${STATIC} ${var}
		if [[ $? -ne 0 ]]; then
			echo "CMD FAILED - RUNNING DEBUG ARGS - ${BASE} ${FAIL_STATIC} ${var}"
			${BASE} ${FAIL_STATIC} ${var}
		fi
	done
}

# Run a command multiple times using an array of values
# The final command uses the name of the file and appends to Arg #4 (LAST)
# Arg #1:  Base command
# Arg #2:  Static arguments
# Arg #3:  Static arguments to call when command fails (debug info)
# Arg #4:  Static arguments to call and append basename of file (without extension)
# Arg #5+: Array of variations to swap into the command
cmds_extra() {
	local BASE=${1}
	shift
	local STATIC=${1}
	shift
	local FAIL_STATIC=${1}
	shift
	local LAST=${1}
	shift
	local VARS=${@} # Rest of arguments

	# Base command
	echo "BASE CMD: ${BASE} ${STATIC}"

	# Iterate over variations
	for var in ${VARS[@]}; do
		TEST_NAME="$(basename ${var} .kll)"
		cmd ${BASE} ${STATIC} ${var} ${LAST}${TEST_NAME}
		if [[ $? -ne 0 ]]; then
			echo "CMD FAILED - RUNNING DEBUG ARGS - ${BASE} ${FAIL_STATIC} ${var} ${LAST}${TEST_NAME}"
			${BASE} ${FAIL_STATIC} ${var} ${LAST}${TEST_NAME}
		fi
	done
}

