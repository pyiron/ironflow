# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from typing import Callable, Optional

import numpy as np
from owlready2 import Thing
from pyiron_atomistics import Project
from pyiron_base import GenericJob
from ryvencore import Node as NodeCore
from ryvencore.Base import Event
from ryvencore.InfoMsgs import InfoMsgs
from ryvencore.NodePort import NodePort
from ryvencore.utils import deserialize

from ironflow.gui.workflows.canvas_widgets.nodes import NodeWidget
from ironflow.model import dtypes
from ironflow.model.otypes import otype_from_str
from ironflow.model.port import NodeInput, NodeInputBP, NodeOutput, NodeOutputBP
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

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
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
    >>>     title = "MyUserNode"
    >>>     init_inputs = [
    >>>         NodeInputBP(dtype=dtypes.Integer(default=1), label="foo")
    >>>     ]
    >>>     init_outputs = [
    >>>        NodeOutputBP(label="bar")
    >>>     ]
    >>>     color = 'cyan'
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
        dtype: Optional[dtypes.DType] = None,
        otype: Optional[Thing] = None,
        insert: Optional[int] = None,
    ):
        """Creates and add a new input port"""
        inp = NodeInput(
            node=self,
            type_=type_,
            label_str=label,
            add_data=add_data,
            dtype=dtype,
            otype=otype,
        )
        self._add_io(self.inputs, inp, insert=insert)

    def create_input_dt(
        self, dtype: dtypes.DType, label: str = "", add_data={}, insert: int = None
    ):
        raise RuntimeError(
            "Ironflow uses custom NodePort classes and this method is not supported. "
            "Please use create_input instead."
        )

    def create_output(
        self,
        type_: str = "data",
        label: str = "",
        dtype: Optional[dtypes.DType] = None,
        otype: Optional[Thing] = None,
        insert: Optional[int] = None,
    ):
        """Create and add a new output port"""
        out = NodeOutput(
            node=self,
            type_=type_,
            label_str=label,
            dtype=dtype,
            otype=otype,
        )
        self._add_io(self.outputs, out, insert=insert)

    def _load_otype(self, data: dict):
        try:
            return otype_from_str(data["otype_namespace"], data["otype_name"])
        except KeyError:
            return None

    def setup_ports(self, inputs_data=None, outputs_data=None):
        # A streamlined version of the ryvencore method which exploits our NodeInput
        # and NodeOutput classes instead, and for which all ports have a dtype
        if not inputs_data and not outputs_data:
            for i in range(len(self.init_inputs)):
                inp = self.init_inputs[i]
                self.create_input(
                    type_=inp.type_,
                    label=inp.label,
                    add_data=inp.add_data,
                    dtype=inp.dtype,
                    otype=inp.otype,
                )

            for o in range(len(self.init_outputs)):
                out = self.init_outputs[o]
                self.create_output(
                    type_=out.type_,
                    label=out.label,
                    dtype=out.dtype,
                    otype=out.otype,
                )

        else:
            # load from data
            # initial ports specifications are irrelevant then

            for inp in inputs_data:
                dtype = dtypes.DType.from_str(inp["dtype"])(
                    _load_state=deserialize(inp["dtype state"])
                )
                self.create_input(
                    type_=inp["type"],
                    label=inp["label"],
                    add_data=inp,
                    dtype=dtype,
                    otype=self._load_otype(inp),
                )

                if "val" in inp:
                    # this means the input is 'data' and did not have any connections,
                    # so we saved its value which was probably represented by some
                    # widget in the front end which has probably overridden the
                    # Node.input() method
                    self.inputs[-1].val = deserialize(inp["val"])

            for out in outputs_data:
                dtype = dtypes.DType.from_str(out["dtype"])(
                    _load_state=deserialize(out["dtype state"])
                )
                self.create_output(
                    type_=out["type"],
                    label=out["label"],
                    dtype=dtype,
                    otype=self._load_otype(out),
                )

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
            inp.label_str: inp
            for inp in self.inputs
            if inp.type_ == "data" and inp.dtype.batched
        }

    @property
    def unbatched_inputs(self):
        return {
            inp.label_str: inp
            for inp in self.inputs
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
                k: v.val[i]
                for k, v in zip(
                    self.batched_inputs.keys(), self.batched_inputs.values()
                )
            }
            for i in range(list(self.batch_lengths.values())[0])
        ]

    def generate_output(self) -> dict:
        if self.batched:
            batch_length_vals = list(self.batch_lengths.values())
            if len(batch_length_vals) > 0 and not np.all(
                np.array(batch_length_vals) == batch_length_vals[0]
            ):
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
        for i, kwargs in enumerate(self._batched_kwargs):
            kwargs.update(self._unbatched_kwargs)
            outputs.append(self.node_function(batch_index=i, **kwargs))
        return {key: [d[key] for d in outputs] for key in outputs[0].keys()}

    def set_output(self):
        try:
            output = self.generate_output()
        except Exception as e:
            self.clear_output()
            raise e
        for k, v in output.items():
            self.outputs.ports[k].set_val(v)
            self.outputs.ports[k].dtype.batched = self.batched

    def clear_output(self):
        for p in self.outputs.ports:
            if p.type_ == "data":
                p.set_val(None)
                p.dtype.batched = self.batched

    def batched_representation(
        self, label: str, representation_function: Callable, *args
    ) -> dict | None:
        """
        Batched output requires multiple representations instead of a single one. Use
        this function to wrap a function that produces your desired representation.
        Resulting batched representations simply get an index added to their label.

        Args:
            label (str): The name of the representation.
            representation_function (Callable): A function producing the representation.
            *args: Members of `self.inputs.values` or `self.outputs.values` needed for
                the representation.

        Returns:
            (dict): The representation(s).

        Examples:
            >>> def extra_representations(self):
            >>>     return {
            >>>         **self.batched_representation(
            >>>             "bigger", self._add5, self.outputs.values.n
            >>>        )
            >>>     }
            >>>
            >>> @staticmethod
            >>> def _add5(n: int):
            >>>     return n + 5
        """
        try:
            if self.batched:
                return {
                    f"{label}_{i}": representation_function(*batch_args)
                    for i, batch_args in enumerate(zip(*args))
                }
            else:
                return {label: representation_function(*args)}
        except Exception as e:
            return {label: f"Failed with: {e}"}

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
            self.set_output()
        else:
            self.clear_output()

    def place_event(self):
        super().place_event()
        self.update()


class JobNode(BatchingNode, ABC):
    """
    A parent class for nodes that run a pyiron job.

    Child classes are required to specify a `_generate_job` method, which takes the
    node input data and returns a `pyiron_base.GenericJob` object, and (optionally) a
    `_get_output_from_job` method which takes the executed job and the node input data
    and returns a dictionary of output with keys corresponding to node output port
    labels. The `job` output type can be made more specific with the `valid_job_classes`
    class attribute.

    In the event that some of the input is batched but the `name` input is *not*
    batched, then the `name` argument passed to `_generate_job` is automatically
    appended with batch index information to prevent jobs from having the same name.

    The node has `run` and `remove` input exec ports and a `ran` output exec port.
    Once the node has been run, all inputs get locked and remain locked until the
    removal process is triggered. Remove clears all the outputs and sets them to `None`.

    If a failure is encountered during the `run` process, the exception is raised, all
    pyiron jobs are deleted (this might need to change if we want to do more expensive
    jobs in the future!), the node output is cleared, and the offending exception is
    raised to the log.

    All descendant classes from this node class expect to have `run`, `remove`, and
    `name` input, and `ran` output. Therefore, when defining additional ports, use this
    format:

    >>> init_inputs = JobNode.init_inputs + [WHATEVER_ELSE_YOU_WANT]
    >>> init_outputs = JobNode.init_outputs + [OTHER_STUFF]
    """

    color = "#c4473f"
    valid_job_classes = None
    init_inputs = [
        NodeInputBP(type_="exec", label="run"),
        NodeInputBP(type_="exec", label="remove"),
        NodeInputBP(dtype=dtypes.String(default="calc"), label="name"),
    ]
    init_outputs = [
        NodeOutputBP(type_="exec", label="ran"),
        NodeOutputBP(dtype=dtypes.Data(valid_classes=GenericJob), label="job"),
    ]

    def place_event(self):
        super().place_event()
        if self.valid_job_classes is not None:
            self.outputs.ports.job.dtype.valid_classes = self.valid_job_classes

    def update_event(self, inp=-1):
        if inp == 0 and (not self.block_updates) and self.all_input_is_valid:
            self.block_updates = True
            try:
                self._jobs = []
                self.set_output()
                self.exec_output(0)
            except Exception as e:
                self._on_remove_signal()
                raise e
        else:
            self.clear_output()

    def update(self, inp=-1):
        if inp == 1:
            # Bypass the `lock_updates` to delete the executed job and unlock updates
            self._on_remove_signal()
            # self.update(-1)
        else:
            super().update(inp=inp)

    def node_function(self, name, *args, **kwargs):
        if self.batched and not self.inputs.ports.name.dtype.batched:
            name = f"{name}_batch{kwargs['batch_index']}"
        job = self._raise_error_if_not_initialized(
            self._generate_job(name, *args, **kwargs)
        )
        self._jobs.append(job)
        job.run()
        data = self._get_output_from_job(job, *args, name=name, **kwargs)
        return {
            "job": job,
            **data,
        }

    def _on_remove_signal(self):
        if hasattr(self, "_jobs"):
            for job in self._jobs:
                job.remove()
        self.clear_output()
        self.block_updates = False

    def _raise_error_if_not_initialized(self, job: GenericJob) -> GenericJob:
        if job.status == "initialized":
            return job
        else:
            self.block_updates = False
            raise RuntimeError(
                f"The job {self.inputs.values.name} already exists. Delete it first or"
                f"choose a different name."
            )

    @abstractmethod
    def _generate_job(self, name: str, *args, **kwargs) -> GenericJob:
        """
        Takes a (potentially modified[^1]) name and the rest of the input data and
        returns a job to `.run()`

        [^1]: If some of the input is batched, but the `name` field is not batched, the
              batch index information will get automatically appended to the name.
        """

        pass

    def _get_output_from_job(self, finished_job: GenericJob, *args, **kwargs) -> dict:
        """
        Takes the executed job and all the node input data, and should return relevant
        output data as a dictionary with keys matching the output port labels.
        """

        return {}


class JobMaker(JobNode, ABC):
    """
    A job-running node that takes creates a new job instance from scratch, ready to
    `.run()`.

    All descendant classes from this node class expect to have `run`, `remove`, `name`,
    and `project` input, and `ran` output. Therefore, when defining additional ports,
    use this format:

    >>> init_inputs = JobMaker.init_inputs + [WHATEVER_ELSE_YOU_WANT]
    >>> init_outputs = JobMaker.init_outputs + [OTHER_STUFF]
    """

    init_inputs = JobNode.init_inputs + [
        NodeInputBP(dtype=dtypes.Data(valid_classes=Project), label="project")
    ]


class JobTaker(JobNode, ABC):
    """
    A job-running node that takes a template job instance as input, and copies and
    modifies it prior to use.

    Valid classes for the `job` input can be overriden with the `valid_job_classes`
    attribute.

    All descendant classes from this node class expect to have `run`, `remove`, `name`,
    and `job` input, and `ran` output. Therefore, when defining additional ports, use
    this format:

    >>> init_inputs = JobTaker.init_inputs + [WHATEVER_ELSE_YOU_WANT]
    >>> init_outputs = JobTaker.init_outputs + [OTHER_STUFF]
    """

    init_inputs = JobNode.init_inputs + [
        NodeInputBP(dtype=dtypes.Data(valid_classes=GenericJob), label="job")
    ]

    def place_event(self):
        super().place_event()
        if self.valid_job_classes is not None:
            self.inputs.ports.job.dtype.valid_classes = self.valid_job_classes

    def _generate_job(self, name: str, job: GenericJob, **kwargs) -> GenericJob:
        copied_job = job.copy_to(new_job_name=name)
        return self._modify_job(copied_job, **kwargs)

    @abstractmethod
    def _modify_job(self, copied_job: GenericJob, *args, **kwargs) -> GenericJob:
        """
        Takes the generated job, modifies it in place using the input data (except for
        the `job` and `name` input values) and returns it ready to be `.run()`
        """
        pass
