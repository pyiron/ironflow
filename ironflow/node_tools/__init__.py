# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
The necessary classes for creating new nodes.

Example:
    >>> from ironflow import GUI
    >>> from ironflow.node_tools import Node, NodeInputBP, NodeOutputBP, dtypes, input_widgets
    >>> gui = GUI(script_title='foo')
    >>>
    >>> class MyNode(Node):
    >>>     title = "MyUserNode"
    >>>     init_inputs = [
    >>>         NodeInputBP(dtype=dtypes.Integer(default=1), label="foo")
    >>>     ]
    >>>     init_outputs = [
    >>>        NodeOutputBP(label="bar")
    >>>    ]
    >>>    color = 'cyan'
    >>>
    >>>     def update_event(self, inp=-1):
    >>>         self.set_output_val(0, self.input(0) + 42)
    >>>
    >>> gui.register_node(MyNode)
"""

import ironflow.node_tools.input_widgets
import ironflow.node_tools.main_widgets
from ironflow.model import dtypes
from ironflow.model.node import (
    Node,
    PlaceholderWidgetsContainer,
    PortList,
    DataNode,
    JobMaker,
    JobTaker,
)
from ironflow.model.port import NodeInputBP, NodeOutputBP
