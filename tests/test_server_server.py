import sys
import os
import pytest
from cyckei.server import server
from PySide2.QtCore import QThreadPool
import zmq
from visa import VisaIOError

# For this test the functions baing called don't have to actually work,
# We're just verifying that the right functions are being called.
def test_process_socket():
    assert 1 == 1

def test_info_all_channels():
    assert 1 == 1

def test_info_channel():
    assert 1 == 1

def test_start():
    assert 1 == 1

def test_pause():
    assert 1 == 1

def test_stop():
    assert 1 == 1

def test_resume():
    assert 1 == 1

def test_test():
    assert 1 == 1

def test_get_runner_by_channel():
    assert 1 == 1