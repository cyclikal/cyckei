import unittest
# TODO: Create more rigorous tests


class PyVISA(unittest.TestCase):
    def setUp(self):
        import visa
        rm = visa.ResourceManager()
        self.resources = rm.list_resources()

    def test_keithley_gpib(self):
        gpib_exists = False
        for resource in self.resources:
            if "GPIB" in resource:
                gpib_exists = True
        self.assertTrue(gpib_exists,
                        "PyVISA did not detect any GPIB instruments.")


class Server(unittest.TestCase):
    def test_placeholder(self):
        self.assertTrue(True, "Placeholder")


class Client(unittest.TestCase):
    def test_placeholder(self):
        self.assertTrue(True, "Placeholder")


if __name__ == "__main__":
    unittest.main()
