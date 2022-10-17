# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
from __future__ import annotations

from abc import ABC

from ryvencore.Base import Event

from ironflow.NENV import Node
from ironflow.ironflow.canvas_widgets.nodes import RepresentableNodeWidget


class NodeBase(Node):
    """
    A parent class for all ironflow nodes. Apart from a small quality-of-life difference where outputs are
    accessible in the same way as inputs (i.e. with a method `output(i)`), the main change here is the `before_update`
    and `after_update` events. Callbacks to happen before and after the update can be added to (removed from) these with
    the `connect` (`disconnect`) methods on the event. Such callbacks need to take the node itself as the first
    argument, and the integer specifying which input channel is being updated as the second argument.
    """

    color = "#ff69b4"  # Add an abrasive default color -- won't crash if you forget to add one, but pops out a bit

    def __init__(self, params):
        super().__init__(params)
        self.before_update = Event(self, int)
        self.after_update = Event(self, int)

    def update(self, inp=-1):
        self.before_update.emit(self, inp)
        super().update(inp=inp)
        self.after_update.emit(self, inp)

    def output(self, i):
        return self.outputs[i].val


class NodeWithRepresentation(NodeBase, ABC):
    """
    A node with a "representation" that gets used in the GUI to give a more detailed look at node data.
    """

    main_widget_class = RepresentableNodeWidget

    def __init__(self, params):
        super().__init__(params)
        self.representation_updated = False
        self.after_update.connect(self._representation_update)

    @staticmethod
    def _representation_update(self, inp):
        self.representation_updated = True

    @property
    def representations(self) -> dict:
        return {
            o.label_str if o.label_str != "" else f"output{i}": o.val
            for i, o in enumerate(self.outputs) if o.type_ == "data"
        }
