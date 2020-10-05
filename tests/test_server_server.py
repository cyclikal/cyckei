import sys
import os
import pytest
from cyckei.server import server, protocols
from tests import mock_source, mock_device
from PySide2.QtCore import QThreadPool
import zmq
from visa import VisaIOError

@pytest.fixture()
def basic_cellrunner():
        # meta arguments for CellRunner with meta arguments
    test_meta = {
        "channel": "test channel",
        "path": "tests/test_path/test_output.txt",
        "cellid": "test id",
        "comment": "Testing comments",
        "package": "Test package",
        "celltype": "Test type",
        "requester": "Test protocol name",
        "plugins": {"testing" : "plugins", "second" : "test"},
        "protocol": "Test protocol",
        "protocol_name": "Test protocol name",
        "cycler": "Test cycler",
        "start_cycle": 0,
        "format": ["Test format"]
    }
    test_runner = protocols.CellRunner({"testing" : "plugins", "second" : "test"}, **test_meta)
    test_mock_device = mock_device.MockDevice()
    test_runner.channel = 'a'
    test_runner.set_source(test_mock_device.get_source(None))
    return test_runner

def test_info_all_channels(basic_cellrunner):
    test_device = mock_device.MockDevice(1000)
    basic_cellrunner.channel = 'a'
    basic_cellrunner.set_source(test_device.get_source(None))
    basic_cellrunner.meta['plugins'] = {}
    basic_cellrunner.load_protocol("from cyckei.server import protocols\nprotocols.CurrentStep(20)")
    basic_cellrunner.run()
    test_info = server.info_all_channels([basic_cellrunner], [basic_cellrunner.source])
    assert test_info != None
    channel_a = test_info['a']
    assert channel_a["channel"] == 'a'
    assert channel_a["status"] == 'started'
    assert channel_a["state"] == 'charge_constant_current'
    assert channel_a["current"] == 20
    assert channel_a["voltage"] == 42.780956028973016
    

def test_info_channel(basic_cellrunner):
    test_device = mock_device.MockDevice(1000)
    basic_cellrunner.channel = 'a'
    basic_cellrunner.set_source(test_device.get_source(None))
    basic_cellrunner.meta['plugins'] = {}
    basic_cellrunner.load_protocol("from cyckei.server import protocols\nprotocols.CurrentStep(20)")
    basic_cellrunner.run()
    test_dict = server.info_channel('a', [basic_cellrunner], [basic_cellrunner.source])
    assert test_dict["channel"] == 'a'
    assert test_dict["status"] == 'started'
    assert test_dict["state"] == 'charge_constant_current'
    assert test_dict["current"] == 20
    assert test_dict["voltage"] == 42.780956028973016

def test_start(basic_cellrunner):
    test_meta = {
        "channel": "test channel",
        "path": "tests/test_path/test_output.txt",
        "cellid": "test id",
        "comment": "Testing comments",
        "package": "Test package",
        "celltype": "Test type",
        "requester": "Test protocol name",
        "plugins": {},
        "protocol": "Test protocol",
        "protocol_name": "Test protocol name",
        "cycler": "Test cycler",
        "start_cycle": 0,
        "format": ["Test format"]
    }
    test_protocol = "from cyckei.server import protocols\nprotocols.CurrentStep(20)"
    assert server.start('a', test_meta, test_protocol, [], [basic_cellrunner.source], []) == "Log file 'test_output.txt' already in use."
    test_meta = {
        "channel": "test channel",
        "path": "tests/test_path/server_test_output.txt",
        "cellid": "test id",
        "comment": "Testing comments",
        "package": "Test package",
        "celltype": "Test type",
        "requester": "Test protocol name",
        "plugins": {},
        "protocol": "Test protocol",
        "protocol_name": "Test protocol name",
        "cycler": "Test cycler",
        "start_cycle": 0,
        "format": ["Test format"]
    }
    assert server.start('a', test_meta, test_protocol, [], [basic_cellrunner.source], []) == "Succeeded in starting channel a."
    assert server.start('a', test_meta, test_protocol, [basic_cellrunner], [basic_cellrunner.source], []) == "Channel a already in use."

def test_pause(basic_cellrunner):
    assert server.pause('a', []) == "Failed in pausing channel a"
    test_device = mock_device.MockDevice(1000)
    basic_cellrunner.channel = 'a'
    basic_cellrunner.set_source(test_device.get_source(None))
    basic_cellrunner.meta['plugins'] = {}
    basic_cellrunner.load_protocol("from cyckei.server import protocols\nprotocols.CurrentStep(20)")
    basic_cellrunner.run()
    assert server.pause('a', [basic_cellrunner]) == "Succeeded in pausing channel a"

def test_stop(basic_cellrunner):
    assert server.stop('a', []) == "Failed in stopping channel a"
    test_device = mock_device.MockDevice(1000)
    basic_cellrunner.channel = 'a'
    basic_cellrunner.set_source(test_device.get_source(None))
    basic_cellrunner.meta['plugins'] = {}
    basic_cellrunner.load_protocol("from cyckei.server import protocols\nprotocols.CurrentStep(20)")
    basic_cellrunner.run()
    assert server.stop('a', [basic_cellrunner]) == "Succeeded in stopping channel a"

def test_resume(basic_cellrunner):
    assert server.resume('a', [basic_cellrunner]) == "Failed in resuming channel a"
    test_device = mock_device.MockDevice(1000)
    basic_cellrunner.channel = 'a'
    basic_cellrunner.set_source(test_device.get_source(None))
    basic_cellrunner.meta['plugins'] = {}
    basic_cellrunner.load_protocol("from cyckei.server import protocols\nprotocols.CurrentStep(20)")
    basic_cellrunner.run()
    basic_cellrunner.pause()
    assert server.resume('a', [basic_cellrunner]) == "Succeeded in resuming channel a"

def test_test():
    assert server.test("ProtocolStep(10.0)") == "Passed"

def test_get_runner_by_channel(basic_cellrunner):
    assert server.get_runner_by_channel("", []) == None
    assert server.get_runner_by_channel("a", [basic_cellrunner]) == basic_cellrunner
    assert server.get_runner_by_channel("a", [basic_cellrunner], 0) == basic_cellrunner
    assert server.get_runner_by_channel("a", [basic_cellrunner], 1) == None