import unittest
import visa
import logging
import sys
import json
import time

script_write_i = """
display.screen = display.SMUA_SMUB
display.smu{ab}.measure.func = display.MEASURE_DCVOLTS
smu{ab}.source.func = smu{ab}.OUTPUT_DCAMPS
smu{ab}.source.autorangei = smu{ab}.AUTORANGE_ON
smu{ab}.source.leveli = {current}
smu{ab}.source.limitv = {v_limit}
smu{ab}.source.output = smu{ab}.OUTPUT_ON
smu{ab}.measure.v()
"""


class TestKeithleyConnection(unittest.TestCase):
    def setUp(self):
        self.rm = visa.ResourceManager()
        resources = self.rm.list_resources()

        with open("tests/test_config.json") as file:
            self.config = json.load(file)

        self.addresses = []
        for dev_raw in resources:
            dev_info = dev_raw.split('::')
            if dev_info[0] == 'GPIB0':
                self.addresses.append(dev_info[1])

        self.sources = []
        for gpib_addr in self.addresses:
            self.sources.append(
                self.rm.open_resource('GPIB0::{}::INSTR'.format(gpib_addr))
            )

    def test_1_available_resources(self):
        error_text = 'No GPIB Devices Found!'
        if self.addresses:
            logging.info("GPIB Addresse(s): {}".format(self.addresses))
        self.assertTrue(self.addresses, error_text)

    def test_2_set_text(self):
        error_text = 'Could not write or read display text!'
        write_text = self.config["set_text"]["text"]
        logging.info('Set text to "{}".'.format(write_text))

        for source in self.sources:
            source.write('reset()')
            source.write('display.clear()')
            source.write('display.settext("{}")'.format(write_text))
            read_text = source.query('print(display.gettext())')

            self.assertTrue(write_text in read_text, error_text)

    def test_3_read_v(self):
        error_text = 'Voltage not in acceptable range!'
        validate = self.config["read_v"]["validate"]
        min_v = self.config["read_v"]["min"]
        max_v = self.config["read_v"]["max"]

        if not validate:
            logging.warning("Will not validate voltage.")

        for address, source in zip(self.addresses, self.sources):
            with open("assets/startup.lua") as file:
                script = file.read()
            source.write("reset()")
            source.write(script)

            source.write("smua.source.output = smua.OUTPUT_ON")
            source.write("smub.source.output = smub.OUTPUT_ON")

            source.write("voltage = smua.measure.v()")
            voltage = float(source.query("print(voltage)"))
            logging.info("{}A: {}V".format(address, voltage))

            if validate:
                self.assertTrue(min_v < voltage < max_v, error_text)

            source.write("voltage = smub.measure.v()")
            voltage = float(source.query("print(voltage)"))
            logging.info("{}B: {}V".format(address, voltage))

            source.write("smua.source.output = smua.OUTPUT_OFF")
            source.write("smub.source.output = smub.OUTPUT_OFF")

            if validate:
                self.assertTrue(min_v < voltage < max_v, error_text)

    def test_4_charge(self):
        duration = self.config["charge"]["duration"]
        current = self.config["charge"]["current"]
        v_limit = self.config["charge"]["voltage_limit"]

        if duration != 0:
            logging.warning(
                "Applying {}A to each cell for {} minutes.".format(current,
                                                                   duration)
            )
            for source in self.sources:
                source.write(script_write_i.format(ab="a", current=current,
                                                   v_limit=v_limit))
                source.write(script_write_i.format(ab="b", current=current,
                                                   v_limit=v_limit))

            end_time = duration * 60 + time.time()
            while time.time() < end_time:
                for address, source in zip(self.addresses, self.sources):
                    source.write("voltage = smua.measure.v()")

            for source in self.sources:
                source.write("smua.source.output = smua.OUTPUT_OFF")
                source.write("smub.source.output = smub.OUTPUT_OFF")

        else:
            logging.warning("Will not charge cells.")


logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format="%(message)s")
unittest.main()
