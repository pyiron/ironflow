import unittest
import ironflow


class TestVersion(unittest.TestCase):
    def test_version(self):
        version = ironflow.__version__
        print(version)
        self.assertTrue(version.startswith('0'))
