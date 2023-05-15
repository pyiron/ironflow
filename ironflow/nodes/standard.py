from __future__ import annotations

import numpy as np

from ironflow.model import dtypes
from ironflow.model.node import DataNode
from ironflow.model.port import NodeInputBP, NodeOutputBP

NUMERIC_TYPES = [int, float, np.number]


class Sin_Node(DataNode):
    """
    Call `numpy.sin` on a value.

    Inputs:
        x (int|float|list|numpy.ndarray|...): The value to sine transform.

    Outputs:
        sin (float|numpy.ndarray): The sine of x.
    """

    title = "Sin"
    version = "v0.1"
    init_inputs = [
        NodeInputBP(dtype=dtypes.List(valid_classes=NUMERIC_TYPES), label="x"),
    ]
    init_outputs = [
        NodeOutputBP(dtype=dtypes.List(valid_classes=NUMERIC_TYPES), label="sin"),
    ]
    color = "#5d95de"

    def node_function(self, x, **kwargs) -> dict:
        return {"sin": np.sin(x)}


class Input_Node(DataNode):
    """
    Give data as a string and cast it to a specific type.
    """

    title = "Input"

    init_inputs = [NodeInputBP(label="input", dtype=dtypes.String())]

    init_outputs = [
        NodeOutputBP(label="as_str", dtype=dtypes.String()),
        NodeOutputBP(label="as_int", dtype=dtypes.Integer()),
        NodeOutputBP(label="as_float", dtype=dtypes.Float()),
    ]

    def node_function(self, input, **kwargs) -> dict:
        try:
            as_int = int(input)
        except ValueError:
            as_int = None
        try:
            as_float = float(input)
        except ValueError:
            as_float = None
        return {
            "as_str": str(input),
            "as_int": as_int,
            "as_float": as_float,
        }


class InputArray_Node(DataNode):
    """
    Give data as a comma-separated string and cast it to a specific type of array.
    """

    title = "InputArray"

    init_inputs = [NodeInputBP(label="input", dtype=dtypes.String())]

    init_outputs = [
        NodeOutputBP(label="as_str", dtype=dtypes.List(valid_classes=str)),
        NodeOutputBP(label="as_int", dtype=dtypes.List(valid_classes=np.integer)),
        NodeOutputBP(label="as_float", dtype=dtypes.List(valid_classes=np.floating)),
    ]

    def node_function(self, input, **kwargs) -> dict:
        as_str = np.array(input.split(","))
        try:
            as_int = as_str.astype(int)
        except ValueError:
            as_int = None
        try:
            as_float = as_str.astype(float)
        except ValueError:
            as_float = None
        return {
            "as_str": as_str,
            "as_int": as_int,
            "as_float": as_float,
        }
