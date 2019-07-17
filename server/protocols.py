import json
import time
from datetime import datetime
import operator
import logging

DATETIME_FORMAT = '%Y-%m-%d_%H:%M:%S.%f'
NEVER = 2 * time.time()

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
STATUS.string_map = {
    STATUS.pending: "pending",
    STATUS.started: "started",
    STATUS.paused: "paused",
    STATUS.completed: "completed",
    STATUS.unknown: "unknown",
    STATUS.available: "available"
}


class CellRunner(object):
    META = {
        "path": None,
        "protocol_name": None,
        "protocol": None,
        "channel": None,
        "cellid": None,
        "comment": None,
        "requester": None,
        "cycler": None,
        "cell_type": None,
        "package": None,
        "start_cycle": None
    }

    def __init__(self, **meta):
        self.meta = self.META.copy()
        for k in self.meta.keys():
            self.meta[k] = meta.get(k, None)

        if self.meta["cycler"] is None:
            self.meta["cycler"] = "Keithley2602"
        if self.meta["cell_type"] is None:
            self.meta["cell_type"] = "unknown"

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
        self.next_time = -1
        self.channel = self.meta["channel"]
        self.data_format = "    " + ",".join(["{:0.8g}"] * 4) + "\n"
        self.last_data = None
        self.total_pause_time = 0.0
        self.source = None

    def set_source(self, source):
        self.source = source
        if self.channel != source.channel:
            raise ValueError(
                "the runner channel ({}) and the source \
                    channel ({}) should be identical".format(
                        self.channel, source.channel
                    ))

    def set_cap_signs(self, direction=None):
        """
        Go through the steps and set their .cap_sign attribute
        based on the "direction" of teh cell.
        This decides whether charging yields positive or negative capacities
        and vice versa for discharge.

        Parameters
        ----------
        direction: str or None
            direction for the cell can be "pos", "neg", or None
            if it is None, the "cell_type" in teh meta data is used,
            if this is not set it defaults to "pos"


        Returns
        -------
        None
        """
        valid_directions = ["pos", "neg", None]
        if direction not in valid_directions:
            raise ValueError(
                "received unsupported direction argument:\
                {}, must be one of {}".format(direction, valid_directions))

        if direction is None:
            direction = 'pos'
            if "anode" in self.meta["cell_type"].lower():
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
        """

        Parameters
        ----------
        protocol: str
            string of python code generating the protocol steps in the runner

        Returns
        -------

        """
        # The protocol is a python string that is executed as code.
        # The CellRunner instance must be present as "parent" in the globals
        # so that the ProtocolSteps can add themselves to the .steps list
        self.isTest = isTest
        exec(protocol, globals().update({"parent": self}))
        # Set the signs for the capacity calculations
        self.set_cap_signs()

    def add_step(self, step):
        self.steps.append(step)

    def next_step(self):
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
        """
        Initializes the protocol, would not normally be called directly,
        but instead is called by the .run() function

        Returns
        -------
        None
        """
        logging.info("cyckei.server.protocols.CellRunner._start: \
            Starting cellrunner instance (channel: {})".format(self.channel))

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
        try:
            return self.steps[self.i_current_step]
        except IndexError:
            return None

            # TODO should next_time be a property?
            # currently there is a protocol.next_time and a step.next_time.
            # TODO Not sure if this is redundant
            #    @property
            #    def next_time(self):
            #        return self.step.next_time

    def run(self, force_report=False):
        """
        Method called by the main loop to start and advance a protocol
        This method triggers the various steps that are loaded in the protocol
        as well as the header writing and the data writing in the data file

        Returns
        -------
        success: bool
            True if is running as expected
            False if it is complete

        """
        logging.debug("cyckei.server.protocols.CellRunner.run: \
            Entering method for channel {}".format(self.channel))
        if self.status == STATUS.completed:
            return False

        if self.status == STATUS.paused:
            return False

        if self.status != STATUS.started:
            self._start()

        if self.step.status != STATUS.started:
            self.write_step_header()

        self.read_and_write(force_report=force_report)

        if self.step.status == STATUS.completed:
            self.next_step()

        if self.status == STATUS.completed:
            self.close()

        return True

    def advance_cycle(self):
        self.cycle += 1
        self.write_cycle_header()

    def write_header(self):
        with open(self.fpath, 'w') as fo:
            header = json.dumps(self.meta, indent=4, sort_keys=True)
            header = "\n".join(
                ["#{}".format(line) for line in header.split("\n")]
            )
            fo.write(header + "\n")

    def write_cycle_header(self):
        with open(self.fpath, 'a') as fo:
            cycle_header = json.dumps({"cycle": self.cycle}) + "\n"
            fo.write(cycle_header)

    def write_step_header(self):
        header = self.step.header()
        if header:
            with open(self.fpath, 'a') as fo:
                fo.write("  " + header + "\n")

    def read_and_write(self, force_report=False):
        data = self.step.run(force_report=force_report)
        self.next_time = self.step.next_time
        if data:
            self.write_data(*data)
            self.last_data = data

    def write_data(self, timestamp, current, voltage, capacity):
        with open(self.fpath, 'a') as fo:
            fo.write(self.data_format.format(
                timestamp - self.start_time - self.total_pause_time,
                current, voltage, capacity)
            )

    def pause(self):
        """
        User must be able to pause a cell arbitrarily
        Returns
        -------

        """
        success = False
        self.read_and_write(force_report=True)
        self.status = STATUS.paused
        if self.step.pause():
            self.next_time = self.step.next_time
            success = True
        return success

    def resume(self):
        self.status = STATUS.started
        self.step.resume()
        return self.run()

    def close(self):
        """
        This is to close
        Returns
        -------

        """
        self.source.off()

    def off(self):
        """
        This is just to turn off the current
        Returns
        -------

        """
        self.source.off()

    def stop(self):
        self.status = STATUS.completed
        self.close()
        return True


class ProtocolStep(object):
    """
    Base class for a protocol step, needs to be subclassed with
    implementation of a start function

    A protocol step stores stores its own data and the reported points
    Keeps track of time, current, voltage, capacity

    Because the protocol files are simply pure python the parent, which is a
    CellRunner instance needs to be present in the global variables as "parent"

    """

    def __init__(self,
                 wait_time: float = 10.0,
                 cellrunner_parent: CellRunner = None):
        """
        Base class for protocols
        the variable "parent" must be a CellRunner
        instance and be present in the globals during instantiation

        Parameters
        ----------
        wait_time: float
            default waiting time in seconds
        """
        # the parent is the CellRunner
        if cellrunner_parent is None:
            self.parent = parent
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

        self.parent.add_step(self)

    def _start(self):
        raise NotImplementedError

    def header(self):
        return False

    def run(self, force_report=False):
        """

        Parameters
        ----------
        force_report: bool
            defaults to False. The run function evaluates the
            report_conditions to decide if a data point should be
            reported, setting force_report to True will report the
            latest data point regardless of conditions.


        Returns
        -------
        data_to_report: tuple of 4
            (time, current, voltage, capacity) tuple to report (write to file)
            returns non if no data to report

        """
        logging.debug(
            "cyckei.server.protocols.ProtocolStep.run: \
            running {} protocol on channel {}".format(self.state_str,
                                                      self.parent.channel))
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

        if self.status == STATUS.completed:
            report_data = True

        else:
            report_data = self.check_report_conditions()

        if report_data or force_report:
            self.report.append(self.data[-1])
            return self.report[-1]
        else:
            return None

    def check_end_conditions(self):
        """

        Returns
        -------
        bool: whether one of the end conditions was satisfied
        """
        for condition in self.end_conditions:
            if condition.check(self):
                self.status = STATUS.completed
                return True
        return False

    def check_report_conditions(self):
        """

        Returns
        -------
        bool: whether one of the report conditions was satisfied
        """
        for condition in self.report_conditions:
            if condition.check(self):
                return True
        return False

    def read_data(self, force_report=False):
        self.last_time = time.time()
        current, voltage = self.parent.source.read_iv()

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
                        / 1000.)
        else:
            capacity = self.starting_capacity

        self.data.append([self.last_time, current, voltage, capacity])

        if len(self.data) > self.data_max_len:
            # we pop 1 and not 0
            # because if we pop 0 it will screw up the total time checking
            self.data.pop(1)

        if force_report:
            self.report.append(self.data[-1])

    def pause(self):
        if self.status != STATUS.started:
            return False

        self.status = STATUS.paused
        self.pause_start = time.time()
        self.parent.off()
        self.next_time = NEVER
        return True

    def resume(self):
        if self.status != STATUS.paused:
            return False
        self.pause_time = time.time() - self.pause_start
        self.parent.total_pause_time += self.pause_time
        self._start()
        # self.status = STATUS.started


def process_reports(reports):
    """

    Parameters
    ----------
    reports:
        desired reports as a tuple of pairs such as
        (("voltage",0.01), ("time",300))

    Returns
    -------
    report_conditions: list
        List of condition objects for reporting a data point

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
    """

    Parameters
    ----------
    ends:
        desired ends conditions as a tuple of triples such as
        (("voltage",">", 4.2), ("time",">","24::"))

    Returns
    -------
    end_conditions: list
        List of condition objects for ending a protocol step

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
    def __init__(self, current,
                 reports=(("voltage", 0.01), ("time", ":5:")),
                 ends=(("voltage", ">", 4.2), ("time", ">", "24::")),
                 wait_time=10.0):
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

        self.v_limit = sign * 5.0
        for e in ends:
            if e[0] == "voltage":
                self.v_limit = e[2] + sign * 0.1

        self.report_conditions = process_reports(reports)
        self.end_conditions = process_ends(ends)

    def _start(self):
        self.status = STATUS.started
        self.parent.source.set_current(current=self.current,
                                       v_limit=self.v_limit)

    def header(self):
        return json.dumps({"state": self.state_str,
                          "date_start_timestr": datetime.now().strftime(
                                DATETIME_FORMAT)}
                          )


class CCCharge(CurrentStep):
    def __init__(self, current,
                 reports=(("voltage", 0.01), ("time", ":5:")),
                 ends=(("voltage", ">", 4.2), ("time", ">", "24::")),
                 wait_time=10.0):
        # Enforce positive current
        current = abs(current)
        super().__init__(current,
                         reports=reports, ends=ends,
                         wait_time=wait_time)
        self.state_str = "charge_constant_current"


class CCDischarge(CurrentStep):
    def __init__(self, current,
                 reports=(("voltage", 0.01), ("time", ":5:")),
                 ends=(("voltage", "<", 3), ("time", ">", "24::")),
                 wait_time=10.0):
        # Enforce negative current
        current = -abs(current)
        super().__init__(current,
                         reports=reports, ends=ends,
                         wait_time=wait_time)
        self.state_str = "discharge_constant_current"


class VoltageStep(ProtocolStep):
    def __init__(self, voltage,
                 reports=(("current", 0.01), ("time", ":5:")),
                 ends=(("current", "<", 0.001), ("time", ">", "24::")),
                 wait_time=10.0):
        super().__init__(wait_time=wait_time)

        self.i_limit = None
        self.voltage = voltage
        self.report_conditions = process_reports(reports)
        self.end_conditions = process_ends(ends)

    def guess_i_limit(self):
        self.i_limit = 1.0
        if self.state_str.startswith("charge"):
            self.i_limit = self.parent.source.current_ranges[-1]
        elif self.state_str.startswith("discharge"):
            self.i_limit = -self.parent.source.current_ranges[-1]

    def _start(self):
        self.status = STATUS.started
        if self.i_limit is None:
            raise ValueError(
                "the i_limit must be set, try using the guess_i_limit method"
            )

        self.parent.source.set_voltage(voltage=self.voltage,
                                       i_limit=self.i_limit)

    def header(self):
        return json.dumps({"state": self.state_str,
                          "date_start_timestr": datetime.now().strftime(
                            DATETIME_FORMAT)}
                          )


class CVCharge(VoltageStep):
    def __init__(self, voltage,
                 reports=(("current", 0.01), ("time", ":5:")),
                 ends=(("current", "<", 0.001), ("time", ">", "24::")),
                 wait_time=10.0):
        super().__init__(voltage,
                         reports=reports, ends=ends,
                         wait_time=wait_time)
        self.state_str = "charge_constant_voltage"
        if parent.isTest:
            pass
        else:
            self.guess_i_limit()


class CVDischarge(VoltageStep):
    def __init__(self, voltage,
                 reports=(("current", 0.01), ("time", ":5:")),
                 ends=(("current", "<", 0.001), ("time", ">", "24::")),
                 wait_time=10.0):
        super().__init__(voltage,
                         reports=reports, ends=ends,
                         wait_time=wait_time)
        self.state_str = "discharge_constant_voltage"
        if parent.isTest:
            pass
        else:
            self.guess_i_limit()


class AdvanceCycle(ProtocolStep):
    def _start(self):
        self.status = STATUS.started

    def run(self, force_report=False):
        self._start()
        self.parent.advance_cycle()
        self.status = STATUS.completed


class Rest(ProtocolStep):
    def __init__(self,
                 reports=(("time", ":5:"),), ends=(("time", ">", "24::"),),
                 wait_time=10.0):
        super().__init__(wait_time=wait_time)

        self.state_str = "rest"
        self.report_conditions = process_reports(reports)
        self.end_conditions = process_ends(ends)

    def _start(self):
        self.status = STATUS.started
        self.parent.source.rest()

    def header(self):
        return json.dumps({"state": self.state_str,
                          "date_start_timestr": datetime.now().strftime(
                            DATETIME_FORMAT)}
                          )


class Pause(ProtocolStep):
    def __init__(self):
        """

        Parameters
        ----------
        parent: Protocol
            Protocol to which this protocol step belongs

        """
        # This is the time between measurements on the channel,
        # putting this arbitrarily large
        super().__init__(wait_time=NEVER)
        self.state_str = "pause"

    def _start(self):
        self.state = STATUS.started
        self.next_time = time.time() + self.wait_time
        self.parent.source.pause()

    def run(self):
        self._start()
        return None

    def resume(self):
        self.status = STATUS.completed


class Sleep(ProtocolStep):
    def __init__(self,
                 reports=(("time", ":5:"),), ends=(("time", ">", "24::"),),
                 wait_time=10.0):
        super().__init__(wait_time=wait_time)

        self.state_str = "sleep"
        self.report_conditions = process_reports(reports)
        self.end_conditions = process_ends(ends)

    def _start(self):
        self.status = STATUS.started
        self.parent.source.off()

    def header(self):
        return json.dumps({"state": self.state_str,
                          "date_start_timestr": datetime.now().strftime(
                            DATETIME_FORMAT)}
                          )

    def read_data(self):
        self.parent.source.rest()
        super().read_data()
        self.parent.source.off()

    def run(self, force_report=False):
        """
        The run method needs to be redefined because the logic of the Sleep
        protocol is unique in that a measurement is
        only desired if a report condition is met as opposed to
        the other steps which measure and then decide whether to report

        Parameters
        ----------
        force_report: bool
            defaults to False. The run function evaluates the
            report_conditions to decide if a data point should be
            reported, setting force_report to True will report the
            latest data point regardless of conditions.


        Returns
        -------
        data_to_report: tuple of 4
            (time, current, voltage, capacity) tuple to report (write to file)
            returns none if no data to report

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


class Condition(object):
    """
    A Condition is an object which given a ProtocolStep
    object to its "check" method will return a boolean
    indicating whether that condition has been met

    A condition object may modify the .next_time attribute of
    the ProtocolStep object to suggest time the
    next time as an absolute timestamp that the condition should be checked
    """

    def check(self, protocol_step: ProtocolStep):
        raise NotImplementedError


class ConditionDelta(Condition):
    def __init__(self, value_str: str, delta: float):
        """
        Change between latest reported value and latest measured value

        Parameters
        ----------
        value_str: str
            value string such as "voltage", "time", "current" etc...
            See DATA_INDEX_MAP module variable
            for valid values
        delta: float
            Delta to compare against
        """
        self.value_str = value_str
        self.index = DATA_INDEX_MAP[value_str]
        self.comparison = OPERATOR_MAP[">="]
        self.delta = abs(delta)
        self.is_time = value_str == "time"

    def check(self, step):
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
                    next_time = extrapolate_time(step.data,
                                                 val + self.delta,
                                                 self.index)
                    step.next_time = min(next_time, step.next_time)

                logging.debug("cyckei.server.protocols.ConditionDelta: \
                {}, set next_time to {}".format(self.value_str,
                                                step.next_time))

                if self.comparison(abs(val - step.report[-1][self.index]),
                                   self.delta):
                    return True
                else:
                    return False
        except IndexError:
            return False


class ConditionTotalDelta(Condition):
    def __init__(self, value_str: str, delta: float):
        """
        Change between first reported value and latest measured value

        Parameters
        ----------
        value_str: str
            value string such as "voltage", "time", "current" etc...
            See DATA_INDEX_MAP module variable
            for valid values
        delta: float
            Delta to compare against
        """
        self.delta = delta
        self.value_str = value_str
        self.index = DATA_INDEX_MAP[value_str]
        self.comparison = OPERATOR_MAP[">="]
        # at what timestamp do we expect the condition to be met
        self.next_time = NEVER

    def check(self, step):
        try:
            delta = abs(step.data[-1][self.index] - step.report[0][self.index])
            return self.comparison(delta, self.delta)
        except IndexError:
            return False


class ConditionTotalTime(ConditionTotalDelta):
    def __init__(self, delta):
        """
        Change between first reported time and latest reported time

        Parameters
        ----------
        delta: float
            Total elapsed time in seconds
        """

        super().__init__("time", delta)

    def check(self, step):
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
                logging.debug(
                    "cyckei.server.protocols.ConditionTotalTime: \
                    {}, set next_time to {}".format(self.value_str,
                                                    step.next_time))
                return False
        except IndexError:
            return False


class ConditionAbsolute(Condition):
    def __init__(self, value_str: str, operator_str: str,
                 value: float, min_time: float = 1.0):
        """

        Parameters
        ----------
        value_str: str
            value string such as "voltage", "time", "current" etc...
            See DATA_INDEX_MAP module variable
            for valid values
        operator_str: str
            String indicating the ocmparison operator.
            See OPERATOR_MAP module variable for valid values
        value: float
            Actual value to compare against
        min_time: float
            minimum time that must have elapsed before evaluating the condition
        """
        self.value = value
        self.value_str = value_str
        self.index = DATA_INDEX_MAP[value_str]
        self.comparison = OPERATOR_MAP[operator_str]
        # at what timestamp do we expect the condition to be met
        self.next_time = 1e30
        self.min_time = min_time

    def check(self, step):
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
                    logging.debug(
                        "cyckei.server.protocols.ConditionTotalTime: \
                        {}, set next_time to {}".format(self.value_str,
                                                        step.next_time))
                    return False
            else:
                return False
        except IndexError:
            return False


def condition_end_voltage(voltage, operator_str):
    return ConditionAbsolute("voltage", operator_str, voltage)


def condition_ucv(voltage):
    return ConditionAbsolute("voltage", ">=", voltage)


def condition_lcv(voltage):
    return ConditionAbsolute("voltage", "<=", voltage)


def condition_min_current(current):
    return ConditionAbsolute("current", "<=", current)


def condition_max_current(current):
    return ConditionAbsolute("current", ">=", current)


def condition_total_time(total_time):
    return ConditionTotalTime(total_time)


def condition_dt(dt):
    return ConditionDelta("time", dt)


def condition_di(di):
    return ConditionDelta("current", di)


def condition_dv(dv):
    return ConditionDelta("voltage", dv)


def condition_dc(dc):
    return ConditionDelta("capacity", dc)


def extrapolate_time(data, target, index):
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

    except (NameError, IndexError, ZeroDivisionError):
        next_time = time.time()

    logging.debug(
        "cyckei.server.protocols.extrapolate_time: \
        Extrapolated time {} using {} index and target value {}".format(
            next_time, DATA_NAME_MAP[index], target)
        )

    return next_time


def time_conversion(t):
    """

    Parameters
    ----------
    t: str or float
        time in the "hh:mm:ss" format, where values can be ommitted
        e.g. "::5" would be five seconds or
        time in seconds

    Returns
    -------
    time (float) in seconds
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
