#!/bin/bash
# Common functions for running kll unit tests
# Jacob Alexander 2016-2017

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

# controller git setup
git_setup() {
	export CONTROLLER=/tmp/test_controller
	cd ${SCRIPT_DIR}/..
	export KLL=$(pwd)

	# Check for latest controller, clone/update if necessary
	if [ -e "${CONTROLLER}/main.c" ]; then
		cd ${CONTROLLER}
		git pull --rebase origin master
	else
		git clone https://github.com/kiibohd/controller.git ${CONTROLLER}
		cd ${CONTROLLER}
	fi

	# Symlink this kll to it
	ln -snf ${KLL} kll
	cd ${SCRIPT_DIR}
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

# Runs a command, but on failure tries again while setting an evironment args for CMake infrastructure
# Arg #1:  Base command
# Arg #2:  CMakeBuildArgs env variable on failure
# Arg #3:  CMakeExtraBuildArgs env variable on failure
cmd_cmake() {
	local BASE=${1}
	shift

	# Base command
	cmd ${BASE}

	# Check result
	if [[ $? -ne 0 ]]; then
		local CMakeBuildArgs=${1}
		shift
		local CMakeExtraBuildArgs=${1}

		echo "CMD FAILED - RUNNING DEBUG ARGS - CMakeBuildArgs=${CMakeBuildArgs} CMakeExtraBuildArgs=${CMakeExtraBuildArgs}"
		${BASE}
	fi
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

