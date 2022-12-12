# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from typing import Optional

import numpy as np
from ryvencore import Node as NodeCore
from ryvencore.Base import Event
from ryvencore.NodePort import NodePort
from ryvencore.utils import deserialize

from ironflow.gui.workflows.canvas_widgets.nodes import NodeWidget
from ironflow.model.dtypes import DType
from ironflow.model.port import NodeInput, NodeOutput
from ironflow.utils import display_string


class PortList(list):
    """
    When used to hold a collection of `NodePort` objects, the values of these ports then become accessible by their
    labels, as long as those labels do not match an existing method of the builtin list class.

    Warning:
        This class makes no check that these labels are unique; if multiple items have the same label, the first one
        is returned.

    Warning:
        Accessing port values in this way side-steps ryven functionality when in exec mode or using an executor
        (i.e. when `running_with_executor`).
    """

    def __init__(self, seq=()):
        super().__init__(self, seq=seq)
        self._port_finder = PortFinder(self)
        self._value_finder = ValueFinder(self)
        # This additional mis-direction is necessary so that ports can have the same labels as list class methods

    @property
    def ports(self):
        """
        Allows attribute-like access to ports by their `label_str`
        """
        return self._port_finder

    @property
    def values(self):
        """
        Allows attribute-like access to port values by their `label_str`

        Calling `port_list.values.some_label` is equivalent to `port_list.ports.some_label.val`
        """
        return self._value_finder

    @property
    def labels(self):
        return [item.label_str if isinstance(item, NodePort) else None for item in self]


class PortFinder:
    def __init__(self, port_list: PortList):
        self._port_list = port_list

    @property
    def _filtered_port_list(self):
        return [item for item in self._port_list if isinstance(item, NodePort)]

    def __getattr__(self, key):
        for node_port in self._filtered_port_list:
            if node_port.label_str == key:
                return node_port
        raise AttributeError(f"No port found with the label {key}")

    def __getitem__(self, item):
        return self.__getattr__(item)

    def __iter__(self):
        return self._filtered_port_list.__iter__()


class ValueFinder(PortFinder):
    def __getattr__(self, key):
        node_port = super().__getattr__(key)
        return node_port.val

    def __iter__(self):
        val_list = [p.val for p in self._filtered_port_list]
        return val_list.__iter__()


class Node(NodeCore):
    """
    A parent class for all ironflow nodes. Apart from a small quality-of-life difference where outputs are
    accessible in the same way as inputs (i.e. with a method `output(i)`), the main change here is the `before_update`
    and `after_update` events. Callbacks to happen before and after the update can be added to (removed from) these with
    the `connect` (`disconnect`) methods on the event. Such callbacks need to take the node itself as the first
    argument, and the integer specifying which input channel is being updated as the second argument.

    Also provides a "representation" that gets used in the GUI to give a more detailed look at node data, which defaults
    to showing output channel values.

    Children should specify a title and some combination of initial input, output, and what to do when updated, e.g.:

    >>> class My_Node(Node):
    >>> title = "MyUserNode"
    >>> init_inputs = [
    >>>     NodeInputBP(dtype=dtypes.Integer(default=1), label="foo")
    >>> ]
    >>> init_outputs = [
    >>>    NodeOutputBP(label="bar")
    >>> ]
    >>> color = 'cyan'
    >>>
    >>> def update_event(self, inp=-1):
    >>>     self.set_output_val(0, self.input(0) + 42)

    Note:
        When registering nodes from a module or .py file, only children of this class with names ending in `_Node` will
        get registered.
    """

    main_widget_class = NodeWidget

    color = "#ff69b4"  # Add an abrasive default color -- won't crash if you forget to add one, but pops out a bit

    def __init__(self, params):
        super().__init__(params)
        self.inputs = PortList()
        self.outputs = PortList()

        self.before_update = Event(self, int)
        self.after_update = Event(self, int)
        self.actions = (
            dict()
        )  # Resolves Todo from ryven.NENV, moving it to our node class instead of ryvencore

        self.representation_updated = False
        self.after_update.connect(self._representation_update)

    def _add_io(self, io_group, new_io, insert: int = None):
        if insert is not None:
            io_group.insert(insert, new_io)
        else:
            io_group.append(new_io)

    def create_input(
        self,
        type_: str = "data",
        label: str = "",
        add_data: Optional[dict] = None,
        dtype: Optional[DType] = None,
        insert: Optional[int] = None,
    ):
        """Creates and add a new input port"""
        inp = NodeInput(
            node=self, type_=type_, label_str=label, add_data=add_data, dtype=dtype
        )
        self._add_io(self.inputs, inp, insert=insert)

    def create_input_dt(
        self, dtype: DType, label: str = "", add_data={}, insert: int = None
    ):
        raise RuntimeError(
            "Ironflow uses custom NodePort classes and this method is not supported. "
            "Please use create_input instead."
        )

    def create_output(
        self,
        type_: str = "data",
        label: str = "",
        dtype: Optional[DType] = None,
        insert: Optional[int] = None,
    ):
        """Create and add a new output port"""
        out = NodeOutput(node=self, type_=type_, label_str=label, dtype=dtype)
        self._add_io(self.outputs, out, insert=insert)

    def setup_ports(self, inputs_data=None, outputs_data=None):
        # A streamlined version of the ryvencore method which exploits our NodeInput
        # and NodeOutput classes instead.
        if not inputs_data and not outputs_data:

            for i in range(len(self.init_inputs)):
                inp = self.init_inputs[i]
                self.create_input(
                    type_=inp.type_,
                    label=inp.label,
                    add_data=inp.add_data,
                    dtype=inp.dtype,
                )

            for o in range(len(self.init_outputs)):
                out = self.init_outputs[o]
                self.create_output(type_=out.type_, label=out.label, dtype=out.dtype)

        else:
            # load from data
            # initial ports specifications are irrelevant then

            for inp in inputs_data:
                if "dtype" in inp:
                    dtype = DType.from_str(inp["dtype"])(
                        _load_state=deserialize(inp["dtype state"])
                    )
                    self.create_input(label=inp["label"], add_data=inp, dtype=dtype)
                else:
                    self.create_input(
                        type_=inp["type"], label=inp["label"], add_data=inp
                    )

                if "val" in inp:
                    # this means the input is 'data' and did not have any connections,
                    # so we saved its value which was probably represented by some widget
                    # in the front end which has probably overridden the Node.input() method
                    self.inputs[-1].val = deserialize(inp["val"])

            # ironflow modification
            for out in outputs_data:
                if "dtype" in out:
                    dtype = DType.from_str(out["dtype"])(
                        _load_state=deserialize(out["dtype state"])
                    )
                    self.create_output(label=out["label"], dtype=dtype)
                else:
                    self.create_output(type_=out["type"], label=out["label"])

    @property
    def all_input_is_valid(self):
        return all([p.valid_val for p in self.inputs.ports])

    def place_event(self):
        # place_event() is executed *before* the connections are built
        super().place_event()
        for inp in self.inputs:
            if (
                inp.val is None
            ):  # Don't over-write data from loaded sessions with defaults
                if inp.dtype is not None:
                    inp.update(inp.dtype.default)
                elif "val" in inp.add_data.keys():
                    inp.update(inp.add_data["val"])

    def update(self, inp=-1):
        self.before_update.emit(self, inp)
        super().update(inp=inp)
        self.after_update.emit(self, inp)

    def output(self, i):
        return self.outputs[i].val

    @staticmethod
    def _representation_update(self, inp):
        self.representation_updated = True

    @property
    def _source_code(self):
        try:
            return inspect.getsource(self.__class__)
        except TypeError:
            # Classes defined in the notebook can't access their source this way
            return ""

    @property
    def _standard_representations(self):
        standard_reps = {
            o.label_str if o.label_str != "" else f"output{i}": o.val
            for i, o in enumerate(self.outputs)
            if o.type_ == "data"
        }
        standard_reps["source code"] = display_string(self._source_code)
        return standard_reps

    @property
    def extra_representations(self):
        """
        When developing nodes, override this with any desired additional representations.

        Note that standard representations exist for all output ports using the port's label (where available), so if
        you add a key here matching one of those labels, you will override the standard output.
        """
        return {}

    @property
    def representations(self) -> dict:
        return {**self._standard_representations, **self.extra_representations}

    def set_all_outputs_to_none(self):
        for i in range(len(self.outputs)):
            self.set_output_val(i, None)


class PlaceholderWidgetsContainer:
    """
    An object that just returns None for all accessed attributes so widgets.MyWidget in the non-ironflow nodes files
    just returns None.
    """

    def __getattr__(self, item):
        return None


class BatchingNode(Node, ABC):
    """
    A node whose update behaviour supports batched inputs.
    """

    @property
    def batched_inputs(self):
        return {
            inp.label_str: inp for inp in self.inputs
            if inp.type_ == "data" and inp.dtype.batched
        }

    @property
    def unbatched_inputs(self):
        return {
            inp.label_str: inp for inp in self.inputs
            if inp.type_ == "data" and not inp.dtype.batched
        }

    @property
    def batched(self):
        return len(self.batched_inputs) > 0

    @property
    def batch_lengths(self):
        return {k: len(v.val) for k, v in self.batched_inputs.items()}

    @property
    def _unbatched_kwargs(self):
        return {k: v.val for k, v in self.unbatched_inputs.items()}

    @property
    def _batched_kwargs(self):
        return [
            {
                k: v.val[i] for k, v in
                zip(self.batched_inputs.keys(), self.batched_inputs.values())
            }
            for i in range(list(self.batch_lengths.values())[0])
        ]

    def generate_output(self) -> dict:
        if self.batched:
            batch_length_vals = list(self.batch_lengths.values())
            if len(batch_length_vals) > 0 and \
                    not np.all(np.array(batch_length_vals) == batch_length_vals[0]):
                raise ValueError(
                    f"Not all batch lengths are the same: {self.batch_lengths}"
                )
            return self.generate_batched_output()
        else:
            return self.generate_unbatched_output()

    def generate_unbatched_output(self):
        return self.node_function(**self._unbatched_kwargs)

    def generate_batched_output(self):
        outputs = []
        for kwargs in self._batched_kwargs:
            kwargs.update(self._unbatched_kwargs)
            outputs.append(self.node_function(**kwargs))
        return {
            key: [d[key] for d in outputs] for key in outputs[0].keys()
        }

    @abstractmethod
    def node_function(self, *args, **kwargs) -> dict:
        """
        Takes all data input as kwargs, must return a dict with one entry for each data
        output
        """
        pass


class DataNode(BatchingNode, ABC):
    """
    A node that can update as soon as all input is valid and produces output data.
    """
    def update_event(self, inp=-1):
        if self.all_input_is_valid:
            try:
                output = self.generate_output()
            except RuntimeError as e:
                self.set_output_val(0, None)
                raise e
            for k, v in output.items():
                self.outputs.ports[k].val = v
                if self.outputs.ports[k].dtype is not None:
                    self.outputs.ports[k].dtype.batched = self.batched
        else:
            for p in self.outputs.ports:
                p.val = None
                if p.dtype is not None:
                    p.dtype.batched = False

