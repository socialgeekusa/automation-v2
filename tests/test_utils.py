import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import utils


def test_detect_device_os_iphone_by_name():
    device = {"id": "123", "name": "My iPhone"}
    assert utils.detect_device_os(device) == "iPhone"


def test_detect_device_os_iphone_by_id():
    device = {"id": "a" * 40, "name": "Device"}
    assert utils.detect_device_os(device) == "iPhone"


def test_detect_device_os_numeric_android():
    device = {"id": "1" * 25, "name": "Android"}
    assert utils.detect_device_os(device) == "Android"


def test_detect_device_os_default_android():
    device = {"id": "abcd1234", "name": "Pixel"}
    assert utils.detect_device_os(device) == "Android"
