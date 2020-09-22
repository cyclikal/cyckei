import numpy as np
import time


class MockSource():
    w = 100.  # mAh
    s = -1.  # shift to avoid dorppping too low in voltage
    R = 2.  # internal resistance in Ohms

    def __init__(self):
        self.current = 0
        self.t0 = 0
        self.x0 = 0
        self.channel = 'a'
        self.safety_reset_seconds = 120

    def nernst(self):
        mAh = self.capacity()
        return 3.7+0.2*(np.log(1./(1./(mAh-self.s)-1./(self.w-self.s)))-np.log(self.w))+self.current*self.R

    def capacity(self, reset=False):
        t = time.time()
        dt = t-self.t0
        mAh = self.x0 + (self.current*1000.)*(dt/3600.)
        if reset:
            self.t0 = t
            self.x0 = mAh

        return mAh

    def read_iv(self):
        return self.current, self.nernst()

    def off(self):
        self.capacity(reset=True)
        self.current = 0

    def pause(self):
        self.off()

    def rest(self):
        self.off

    def set_current(self, current=0, v_limit=None):
        self.t0 = time.time()
        self.current = current