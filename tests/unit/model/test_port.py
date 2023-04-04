# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from unittest import TestCase

from ironflow.model.dtypes import String
from ironflow.model.port import NodeInput, NodeOutput, NodeOutputBP


class DummyInputs:
    def index(self, node):
        pass


class DummyNode:
    def update(self, inp):
        pass

    @property
    def inputs(self):
        return DummyInputs()


class TestPorts(TestCase):
    def test_for_dtype(self):
        """The `dtype` attribute should always be present, although it may be None"""
        self.assertTrue(hasattr(NodeInput(node=None), 'dtype'))
        self.assertTrue(hasattr(NodeOutput(node=None), 'dtype'))
        self.assertTrue(hasattr(NodeOutputBP(), 'dtype'))

    def test_validity(self):
        with self.subTest("Without dtype set"):
            p0 = NodeInput(node=DummyNode(), dtype=None)
            p0.update(None)
            self.assertTrue(p0.ready)
            p0.update("foo")
            self.assertTrue(p0.ready)
            p0.update(42)
            self.assertTrue(p0.ready)

        with self.subTest("With allow none"):
            p0 = NodeInput(node=DummyNode(), dtype=String(allow_none=True))
            p0.update(None)
            self.assertTrue(p0.ready)
            p0.update("foo")
            self.assertTrue(p0.ready)
            p0.update(42)
            self.assertFalse(p0.ready, msg="Should be wrong type")

        with self.subTest("With allow none"):
            p0 = NodeInput(node=DummyNode(), dtype=String(allow_none=False))
            p0.update(None)
            self.assertFalse(p0.ready, msg="None should be disallowed")
            p0.update("foo")
            self.assertTrue(p0.ready)
            p0.update(42)
            self.assertFalse(p0.ready, msg="Should be wrong type")
