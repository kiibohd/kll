'''
syntax test
Runs various .kll files through the compiler to make sure that they are processed without unexpected errors
'''

### Imports ##

import pytest
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
def test_syntax(input_file):
    '''
    Runs syntax test on each of the specified files
    '''
    args = ['--emitter', 'none', '--data-finalization-display', input_file]
    header_test(input_file, args)
    ret = kll_run(args)
    assert ret == 0

@pytest.mark.parametrize('input_file', test_files)
def test_syntax_token_debug(input_file):
    '''
    Runs syntax test on each of the specified files, including --parser-token-debug
    '''
    args = ['--emitter', 'none', '--data-finalization-display', '--parser-token-debug', input_file]
    header_test(input_file, args)
    ret = kll_run(args)
    assert ret == 0

@pytest.mark.parametrize('input_file', test_files)
def test_syntax_operation_debug(input_file):
    '''
    Runs syntax test on each of the specified files, including --operation-organization-display
    '''
    args = ['--emitter', 'none', '--data-finalization-display', '--operation-organization-display', input_file]
    header_test(input_file, args)
    ret = kll_run(args)
    assert ret == 0

@pytest.mark.parametrize('input_file', test_files)
def test_syntax_fail_debug(input_file):
    '''
    Runs syntax test on each of the specified files, including failure debug options
    '''
    args = ['--emitter', 'none', '--token-debug', '--parser-token-debug', '--operation-organization-display', '--data-organization-display', '--data-finalization-display', input_file]
    header_test(input_file, args)
    ret = kll_run(args)
    assert ret == 0

