'''
locale test
Uses locale .kll files to check locale alias name lookup handling
'''

### Imports ##

import os
import pytest
import tempfile
from tests.klltest import kll_run, header_test



### Variables ###

test_files = [
    ['kll/examples/locale/base.locale-test.kll', 'kll/examples/locale/de_DE.locale-test.kll'],
]



### Tests ###

@pytest.mark.parametrize('input_files', test_files)
def test_locale(input_files):
    '''
    Runs locale test on each of the specified file sets
    '''
    # Prepare tmp directory
    sanitized_input_file = "_".join(input_files).replace('/', '-')
    tmp_dir = os.path.join(tempfile.gettempdir(), 'kll_pytest')
    os.makedirs(tmp_dir, exist_ok=True)
    target_dir = tempfile.mkdtemp(suffix='-{}'.format(sanitized_input_file), prefix='locale-', dir=tmp_dir)

    # Run test
    args = ['--emitter', 'kll', '--output-debug', '--target-dir', target_dir] + input_files
    header_test('{} {}'.format(" ".join(input_files), target_dir), args)
    ret = kll_run(args)
    assert ret == 0

