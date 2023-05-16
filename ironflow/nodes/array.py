from __future__ import annotations

import numpy as np

from ironflow.model import dtypes
from ironflow.model.node import DataNode
from ironflow.model.port import NodeInputBP, NodeOutputBP


class Select_Node(DataNode):
    """
    Select a single elemnt of an iterable input.
    """

    title = "Select"
    init_inputs = [
        NodeInputBP(dtype=dtypes.List(valid_classes=object), label="array"),
        NodeInputBP(dtype=dtypes.Integer(default=0), label="i"),
    ]
    init_outputs = [
        NodeOutputBP(label="item", dtype=dtypes.Data(valid_classes=object)),
    ]
    color = "#aabb44"

    def update_event(self, inp=-1):
        self.outputs.ports.item.dtype.valid_classes = [
            type(self.inputs.values.array[self.inputs.values.i])
        ]
        super().update_event(inp=inp)

    def node_function(self, array, i, **kwargs) -> dict:
        return {"item": array[i]}


class Slice_Node(DataNode):
    """
    Slice a numpy array, list, or tuple, and return it as a numpy array.

    When both `i` and `j` are `None`: Return the input whole.
    When `i` is not `None` and `j` is: Return the slice `[i:]`
    When `i` is `None` and `j` isn't: Return the slice `[:j]`
    When neither are `None`: Return the slice `[i:j]`
    """

    title = "Slice"
    init_inputs = [
        NodeInputBP(dtype=dtypes.List(valid_classes=object), label="array"),
        NodeInputBP(dtype=dtypes.Integer(default=None, allow_none=True), label="i"),
        NodeInputBP(dtype=dtypes.Integer(default=None, allow_none=True), label="j"),
    ]
    init_outputs = [
        NodeOutputBP(label="sliced", dtype=dtypes.List(valid_classes=object)),
    ]
    color = "#aabb44"

    def update_event(self, inp=-1):
        self.outputs.ports.sliced.dtype = dtypes.List(
            valid_classes=list(
                set(
                    type(obj)
                    for obj in self._slice(
                        self.inputs.values.array,
                        self.inputs.values.i,
                        self.inputs.values.j,
                    )
                )
            )
        )
        super().update_event(inp=inp)

    @staticmethod
    def _slice(array, i, j):
        converted = np.array(array)
        if i is None and j is None:
            sliced = converted
        elif i is not None and j is None:
            sliced = converted[i:]
        elif i is None and j is not None:
            sliced = converted[:j]
        else:
            sliced = converted[i:j]
        return sliced

    def node_function(self, array, i, j, **kwargs) -> dict:
        return {"sliced": self._slice(array, i, j)}


class Transpose_Node(DataNode):
    """
    Interprets list-like input as a numpy array and transposes it.
    """

    title = "Transpose"
    init_inputs = [
        NodeInputBP(dtype=dtypes.List(valid_classes=object), label="array"),
    ]
    init_outputs = [
        NodeOutputBP(dtype=dtypes.List(valid_classes=object), label="transposed"),
    ]
    color = "#aabb44"

    def node_function(self, array, **kwargs) -> dict:
        array = np.array(array)  # Ensure array
        if len(array.shape) < 2:
            array = np.array([array])  # Ensure transposable
        return {"transposed": np.array(array).T}


class IntRand_Node(DataNode):
    """
    Generate a random non-negative integer.

    Inputs:
        high (int): Biggest possible integer. (Default is 1).
        length (int): How many random numbers to generate. (Default is 1.)

    Outputs:
        randint (int|numpy.ndarray): The randomly generated value(s).
    """

    # this __doc__ string will be displayed as tooltip in the editor

    title = "IntRandom"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Integer(default=0), label="low"),
        NodeInputBP(dtype=dtypes.Integer(default=1), label="high"),
        NodeInputBP(dtype=dtypes.Integer(default=1), label="length"),
    ]
    init_outputs = [
        NodeOutputBP(dtype=dtypes.List(valid_classes=np.integer), label="randint"),
    ]
    color = "#aabb44"

    def node_function(self, low, high, length, *args, **kwargs) -> dict:
        return {"randint": np.random.randint(low, high=high, size=length)}


class Linspace_Node(DataNode):
    """
    Generate a linear mesh in a given range using `np.linspace`.

    Inputs:
        min (int): The lower bound (inclusive). (Default is 1.)
        max (int): The upper bound (inclusive). (Default is 2.)
        steps (int): How many samples to take inside (min, max). (Default is 10.)

    Outputs:
        linspace (numpy.ndarray): A uniform sampling over the requested range.
    """

    # this __doc__ string will be displayed as tooltip in the editor

    title = "Linspace"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Float(default=1.0), label="min"),
        NodeInputBP(dtype=dtypes.Float(default=2.0), label="max"),
        NodeInputBP(dtype=dtypes.Integer(default=10), label="steps"),
    ]
    init_outputs = [
        NodeOutputBP(dtype=dtypes.List(valid_classes=np.floating), label="linspace")
    ]
    color = "#aabb44"

    def node_function(self, min, max, steps, **kwargs) -> dict:
        return {"linspace": np.linspace(min, max, steps)}
