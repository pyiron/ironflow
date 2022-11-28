# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

import sys
from unittest import TestCase

from ironflow.gui.log import LogController


class TestLogController(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lc = LogController()

    def setUp(self) -> None:
        self.lc.log_to_stdout()

    def tearDown(self) -> None:
        self.lc.log_to_stdout()

    def test_on_off(self):
        self.assertNotEqual(sys.stdout, self.lc.stdoutput, msg="Expected to start 'off'")
        self.lc.log_to_display()
        self.assertEqual(sys.stdout, self.lc.stdoutput, msg="Failed to turn 'on'")
        self.lc.log_to_stdout()
        self.assertNotEqual(sys.stdout, self.lc.stdoutput, msg="Failed to turn  'off'")

    def test_preservation_of_original_stream(self):
        self.assertEqual(sys.stdout, self.lc._standard_stdout)
        self.assertNotEqual(self.lc.stdoutput, self.lc._standard_stdout)
        self.lc.log_to_display()
        lc2 = LogController()
        self.assertEqual(sys.stdout, lc2.stdoutput)
        self.assertNotEqual(lc2.stdoutput, lc2._standard_stdout)
