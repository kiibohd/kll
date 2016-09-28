#!/bin/bash
# Basic sanity check for kll compiler
# Currently runs both versions of the compiler
set +x

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

	# Check command
	if [[ $? -ne 0 ]]; then
		((FAILED++))
	else
		((PASSED++))
	fi
}


# Start in kll top-level directory
cd ${SCRIPT_DIR}/..

cmd ./kll.py --version
cmd ./kll --version

result
exit $?

