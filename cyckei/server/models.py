"""Classes to handle interfacing with Keithleys and their channels"""

import time
import visa

from pkg_resources import resource_filename


def source_from_gpib(gpib_address, channel):
    """Opens GPIB resource and returns as Source object"""
    resource_manager = visa.ResourceManager()
    source_meter = resource_manager.open_resource(
        "GPIB0::{}::INSTR".format(gpib_address)
    )
    return Source(source_meter, channel)


class Keithley2602(object):
    """Represents a single keithley Interface"""

    # TODO something in the startup script screws up CC discharge.
    # It does constant V discharge instead
    script_startup = open(
        resource_filename("cyckei.server", "res/startup.script")).read()

    current_ranges = [100 * 1e-9, 1e-6, 10e-6,
                      100e-6, 1e-3, 0.01,
                      0.1, 1.0, 3.0]

    def __init__(self, gpib_addr, load_scripts=True):
        resource_manager = visa.ResourceManager()
        self.gpib_addr = gpib_addr
        self.source_meter = resource_manager.open_resource(
            "GPIB0::{}::INSTR".format(gpib_addr)
        )
        # TODO do not reset? Do something else, clear buffers I think
        self.source_meter.write("reset()")
        if load_scripts:
            self.source_meter.write(self.script_startup)

    def get_source(self, kch, channel=None):
        """Get source object of Keithley"""
        return Source(self.source_meter, kch, channel=channel)


class Source(object):
    """Represents an individual source"""
    current_ranges = [100 * 1e-9, 1e-6, 10e-6,
                      100e-6, 1e-3, 0.01,
                      0.1, 1.0, 3.0]

    def __init__(self, source_meter, kch, channel=None):
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

    def off(self):
        self.source_meter.write(
            "smu{ch}.source.output = smu{ch}.OUTPUT_OFF".format(ch=self.kch)
        )

    def get_range(self, current):
        return min([c for c in self.current_ranges if c > abs(current)])

    def set_current(self, current, v_limit):

        script = """display.screen = display.SMUA_SMUB
display.smu{ch}.measure.func = display.MEASURE_DCVOLTS
smu{ch}.source.func = smu{ch}.OUTPUT_DCAMPS
smu{ch}.source.autorangei = smu{ch}.AUTORANGE_ON
smu{ch}.source.leveli = {current}
smu{ch}.source.limitv = {v_limit}
smu{ch}.source.output = smu{ch}.OUTPUT_ON""".format(ch=self.kch,
                                                    current=current,
                                                    v_limit=v_limit)
        self._run_script(script, "setcurrent")

    def rest(self, v_limit=5.0):
        self.set_current(0.0, v_limit)

    def _run_script(self, script, scriptname):
        instruction = "loadscript {}()\n{}\nendscript\n{}()".format(
            scriptname, script, scriptname
        )
        return self.source_meter.write(instruction)

    def pause(self):
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

    def read_iv(self):
        self.source_meter.write(
            "current, voltage = smu{}.measure.iv()".format(self.kch)
        )
        current = float(self.source_meter.ask("print(current)"))
        voltage = float(self.source_meter.ask("print(voltage)"))

        # The Keithley will report totally out of range numbers like 9.91e+37
        # if asked to e.g. charge to 3.9V when the cell is already at 4.2V
        # It is basically its way of saying the condition cannot be achieved
        # The actual current sent is 0.0 A.
        if abs(current) > 1.0e10:
            current = 0.0
        return current, voltage

    def read_data(self):
        t = time.time()
        self.source_meter.write(
            "current, voltage = smu{}.measure.iv()".format(self.kch)
        )
        current = float(self.source_meter.ask("print(current)"))
        voltage = float(self.source_meter.ask("print(voltage)"))
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

    def ask(self, *args, **kwargs):
        self.source_meter.ask(*args, **kwargs)
