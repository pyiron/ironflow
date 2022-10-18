import unittest
import pyiron_module


class TestVersion(unittest.TestCase):
    def test_version(self):
        version = pyiron_module.__version__
        print(version)
        self.assertTrue(version.startswith('0'))
