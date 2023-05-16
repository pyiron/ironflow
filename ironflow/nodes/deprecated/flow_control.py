from __future__ import annotations

from ironflow.model import dtypes
from ironflow.model.node import Node
from ironflow.model.port import NodeInputBP, NodeOutputBP
from ironflow.node_tools import main_widgets
from ironflow.nodes.deprecated.special_nodes import DualNodeBase


class ForEach_Node(Node):
    title = "ForEach"
    version = "v0.1"
    init_inputs = [
        NodeInputBP(type_="exec", label="start"),
        NodeInputBP(type_="exec", label="reset"),
        NodeInputBP(dtype=dtypes.List(), label="elements"),
    ]
    init_outputs = [
        NodeOutputBP(label="loop", type_="exec"),
        NodeOutputBP(label="e", type_="data"),
        NodeOutputBP(label="finished", type_="exec"),
    ]
    color = "#b33a27"

    _count = 0

    def update_event(self, inp=-1):
        if inp == 0:
            self._count += 1
            if len(self.inputs.values.elements) > self._count:
                e = self.inputs.values.elements[self._count]
                self.set_output_val(1, e)
                self.exec_output(0)
            else:
                self.exec_output(2)
        elif inp > 0:
            self._count = 0
        self.val = self._count


class ExecCounter_Node(DualNodeBase):
    title = "ExecCounter"
    version = "v0.1"
    init_inputs = [
        NodeInputBP(type_="exec"),
    ]
    init_outputs = [
        NodeOutputBP(type_="exec"),
    ]
    color = "#5d95de"

    def __init__(self, params):
        super().__init__(params, active=True)
        self._count = 0

    def update_event(self, inp=-1):
        if self.active and inp == 0:
            self._count += 1
            self.val = self._count
        elif not self.active:
            self.val = self.input(0)


class Click_Node(Node):
    title = "Click"
    version = "v0.1"
    main_widget_class = main_widgets.ButtonNodeWidget
    init_inputs = []
    init_outputs = [NodeOutputBP(type_="exec")]
    color = "#99dd55"

    def update_event(self, inp=-1):
        self.exec_output(0)
