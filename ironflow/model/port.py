# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A new output port class that has a dtype.
"""

from copy import deepcopy
from typing import Optional

from ryvencore.NodePort import NodeOutput
from ryvencore.NodePortBP import NodeOutputBP as NodeOutputBPCore
from ryvencore.utils import serialize

from ironflow.model.dtypes import DType


class NodeOutputDT(NodeOutput):
    def __init__(self, node, type_, label_str='', dtype: DType = None):
        super().__init__(node=node, type_=type_, label_str=label_str)
        self.dtype = deepcopy(dtype)  # Some dtypes have mutable fields

    def data(self) -> dict:
        data = super().data()

        data['dtype'] = str(self.dtype)
        data['dtype state'] = serialize(self.dtype.get_state())

        return data


class NodeOutputBP(NodeOutputBPCore):
    def __init__(
            self, label: str = '', type_: str = 'data', dtype: Optional[DType] = None
    ):
        super().__init__(label=label, type_=type_)
        self.dtype = dtype
