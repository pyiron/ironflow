# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from unittest import TestCase

from ironflow.model import dtypes
from ironflow.model.model import HasSession
from ironflow.model.node import Node
from ironflow.model.port import NodeInputBP


class Choice_Node(Node):
    init_inputs = [
        NodeInputBP(
            dtype=dtypes.Choice(
                default="Initial choice", items=["Initial choice"]
            ),
            label="choices",
        )
    ]


class TestMutability(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.model = HasSession("integration", extra_nodes_packages=[[Choice_Node]])
        cls.model.create_script()

    def tearDown(self) -> None:
        self.model.delete_script()

    def test_dtype_mutability(self):
        self.model.flow.create_node(Choice_Node)
        self.model.flow.create_node(Choice_Node)

        p0 = self.model.flow.nodes[0].inputs.ports.choices
        p1 = self.model.flow.nodes[1].inputs.ports.choices

        self.assertNotEqual(p0, p1, msg="Ports should be unique instances")
        self.assertNotEqual(p0.dtype, p1.dtype, msg="DTypes should be unique instances")
        p1.dtype.val = "New choice"
        p1.dtype.items = ["Initial choice", "New choice"]
        self.assertNotEqual(
            p0.dtype.items, p1.dtype.items, msg="Mutable attributes of DTypes should be unique instances"
        )
