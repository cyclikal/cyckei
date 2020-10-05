from tests import mock_source

class MockDevice(object):
    """Represents a mock keithley Interface"""
    current_ranges = [100 * 1e-9, 1e-6, 10e-6,
                      100e-6, 1e-3, 0.01,
                      0.1, 1.0, 3.0]

    def __init__(self, accel=1):
        self.source = mock_source.MockSource(accel)
        self.safety_reset_seconds = 120

    def get_source(self, kch, channel=None):
        """Get source object of Keithley"""
        return self.source