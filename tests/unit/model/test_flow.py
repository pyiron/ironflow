# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from unittest import TestCase

from ironflow.model.dtypes import Integer, String
from ironflow.model.port import NodeInput, NodeOutput
from ironflow.model.session import Session


class FakeNode:
    def __init__(self, title):
        self.title = title


class TestFlow(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.session = Session()
        cls.session.create_script()
        cls.flow = cls.session.scripts[0].flow

    def test_check_connection_validity(self):
        i0 = NodeInput(FakeNode("input"))
        i1 = NodeInput(FakeNode("input"), dtype=Integer(allow_none=True))
        i2 = NodeInput(FakeNode("input"), dtype=Integer(allow_none=False))

        o0 = NodeOutput(FakeNode("output"))
        o0.val = None
        o1 = NodeOutput(FakeNode("output"))
        o1.val = 42
        o2 = NodeOutput(FakeNode("output"), dtype=Integer(allow_none=True))
        o2.val = 42
        o3 = NodeOutput(FakeNode("output"), dtype=Integer(allow_none=False))
        o3.val = 42
        o4 = NodeOutput(FakeNode("output"), dtype=String())

        expectations = (
            (i0, o0, True),
            (i0, o1, True),
            (i0, o2, True),
            (i0, o3, True),
            (i0, o4, True),
            (i1, o0, True),
            (i1, o1, True),
            (i1, o2, True),
            (i1, o3, True),
            (i1, o4, False),  # Wrong dtype
            (i2, o0, False),  # Value is None
            (i2, o1, True),
            (i2, o2, False),  # Other dtype not specific enough (allows None)
            (i2, o3, True),
            (i2, o4, False),  # Wrong dtype
        )

        for e in expectations:
            self.assertEqual(
                e[2],
                self.flow.check_connection_validity(e[0], e[1]),
                msg=f"Input with dtype {e[0].dtype} and allow_none "
                    f"{e[0].dtype.allow_none if hasattr(e[0].dtype, 'allow_none') else None} compared {e[2]} "
                    f"against output with dtype {e[1].dtype}, allow_none "
                    f"{e[1].dtype.allow_none if hasattr(e[1].dtype, 'allow_none') else None}, and value "
                    f"{e[1].val}"
            )
