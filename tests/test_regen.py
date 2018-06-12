'''
regen test
Runs kll compiler in kll emitter mode, generating a kll file from a kll file.
After creating new kll files (for each stage), compare the final kll file with a known good one.
'''

### Imports ##

import difflib
import filecmp
import os
import pytest
import tempfile
from tests.klltest import kll_run, header_test



### Variables ###

test_files = [
    'kll/examples/assignment.kll',
    'kll/examples/capabilitiesExample.kll',
    'kll/examples/colemak.kll',
    'kll/examples/defaultMapExample.kll',
    'kll/examples/example.kll',
    'kll/examples/hhkbpro2.kll',
    'kll/examples/leds.kll',
    'kll/examples/mapping.kll',
    'kll/examples/md1Map.kll',
    'kll/examples/simple1.kll',
    'kll/examples/simple2.kll',
    'kll/examples/simpleExample.kll',
    'kll/examples/state_scheduling.kll',
    'kll/layouts/mouseTest.kll',
    'kll/layouts/klltest.kll',
    'kll/examples/triggers.kll',
]



### Tests ###

@pytest.mark.parametrize('input_file', test_files)
def test_regen(input_file):
    '''
    Runs regen test on each of the specified files
    '''
    # Prepare tmp directory
    sanitized_input_file = input_file.replace('/', '-')
    tmp_dir = os.path.join(tempfile.gettempdir(), 'kll_pytest')
    os.makedirs(tmp_dir, exist_ok=True)
    target_dir = tempfile.mkdtemp(suffix='-{}'.format(sanitized_input_file), prefix='regen-', dir=tmp_dir)

    # Determine cmp and new files
    cmp_filename = '{}_final.kll'.format(os.path.splitext(os.path.basename(input_file))[0])
    cmp_file = os.path.join('tests', 'cmp_regen', cmp_filename)
    new_file = os.path.join(target_dir, 'final.kll')

    # Run test
    args = ['--emitter', 'kll', '--output-debug', input_file, '--target-dir', target_dir]
    header_test('{} {} {}'.format(input_file, target_dir, cmp_file), args)
    ret = kll_run(args)
    assert ret == 0

    # Check if files are different
    if not filecmp.cmp(cmp_file, new_file):
        # Run diff as both files are different
        with open(cmp_file, 'r') as cmpfile:
            with open(new_file, 'r') as newfile:
                # Run diff and fail the test
                diff = difflib.ndiff(cmpfile.readlines(), newfile.readlines())
                print(''.join(diff), end="")
                assert False

