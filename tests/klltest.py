'''
Test functions/libraries for the kll compiler
'''

### Imports ###

import kll
import os
import pytest
import tempfile
from git import Repo



### Functions ###

def header_test(name, args):
    '''
    Prints out the name of the test and the arguments passed

    @param name: Name of the test
    @param args: List of arguments
    '''
    print('\n---- {} ---- {}'.format(name, args))

def kll_run(args):
    '''
    Run kll compiler

    @return: Exit code
    '''
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        kll.main(args)
    assert pytest_wrapped_e.type == SystemExit
    return pytest_wrapped_e.value.code

@pytest.fixture(scope="session")
def kiibohd_controller_repo():
    '''
    Downloads a cached copy of the kiibohd controller repo
    '''
    tmp_dir = os.path.join(tempfile.gettempdir(), 'kll_controller_test')
    kll_dir = os.path.join(tmp_dir, 'kll')

    if not os.path.isdir(tmp_dir):
        # Clone if not available
        Repo.clone_from('https://github.com/kiibohd/controller.git', tmp_dir)
    else:
        # Update otherwise
        repo = Repo(tmp_dir)
        repo.remotes.origin.pull()

    # Check for kll compiler as well (not used during testing, but required for controller tests)
    if not os.path.isdir(kll_dir):
        # Clone if not available
        Repo.clone_from('https://github.com/kiibohd/kll.git', kll_dir)
    else:
        # Update otherwise
        repo_kll = Repo(kll_dir)
        repo_kll.remotes.origin.pull()

    return tmp_dir

