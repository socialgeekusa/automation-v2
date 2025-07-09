import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import utils


def test_detect_device_os_prefix_Z_is_iphone():
    device = {"id": "Z12345", "name": "Phone"}
    assert utils.detect_device_os(device) == "iPhone"


def test_detect_device_os_prefix_0_is_android():
    device = {"id": "012345", "name": "Device"}
    assert utils.detect_device_os(device) == "Android"


def test_detect_device_os_default_android():
    device = {"id": "abcd1234", "name": "Pixel"}
    assert utils.detect_device_os(device) == "Android"
