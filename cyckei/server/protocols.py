"""Classes that handle controlling Keithley Source objects and enacting protocols on them.
"""
import json
import time
from datetime import datetime
import operator
import logging

logger = logging.getLogger('cyckei_server')


DATETIME_FORMAT = '%Y-%m-%d_%H:%M:%S.%f'
NEVER = float('inf')
MIN_WAIT_TIME = 1.0  # Minimum number of seconds between I/V measurements

OPERATOR_MAP = {
    "<": operator.lt,
    "<=": operator.le,
    "=<": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
    "=!": operator.ne,
    ">=": operator.ge,
    "=>": operator.ge,
    ">": operator.gt,
    "lt": operator.lt,
    "le": operator.le,
    "eq": operator.eq,
    "ne": operator.ne,
    "ge": operator.ge,
    "gt": operator.gt}

DATA_INDEX_MAP = {
    "time": 0,
    "current": 1,
    "voltage": 2,
    "capacity": 3
}

DATA_NAME_MAP = {v: k for (k, v) in DATA_INDEX_MAP.items()}


class VariableHolder:
    pass


STATUS = VariableHolder()
STATUS.available = -1
STATUS.pending = 0
STATUS.started = 1
STATUS.paused = 2
STATUS.completed = 3
STATUS.unknown = 4
STATUS.nocontrol = 5
STATUS.string_map = {
    STATUS.pending: "pending",
    STATUS.started: "started",
    STATUS.paused: "paused",
    STATUS.completed: "completed",
    STATUS.unknown: "unknown",
    STATUS.available: "available",
    STATUS.nocontrol: "no control"
}


class CellRunner(object):
    """Turns a protocol into a list of held ProtocolSteps that are executed to complete the protocol. Also 
    holds meta information about the protocol being run.

    Attributes:
        channel (str): The Keithley channel this protocol should be run on. 
        current_step (ProtocolStep): The active ProtocolStep. UNUSED.
        fpath (str): The file path to the file that will have data written to it.
        i_current_step (int): The index of the ProtocolStep being run from the steps list.
        isTest (bool): Controls whether this is a real protocol run or a test protocol being run.
        last_data (list): A list of values from the previous measurement recorded in a ProtocolStep.
        meta (dict): Meta data for: channel, path, cellid, comment, package, celltype, requester, plugins,
            protocol, protocol_name, cycler, start_cycle, and format.
        _next_time (float): The next time at which a ProtocolStep should read data from the Keithley.
        plugin_objects (list): A list of PluginControllers extending the BaseController object. 
            (The same as 'plugins' and 'plugin_objects' in functions of server.py)
        prev_cycle (int): The previous cycle number. UNUSED.
        safety_reset_seconds (float): The number of seconds before the Keithley's safety reset.
        source (keithley2602.Source): The Keithley being controlled by this CellRunner.
        start_time (float): The epoch time in seconds at which the CellRunenr started running the protocol (ProtocolSteps).
        status (int): The status that maps to the STATUS string map. Values -1 to 5.
        steps (list): A list of the ProtocolSteps to be run in order to complete a protocol.
        total_pause_time (float): The time in seconds that a ProtoclStep has been paused for.
    """

    META = {
        "channel": None,
        "path": None,
        "cellid": None,
        "comment": None,
        "package": None,
        "celltype": None,
        "requester": None,
        "plugins": {},
        "protocol": None,
        "protocol_name": None,
        "cycler": None,
        "start_cycle": None,
        "format": None
    }

    def __init__(self, plugin_objects=None, **meta):
        """Inits channel, current_step, fpath, i_current_step, last_data, meta, _next_time, plugin_objects,
        prev_cycle, safety_reset_seconds, source, start_time, status, steps, and total_pause_time.

        Args:
           plugin_objects (list, optional): A list of PluginControllers extending the BaseController object. 
                (The same as 'plugins' and 'plugin_objects' in functions of server.py) Defaults to None.
        """
        self.meta = self.META.copy()
        for k in self.meta.keys():
            self.meta[k] = meta.get(k, None)
        if self.meta["cycler"] is None:
            self.meta["cycler"] = "Keithley2602"
        if self.meta["celltype"] is None:
            self.meta["celltype"] = "unknown"
        self.meta["format"] = ["time", "current", "voltage", "capacity"]

        self.plugin_objects = plugin_objects
        if self.plugin_objects and self.meta["plugins"]:
            for plugin, source in self.meta["plugins"].items():
                if source != "None":
                    self.meta["format"].append(f"{plugin}:{source}")

        # Enforce a str channel
        self.meta["channel"] = str(self.meta["channel"])
        self.fpath = self.meta["path"]
        self.steps = []
        self.status = STATUS.pending
        self.current_step = None
        self.start_time = None
        self.i_current_step = None
        if self.meta["start_cycle"] is not None:
            self.cycle = self.meta["start_cycle"]
        else:
            self.cycle = 0
        self.prev_cycle = None
        self._next_time = -1
        self.channel = self.meta["channel"]
        self.last_data = None
        self.total_pause_time = 0.0
        self.source = None
        self.safety_reset_seconds = None

    @property
    def next_time(self):
        """Returns the next time to read data.

        Returns:
            float: The next time in seconds at which to read data.
        """
        return self._next_time

    @next_time.setter
    def next_time(self, value):
        """Sets the next time to read data.

        The next time to read data is enforced to be at least MIN_WAIT_TIME, but no greater than NEVER (inf).

        Args:
            value (float): The next time in seconds at which to read data.
        """
        # Enforce at least minimum wait time
        value = max(MIN_WAIT_TIME, value)

        # Enforce at most the safety_reset
        if self.safety_reset_seconds and value < NEVER:
            self._next_time = min(time.time()+self.safety_reset_seconds, value)
        else:
            self._next_time = value

    def set_source(self, source):
        """Tries to set the CellRunner's source (the Keithley it controlls) to the passed in source.

        Args:
            source (keithley2602.Source): The Source object used for controlling a specific Keithley.

        Raises:
            ValueError: Error raised when the CellRunner does not have the same channel as the Keithley it is controlling.
        """
        self.source = source
        if self.channel != source.channel:
            raise ValueError(
                "the runner channel ({}) and the source"
                "channel ({}) should be identical".format(
                    self.channel, source.channel
                ))
        self.safety_reset_seconds = source.safety_reset_seconds * 0.5

    def set_cap_signs(self, direction=None):
        """Decides whether charging/discharging yields positive or negative capacities.

        Go through the steps and set their .cap_sign attribute based on the "direction" of the cell.
        Charging yields positive capacities because cap_sign is 1 and discharge yields negative capacities
        because cap_sign is -1.

        Args:
            direction (str or None): Direction for the cell can be "pos", "neg", or None
                if it is None, the "celltype" in the meta data is used, if this is not 
                set it defaults to "pos".
        """
        valid_directions = ["pos", "neg", None]
        if direction not in valid_directions:
            raise ValueError(
                "received unsupported direction argument:"
                "{}, must be one of {}".format(direction, valid_directions)
            )

        if direction is None:
            direction = 'pos'
            if "anode" in self.meta["celltype"].lower():
                direction = 'neg'

        if direction == "pos":
            for step in self.steps:
                if step.state_str.startswith("charge"):
                    step.cap_sign = 1.0
                elif step.state_str.startswith("discharge"):
                    step.cap_sign = -1.0
                else:
                    step.cap_sign = 1.0

        elif direction == "neg":
            for step in self.steps:
                if step.state_str.startswith("charge"):
                    step.cap_sign = -1.0
                elif step.state_str.startswith("discharge"):
                    step.cap_sign = 1.0
                else:
                    step.cap_sign = 1.0

    def load_protocol(self, protocol: str, isTest=False):
        """Executes a string of python code to add a step to the steps list.

        Args:
            protocol (str): string of python code generating the protocol steps in the runner.
        """
        # The protocol is a python string that is executed as code.
        # The CellRunner instance must be present as "parent" in the globals
        # so that the ProtocolSteps can add themselves to the .steps list
        self.isTest = isTest
        exec(protocol, globals().update({"parent": self}))
        # Set the signs for the capacity calculations
        self.set_cap_signs()

    def add_step(self, step):
        """Adds a ProtocolStep to the steps list.

        Args:
            step (ProtocolStep): ProtocolStep to be added to the steps list.
        """
        self.steps.append(step)

    def next_step(self):
        """Attempts to move to the next step of the protocol.

        Attempts to increment the i_current_step by 1 to move to the next step in the steps list. If the length of steps is
        passed then False is returned and status is set to completed to indicate that the prtocol is over. Otherwise, capacity is adjusted
        to the last recorded capactiy and true is returned.

        Returns:
            bool: True indicates that the next step is ready, False is returned if there are no more steps.
        """
        self.i_current_step += 1
        if self.i_current_step >= len(self.steps):
            # reached end of the steps
            self.status = STATUS.completed
            return False

        # Give the last recorded capacity as a starting point to the new step
        if self.last_data is not None:
            self.step.starting_capacity = self.last_data[3]

        # On a new step you want to start as soon as possible on the main loop
        self.next_time = time.time()
        return True

    def _start(self):
        """Initializes the protocol. 
        
        Would not normally be called directly, but instead is called by the
            .run() function. Sets current step to 0, sets the start_time, and writes the initial headers
            with write_header() and write_cycle_header().
        """
        logger.info("Starting cellrunner instance \
                    (channel: {})".format(self.channel))

        self.i_current_step = 0
        self.status = STATUS.started
        self.start_time = time.time()
        self.meta["date_start_timestamp"] = self.start_time
        self.meta["date_start_timestr"] = (
            datetime.fromtimestamp(self.start_time).strftime(DATETIME_FORMAT)
        )
        self.write_header()
        self.write_cycle_header()

    @property
    def step(self):
        """Uses the index of the current step to pull the current step from the steps list.

        Returns:
            ProtocolStep: The current step that the CellRunner is on.
        """
        try:
            return self.steps[self.i_current_step]
        except IndexError:
            return None

    def run(self, force_report=False):
        """Starts and advances protocols.

        Method called by the main loop to start and advance a protocol
        This method triggers the various steps that are loaded in the protocol
        as well as the header writing and the data writing in the data file

        Returns:
            bool: True if is running as expected, False if it is complete.

        """
        logger.debug("Entering method for channel {}".format(self.channel))
        if self.status == STATUS.completed:
            return False

        if self.status == STATUS.nocontrol:
            return False

        if self.status == STATUS.paused:
            return False

        if self.status != STATUS.started:
            self._start()

        if self.step.status != STATUS.started:
            self.write_step_header()

        self.read_and_write(force_report=force_report)

        if self.step.status == STATUS.nocontrol:
            self.close()
            self.status = STATUS.nocontrol

        if self.step.status == STATUS.completed:
            self.next_step()

        if self.status == STATUS.completed:
            self.close()

        return True

    def advance_cycle(self):
        """Advances the cycle stored in CellRunner by 1.
        """
        self.cycle += 1
        self.write_cycle_header()

    def write_header(self):
        """Creates a JSON string using the CellRunner meta and writes it to the file stored in fpath.
        """
        try:
            with open(self.fpath, 'w') as fo:
                header = json.dumps(self.meta, indent=4, sort_keys=True)
                header = "\n".join(
                    ["#{}".format(line) for line in header.split("\n")]
                )
                fo.write(header + "\n")
        except IOError as error:
            logger.error(f"Error opening file in write_header(): {error}")

    def write_cycle_header(self):
        """Writes the cycle that the CellRunner is on to the file stored in fpath.
        """
        try:
            with open(self.fpath, 'a') as fo:
                cycle_header = json.dumps({"cycle": self.cycle}) + "\n"
                fo.write(cycle_header)
        except IOError as error:
            logger.error(f"Error opening file in write_cycle_header(): {error}")

    def write_step_header(self):
        """Collects the header from the current ProtocolStep and writes it to the file stored in fpath.
        """
        header = self.step.header()
        if header:
            try:
                with open(self.fpath, 'a') as fo:
                    fo.write("  " + header + "\n")
            except IOError as error:
                logger.error(f"Error opening file in write_step_header(): {error}")

    def read_and_write(self, force_report=False):
        """Reads data from the current ProtocolStep and records it.

        Calls the current ProtocolStep to collect data and tries to write that data to the data file using write_data().
        Also sets the last_data value to this most recently read data.

        Args:
            force_report (bool, optional): Passed to the ProtocolStep run() function to control reporting. Defaults to False.
        """
        data = self.step.run(force_report=force_report)
        self.next_time = self.step.next_time
        if data:
            self.write_data(*data)
            self.last_data = data

    def write_data(self, timestamp, current, voltage, capacity, plugin):
        """Attempts to write the passed in data to the fpath file.

        Args:
            capacity (float): The calculated capacity of the cell being controlled in mAh.
            current (float): The recorded current data of the controlled cell.
            plugin (list): A list of values recorded from plugins, either ints or floats.
            timestamp (float): The recorded time data of the controlled cell.
            voltage (float): The recorded voltage data of the controlled cell.
        """
        try:
            with open(self.fpath, 'a') as file:
                try:
                    time = timestamp - self.start_time - self.total_pause_times
                except AttributeError:
                    time = timestamp - self.start_time
                data_format = "    " + ",".join(["{:0.8g}"] * 4)
                writeout = data_format.format(time, current, voltage, capacity)
                for value in plugin:
                    writeout += ",{:0.8g}".format(value[1])
                writeout += "\n"

                file.write(writeout)
                logger.debug("Wrote data point to file.")
        except PermissionError as e:
            logger.critical("Permission Error, could not write data: %s", e)
        except IOError as error:
            logger.error(f"Error opening file in write_data(): {error}")

    def pause(self):
        """Attempts to pause the active step. Also calls the read_and_write function.

        Returns:
            bool: True if the pause was successful, otherwise False.
        """
        success = False
        self.read_and_write(force_report=True)
        self.status = STATUS.paused
        if self.step.pause():
            self.next_time = self.step.next_time
            success = True
        return success

    def resume(self):
        """Calls resume on the current step. Then calls the run() function.

        Returns:
            bool: The result of calling the run() function.
        """
        self.status = STATUS.started
        self.step.resume()
        return self.run()

    def close(self):
        """Calls the off() function for the stored source.
        """
        self.source.off()

    def off(self):
        """Calls the off() function for the stored source.
        """
        self.source.off()

    def stop(self):
        """Calls the close() function.

        Returns:
            bool: Always returns True.
        """
        self.status = STATUS.completed
        self.close()
        return True


class ProtocolStep(object):
    """
    Base class for a protocol step, needs to be subclassed with implementation of a start function.

    A protocol step stores its own data and the reported points
    Keeps track of time, current, voltage, capacity. Because the protocol files are simply pure 
    python the parent, which is a CellRunner instance, needs to be present in the global 
    variables as "parent".

    Attributes:
        cap_sign (float): The cap sign determines whether the capacitiy increases or decreases during
            charge and discharge. Either 1 or -1. 
        data (list): A list of lists. Each list is a set of measurements, [[time,current,voltage,capacity],
            [time,current,voltage,capacity], ...] current is stored in absolute value. Contains every measurement taken.
        data_max_len (int): The max number ofitems in the data list.
        end_conditions (list): A list of conditions that determine when the ProtocolStep should be ended.
        in_control (bool): Indicates if the protocol step is operating within it's designed parameters.
        last_time (float): The previous measured time in seconds.
        next_time (float): This is the time in seconds since epoch at which this protocol step is expecting to do another read
            operation on the channel. -1 means it has never been set.
        parent (CellRunner): The CellRunner holding this protocol step.
        pause_start (float): The time in seconds at which the protocol was paused.
        pause_time (float): The total time in seconds for which the protocol was paused.
        report (list): A list of lists. Each list is a set of measurements, [[time,current,voltage,capacity],
            [time,current,voltage,capacity], ...]. This list only contains measurements taken that are 
            specified to be reported.
        report_conditions (list): A list of Condition objects used to determine when a data measurement is reported.
        starting_capacity (float): The initital capacity of the cell. This gets set at the protocol level (parent).
        state_str (str): A string representation of the state of the cell i.e charging, discharging, etc.
        status (int): An int representation of the status of the step, i.e started, paused, etc.
        wait_time (float): Time between data measurements in seconds.
    """

    def __init__(self, wait_time: float = 10.0,
                 cellrunner_parent: CellRunner = None):
        """Inits ProtocolStep with parent, data_max_len, status, state_str, last_time, pause_start, pause_time, cap_sign, next_time,  starting_capacity, 
        wait_time, end_conditions, report_conditions, in_control.

        Base class for protocols the variable "parent" must be a CellRunner
        instance and be present in the globals during instantiation.

        Args:
            cellrunner_parent (CellRunner): The CellRunner this protocol is attached to.
            wait_time (float): Default waiting time in seconds.
                If no other conditions are met, the step will check V & I at this interval.
        """
        # the parent is the CellRunner
        if cellrunner_parent is None:
            self.parent = parent  # noqa: F821)
        else:
            self.parent = cellrunner_parent

        # list of lists [[time,current,voltage,capacity],
        # [time,current,voltage,capacity], ...]
        # one entry for each measurement, current is stored in absolute value
        self.data = []
        self.data_max_len = 10000
        # same format as data but only for the reported points
        self.report = []

        # Status must be one of the values in STATUS module variable
        self.status = STATUS.pending

        # State string, defaults to unknown
        self.state_str = "unknown"

        # Never run before
        self.last_time = -1

        # Need to track time spent in pause state for time-based conditions
        self.pause_start = None
        self.pause_time = 0.0

        # The cap sign determines whether the capacitiy
        # increases or decreases during
        # charge and discharge. The parent (protocol) must set this
        # attribute with .set_cap_sign() since
        # it depends on the cell type and is unknown to the step itself
        self.cap_sign = 1.0

        # this is the time in seconds since epoch at which this protocol
        # step is expecting to do another read
        # operation on the channel. -1 means it has never been set.
        self.next_time = -1

        # This gets set at the protocol level (parent)
        self.starting_capacity = 0.

        # Wait time is defaults wait time between data measurements
        # assumming no other conditions are present
        self.wait_time = wait_time

        # Lists which will hold the conditions for reporting and ending
        self.end_conditions = []
        self.report_conditions = []

        # Boolean indicating if the protocol step is occurring within
        # it's designed parameters
        self.in_control = True

        self.parent.add_step(self)

    def _start(self):
        """Unimplemented function. Meant for being overridden. 

        Raises:
            NotImplementedError: Always raised as this function is meant for being overridden by a child.
        """
        raise NotImplementedError

    def header(self):
        """Unimplemented function. Meant for being overridden. 

        Returns:
            bool: Always returns False.
        """
        return False

    def run(self, force_report=False):
        """Calls the read_data() function, also decides if the read data should be reported.

         Calls the read_data() function and checks the end_conditions for if the ProtocolStep should end.
         The run function evaluates the report_conditions to decide if a data point should be reported, 
         setting force_report to True will report the latest data point regardless of conditions.

        Args:
            force_report (bool): Defaults to False. Forces a report if True.

        Returns:
            tuple: (time, current, voltage, capacity) tuple to report (write to file).
                Returns none if no data to report.
        """
        logger.debug("Running {} protocol on channel {}".format(
            self.state_str, self.parent.channel))
        if self.status == STATUS.paused:
            self.next_time = NEVER
            return None

        if self.status != STATUS.started:
            self._start()

        self.read_data()

        # Set the next read time using the default wait_time
        # this may get modified by the evaluations of conditions
        self.next_time = self.data[-1][0] + self.wait_time

        self.check_end_conditions()

        if self.status == STATUS.completed or self.status == STATUS.nocontrol:
            report_data = True

        else:
            report_data = self.check_report_conditions()

        if report_data or force_report:
            self.report.append(self.data[-1])
            return self.report[-1]
        else:
            return None

    def check_end_conditions(self):
        """Checks if it's time for step to be ended.

        Returns:        
            bool: True if the end condition was satisfied, otherwise False
        """
        for condition in self.end_conditions:
            if condition.check(self):
                self.status = STATUS.completed
                return True
        return False

    def check_report_conditions(self):
        """Check if it's time for step info to be reported.

        Returns:        
            bool: True if the end condition was satisfied, otherwise False
        """
        for condition in self.report_conditions:
            if condition.check(self):
                return True
        return False

    def check_in_control(self, last_time, current, voltage):
        """Abstract Method for checking if the desired condition is actually met.
        
        For example
            - constant current : check current is correct
            - constant voltage: check voltage is correct

        Args:
            current (float): Current in amps. NOTE THAT THIS IS NOT ABSOLUTE CURRENT
                IT IS THE CURRENT DIRECTLY REPORTED FROM THE INSTRUMENT.
            last_time (float): Timestamp of last measurement.
            voltage (float): Voltage in volts.

        Raises:
            NotImplementedError: Raises immediately as this is an Abstract Method.
        """
        raise NotImplementedError("Please Implement this method")

    def read_data(self, force_report=False):
        """Reads and reports data from the Keithley source.

        Reads data from the Keithley source. Next scans the list of plugins checking for active ones. If there are active
        plugins their read() function is called and the output is checked. int and float are acceptable return values from the plugins.
        A 0 will replace non int or non float values. If data has been previously reported that data is used to calculate current capacity,
        otherwise capacity is the starting capacity. The read values of last_time, current, voltage, capacity, plugin_values are then compiled 
        into a list and appended to the data list. If the data list is oversized its second to last oldest value is popped from the list
        (removing the first value would mess up calculating total changes). Finally the data is added to the end of the report if force_report is true.

        Args:
            force_report (bool, optional): If True then the collected data is added to the report list. Defaults to False.
        """
        self.last_time = time.time()
        current, voltage = self.parent.source.read_iv()

        # Get plugin values
        plugin_values = []
        for en_plugin, plugin_source in self.parent.meta["plugins"].items():
            if plugin_source != "None":
                plugin = None
                for available_plugin in self.parent.plugin_objects:
                    if available_plugin.name == en_plugin:
                        plugin = available_plugin
                        break
                if plugin:
                    value = plugin.read(plugin_source)
                    if type(value) not in [int, float]:
                        # raise TypeError(
                        #   f"Plugin {plugin.name} did not return int or float")
                        logger.error(
                            f"Plugin {plugin.name} did not return int or float")
                        value = 0
                    plugin_values.append((plugin.name, value))
                else:
                    value = 0
                    logger.error(f"Failed bind plugin {en_plugin[0]}")
        logger.debug(f"Values from plugins: {plugin_values}")

        self.check_in_control(self.last_time, current, voltage)

        # Currents are reported only in absolute values
        current = abs(current)

        if self.data:
            # Record the capacity in mAh
            capacity = (self.data[-1][3]
                        + (self.last_time - self.data[-1][0])
                        / 3600.
                        * self.cap_sign
                        * (current + self.data[-1][1])
                        / 2.0
                        * 1000.)
        else:
            capacity = self.starting_capacity

        self.data.append([self.last_time, current,
                          voltage, capacity, plugin_values])

        if len(self.data) > self.data_max_len:
            # we pop 1 and not 0
            # because if we pop 0 it will screw up the total time checking
            self.data.pop(1)

        if force_report:
            self.report.append(self.data[-1])

    def pause(self):
        """If step is started turns the source off and sets the status to paused.

        Returns:
            bool: Returns False if the step hasn't been started. Otherwise True.
        """
        if self.status != STATUS.started:
            return False

        self.status = STATUS.paused
        self.pause_start = time.time()
        self.parent.off()
        self.next_time = NEVER
        return True

    def resume(self):
        """Resumes the step by calling _start(), also calculates pause time.

        Returns:
            bool: Returns True if the step hasn't been paused.
        """
        if self.status != STATUS.paused:
            return False
        self.pause_time = time.time() - self.pause_start
        self.parent.total_pause_time += self.pause_time
        self._start()
        # self.status = STATUS.started


def process_reports(reports):
    """Takes reports in the form of a tuple of pairs and creates a list of Condition objects for when to report.

    Args:
        reports (((str, float), (str, int))): Desired reports as a tuple of pairs such as
            (("voltage",0.01), ("time",300))

    Returns:
        list: List of condition objects for reporting a data point

    """
    report_conditions = []
    for k, v in reports:
        if k == "voltage":
            report_conditions.append(condition_dv(v))
        elif k == "time":
            report_conditions.append(condition_dt(time_conversion(v)))
        elif k == "current":
            report_conditions.append(condition_di(v))
        elif k == "capacity":
            report_conditions.append(condition_dc(v))
    return report_conditions


def process_ends(ends):
    """Takes end_conditions in tuple form and converts them into Condition objects.

    Args:
        ends (((str, str, float), (str, str, str))): Desired ends conditions as a tuple of triples such as
            (("voltage",">", 4.2), ("time",">","24::")).

    Returns:
        list: List of Condition objects for ending a protocol step.

    """
    end_conditions = []
    for args in ends:
        if args[0] == "time":
            time_seconds = time_conversion(args[2])
            end_conditions.append(ConditionTotalTime(time_seconds))
        else:
            end_conditions.append(ConditionAbsolute(*args))
    return end_conditions


class CurrentStep(ProtocolStep):
    """Extends ProtocolStep. A step for controlling the current output by the source (i.e Keithley). 

    Attributes:
        current (float): The current rate being enforced.
        v_limit (float): Voltage limit for source. This is not a voltage cutoff condition.
                It is the maximum voltage allowed by the Keithley under any
                condition. The Keithley enforces +/- v_limit.
                Having a battery with a voltage outside of +/- v_limit could
                damage the Keithley. Defaults to 5.0.

    """
    def __init__(self, current,
                 reports=(("voltage", 0.01), ("time", ":5:")),
                 ends=(("voltage", ">", 4.2), ("time", ">", "24::")),
                 wait_time=10.0):
        """Inits current, end_conditions, report_conditions, state_str, and v_limit. Calls parent ProtocolStep constructor with wait_time.

        Args:
            current (float): The current rate being enforced.
            ends (tuple, optional): A tuple of tuples, holds the voltage cutoff and the total time the protocol should run for in hours:minutes:seconds format. 
                Defaults to (("voltage", ">", 4.2), ("time", ">", "24::")).
            reports (tuple, optional): A tuple of tuples, holds the change in voltage or time for a report to occur, time in in hours:minutes:seconds format.
                Defaults to (("voltage", 0.01), ("time", ":5:")).
            wait_time (float, optional): Time between data measurements in seconds. Defaults to 10.0.

        Raises:
            ValueError: Current should not be 0 during a CurrentStep, this is raised if current is 0.
        """
        super().__init__(wait_time=wait_time)
        if current > 0:
            self.state_str = "charge_constant_current"
            sign = 1
        elif current < 0:
            self.state_str = "discharge_constant_current"
            sign = -1
        else:
            raise ValueError("current argument should be non-zero")
        self.current = current

        self.v_limit = 5.0
        # The concept of v_limit for the Keithley only applies for charge
        # Here we give ourselves a 0.1 V margin
        if current > 0:
            for e in ends:
                if e[0] == "voltage":
                    self.v_limit = min(e[2] + 0.1, self.v_limit)

        self.report_conditions = process_reports(reports)
        self.end_conditions = process_ends(ends)

    def _start(self):
        """Starts the protocol by setting the current rate on the CellRunner-parent's Keithley source.
        """
        self.status = STATUS.started
        self.parent.source.set_current(current=self.current,
                                       v_limit=self.v_limit)

    def header(self):
        """Returns the current state and time in json form.

        Returns:
            JSON: A JSON string of the current protocol state and time.
        """
        return json.dumps({"state": self.state_str,
                           "date_start_timestr": datetime.now().strftime(
                               DATETIME_FORMAT)}
                          )

    def check_in_control(self, last_time, current, voltage):
        """Method for checking if the desired condition is actually met.

        Returning False will completely kill the cell.

        Args:
            current (float): The current rate being enforced.
            last_time (float): The measured time in seconds. UNUSED
            voltage (float): The measured voltage to be compared against this step's set voltage. UNUSED

        Returns:       
            bool: True if cell is in control, False otherwise
        """
        if self.data:
            self.in_control = abs((current-self.current)/self.current) < 0.95

        if not self.in_control:
            self.status = STATUS.nocontrol

        return self.in_control


class CCCharge(CurrentStep):
    """Extends CurrentStep. A step for enforcing a positive current.
    """
    def __init__(self, current,
                 reports=(("voltage", 0.01), ("time", ":5:")),
                 ends=(("voltage", ">", 4.2), ("time", ">", "24::")),
                 wait_time=10.0):
        """Inits state_str, calls the parent CurrentStep constructor with current, ends, reports, and wait_time.

        Args:
            current (float): The current charge rate being enforced.
            ends (tuple, optional): A tuple of tuples, holds the voltage cutoff and the total time the protocol should run for in hours:minutes:seconds format. 
                Defaults to (("voltage", "<", 3), ("time", ">", "24::")).
            reports (tuple, optional): A tuple of tuples, holds the change in voltage or time for a report to occur, time in in hours:minutes:seconds format.
                Defaults to (("voltage", 0.01), ("time", ":5:")).
            wait_time (float, optional): Time between data measurements in seconds. Defaults to 10.0.
        """
        # Enforce positive current
        current = abs(current)
        super().__init__(current,
                         reports=reports, ends=ends,
                         wait_time=wait_time)
        self.state_str = "charge_constant_current"


class CCDischarge(CurrentStep):
    """Extends CurrentStep. A step for enforcing a negative current.
    """
    def __init__(self, current,
                 reports=(("voltage", 0.01), ("time", ":5:")),
                 ends=(("voltage", "<", 3), ("time", ">", "24::")),
                 wait_time=10.0):
        """Inits state_str, calls the parent CurrentStep constructor with current, ends, reports, and wait_time.

        Args:
            current (float): The current discharge rate being enforced.
            ends (tuple, optional): A tuple of tuples, holds the voltage cutoff and the total time the protocol should run for in hours:minutes:seconds format. 
                Defaults to (("voltage", "<", 3), ("time", ">", "24::")).
            reports (tuple, optional): A tuple of tuples, holds the change in voltage or time for a report to occur, time in in hours:minutes:seconds format.
                Defaults to (("voltage", 0.01), ("time", ":5:")).
            wait_time (float, optional): Time between data measurements in seconds. Defaults to 10.0.
        """
        # Enforce negative current
        current = -abs(current)
        super().__init__(current,
                         reports=reports, ends=ends,
                         wait_time=wait_time)
        self.state_str = "discharge_constant_current"


class VoltageStep(ProtocolStep):
    """Extends ProtocolStep. A step for controlling the voltage of a cell.

    Attributes:
        i_limit (float): The maximum allowed current when charging or discharing.
        voltage (float): The desired voltage for the cell to reach.
    """
    def __init__(self, voltage,
                 reports=(("current", 0.01), ("time", ":5:")),
                 ends=(("current", "<", 0.001), ("time", ">", "24::")),
                 wait_time=10.0):
        """Inits i_limit, end_conditions, report_conditions, and voltage.

        Args:
            ends (tuple, optional): A tuple of tuples, holds the current cutoff and the total time the protocol should run for in hours:minutes:seconds format. 
                Defaults to (("current", "<", 0.001), ("time", ">", "24::")).
            reports (tuple, optional): A tuple of tuples, holds the change in current or time for a report to occur, time in in hours:minutes:seconds format.
                Defaults to (("current", 0.01), ("time", ":5:")).
            voltage (float): The desired voltage for the cell to reach.
            wait_time (float, optional): Time between data measurements in seconds. Defaults to 10.0.
        """
        super().__init__(wait_time=wait_time)
        self.i_limit = None
        self.voltage = voltage
        self.report_conditions = process_reports(reports)
        self.end_conditions = process_ends(ends)

    def guess_i_limit(self):
        """Takes the last value in the CellRunner Parent's Keithley's current_ranges and sets it positive
        or negative depending on charge or discharge.
        """
        self.i_limit = 1.0
        if self.state_str.startswith("charge"):
            print(self.parent.source.current_ranges[-1])
            self.i_limit = self.parent.source.current_ranges[-1]
        elif self.state_str.startswith("discharge"):
            self.i_limit = -self.parent.source.current_ranges[-1]

    def _start(self):
        """Sets the step's status to started, if an i_limit has been set the Parent CellRunner's Keithley voltage is set.

        Raises:
            ValueError: If no i_limit has been set the cell should not be charged or discharged, hence an error being raised.
        """
        self.status = STATUS.started
        if self.i_limit is None:
            raise ValueError(
                "the i_limit must be set, try using the guess_i_limit method"
            )

        self.parent.source.set_voltage(voltage=self.voltage,
                                       i_limit=self.i_limit)

    def header(self):
        """Returns the current state and time in json form.

        Returns:
            JSON: A JSON string of the current protocol state and time.
        """
        return json.dumps({"state": self.state_str,
                           "date_start_timestr": datetime.now().strftime(
                               DATETIME_FORMAT)}
                          )

    def check_in_control(self, last_time, current, voltage):
        """Method for checking if the desired condition is actually met.
        
        Voltage can take a moment to stabalize when a cell is first started, so the tolerance is adjusted accordingly. Otherwise,
        The currently measured voltage is compared against the voltage set in this step and if it is too different the in_control value
        is set to False. in_control is then returned. Returning False will completely kill the cell.

        Args:
            current (float): The measured current. UNUSED.
            last_time (float): The measured time in seconds.
            voltage (float): The measured voltage to be compared against this step's set voltage.

        Returns:
            bool: True if cell is in control, False otherwise
        """
        if self.data:
            # Give some leeway if the protocol has just been started
            tolerance = 0.1
            dt = last_time - self.data[0][0]
            if dt > 5:
                tolerance = 0.01

            # This one is a little loose as V can take a few steps to stabilize
            self.in_control = abs((voltage-self.voltage)) < tolerance

        if not self.in_control:
            self.status = STATUS.nocontrol

        return self.in_control


class CVCharge(VoltageStep):
    """Extends VoltageStep. A step for charging at a constant voltage.
    """
    def __init__(self, voltage,
                 reports=(("current", 0.01), ("time", ":5:")),
                 ends=(("current", "<", 0.001), ("time", ">", "24::")),
                 wait_time=10.0):
        """[summary]

        Args:
            ends (tuple, optional): A tuple of tuples, holds the current cutoff and the total time the protocol should run for in hours:minutes:seconds format. 
                Defaults to (("current", "<", 0.001), ("time", ">", "24::")).
            reports (tuple, optional): A tuple of tuples, holds the change in current or time for a report to occur, time in in hours:minutes:seconds format.
                Defaults to (("current", 0.01), ("time", ":5:")).
            voltage (float): The desired voltage for the cell to reach.
            wait_time (float, optional): Time between data measurements in seconds. Defaults to 10.0.
        """
        super().__init__(voltage,
                         reports=reports, ends=ends,
                         wait_time=wait_time)
        self.state_str = "charge_constant_voltage"
        if parent.isTest:  # noqa: F821
            pass
        else:
            self.guess_i_limit()


class CVDischarge(VoltageStep):
    """Extends VoltageStep. A step for discharging at a constant voltage.
    """
    def __init__(self, voltage,
                 reports=(("current", 0.01), ("time", ":5:")),
                 ends=(("current", "<", 0.001), ("time", ">", "24::")),
                 wait_time=10.0):
        """Inits state_str, calls Parent Class' constructor with voltage, reports, ends, and wait_time.

        Args:
            ends (tuple, optional): A tuple of tuples, holds the current cutoff and the total time the protocol should run for in hours:minutes:seconds format. 
                Defaults to (("current", "<", 0.001), ("time", ">", "24::")).
            reports (tuple, optional): A tuple of tuples, holds the change in current or time for a report to occur, time in in hours:minutes:seconds format.
                Defaults to (("current", 0.01), ("time", ":5:")).
            voltage (float): The desired voltage for the cell to reach.
            wait_time (float, optional): Time between data measurements in seconds. Defaults to 10.0.
        """
        super().__init__(voltage,
                         reports=reports, ends=ends,
                         wait_time=wait_time)
        self.state_str = "discharge_constant_voltage"
        if parent.isTest:  # noqa: F821
            pass
        else:
            self.guess_i_limit()


class AdvanceCycle(ProtocolStep):
    """Extends ProtocolStep. A step for advancing the cycle number in the parent CellRunner.
    """
    def _start(self):
        """Sets own status to started.
        """
        self.status = STATUS.started

    def run(self, force_report=False):
        """Calls the parent CellRunner's advance_cycle() function.

        Args:
            force_report (bool, optional): Forces a printed report if True.
                Unused in this case. Defaults to False.
        """
        self._start()
        self.parent.advance_cycle()
        self.status = STATUS.completed

    def check_in_control(self, *args):
        """Normally checks that battery is in control.

        Since AdvanceCycle doesn't affect the connected cell True is always returned.

        Returns:
            bool: Always returns True.
        """
        return True


class Rest(ProtocolStep):
    """Extends ProtocolStep. A step for putting a the CellRunner and Keithley to rest.
    """
    def __init__(self,
                 reports=(("time", ":5:"),), ends=(("time", ">", "24::"),),
                 wait_time=10.0):
        """Inits end_conditions, report_conditions, and state_str.

        Args:
            ends (tuple, optional): The total time the protocol should run for in hours:minutes:seconds format. Defaults to (("time", ">", "24::"),).
            reports (tuple, optional): The time betweem reports in hours:minutes:seconds format. Defaults to (("time", ":5:"),).
            wait_time (float, optional): Time between data measurements in seconds. Defaults to 10.0.
        """
        super().__init__(wait_time=wait_time)

        self.state_str = "rest"
        self.report_conditions = process_reports(reports)
        self.end_conditions = process_ends(ends)

    def _start(self):
        """Sets the step status to started and calls the CellRunner Parent's Keithley to rest.
        """
        self.status = STATUS.started
        self.parent.source.rest()

    def header(self):
        """Returns the current state and time in json form.

        Returns:
            JSON: A JSON string of the current protocol state and time.
        """
        return json.dumps({"state": self.state_str,
                           "date_start_timestr": datetime.now().strftime(
                               DATETIME_FORMAT)}
                          )

    def check_in_control(self, last_time, current, voltage):
        """Method for checking if the desired condition is actually met.
        
        Compares the given current to 0.00001 to check if it is essentially 0. Sets in_control, the return value,
        to True if the current is essentially 0. Returning False will completely kill the cell.

        Args:
            current (float): The measured current to compare to 0.00001.
            last_time (float): The last measurement time, UNUSED.
            voltage (float): The measured voltage of the cell, UNUSED.

        Returns:
            bool: True if cell is in control, False otherwise.
        """
        self.in_control = abs(current) < 0.00001

        if not self.in_control:
            self.status = STATUS.nocontrol

        return self.in_control


class Pause(ProtocolStep):
    """Extends ProtocolStep. Pauses the CellRunner and its Keithley source.
    """
    def __init__(self):
        """Inits state_str and invokes the parent's constructor with infinite wait time.
        """
        # This is the time between measurements on the channel,
        # putting this arbitrarily large
        super().__init__(wait_time=NEVER)
        self.state_str = "pause"

    def _start(self):
        """Sets the Pause step's state to started, the next time to infinite seconds away, and calls pause on the CellRunner Parent's Keithley.
        """
        self.state = STATUS.started
        self.next_time = time.time() + self.wait_time
        self.parent.source.pause()

    def run(self):
        """Calls the Pause start() function.

        Returns:
            None: None returned.
        """
        self._start()
        return None

    def resume(self):
        """Sets the Pause step's status to completed in order to move on from being paused.
        """
        self.status = STATUS.completed

    def check_in_control(self, *args):
        """When a everything is paused in_control means nothing, hence this function does nothing but return True.

        Returns:
            bool: Always returns True
        """
        return True


class Sleep(ProtocolStep):
    """Extends ProtocolStep. A protocol used for putting the CellRunner and Keithley to sleep.
    """
    def __init__(self,
                 reports=(("time", ":5:"),), ends=(("time", ">", "24::"),),
                 wait_time=10.0):
        """Inits end_conditions, report_conditions, and state_str.

        Args:
            ends (tuple, optional): The total time the protocol should run for in hours:minutes:seconds format. Defaults to (("time", ">", "24::"),).
            reports (tuple, optional): The time betweem reports in hours:minutes:seconds format. Defaults to (("time", ":5:"),).
            wait_time (float, optional): Time between data measurements in seconds. Defaults to 10.0.
        """
        super().__init__(wait_time=wait_time)

        self.state_str = "sleep"
        self.report_conditions = process_reports(reports)
        self.end_conditions = process_ends(ends)

    def _start(self):
        """Sets the protocol status to started and then sets the CellRunner Parent's source to off.
        """
        self.status = STATUS.started
        self.parent.source.off()

    def header(self):
        """Returns the current state and time in json form.

        Returns:
            JSON: A JSON string of the current protocol state and time.
        """
        return json.dumps({"state": self.state_str,
                           "date_start_timestr": datetime.now().strftime(
                               DATETIME_FORMAT)}
                          )

    def read_data(self):
        """Reads the data from the Keithley source by calling the parent class' read_data().
        """
        self.parent.source.rest()
        super().read_data()
        self.parent.source.off()

    def run(self, force_report=False):
        """Calls the start function of the sleep protocol, checks end conditions, and reports data.

        The run method needs to be redefined because the logic of the Sleep
        protocol is unique in that a measurement is only desired if a report condition is met as opposed to
        the other steps which measure and then decide whether to report

        Args:
            force_report (bool): Defaults to False. The run function evaluates the
                report_conditions to decide if a data point should be
                reported, setting force_report to True will report the
                latest data point regardless of conditions.


        Returns:
            tuple: (time, current, voltage, capacity) tuple to report (write to file).
                Returns none if no data to report.

        """

        if self.status == STATUS.paused:
            self.next_time = NEVER
            return None

        report_data = False
        if self.status != STATUS.started:
            self._start()
            report_data = True
        self.next_time = time.time() + self.wait_time

        self.check_end_conditions()

        if self.status == STATUS.completed:
            report_data = True
        else:
            report_data = report_data or self.check_report_conditions()

        if report_data or force_report:
            self.read_data()
            self.report.append(self.data[-1])
            return self.report[-1]
        else:
            return None

    def check_in_control(self, last_time, current, voltage):
        """Method for checking if the desired condition is actually met.
        
        Returning False will completely kill the cell

        Args:
            current ():
            last_time ():
            voltage ():

        Returns:    
            bool: True if cell is in control, False otherwise
        """
        self.in_control = abs(current) < 0.00001

        if not self.in_control:
            self.status = STATUS.nocontrol

        return self.in_control


class Condition(object):
    """A Condition is an abstract class. A Condition takes a ProtocolStep into its check() method,
    and returns a boolean indicating whether that condition has been met.

    A condition object may modify the .next_time attribute of
    the ProtocolStep object to suggest time the
    next time as an absolute timestamp that the condition should be checked
    """

    def check(self, protocol_step: ProtocolStep):
        """Abstract Function that checks whether certain conditions are met and 
        returns a bool.

        Args:
            protocol_step (ProtocolStep): The step being checked on whether it has met
                 the condition.

        Raises:
            NotImplementedError: Raises this by default since check is an Abstract Method.
        """
        raise NotImplementedError


class ConditionDelta(Condition):
    """Condition that checks change between latest reported value and latest measured value.

    Attributes:
        comparison (func): An operator function that performs comparisons, in this case it is greater than or equal to, since the comparison is change in value.
        delta (float): Delta to compare step data against.
        index (int): The integer that maps to a constant data map referencing data type being compared.
        is_time (bool): True means that this condition compares time values. False means it does not.
        value_str (str): Value string such as "voltage", "time", "current" etc... See DATA_INDEX_MAP module variable for valid values.
    """
    def __init__(self, value_str: str, delta: float):
        """Inits with comparison, delta, index, and is_time, and value_str.
        
        Args:
            value_str (str): Value string such as "voltage", "time", "current" etc... See DATA_INDEX_MAP module variable for valid values.
            delta (float): Delta to compare step data against.
        """
        self.value_str = value_str
        self.index = DATA_INDEX_MAP[value_str]
        self.comparison = OPERATOR_MAP[">="]
        self.delta = abs(delta)
        self.is_time = value_str == "time"

    def check(self, step):
        """Checks the provided step's value against the delta value.

        Takes the most recent list of readings from the data list in step and indexes into the matching value to compare against delta.

        Args:
            step (ProtocolStep): The step to have data pulled from its data list.

        Returns:        
            bool: True if the end condition was satisfied, otherwise False
        """
        try:
            if len(step.report) == 0:
                step.next_time = time.time()
                return True
            else:
                if self.is_time:
                    val = time.time()
                    delta = (abs(val - step.report[-1][self.index])
                             - step.pause_time)
                    next_time = self.delta - delta + val
                    step.next_time = min(next_time, step.next_time)
                else:
                    val = step.data[-1][self.index]
                    if step.state_str.lower().startswith('discharge') \
                            and self.value_str == 'voltage':
                        target_value = val - self.delta
                    else:
                        target_value = val + self.delta

                    next_time = extrapolate_time(step.data,
                                                 target_value,
                                                 self.index)
                    step.next_time = min(next_time, step.next_time)

                logger.debug("Set next_time to {:.2f} (in {:.2f} sec)".format(
                    step.next_time, step.next_time-time.time()
                ))
                print(abs(val - step.report[-1][self.index]))
                print(step.report[-1])
                print()
                if self.comparison(abs(val - step.report[-1][self.index]),
                                   self.delta):
                    return True
                else:
                    return False
        except IndexError:
            return False


class ConditionTotalDelta(Condition):
    """Object for checking the change between the first reported value and latest measured value of a step.

    Attributes:
        comparison (func): An operator function that performs comparisons, in this case it is greater than or equal to, since the comparison is change in value.
        delta (float): Delta to compare step data against.
        index (int): The integer that maps to a constant data map referencing data type being compared.
        next_time (float): At what timestamp do we expect the condition to be met. Defaults as infinite.
        value_str (str): Value string such as "voltage", "time", "current" etc... See DATA_INDEX_MAP module variable for valid values.
    """
    def __init__(self, value_str: str, delta: float):
        """Inits with comparison, delta, index, next_time, and value_str.

        Args:
            value_str (str): Value string such as "voltage", "time", "current" etc... See DATA_INDEX_MAP module variable for valid values.
            delta (float): Delta to compare step data against.
        """
        self.delta = delta
        self.value_str = value_str
        self.index = DATA_INDEX_MAP[value_str]
        self.comparison = OPERATOR_MAP[">="]
        # at what timestamp do we expect the condition to be met
        self.next_time = NEVER

    def check(self, step):
        """Checks the provided step's value against the delta value.

        Takes the first list of readings from the data list in step and indexes into the matching value to compare against delta.

        Args:
            step (ProtocolStep): The step to have data pulled from its data list.

        Returns:        
            bool: True if the end condition was satisfied, otherwise False.
        """
        try:
            delta = abs(step.data[-1][self.index] - step.report[0][self.index])
            return self.comparison(delta, self.delta)
        except IndexError:
            return False


class ConditionTotalTime(ConditionTotalDelta):
    """Object for checking the change between the first reported time and latest measured time of a step.

    Extends ConditionTotalDelta and simply calls its parent class' constructor with time as the value_str.
    """
    def __init__(self, delta):
        """Calls the parent class' constructor to make a ConditionTotalDelta with time.

        Args:
            delta (float): Total elapsed time in seconds.
        """

        super().__init__("time", delta)

    def check(self, step):
        """Checks the provided step's value against the delta value.

        Takes the first list of readings from the data list in step and indexes into the matching value to compare against delta.

        Args:
            step (ProtocolStep): The step to have data pulled from its data list.

        Returns:        
            bool: True if the end condition was satisfied, otherwise False.
        """
        try:
            # Previously was using the last step.data to do the check, however,
            # in the case where no measurements are
            # performed prioir to evaluating the condition this does not give
            # the correct result
            # I see no downside to taking the clock time instead
            delta = abs(time.time() - step.report[0][self.index]) \
                - step.pause_time

            if self.comparison(delta, self.delta):
                return True
            else:
                next_time = self.delta - delta + time.time()
                step.next_time = min(step.next_time, next_time)
                logger.debug("{}, set next_time to {}".format(
                    self.value_str,
                    step.next_time))
                return False
        except IndexError:
            return False


class ConditionAbsolute(Condition):
    """An object for comparing the most recent measurement of a ProtocolStep to a user designated value.

    Attributes:
        comparison (func): The comparison func to use when comparing values i.e. greater than, less than, etc.
        index (int): The index that relates to the value string in the data lists from Steps.
        min_time (float): Minimum time that must have elapsed before evaluating the condition.
        next_time (float): The next expected time for data to be checked. NEVER USED. Defaults to infinity.
        value (float): Actual value to compare against step data.
        value_str (str): Value string such as "voltage", "time", "current" etc... See DATA_INDEX_MAP module variable for valid values.
    """
    def __init__(self, value_str: str, operator_str: str,
                 value: float, min_time: float = 1.0):
        """Inits with comparison, index, min_time, next_time, value, and value_str.

        Args:
            value_str (str): Value string such as "voltage", "time", "current" etc... See DATA_INDEX_MAP module variable for valid values.
            operator_str (str): String indicating the comparison operator. See OPERATOR_MAP module variable for valid values.
            value (float): Actual value to compare against step data.
            min_time (float): Minimum time that must have elapsed before evaluating the condition.
        """
        self.value = value
        self.value_str = value_str
        self.index = DATA_INDEX_MAP[value_str]
        self.comparison = OPERATOR_MAP[operator_str]
        # at what timestamp do we expect the condition to be met
        self.next_time = NEVER
        self.min_time = min_time

    def check(self, step):
        """Compares absolute set value to step data.

        First checks to see if enough time has passed between the most recent report and the newest data. If enough
        time has passed then the newest data value is compared against the set value.

        Args:
            step (ProtocolStep): The step to have data pulled from its data list.

        Returns:        
            bool: True if the end condition was satisfied, otherwise False
        """
        try:
            execute_check = True
            if self.min_time is not None:
                execute_check = (
                    step.data[-1][0] - step.report[0][0] > self.min_time
                )

            if execute_check:
                if self.comparison(step.data[-1][self.index], self.value):
                    return True
                else:
                    next_time = extrapolate_time(step.data,
                                                 self.value,
                                                 self.index)
                    step.next_time = min(next_time, step.next_time)
                    logger.debug(f"{self.value_str} set next_time to \
                                   {step.next_time:.2f} (in \
                                   {step.next_time - time.time():.2f} sec)")
                    return False
            else:
                return False
        except IndexError:
            return False


def condition_end_voltage(voltage, operator_str):
    """Function for creating a ConditionAbsolute object using a voltage endpoint.

    Loads a ConditionAbsolute object with a comparison voltage and the mathematical 
    comparison operator to use.

    Args:
        voltage (float): The voltage to initialize ConditionAbsolute with.
        operator_str (str): A string representing a mathematical operator i.e. ><= . 

    Returns:
        ConditionAbsolute: Initialized with the given voltage and operator_str.
    """
    return ConditionAbsolute("voltage", operator_str, voltage)


def condition_ucv(voltage):
    """Function for creating a ConditionAbsolute object using an upper cutoff voltage.

    Args:
        voltage (float): The voltage to initialize ConditionAbsolute with.

    Returns:
        ConditionAbsolute: Initialized with the given voltage and >= as the operator.
    """
    return ConditionAbsolute("voltage", ">=", voltage)


def condition_lcv(voltage):
    """Function for creating a ConditionAbsolute object using a lower cutoff voltage.

    Args:
        voltage (float): The voltage to initialize ConditionAbsolute with.

    Returns:
        ConditionAbsolute: Initialized with the given voltage and <= as the operator.
    """
    return ConditionAbsolute("voltage", "<=", voltage)


def condition_min_current(current):
    """Function for creating a ConditionAbsolute object using a min current.

    Args:
        current (float): The current to initialize ConditionAbsolute with.

    Returns:
        ConditionAbsolute: Initialized with the given current and <= as the operator.
    """
    return ConditionAbsolute("current", "<=", current)


def condition_max_current(current):
    """Function for creating a ConditionAbsolute object using a max current.

    Args:
        current (float): The current to initialize ConditionAbsolute with.

    Returns:
        ConditionAbsolute: Initialized with the given current and >= as the operator.
    """
    return ConditionAbsolute("current", ">=", current)


def condition_total_time(total_time):
    """Function for creating a ConditionTotalTime object for a total time condition.

    Args:
        total_time (float): The total_time to be used in the ConditionTotalTime.

    Returns:
        ConditionTotalTime: Initialized with the given total_time.
    """
    return ConditionTotalTime(total_time)


def condition_dt(dt):
    """Function for creating a ConditionDelta object using time.

    Args:
        dt (float): The change in time in seconds.

    Returns:
        ConditionDelta: A Condition that can be used on steps to compare changes in time.
    """
    return ConditionDelta("time", dt)


def condition_di(di):
    """Function for creating a ConditionDelta object using current.

    Args:
        di (float): The change in current.

    Returns:
        ConditionDelta: A Condition that can be used on steps to compare changes in current.
    """
    return ConditionDelta("current", di)


def condition_dv(dv):
    """Function for creating a ConditionDelta object using voltage.

    Args:
        dv (float): The change in voltage.

    Returns:
        ConditionDelta: A Condition that can be used on steps to compare changes in voltage.
    """
    return ConditionDelta("voltage", dv)


def condition_dc(dc):
    """Function for creating a ConditionDelta object using capacity.

    Args:
        dc (float): The change in capacity.

    Returns:
        ConditionDelta: A Condition that can be used on steps to compare changes in capacity.
    """
    return ConditionDelta("capacity", dc)


def extrapolate_time(data, target, index):
    """Estimates the time until a voltage cutoff is reached.

    Args:
        data (list): A list of lists of measurements taken (voltages, currents, times) at each time.
        target (float): The target voltage being extrapolated to.
        index (int): Which of the values being tested against i.e. [0:self.last_time, 1:current,
                2:voltage, 3:capacity, 4:plugin_values]

    Returns:
        float: The time at which the target will be hit.
    """
    try:
        # Project when it will be hit
        d1 = data[-1]
        # require at least 10 mV of difference for projection
        for i in range(2, 100):
            d0 = data[-i]
            if abs(d1[2] - d0[2]) > 0.0001:
                break
        next_time = ((target - d1[index])
                     / (d1[index] - d0[index])
                     * (d1[0] - d0[0]) + d1[0])
        current_time = time.time()
        logger.debug("Current time {:.2f}, \
                      Extrapolated time {:.2f} (in {:.2f} sec) \
                      using {} index and target value {}".format(
            current_time, next_time, next_time-current_time,
            DATA_NAME_MAP[index], target))

    except (NameError, IndexError, ZeroDivisionError):
        next_time = NEVER
        logger.debug("Failed extrapolating, next_time: {}".format(next_time))

    return next_time


def time_conversion(t):
    """Converts time in the "hh:mm:ss" format to seconds as a float.

    Args:
        t (str or float): time in the "hh:mm:ss" format, where values can be ommitted
            e.g. "::5" would be five seconds or time in seconds.

    Returns:
        float: Calculated time in Seconds.
    """
    t_float = None
    try:
        t_float = float(t)
    except ValueError:
        try:
            time_tuple = [float(x) if x else 0 for x in t.split(":")]
            t_float = (time_tuple[0]
                       * 3600.
                       + time_tuple[1]
                       * 60.0
                       + time_tuple[2])
        except AttributeError:
            pass
    return t_float
