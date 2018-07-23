'''
Test typical usage of kll compiler
Similar to what the kiibohd firmware uses to compile .kll files
'''

### Imports ##

import os
import pytest
import tempfile
from tests.klltest import kll_run, header_test, kiibohd_controller_repo



### Tests ###

def test_kiibohd_simple(kiibohd_controller_repo):
    '''
    Runs a simple kiibohd test
    '''
    # Prepare tmp directory
    tmp_dir = os.path.join(tempfile.gettempdir(), 'kll_pytest')
    os.makedirs(tmp_dir, exist_ok=True)
    target_dir = tempfile.mkdtemp(suffix='-simple', prefix='kiibohd-', dir=tmp_dir)

    # Controller git repo
    controller = kiibohd_controller_repo

    # Run test
    args = [
        '--config',
        os.path.join(controller, 'Scan/Devices/MatrixARM/capabilities.kll'),
        os.path.join(controller, 'Macro/PartialMap/capabilities.kll'),
        os.path.join(controller, 'Output/USB/capabilities.kll'),
        '--base',
        os.path.join(controller, 'Scan/Infinity_60/scancode_map.kll'),
        'kll/examples/nonetest.kll',
        '--default',
        'kll/layouts/stdFuncMap.kll',
        '--emitter', 'kiibohd',
        '--def-output', os.path.join(target_dir, 'kll_defs.h'),
        '--map-output', os.path.join(target_dir, 'generatedKeymap.h'),
        '--hid-output', os.path.join(target_dir, 'usb_hid.h'),
        '--pixel-output', os.path.join(target_dir, 'generatedPixelmap.c'),
        '--json-output', os.path.join(target_dir, 'kll.json'),
    ]
    header_test('{}'.format(target_dir), args)
    ret = kll_run(args)
    assert ret == 0

def test_kiibohd_func1(kiibohd_controller_repo):
    '''
    Multiple Function1 test (WhiteFox)
    '''
    # Prepare tmp directory
    tmp_dir = os.path.join(tempfile.gettempdir(), 'kll_pytest')
    os.makedirs(tmp_dir, exist_ok=True)
    target_dir = tempfile.mkdtemp(suffix='-func1', prefix='kiibohd-', dir=tmp_dir)

    # Controller git repo
    controller = kiibohd_controller_repo

    # Run test
    args = [
        '--config',
        os.path.join(controller, 'Scan/Devices/ISSILed/capabilities.kll'),
        os.path.join(controller, 'Scan/Devices/MatrixARM/capabilities.kll'),
        os.path.join(controller, 'Macro/PartialMap/capabilities.kll'),
        os.path.join(controller, 'Macro/PixelMap/capabilities.kll'),
        os.path.join(controller, 'Output/HID-IO/capabilities.kll'),
        os.path.join(controller, 'Output/USB/capabilities.kll'),
        '--base',
        os.path.join(controller, 'Scan/WhiteFox/scancode_map.kll'),
        os.path.join(controller, 'Scan/WhiteFox/scancode_map.truefox.kll'),
        '--default',
        'kll/layouts/tab_function.kll',
        'kll/layouts/stdFuncMap.kll',
        '--partial',
        'kll/layouts/whitefox/whitefox.kll',
        'kll/layouts/stdFuncMap.kll',
        '--emitter', 'kiibohd',
        '--def-output', os.path.join(target_dir, 'kll_defs.h'),
        '--map-output', os.path.join(target_dir, 'generatedKeymap.h'),
        '--hid-output', os.path.join(target_dir, 'usb_hid.h'),
        '--pixel-output', os.path.join(target_dir, 'generatedPixelmap.c'),
        '--json-output', os.path.join(target_dir, 'kll.json'),
    ]
    header_test('{}'.format(target_dir), args)
    ret = kll_run(args)
    assert ret == 0

def test_kiibohd_add(kiibohd_controller_repo):
    '''
    Add test (K-Type)
    '''
    # Prepare tmp directory
    tmp_dir = os.path.join(tempfile.gettempdir(), 'kll_pytest')
    os.makedirs(tmp_dir, exist_ok=True)
    target_dir = tempfile.mkdtemp(suffix='-add', prefix='kiibohd-', dir=tmp_dir)

    # Controller git repo
    controller = kiibohd_controller_repo

    # Run test
    args = [
        '--config',
        os.path.join(controller, 'Scan/Devices/ISSILed/capabilities.kll'),
        os.path.join(controller, 'Scan/Devices/MatrixARM/capabilities.kll'),
        os.path.join(controller, 'Scan/Devices/PortSwap/capabilities.kll'),
        os.path.join(controller, 'Scan/Devices/UARTConnect/capabilities.kll'),
        os.path.join(controller, 'Macro/PartialMap/capabilities.kll'),
        os.path.join(controller, 'Macro/PixelMap/capabilities.kll'),
        os.path.join(controller, 'Output/HID-IO/capabilities.kll'),
        os.path.join(controller, 'Output/USB/capabilities.kll'),
        '--base',
        os.path.join(controller, 'Scan/K-Type/scancode_map.kll'),
        os.path.join(controller, 'Scan/WhiteFox/scancode_map.truefox.kll'),
        '--default',
        'kll/layouts/animation_test.kll',
        'kll/layouts/stdFuncMap.kll',
        '--partial',
        'kll/layouts/k-type/unset_v1.kll',
        'kll/layouts/k-type/rainbow_wipe.kll',
        '--partial',
        'kll/layouts/k-type/unset_v1.kll',
        'kll/layouts/k-type/color_painter.kll',
        '--emitter', 'kiibohd',
        '--def-output', os.path.join(target_dir, 'kll_defs.h'),
        '--map-output', os.path.join(target_dir, 'generatedKeymap.h'),
        '--hid-output', os.path.join(target_dir, 'usb_hid.h'),
        '--pixel-output', os.path.join(target_dir, 'generatedPixelmap.c'),
        '--json-output', os.path.join(target_dir, 'kll.json'),
    ]
    header_test('{}'.format(target_dir), args)
    ret = kll_run(args)
    assert ret == 0

def test_kiibohd_interconnect(kiibohd_controller_repo):
    '''
    Interconnect test (Infinity Ergodox)
    '''
    # Prepare tmp directory
    tmp_dir = os.path.join(tempfile.gettempdir(), 'kll_pytest')
    os.makedirs(tmp_dir, exist_ok=True)
    target_dir = tempfile.mkdtemp(suffix='-interconnect', prefix='kiibohd-', dir=tmp_dir)

    # Controller git repo
    controller = kiibohd_controller_repo

    # Run test
    args = [
        '--config',
        os.path.join(controller, 'Scan/Devices/ISSILed/capabilities.kll'),
        os.path.join(controller, 'Scan/Devices/MatrixARM/capabilities.kll'),
        os.path.join(controller, 'Scan/Devices/STLcd/capabilities.kll'),
        os.path.join(controller, 'Scan/Devices/UARTConnect/capabilities.kll'),
        os.path.join(controller, 'Macro/PartialMap/capabilities.kll'),
        os.path.join(controller, 'Macro/PixelMap/capabilities.kll'),
        os.path.join(controller, 'Output/HID-IO/capabilities.kll'),
        os.path.join(controller, 'Output/USB/capabilities.kll'),
        '--base',
        os.path.join(controller, 'Scan/Infinity_Ergodox/scancode_map.kll'),
        os.path.join(controller, 'Scan/Infinity_Ergodox/leftHand.kll'),
        os.path.join(controller, 'Scan/Infinity_Ergodox/slave1.kll'),
        os.path.join(controller, 'Scan/Infinity_Ergodox/rightHand.kll'),
        'kll/examples/nonetest.kll',
        '--default',
        'kll/layouts/infinity_ergodox/mdergo1Overlay.kll',
        'kll/layouts/infinity_ergodox/lcdFuncMap.kll',
        '--partial',
        'kll/layouts/infinity_ergodox/iced_func.kll',
        'kll/layouts/infinity_ergodox/mdergo1Overlay.kll',
        'kll/layouts/infinity_ergodox/lcdFuncMap.kll',
        '--partial',
        'kll/layouts/infinity_ergodox/iced_numpad.kll',
        '--emitter', 'kiibohd',
        '--def-output', os.path.join(target_dir, 'kll_defs.h'),
        '--map-output', os.path.join(target_dir, 'generatedKeymap.h'),
        '--hid-output', os.path.join(target_dir, 'usb_hid.h'),
        '--pixel-output', os.path.join(target_dir, 'generatedPixelmap.c'),
        '--json-output', os.path.join(target_dir, 'kll.json'),
    ]
    header_test('{}'.format(target_dir), args)
    ret = kll_run(args)
    assert ret == 0

def test_kiibohd_klltest1(kiibohd_controller_repo):
    '''
    Kiibohd test using klltest.kll
    '''
    # Prepare tmp directory
    tmp_dir = os.path.join(tempfile.gettempdir(), 'kll_pytest')
    os.makedirs(tmp_dir, exist_ok=True)
    target_dir = tempfile.mkdtemp(suffix='-klltest1', prefix='kiibohd-', dir=tmp_dir)

    # Controller git repo
    controller = kiibohd_controller_repo

    # Run test
    args = [
        '--config',
        os.path.join(controller, 'Scan/Devices/MatrixARM/capabilities.kll'),
        os.path.join(controller, 'Macro/PartialMap/capabilities.kll'),
        os.path.join(controller, 'Output/USB/capabilities.kll'),
        '--base',
        os.path.join(controller, 'Scan/Infinity_60/scancode_map.kll'),
        '--default',
        'kll/layouts/klltest.kll',
        '--emitter', 'kll',
        '--target-dir', os.path.join(target_dir, 'kll.json'),
    ]
    header_test('{}'.format(target_dir), args)
    ret = kll_run(args)
    assert ret == 0

def test_kiibohd_klltest2(kiibohd_controller_repo):
    '''
    Kiibohd test using klltest.kll
    '''
    # Prepare tmp directory
    tmp_dir = os.path.join(tempfile.gettempdir(), 'kll_pytest')
    os.makedirs(tmp_dir, exist_ok=True)
    target_dir = tempfile.mkdtemp(suffix='-klltest2', prefix='kiibohd-', dir=tmp_dir)

    # Controller git repo
    controller = kiibohd_controller_repo

    # Run test
    args = [
        '--config',
        os.path.join(controller, 'Scan/Devices/MatrixARM/capabilities.kll'),
        os.path.join(controller, 'Macro/PartialMap/capabilities.kll'),
        os.path.join(controller, 'Output/USB/capabilities.kll'),
        '--base',
        os.path.join(controller, 'Scan/Infinity_60/scancode_map.kll'),
        '--default',
        'kll/layouts/klltest.kll',
        '--emitter', 'kiibohd',
        '--def-output', os.path.join(target_dir, 'kll_defs.h'),
        '--map-output', os.path.join(target_dir, 'generatedKeymap.h'),
        '--hid-output', os.path.join(target_dir, 'usb_hid.h'),
        '--pixel-output', os.path.join(target_dir, 'generatedPixelmap.c'),
        '--json-output', os.path.join(target_dir, 'kll.json'),
    ]
    header_test('{}'.format(target_dir), args)
    ret = kll_run(args)
    assert ret == 0

