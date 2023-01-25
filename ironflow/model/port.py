# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A new output port class that has a dtype.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Optional, TYPE_CHECKING

from owlready2 import Thing
from ryvencore.NodePort import NodeInput as NodeInputCore, NodeOutput as NodeOutputCore
from ryvencore.NodePortBP import (
    NodeOutputBP as NodeOutputBPCore, NodeInputBP as NodeInputBPCore
)
from ryvencore.utils import serialize

from ironflow.model.dtypes import DType, Untyped

if TYPE_CHECKING:
    from ironflow.model.node import Node


class HasDType:
    """A mixin to add the valid value check property"""

    @property
    def valid_val(self):
        if self.dtype is not None:
            if self.val is not None:
                return self.dtype.valid_val(self.val)
            else:
                return self.dtype.allow_none
        else:
            return True


class NodeInput(NodeInputCore, HasDType):
    def __init__(
        self,
        node: Node,
        type_: str = "data",
        label_str: str = "",
        add_data: Optional[dict] = None,
        dtype: Optional[DType] = None,
        otype: Optional[Thing] = None,
    ):
        super().__init__(
            node=node,
            type_=type_,
            label_str=label_str,
            add_data=add_data if add_data is not None else {},
            dtype=Untyped() if dtype is None else deepcopy(dtype),
        )
        self.otype = otype

    def _update_node(self):
        self.node.update(self.node.inputs.index(self))

    def batch(self):
        if self.dtype is not None and not self.dtype.batched:
            self.dtype.batched = True
            if len(self.connections) == 0:
                self.val = [self.val]
            self._update_node()

    def unbatch(self):
        if self.dtype is not None and self.dtype.batched:
            self.dtype.batched = False
            if len(self.connections) == 0:
                self.val = self.val[-1]
            self._update_node()


class NodeOutput(NodeOutputCore, HasDType):
    def __init__(
            self,
            node,
            type_="data",
            label_str="",
            dtype: Optional[DType] = None,
            otype: Optional[Thing] = None
    ):
        super().__init__(node=node, type_=type_, label_str=label_str)
        self.dtype = Untyped() if dtype is None else deepcopy(dtype)
        self.otype = otype

    def data(self) -> dict:
        data = super().data()

        if self.dtype is not None:
            data["dtype"] = str(self.dtype)
            data["dtype state"] = serialize(self.dtype.get_state())

        return data


class NodeInputBP(NodeInputBPCore):
    def __init__(
            self,
            label: str = "",
            type_: str = "data",
            dtype: DType = None,
            add_data={},
            otype: Optional[Thing] = None,
    ):
        super().__init__(label=label, type_=type_, dtype=dtype, add_data=add_data)
        self.otype = otype


class NodeOutputBP(NodeOutputBPCore):
    def __init__(
            self,
            label: str = "",
            type_: str = "data",
            dtype: Optional[DType] = None,
            otype: Optional[Thing] = None,
    ):
        super().__init__(label=label, type_=type_)
        self.dtype = dtype
        self.otype = otype
