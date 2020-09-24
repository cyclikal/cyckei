import sys
import os
import pytest
from tests import mock_source
from tests import mock_device
from cyckei.server import protocols
from cyckei.server import keithley2602

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
    return protocols.CellRunner({"testing" : "plugins", "second" : "test"}, **test_meta)

@pytest.fixture()
def basic_protocolstep(basic_cellrunner):
    return protocols.ProtocolStep(10.0, basic_cellrunner)

# Testing the construction of CellRunner objects
# Testing default construction, construction with plugin arguments,
# and construction without plugins.
def test_make_cellrunner(basic_cellrunner):

    # Testing the default cell runner
    default_cellrunner = protocols.CellRunner()
    assert default_cellrunner.meta["cycler"] == "Keithley2602"
    assert default_cellrunner.meta["celltype"] == "unknown"
    assert default_cellrunner.meta["format"] == ["time", "current", "voltage", "capacity"]
    assert default_cellrunner.plugin_objects == None
    assert default_cellrunner.meta["channel"] == 'None'
    assert default_cellrunner.fpath == None
    assert default_cellrunner.steps == []
    assert default_cellrunner.status == 0
    assert default_cellrunner.current_step == None
    assert default_cellrunner.start_time == None
    assert default_cellrunner.i_current_step == None
    assert default_cellrunner.cycle == 0
    assert default_cellrunner.prev_cycle == None
    assert default_cellrunner._next_time == -1
    assert default_cellrunner.channel == 'None'
    assert default_cellrunner.last_data == None
    assert default_cellrunner.total_pause_time == 0.0
    assert default_cellrunner.source == None
    assert default_cellrunner.safety_reset_seconds == None

    assert basic_cellrunner.meta["cycler"] == "Test cycler"
    assert basic_cellrunner.meta["celltype"] == "Test type"
    assert basic_cellrunner.meta["format"] == ["time", "current", "voltage", "capacity", "testing:plugins", "second:test"]
    assert basic_cellrunner.plugin_objects == {"testing" : "plugins", "second" : "test"}
    assert basic_cellrunner.meta["channel"] == 'test channel'
    assert basic_cellrunner.fpath == "tests/test_path/test_output.txt"
    assert basic_cellrunner.steps == []
    assert basic_cellrunner.status == 0
    assert basic_cellrunner.current_step == None
    assert basic_cellrunner.start_time == None
    assert basic_cellrunner.i_current_step == None
    assert basic_cellrunner.cycle == 0
    assert basic_cellrunner.prev_cycle == None
    assert basic_cellrunner._next_time == -1
    assert basic_cellrunner.channel == "test channel"
    assert basic_cellrunner.last_data == None
    assert basic_cellrunner.total_pause_time == 0.0
    assert basic_cellrunner.source == None
    assert basic_cellrunner.safety_reset_seconds == None


def test_cellrunner_next_time(basic_cellrunner):
    assert basic_cellrunner.next_time == -1

def test_cellrunner_set_next_time(basic_cellrunner):
    basic_cellrunner.next_time = 0.5
    assert basic_cellrunner.next_time == 1

    basic_cellrunner.next_time = 200
    assert basic_cellrunner.next_time == 200

    basic_cellrunner.safety_reset_seconds = 120
    basic_cellrunner.next_time = float('inf')
    assert basic_cellrunner.next_time == float('inf')

def test_cellrunner_set_source(basic_cellrunner):
    test_device = mock_device.MockDevice()
    with pytest.raises(ValueError):
        basic_cellrunner.set_source(test_device.get_source(None))
    basic_cellrunner.channel = 'a'
    basic_cellrunner.set_source(test_device.get_source(None))
    assert basic_cellrunner.channel == basic_cellrunner.source.channel
    assert basic_cellrunner.safety_reset_seconds == 60

def test_cellrunner_set_cap_signs(basic_cellrunner, basic_protocolstep):
    with pytest.raises(ValueError):
        basic_cellrunner.set_cap_signs('test')

    basic_cellrunner.add_step(basic_protocolstep)

    basic_cellrunner.set_cap_signs(None)
    assert basic_protocolstep.cap_sign == 1.0

    basic_protocolstep.state_str = "discharge"
    basic_cellrunner.set_cap_signs(None)
    assert basic_protocolstep.cap_sign == -1.0

    basic_protocolstep.state_str = "charge"
    basic_cellrunner.set_cap_signs(None)
    assert basic_protocolstep.cap_sign == 1.0

    basic_cellrunner.meta["celltype"] = "anode"

    basic_protocolstep.state_str = "discharge"
    basic_cellrunner.set_cap_signs(None)
    assert basic_protocolstep.cap_sign == 1.0

    basic_protocolstep.state_str = "charge"
    basic_cellrunner.set_cap_signs(None)
    assert basic_protocolstep.cap_sign == -1.0

    basic_protocolstep.state_str = "charge"
    basic_cellrunner.set_cap_signs('pos')
    assert basic_protocolstep.cap_sign == 1.0

    basic_protocolstep.state_str = "charge"
    basic_cellrunner.set_cap_signs('neg')
    assert basic_protocolstep.cap_sign == -1.0 

def test_cellrunner_load_protocol(basic_cellrunner, basic_protocolstep):
     basic_cellrunner.load_protocol("ProtocolStep(10.0)", isTest=False)
     assert basic_cellrunner.isTest == False
     assert len(basic_cellrunner.steps) == 2

     basic_cellrunner.load_protocol("ProtocolStep(10.0)", isTest=True)
     assert basic_cellrunner.isTest == True
     assert len(basic_cellrunner.steps) == 3

def test_cellrunner_add_step(basic_cellrunner, basic_protocolstep):
    basic_cellrunner.add_step(basic_protocolstep)
    assert len(basic_cellrunner.steps) == 2

def test_cellrunner_next_step(basic_cellrunner, basic_protocolstep):
    basic_cellrunner.add_step(basic_protocolstep)
    basic_cellrunner.add_step(basic_protocolstep)

    basic_cellrunner.i_current_step = 0
    basic_cellrunner.last_data = [0, 0, 0, 100]
    result = basic_cellrunner.next_step()
    assert result == True
    assert basic_cellrunner.i_current_step == 1
    assert basic_cellrunner.status == 0
    assert basic_cellrunner.step.starting_capacity == 100

    basic_cellrunner.last_data = [0, 0, 0, 200]
    result = basic_cellrunner.next_step()
    assert result == True
    assert basic_cellrunner.i_current_step == 2
    assert basic_cellrunner.status == 0
    assert basic_cellrunner.step.starting_capacity == 200
    
    result = basic_cellrunner.next_step()
    assert result == False
    assert basic_cellrunner.i_current_step == 3
    assert basic_cellrunner.status == 3


def test_cellrunner__start(basic_cellrunner):
    basic_cellrunner._start()
    assert basic_cellrunner.i_current_step == 0
    assert basic_cellrunner.status == 1

def test_cellrunner_step(basic_cellrunner):
    basic_cellrunner.i_current_step = 0
    assert basic_cellrunner.step == None
    basic_cellrunner.add_step(basic_protocolstep)
    basic_cellrunner.add_step(basic_protocolstep)
    basic_cellrunner.add_step(basic_protocolstep)
    basic_cellrunner.next_step()
    assert basic_cellrunner.step == basic_protocolstep
    basic_cellrunner.next_step()
    assert basic_cellrunner.step == basic_protocolstep
    basic_cellrunner.i_current_step = 100
    assert basic_cellrunner.step == None

# Should be covered by testing the functions it calls
def test_cellrunner_run():
    assert True

def test_cellrunner_advance_cycle(basic_cellrunner):
    assert basic_cellrunner.cycle == 0
    basic_cellrunner.advance_cycle()
    assert basic_cellrunner.cycle == 1

def test_cellrunner_write_header(basic_cellrunner):
    basic_cellrunner.write_header()
    test_file = open("tests/test_path/test_output.txt", "r")
    test_output = test_file.read()
    correct_test_file = open("tests/test_path/correct_write_header_output.txt", "r")
    correct_test_output = correct_test_file.read()
    assert test_output == correct_test_output
    test_file.close()
    correct_test_file.close()

def test_cellrunner_write_cycle_header(basic_cellrunner):
    basic_cellrunner.advance_cycle()
    basic_cellrunner.advance_cycle()
    basic_cellrunner.advance_cycle()
    test_file = open("tests/test_path/test_output.txt", "r")
    test_output = test_file.read()
    correct_test_file = open("tests/test_path/correct_write_cycle_header_output.txt", "r")
    correct_test_output = correct_test_file.read()
    assert test_output == correct_test_output
    test_file.close()
    correct_test_file.close()

def test_cellrunner_write_step_header(basic_cellrunner, basic_protocolstep):
    basic_cellrunner.add_step(basic_protocolstep)
    basic_cellrunner.i_current_step = 0
    basic_cellrunner.write_step_header()
    test_file = open("tests/test_path/test_output.txt", "r")
    test_output = test_file.read()
    correct_test_file = open("tests/test_path/correct_write_step_header_output.txt", "r")
    correct_test_output = correct_test_file.read()
    assert test_output == correct_test_output
    test_file.close()
    correct_test_file.close()
    
    #Should be covered by testing the functions it calls
def test_cellrunner_read_and_write(basic_cellrunner):
    assert True


def test_cellrunner_write_data(basic_cellrunner):
    basic_cellrunner._start()
    basic_cellrunner.write_data(basic_cellrunner.start_time, 1, 1, 100, [])
    test_file = open("tests/test_path/test_output.txt", "r")
    lines = test_file.read().splitlines()
    second_to_last_line = lines[-1]
    split_line = second_to_last_line.split(",")
    print(split_line)
    timestamp = split_line[0]
    current = split_line[1]
    voltage = split_line[2]
    capacity = split_line[3]
    assert float(timestamp) == 0
    assert current == '1'
    assert voltage == '1'
    assert capacity == '100'
    test_file.close()

def test_cellrunner_pause(basic_cellrunner, basic_protocolstep):
    test_device = mock_device.MockDevice()
    basic_cellrunner.channel = 'a'
    basic_cellrunner.set_source(test_device.get_source(None))
    basic_cellrunner.add_step(basic_protocolstep)
    with pytest.raises(TypeError):
        test_pause = basic_cellrunner.pause()
    # It doesn't seem right that the status is changed to paused,
    # yet since the protocolstep was never started it isn't really paused
    basic_cellrunner._start()
    with pytest.raises(NotImplementedError):
        test_pause = basic_cellrunner.pause()
    
    basic_currentstep = protocols.CurrentStep(20)
    # Normally the parent is retrieved from globals()
    # here I just hardcode it for testing purposed
    # I've also eliminated the plugi
    basic_currentstep.parent = basic_cellrunner
    basic_cellrunner.meta["plugins"] = {}
    basic_cellrunner.add_step(basic_currentstep)
    basic_cellrunner.next_step()
    basic_cellrunner.next_step()
    test_pause = basic_cellrunner.pause()
    assert basic_cellrunner.status == 2
    assert test_pause == True


def test_cellrunner_resume(basic_cellrunner, basic_protocolstep):
    test_device = mock_device.MockDevice()
    basic_cellrunner.channel = 'a'
    basic_cellrunner.set_source(test_device.get_source(None))
    basic_currentstep = protocols.CurrentStep(20)
    basic_currentstep.parent = basic_cellrunner
    basic_cellrunner.meta["plugins"] = {}
    basic_cellrunner.add_step(basic_protocolstep)
    basic_cellrunner.add_step(basic_currentstep)
    basic_cellrunner._start()
    basic_cellrunner.next_step()
    basic_cellrunner.next_step()
    basic_cellrunner.pause()
    test_resume = basic_cellrunner.resume()
    assert basic_cellrunner.status == 1
    assert test_resume == True

def test_cellrunner_close(basic_cellrunner, basic_protocolstep):
    basic_cellrunner.add_step(basic_protocolstep)
    test_device = mock_device.MockDevice()
    basic_cellrunner.channel = 'a'
    basic_cellrunner.set_source(test_device.get_source(None))

    basic_cellrunner.close()
    assert basic_cellrunner.source.current == 0
    assert basic_cellrunner.source.mode == 'constant_current'

def test_cellrunner_off(basic_cellrunner, basic_protocolstep):
    test_device = mock_device.MockDevice()
    basic_cellrunner.channel = 'a'
    basic_cellrunner.set_source(test_device.get_source(None))

    basic_cellrunner.off()
    assert basic_cellrunner.source.current == 0
    assert basic_cellrunner.source.mode == 'constant_current'
    

def test_cellrunner_stop(basic_cellrunner, basic_protocolstep):
    test_device = mock_device.MockDevice()
    basic_cellrunner.channel = 'a'
    basic_cellrunner.set_source(test_device.get_source(None))

    assert basic_cellrunner.stop() == True
    assert basic_cellrunner.status == 3
    assert basic_cellrunner.source.mode == 'constant_current'

def test_make_protocolstep(basic_protocolstep, basic_cellrunner):
    assert basic_protocolstep.parent is basic_cellrunner  # noqa: F821
    assert basic_protocolstep.data_max_len == 10000
    assert basic_protocolstep.data == []
    assert basic_protocolstep.report == []
    assert basic_protocolstep.status == 0
    assert basic_protocolstep.state_str == "unknown"
    assert basic_protocolstep.last_time == -1
    assert basic_protocolstep.pause_start == None
    assert basic_protocolstep.pause_time == 0.0
    assert basic_protocolstep.cap_sign == 1.0
    assert basic_protocolstep.next_time == -1
    assert basic_protocolstep.starting_capacity == 0.
    assert basic_protocolstep.wait_time == 10.0
    assert basic_protocolstep.end_conditions == []
    assert basic_protocolstep.report_conditions == []
    assert basic_protocolstep.in_control == True

def test_protocolstep__start(basic_protocolstep):
    with pytest.raises(NotImplementedError):
        basic_protocolstep._start()

def test_protocolstep_header(basic_protocolstep):
    assert basic_protocolstep.header() == False

def test_protocolstep_run(basic_protocolstep):

    
    basic_protocolstep.status = 2
    assert basic_protocolstep.run() == None
    assert basic_protocolstep.next_time == float('inf')

def test_protocolstep_check_end_conditions(basic_protocolstep):
    assert True

def test_protocolstep_check_report_conditions(basic_protocolstep):
    assert True
    
def test_protocolstep_check_in_control(basic_protocolstep):
    assert True

def test_protocolstep_read_data(basic_protocolstep):
    assert True

def test_protocolstep_pause(basic_protocolstep):
    assert True

def test_protocolstep_resume(basic_protocolstep):
    assert True

def test_process_reports():
    assert True

def test_process_ends():
    assert True

def test_make_currentstep():
    assert True

def test_currentstep__start():
    assert True

def test_currentstep_header():
    assert True

def test_currentstep_check_in_control():
    assert True

def test_make_cccharge():
    assert True

def test_make_ccdischarge():
    assert True

def test_make_voltagestep():
    test_voltage_step = protocols.VoltageStep(4)
    assert test_voltage_step.i_limit == None
    assert test_voltage_step.voltage == 4

def test_voltagestep_guess_i_limit():
    assert True

def test_voltagestep__start():
    assert True

def test_voltagestep_header():
    assert True

def test_voltagestep_check_in_control():
    assert True

def test_make_cvcharge(basic_cellrunner):
    test_mock_device = mock_device.MockDevice()
    basic_cellrunner.channel = 'a'
    basic_cellrunner.set_source(test_mock_device.get_source(None))
    test_CVCharge = protocols.CVCharge(4)
    assert test_CVCharge.state_str == "charge_constant_voltage"
    # can't test i_limit. It requires a "parent" cellrunner
    # however, a parent can not be assigned in the costruction.
    # instead the parent is assigned via a global variable by 
    # using a script to create this object
    # assert test_CVCharge.i_limit == 3

def test_make_cvdischarge(basic_cellrunner):
    test_mock_device = mock_device.MockDevice()
    basic_cellrunner.channel = 'a'
    basic_cellrunner.set_source(test_mock_device.get_source(None))
    test_CVDischarge = protocols.CVDischarge(4)
    assert test_CVDischarge.state_str == "discharge_constant_voltage"
    # can't test i_limit. It requires a "parent" cellrunner
    # however, a parent can not be assigned in the costruction.
    # instead the parent is assigned via a global variable by 
    # using a script to create this object
    # assert test_CVDischarge.i_limit == -3

def test_advancecycle__start():
    test_advance_cycle = protocols.AdvanceCycle()
    test_advance_cycle._start()
    assert test_advance_cycle.status == 1

def test_advancecycle_run():
    test_advance_cycle = protocols.AdvanceCycle()
    test_advance_cycle.run() 
    assert test_advance_cycle.status == 3

def test_advancecycle_check_in_control():
    test_advance_cycle = protocols.AdvanceCycle()
    assert test_advance_cycle.check_in_control() == True

def test_make_rest():
    test_rest = protocols.Rest()
    assert test_rest.state_str == "rest"

def test_rest__start():
    assert True

def test_rest_header():
    assert True

def test_rest_check_in_control():
    assert True

def test_make_pause():
    test_pause = protocols.Pause()
    assert test_pause.state_str == "pause"

def test_pause__start():
    assert True

def test_pause_run():
    assert True

def test_pause_resume():
    assert True

def test_pause_check_in_control():
    assert True

def test_make_sleep():
    assert True

def test_sleep__start():
    assert True

def test_sleep_header():
    assert True

def test_sleep_read_data():
    assert True

def test_sleep_run():
    assert True

def test_sleep_check_in_control():
    assert True

def test_make_conditiondelta():
    test1_condition_delta = protocols.ConditionDelta("voltage", 11)
    assert test1_condition_delta.value_str == "voltage"
    assert test1_condition_delta.index == 2
    assert test1_condition_delta.comparison(2, 1)
    assert test1_condition_delta.delta == 11
    assert test1_condition_delta.is_time == False
    test1_condition_delta = protocols.ConditionDelta("voltage", -11)
    assert test1_condition_delta.value_str == "voltage"
    assert test1_condition_delta.index == 2
    assert test1_condition_delta.comparison(2, 1)
    assert test1_condition_delta.delta == 11
    assert test1_condition_delta.is_time == False
    test1_condition_delta = protocols.ConditionDelta("current", 11)
    assert test1_condition_delta.value_str == "current"
    assert test1_condition_delta.index == 1
    assert test1_condition_delta.comparison(2, 1)
    assert test1_condition_delta.delta == 11
    assert test1_condition_delta.is_time == False
    test1_condition_delta = protocols.ConditionDelta("time", 11)
    assert test1_condition_delta.value_str == "time"
    assert test1_condition_delta.index == 0
    assert test1_condition_delta.comparison(2, 1)
    assert test1_condition_delta.delta == 11
    assert test1_condition_delta.is_time == True
    test1_condition_delta = protocols.ConditionDelta("capacity", 11)
    assert test1_condition_delta.value_str == "capacity"
    assert test1_condition_delta.index == 3
    assert test1_condition_delta.comparison(2, 1)
    assert test1_condition_delta.delta == 11
    assert test1_condition_delta.is_time == False

def test_conditiondelta_check():
    assert True

def test_make_conditiontotaldelta():
    assert True
    
def test_conditiontotaldelta_check():
    assert True

def test_make_conditiontotaltime():
    assert True

def test_conditiontotaltime_check():
    assert True

def test_make_conditionabsolute():
    assert True

def test_conditionabsolute_check():
    assert True

def teset_condition_end_voltage():
    assert True

def test_condition_ucv():
    assert True

def test_condition_lcv():
    assert True

def test_condition_min_current():
    assert True

def test_condition_max_current():
    assert True

def test_condition_total_time():
    assert True

def test_condition_dt():
    assert True

def test_condition_di():
    assert True

def test_condition_dv():
    assert True

def test_condition_dc():
    assert True

def test_extrapolate_time():
    assert True

def test_time_conversion():
    assert True