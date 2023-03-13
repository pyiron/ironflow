# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A new output port class that has a dtype.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Optional, TYPE_CHECKING

from ryvencore.NodePort import NodeInput as NodeInputCore, NodeOutput as NodeOutputCore
from ryvencore.NodePortBP import (
    NodeOutputBP as NodeOutputBPCore,
    NodeInputBP as NodeInputBPCore,
)
from ryvencore.utils import serialize

from ironflow.model.dtypes import DType, Untyped

if TYPE_CHECKING:
    from ironflow.model.node import Node


class TypeHaver:
    """
    A parent class for the has-type classes to facilitate super calls, regardless of
    the order these havers appear as mixins to other classes.
    """

    @property
    def valid_val(self):
        try:
            other_type_checks = super().valid_val
        except AttributeError:
            other_type_checks = True
        return other_type_checks


class HasDType(TypeHaver):
    """A mixin to add the valid value check property"""

    @property
    def valid_val(self):
        return self._dtype_ok and super().valid_val

    @property
    def _dtype_ok(self):
        if self.dtype is not None:
            if self.val is not None:
                return self.dtype.valid_val(self.val)
            else:
                return self.dtype.allow_none
        else:
            return True


class HasOType(TypeHaver):
    """A mixin to add the valid value check to properties with an ontology type"""

    @property
    def valid_val(self):
        return self._otype_ok and super().valid_val

    @property
    def _otype_ok(self):
        if (
            isinstance(self, NodeInput)
            and self.otype is not None
            and len(self.connections) > 0
        ):
            upstream = self.connections[0].out
            # TODO: Catch the connection in use (most recently updated?) not the zeroth
            if upstream.otype is not None:
                return self._accepts_other_with_otype(upstream)
            else:
                return True
        else:
            return True

    def _accepts_other_with_otype(self, other):
        downstream_requirements = self.get_downstream_requirements()
        return other.otype in self.otype.get_sources(downstream_requirements)
        # And the other's sources need to recursively be OK with these requirments

    def get_downstream_requirements(self):
        downstream_requirements = []
        for out in self.node.outputs:
            if out.otype is not None:
                for downstream_inp in [conn.inp for conn in out.connections]:
                    if downstream_inp.otype is not None:
                        downstream_requirements += (
                            downstream_inp.get_downstream_requirements()
                        )
        try:
            return self.otype.get_requirements(list(set(downstream_requirements)))
        except AttributeError:
            return list(set(downstream_requirements))


class NodeInput(NodeInputCore, HasDType, HasOType):
    def __init__(
        self,
        node: Node,
        type_: str = "data",
        label_str: str = "",
        add_data: Optional[dict] = None,
        dtype: Optional[DType] = None,
        otype=None,
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

    def data(self) -> dict:
        data = super().data()

        if self.otype is not None:
            data["otype_namespace"] = self.otype.namespace.name
            data["otype_name"] = self.otype.name

        return data

    def can_receive_other_with_otype(self, other):
        return self._accepts_other_with_otype(other)


class NodeOutput(NodeOutputCore, HasDType, HasOType):
    def __init__(
        self,
        node,
        type_="data",
        label_str="",
        dtype: Optional[DType] = None,
        otype=None,
    ):
        super().__init__(node=node, type_=type_, label_str=label_str)
        self.dtype = Untyped() if dtype is None else deepcopy(dtype)
        self.otype = otype

    def data(self) -> dict:
        data = super().data()

        if self.dtype is not None:
            data["dtype"] = str(self.dtype)
            data["dtype state"] = serialize(self.dtype.get_state())

        if self.otype is not None:
            data["otype_namespace"] = self.otype.namespace.name
            data["otype_name"] = self.otype.name

        return data


class NodeInputBP(NodeInputBPCore):
    def __init__(
        self,
        label: str = "",
        type_: str = "data",
        dtype: DType = None,
        add_data={},
        otype=None,
    ):
        super().__init__(label=label, type_=type_, dtype=dtype, add_data=add_data)
        self.otype = otype


class NodeOutputBP(NodeOutputBPCore):
    def __init__(
        self,
        label: str = "",
        type_: str = "data",
        dtype: Optional[DType] = None,
        otype=None,
    ):
        super().__init__(label=label, type_=type_)
        self.dtype = dtype
        self.otype = otype
