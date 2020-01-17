"""Classes to handle interfacing with Keithleys and their channels"""

import logging
import time

import visa

from cyckei.functions import func

logger = logging.getLogger('cyckei')

SCRIPT_RUN_TIME_BUFFER = 2  # seconds, extra time for Keithley to load program


def source_from_gpib(gpib_address, channel):
    """Opens GPIB resource and returns as Source object"""
    resource_manager = visa.ResourceManager()
    source_meter = resource_manager.open_resource(
        "GPIB0::{}::INSTR".format(gpib_address)
    )
    return Source(source_meter, channel)


# Wrapper function for the Source class to enforce the use of a safety script
# Safety cutoff will shut the keithley off after {safety_reset_seconds}
# if it is not at least checked
def with_safety(fn):
    def decorated(self, *args, **kwargs):
        self.write('abort')
        self.write('errorqueue.clear()')
        response = fn(self, *args, **kwargs)
        self.write(f'safetycutoff({self.safety_reset_seconds})')
        return response
    return decorated


class Keithley2602(object):
    """Represents a single keithley Interface"""
    script_startup = open(func.asset_path("startup.lua")).read()
    current_ranges = [100 * 1e-9, 1e-6, 10e-6,
                      100e-6, 1e-3, 0.01,
                      0.1, 1.0, 3.0]

    def __init__(self, gpib_addr, load_scripts=True, safety_reset_seconds=120):
        resource_manager = visa.ResourceManager()
        self.gpib_addr = gpib_addr
        self.source_meter = resource_manager.open_resource(
            "GPIB0::{}::INSTR".format(gpib_addr)
        )
        # TODO do not reset? Do something else, clear buffers I think
        self.source_meter.write("abort")
        self.source_meter.write("reset()")
        if load_scripts:
            logger.info(f'Initializing Keithley at GPIB {gpib_addr} with \
                        {self.script_startup}')
            self.source_meter.write(self.script_startup)
            time.sleep(1)
        else:
            # No matter what we need the safety shutoff script
            logger.info(f'Initializing Keithley at GPIB {gpib_addr} with \
                        hardcoded safety script')
            safety_shutoff_script = \
                """
                loadscript safety()
                    function safetycutoff(t)
                        delay(t)
                        smua.source.output = smua.OUTPUT_OFF
                        smub.source.output = smub.OUTPUT_OFF
                    end
                endscript
                safety()
                """
            self.source_meter.write(safety_shutoff_script)
            time.sleep(1)

        self.safety_reset_seconds = safety_reset_seconds

    def get_source(self, kch, channel=None):
        """Get source object of Keithley"""
        return Source(self.source_meter, kch, channel=channel,
                      safety_reset_seconds=self.safety_reset_seconds)


class Source(object):
    """Represents an individual source"""
    current_ranges = [100 * 1e-9, 1e-6, 10e-6,
                      100e-6, 1e-3, 0.01,
                      0.1, 1.0, 3.0]

    def __init__(self, source_meter, kch, channel=None,
                 safety_reset_seconds=120):
        """

        Parameters
        ----------
        source_meter: sourcemeter
            Obtained from an open_resource visa call
        kch: str
            Keithley channel ("a" or "b").
            Stored lower case internally and accessible in the kch attribute
        channel: int or str
            Channel that the user sees. Can be integer or string,
            however will be used to sort and display channels
            Defaults to None

        Source is typically gnerated from the
        Keithley object's get_source function
        """
        self.source_meter = source_meter
        # This is the Keithley channel on dual channel Keithleys
        # It can be "a" or "b"
        kch = kch.lower()
        if kch == "a":
            self.snum = 1
            self.identification = "smua"
            self.kch = "a"
        elif kch == "b":
            self.snum = 2
            self.identification = "smub"
            self.kch = "b"
        else:
            raise ValueError("ch argument must be 'a' or 'b'")
        self.chd = {"a": 1, "b": 2}

        # this is the channel that the user sees, it should be a string
        #
        self.channel = str(channel)
        self.data = []  # will hold, timestamp, current, voltage
        self.report = []
        self.data_max_len = 500

        # Show the channel number on the screen
        if self.channel:
            self.set_text(text1="Channel {}".format(self.channel))

        self.safety_reset_seconds = safety_reset_seconds

    def off(self):
        self.write('abort')
        self.write(f"smu{self.kch}.source.offmode \
                   = smu{self.kch}.OUTPUT_HIGH_Z")
        self.write(f"smu{self.kch}.source.output = smu{self.kch}.OUTPUT_OFF")

    def get_range(self, current):
        return min([c for c in self.current_ranges if c > abs(current)])

    @with_safety
    def set_current(self, current, v_limit):
        """
        Set the current on the Source

        Parameters
        ----------
        current: float
            desired current in Amps
        v_limit: float
            voltage limit for source. This is not a voltage cutoff condition.
            It is the maximum voltage allowed by the Keithley under any
            condition. The Keithley enforces +/- v_limit.
            Having a battery with a voltage outside of +/- v_limit could
            damage the Keithley.
        """
        ch = self.kch
        script = f"""display.screen = display.SMUA_SMUB
display.smu{ch}.measure.func = display.MEASURE_DCVOLTS
smu{ch}.source.func = smu{ch}.OUTPUT_DCAMPS
smu{ch}.source.leveli = {current}
smu{ch}.source.sink = smu{ch}.{'ENABLE' if current < 0.0 else 'DISABLE'}
smu{ch}.source.limitv = {v_limit}
smu{ch}.source.output = smu{ch}.OUTPUT_ON"""

        self.source_meter.write(script)
        # self._run_script(script, "setcurrent")

        # If the keithley gets hit with a "read" (and hence an abort)
        # too quickly after trying to load the
        # script it will fail to load it
        time.sleep(SCRIPT_RUN_TIME_BUFFER)

    @with_safety
    def rest(self, v_limit=5.0):
        self.set_current(0.0, v_limit)

    def _run_script(self, script, scriptname):
        instruction = \
            f"""
            loadscript {scriptname}()
            {script}
            endscript
            {scriptname}()
            """
        return self.source_meter.write(instruction)

    def pause(self):
        self.write('abort')
        self.write(
            "smu{ch}.source.output = smu{ch}.OUTPUT_OFF".format(ch=self.kch)
        )

    def set_text(self, text1: str = "", text2: str = ""):
        """
        Unfortunately the Keithley does not treat the two channels
        independently for display purposes. So setting the text for one
        channels removes all the info for the other channel rendering this
        functionality nearly useless.

        Parameters
        ----------
        text1: str
            top line of text, 10 max chars
        text2: str
            bottom line of text, 16 max chars

        Returns
        -------

        """
        ''
        letters = "".join(map(chr, range(65, 91)))
        letters += letters.lower()
        numbers = "".join(map(chr, range(48, 58)))
        others = " :,-_"
        acceptable_chr = letters + numbers + others

        if text1:
            text1 = "".join([c for c in text1 if c in acceptable_chr])[:10]
            startpos = {"a": 1, "b": 11}[self.kch]
            self.write("display.setcursor(1,{})".format(startpos))
            self.write('display.settext("{}")'.format(text1.ljust(10)))

        if text2:
            text2 = "".join([c for c in text2 if c in acceptable_chr])[:16]
            startpos = {"a": 1, "b": 17}[self.kch]
            self.write("display.setcursor(2,{})".format(startpos))
            self.write('display.settext("{}")'.format(text2.ljust(16)))

    @with_safety
    def set_voltage(self, voltage, i_limit):
        script = \
            """display.screen = display.SMUA_SMUB
            display.smu{ch}.measure.func = display.MEASURE_DCAMPS
            smu{ch}.source.func = smu{ch}.OUTPUT_DCVOLTS
            smu{ch}.source.autorangei = smu{ch}.AUTORANGE_ON
            smu{ch}.source.levelv = {voltage}
            smu{ch}.source.limiti = {current}
            smu{ch}.source.output = smu{ch}.OUTPUT_ON
            """.format(ch=self.kch, voltage=voltage, current=i_limit)
        self._run_script(script, "setvoltage")
        time.sleep(SCRIPT_RUN_TIME_BUFFER)

    @with_safety
    def read_iv(self):
        self.source_meter.write(
            "current, voltage = smu{}.measure.iv()".format(self.kch)
        )
        current = float(self.source_meter.query("print(current)"))
        voltage = float(self.source_meter.query("print(voltage)"))

        logger.debug(f'models.Source.read_iv: current:{current}, \
                     voltage:{voltage}')
        # The Keithley will report totally out of range numbers like 9.91e+37
        # if asked to e.g. charge to 3.9V when the cell is already at 4.2V
        # It is basically its way of saying the condition cannot be achieved
        # The actual current sent is 0.0 A.
        if abs(current) > 1.0e10 or abs(current) < 1.0e-8:
            current = 0.0
        if abs(voltage) < 5.0e-4:
            voltage = 0.0
        return current, voltage

    @with_safety
    def read_data(self):
        t = time.time()
        self.source_meter.write(
            "current, voltage = smu{}.measure.iv()".format(self.kch)
        )
        current = float(self.source_meter.query("print(current)"))
        voltage = float(self.source_meter.query("print(voltage)"))
        self.data.append([t, current, voltage])

        if len(self.data) > self.data_max_len:
            # we pop 1 and not 0
            # because if we pop 0 it will screw up the total time checking
            self.data.pop(1)

    def read_until(self, write_conditions, end_conditions, wait_time=5.):
        count = 0
        ctn = True
        while ctn:
            self.read_data()
            print(self.data[-1], end='\n', flush=True)
            next_time = self.data[-1][0] + wait_time
            for condition in end_conditions:
                if condition.check(self.data):
                    ctn = False
                    break
                else:
                    next_time = min(condition.next_time, next_time)

            if ctn:
                for condition in write_conditions:
                    if condition.check(self.data, self.report):
                        self.report.append(self.data[-1])
                        print('\nwriting {}'.format(self.report[-1]),
                              flush=True)
                        break
            else:
                self.report.append(self.data[-1])
                print('\nwriting')
                break

            actual_wait = next_time - time.time()
            print('waiting: {}'.format(actual_wait), end='\n', flush=True)
            if actual_wait > 0:
                time.sleep(actual_wait)
            count += 1

    def write(self, *args, **kwargs):
        self.source_meter.write(*args, **kwargs)

    def query(self, *args, **kwargs):
        self.source_meter.query(*args, **kwargs)
