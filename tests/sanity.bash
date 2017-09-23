#!/bin/bash
# Basic sanity check for kll compiler
# Jacob Alexander 2016-2017
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Common functions
source ${SCRIPT_DIR}/common.bash

# Start in kll top-level directory
cd ${SCRIPT_DIR}/..


## Tests

cmd ./kll --version

## Tests complete


result
exit $?

