"""Classes to handle interfacing with Keithleys and their channels"""

import logging
import time

import pyvisa as visa

from cyckei.functions import func

logger = logging.getLogger('cyckei_server')

SCRIPT_RUN_TIME_BUFFER = 2  # seconds, extra time for Keithley to load program


def parse_gpib_address(gpib_address):
    """Takes int or str and returns full str GPIB address
    
    Args:
        gpib_address (int or str): Either the int part of the GPIB address or the full
            GPIB address as a str.

    Returns:
        str: The full GPIB address.
    |
    """
    try:
        int(gpib_address)
        full_address = "GPIB0::{}::INSTR".format(gpib_address)
    except ValueError:
        full_address = gpib_address

    return full_address

def with_safety(fn):
    """Wrapper function for the Source class to enforce the use of a safety script
    
    Safety cutoff will shut the keithley off after {safety_reset_seconds}
    if it is not at least checked.

    Args:
        fn (funtion): The function being decorate for safety cutoff.

    Returns:
        Any: The result of the function that is being called through here. Could return anything.
    |
    """
    def decorated(self, *args, **kwargs):
        """Shuts the Keithely off after {safety_reset_seconds} if the Keithley is
        not checked in that time.

        Returns:
            Any: The result of the function that is being called through here. Could return anything.
        |
        """
        self.write('abort')
        self.write('errorqueue.clear()')
        response = fn(self, *args, **kwargs)
        self.write(f'safetycutoff({self.safety_reset_seconds})')
        return response
    return decorated


class DeviceController(object):
    """Represents a single keithley Interface
    
    Attributes:
        gpib_addr (int or str): Either the int part of the GPIB address or the full
            GPIB address as a str.
        safety_reset_seconds (int): How many seconds the Keithley can go without being
            checked before being shut off.
        source_meter (visa GPIBInstrument): The Keithley connected using pyvisa.
    |
    """

    script_startup = open(func.asset_path("startup.lua")).read()
    current_ranges = [100 * 1e-9, 1e-6, 10e-6,
                      100e-6, 1e-3, 0.01,
                      0.1, 1.0, 3.0]

    def __init__(self, gpib_addr, load_scripts=True, safety_reset_seconds=120):
        """Inits Device Controller with gpib_addr, safety_reset_seconds, and
        source_meter. 

        Also resets the source meter and initializes it with either a startup
        scrip or a safety shut off script.

        Args:
            gpib_addr (int or str): Either the int part of the GPIB address or the full
                GPIB address as a str.
            load_scripts (bool, optional): Defaults to True. Whether the source should be
                able to load scripts.
            safety_reset_seconds (int, optional): How many seconds the Keithley can go without being
                checked before being shut off.
        |
        """
        resource_manager = visa.ResourceManager()
        self.gpib_addr = gpib_addr
        self.source_meter = resource_manager.open_resource(
            parse_gpib_address(gpib_addr))
        # TODO do not reset? Do something else, clear buffers I think
        self.source_meter.write("abort")
        self.source_meter.write("reset()")
        if load_scripts:
            logger.info(f'Initializing device at address {gpib_addr}')
            self.source_meter.write(self.script_startup)
            time.sleep(1)
        else:
            # No matter what we need the safety shutoff script
            logger.info(f'Initializing device at address {gpib_addr}')
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
                |
                """
            self.source_meter.write(safety_shutoff_script)
            time.sleep(1)

        self.safety_reset_seconds = safety_reset_seconds

    def get_source(self, kch, channel=None):
        """Creates a source object of a Keithley with the specified kch channel.

        Args:
            kch (str): 'a' or 'b', used to set whether a or b on the keithley is used.
            channel (str, optional): User specified name of the channel. Defaults to None
        
        Returns:
            Source: Initialized with source_meter, kch, channl, and safety_reset_seconds.
        |
        """
        return Source(self.source_meter, kch, channel=channel,
                      safety_reset_seconds=self.safety_reset_seconds)


class Source(object):
    """Represents an individual source.
    
    Typically generated from a Keithley object's get_source function

    Attributes:
        channel (str): Channel name that the user sees. Will be used to sort and 
            display channels. Defaults to None.
        chd (dict): Holds the connection between kch and snum, {"a":1, "b":2}.
        data (list): The backlog of data being stored; holds timestamp, current, and voltage.
        data_max_len (int): Defaults to 500. The legnth of the backlog of data being stored.
        identification (str): Either 'smua' or 'smub', corresponds with whether the kch is 'a' or 'b'.
        kch (str):  Keithley channel ("a" or "b"). Stored lower case internally
            and accessible in the kch attribute.
        report (list): List of points from data list added whenever a condition is met.
        safety_reset_seconds (int): How many seconds the Keithley can go without being
            checked before being shut off.
        source_meter (visa GPIBInstrument): The Keithley source, btained from an open_resource pyvisa call.
        snum (int): Either 1 or 2, corresponds with whether the kch is 'a' or 'b'.
    |
    """
    
    current_ranges = [100 * 1e-9, 1e-6, 10e-6,
                      100e-6, 1e-3, 0.01,
                      0.1, 1.0, 3.0]

    def __init__(self, source_meter, kch, channel=None,
                 safety_reset_seconds=120):
        """Constructs necessary parameters for a Source object.

        Args:
            channel (int or str): Channel that the user sees. Can be integer or string,
                however will be used to sort and display channels. Defaults to None.
            kch (str): Keithley channel ("a" or "b"). Stored lower case internally and accessible in the kch attribute.
            source_meter (visa GPIBInstrument): The Keithley source, btained from an open_resource pyvisa call.            
        |
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
        """Stops the protocol on the Keithley and sets the Keithley to off-mode.
        
        |
        """
        self.write('abort')
        self.write(f"smu{self.kch}.source.offmode \
                   = smu{self.kch}.OUTPUT_HIGH_Z")
        self.write(f"smu{self.kch}.source.output = smu{self.kch}.OUTPUT_OFF")

    def get_range(self, current):
        """Compares the current_range to the provided current and returns the
        smallest number in the range still larger than the provided current.

        Args:
            current (int): Current to compare to the current_range

        Returns:
            int: The smallest current in the current_range still larger than the
                provided current.
        |
        """
        return min([c for c in self.current_ranges if c > abs(current)])

    @with_safety
    def set_current(self, current, v_limit):
        """Set the current on the Source.

        Args:
            current (float): Desired current in Amps.
            v_limit (float): Voltage limit for source. This is not a voltage cutoff condition.
                It is the maximum voltage allowed by the Keithley under any
                condition. The Keithley enforces +/- v_limit.
                Having a battery with a voltage outside of +/- v_limit could
                damage the Keithley.
        |
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
        """Sets the source (Keithley) current to 0. 

        Args:
            v_limit (float, optional): Voltage limit for source. This is not a voltage cutoff condition.
                It is the maximum voltage allowed by the Keithley under any
                condition. The Keithley enforces +/- v_limit.
                Having a battery with a voltage outside of +/- v_limit could
                damage the Keithley. Defaults to 5.0.
        |
        """
        self.set_current(0.0, v_limit)

    def _run_script(self, script, scriptname):
        """Takes a script and a script name and attempts to load them onto the Keithley source.

        Args:
            script (str): The script being sent to the Keithley.
            scriptname (str): The name of the script being sent to the Keithley.

        Returns:
            str: The Keithley's response string to having instructions written to it.
        |
        """
        instruction = \
            f"""
            loadscript {scriptname}()
            {script}
            endscript
            {scriptname}()
            """
        return self.source_meter.write(instruction)

    def pause(self):
        """Attempts to pause the Keithley script by writing abort to the Keithley
        and changing the output.
        
        |
        """
        self.write('abort')
        self.write(
            "smu{ch}.source.output = smu{ch}.OUTPUT_OFF".format(ch=self.kch)
        )

    def set_text(self, text1: str = "", text2: str = ""):
        """Sets the display test on the Keithley screen

        Unfortunately the Keithley does not treat the two channels
        independently for display purposes. So setting the text for one
        channels removes all the info for the other channel rendering this
        functionality nearly useless.

        Args:
            text1 (str): top line of text, 10 max chars
            text2 (str): bottom line of text, 16 max chars
        |
        """
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
        """Writes and sends a script to the Keithley using the _run_script() function.

        Args:
            i_limit (float): The maximum allowed current.
            voltage (float): The voltage level to set the Keithley to.
        |
        """
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
        """Reads the voltage and current from the Keithley.

        Writes a message to the Keithley source and reads the response
        from the source. Also parses the responses received to make numbers
        more meaningful.

        Returns:
            (float, float): Returns the (current, voltage) as a tuple.
        |
        """
        self.source_meter.write(
            "current, voltage = smu{}.measure.iv()".format(self.kch)
        )
        current = float(self.source_meter.query("print(current)"))
        voltage = float(self.source_meter.query("print(voltage)"))

        logger.debug(f'Current: {current}, Voltage: {voltage}')
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
        """Reads the current and voltage from the source and adds it to the data list.
        
        |
        """
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
        """Records data from a Keithley at regular intervals until an end condition is met.

        Args:
            end_conditions (list): A list of Conditions from protocols.py to be checked
                against to end the process.
            wait_time (int, optional): Time in seconds between checks. Defaults to 5.
            write_conditions (list): A list of Conditions from protocols.py to be checked
                against determining whether to write data.
        |
        """
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
        """Makes a call to write the included arguments to the Keithley source.
        
        |
        """
        self.source_meter.write(*args, **kwargs)

    def query(self, *args, **kwargs):
        """Makes a call to query the Keithley source.
        
        |
        """
        self.source_meter.query(*args, **kwargs)
