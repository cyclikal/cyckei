import numpy as np
from scipy.integrate import solve_ivp
import time


class MockSource():
    w = 100.  # mAh
    s = -1.  # shift to avoid dorppping too low in voltage
    R = 2.  # internal resistance in Ohms
    current_ranges = [100 * 1e-9, 1e-6, 10e-6,
                      100e-6, 1e-3, 0.01,
                      0.1, 1.0, 3.0]

    def __init__(self, acceleration=1.0):
        self.channel = 'a'
        self.safety_reset_seconds = 120
        self._current = 0  # current in Amps
        self._voltage = None  # Voltage in volts
        self.t = 0  # time of last state of charge in seconds
        self.x = 0  # State of charge in mAh
        self.mode = 'constant_current'
        self.acceleration = acceleration
        # Set the internal _voltage variable
        self.voltage

    def time(self):
        return self.acceleration * time.time()

    @property
    def voltage(self):
        '''
        Use the Nernst equation to get the Voltage at constant current
        '''
        if self.mode == 'constant_current':
            t = self.time()
            dt = t - self.t
            self.x += (self._current*1000.)*(dt/3600.)
            self.t = t
            self._voltage = 3.7+0.2 * \
                (np.log(1./(1./(self.x-self.s)-1./(self.w-self.s))) -
                 np.log(self.w))+self._current*self.R
            return self._voltage

        elif self.mode == 'constant_voltage':
            return self._voltage

    @property
    def current(self):
        '''
        integrate the Nernst equation as an ODE to find capacity and current at constant voltage
        '''
        if self.mode == 'constant_current':
            return self._current
        elif self.mode == 'constant_voltage':
            def cv(t, mAh):
                return (self._voltage - (3.7+0.2*(np.log(1./(1./(mAh-self.s)-1./(self.w-self.s)))-np.log(self.w))))/self.R

            t = self.time()
            dt = t - self.t

            # Solve the dx/t = cv(t,x) equation for x
            sol = solve_ivp(cv, (0.0, dt), np.array([self.x]))

            self.t = t
            self.x = sol.y[0][-1]
            self._current = cv(0, sol.y[0][-1])

            return self._current

    def read_iv(self):
        return self.current, self.voltage

    def off(self):
        self.read_iv()
        self._current = 0
        self.mode = 'constant_current'

    def pause(self):
        self.off()

    def rest(self):
        self.off()

    def set_current(self, current=0, v_limit=None):
        self.off()
        self._current = current
        self.mode = 'constant_current'

    def set_voltage(self, voltage=3):
        self.off()
        self._voltage = voltage
        self.mode = 'constant_voltage'
