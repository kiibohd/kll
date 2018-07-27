'''
Test building the firmware of each of the Input Club keyboards to make sure changes haven't broken the builds of the controller repo
'''

### Imports ##

import os
import pytest
import subprocess
import tempfile
from tests.klltest import kll_run, header_test, kiibohd_controller_repo



### Variables ###

test_builds = [
    'Keyboards/ergodox.bash',
    'Keyboards/infinity.alphabet.bash',
    'Keyboards/infinity.hacker.bash',
    'Keyboards/infinity.standard.bash',
    'Keyboards/infinity_led.alphabet.bash',
    'Keyboards/infinity_led.hacker.bash',
    'Keyboards/infinity_led.standard.bash',
    'Keyboards/kira.bash',
    'Keyboards/k-type.bash',
    'Keyboards/whitefox.aria.bash',
    'Keyboards/whitefox.iso.bash',
    'Keyboards/whitefox.jackofalltrades.bash',
    'Keyboards/whitefox.truefox.bash',
    'Keyboards/whitefox.vanilla.bash',
    'Keyboards/whitefox.winkeyless.bash',
]



### Tests ###

@pytest.mark.skip(reason="Missing full controller infrastructure...")
@pytest.mark.parametrize('input_build', test_builds)
def test_build(input_build, kiibohd_controller_repo):
    '''
    Runs a kiibohd controller build to test the functionality of the kll compiler
    Uses this version of the kll compiler, not the built-in version of the controller repo
    This does not actually run the C compiler to generate the firmware image (only the kll compiler runs)
    '''
    # Prepare tmp directory
    sanitized_input_build = input_build.replace('/', '-')
    tmp_dir = os.path.join(tempfile.gettempdir(), 'kll_pytest')
    os.makedirs(tmp_dir, exist_ok=True)
    target_dir = tempfile.mkdtemp(suffix='-{}'.format(sanitized_input_build), prefix='controller-', dir=tmp_dir)

    # Determine script path
    script_path = os.path.join(kiibohd_controller_repo, input_build)
    working_dir = os.path.dirname(script_path)

    # Determine KLL executable
    script_dir = os.path.dirname(os.path.realpath(__file__))
    kll_working_directory = os.path.abspath(os.path.join(script_dir, '..'))
    kll_executable = os.path.join(kll_working_directory, 'kll', 'kll')

    # Run test
    # Need to add environment variables, including the system ones so CMake can find CMAKE_ROOT (using PATH variable)
    new_env = {
        'CMakeBuildArgs': '',
        'CMakeExtraArgs': '-DCompilerOverride=host -DKLL_EXECUTABLE={0} -DKLL_WORKING_DIRECTORY={1}'.format(kll_executable, kll_working_directory),
        'CMakeExtraBuildArgs': '-- kll_regen',
        'CMakeListsPath': kiibohd_controller_repo,
        'ExtraBuildPath': '.host_override',
        'ExtraBuildPathPrepend': target_dir,
    }
    env = os.environ.copy()
    env.update(new_env)
    try:
        subprocess.check_call(script_path, env=env, cwd=working_dir)
    except subprocess.CalledProcessError:
        # If an error has occurred, try again with debugging
        env['CMakeExtraBuildArgs'] = '-- kll_token kll_parser kll_debug kll_display',
        subprocess.check_call(script_path, env=env, cwd=working_dir)

