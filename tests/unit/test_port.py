# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from unittest import TestCase

from ryvencore.utils import deserialize, serialize

from ironflow.model.port import NodeInput, NodeOutput, NodeOutputBP


class TestPorts(TestCase):
    def test_for_dtype(self):
        """The `dtype` attribute should always be present, although it may be None"""
        self.assertTrue(hasattr(NodeInput(node=None), 'dtype'))
        self.assertTrue(hasattr(NodeOutput(node=None), 'dtype'))
        self.assertTrue(hasattr(NodeOutputBP(), 'dtype'))

    def test_spoof(self):
        raise RuntimeError
