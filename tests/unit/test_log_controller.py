# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

import sys
from unittest import TestCase

from ironflow.gui.log import LogController


class TestLogController(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.og_stdout = sys.stdout

    @classmethod
    def tearDownClass(cls) -> None:
        sys.stdout = cls.og_stdout

    def setUp(self) -> None:
        sys.stdout = self.og_stdout

    def test_on_off(self):
        lc = LogController()
        self.assertNotEqual(sys.stdout, lc._stdoutput, msg="Expected to start 'off'")
        lc.log_to_display()
        self.assertEqual(sys.stdout, lc._stdoutput, msg="Failed to turn 'on'")
        lc.log_to_stdout()
        self.assertNotEqual(sys.stdout, lc._stdoutput, msg="Failed to turn  'off'")

    def test_preservation_of_original_stream(self):
        lc = LogController()
        self.assertEqual(self.og_stdout, lc._standard_stdout)
        lc.log_to_display()
        lc2 = LogController()
        self.assertEqual(self.og_stdout, lc._standard_stdout)
        lc2.log_to_stdout()  # Clean up
