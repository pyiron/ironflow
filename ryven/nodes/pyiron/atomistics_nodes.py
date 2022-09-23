# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from __future__ import annotations

import matplotlib.pylab as plt
import numpy as np
import json
from pyiron_atomistics import Project
from pyiron_atomistics.lammps import list_potentials
from pyiron_atomistics.atomistics.job.atomistic import AtomisticGenericJob
from ryven.NENV import Node, NodeInputBP, NodeOutputBP, dtypes
from ryven.ironflow.canvas_widgets.nodes import RepresentableNodeWidget, ButtonNodeWidget

from abc import ABC, abstractmethod
from ryven.nodes.std.special_nodes import DualNodeBase

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyiron_base import HasGroups


__author__ = "Joerg Neugebauer, Liam Huber"
__copyright__ = (
    "Copyright 2020, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Liam Huber"
__email__ = "liamhuber@greyhavensolutions.com"
__status__ = "production"
__date__ = "May 10, 2022"


class BeautifulHasGroups:
    def __init__(self, has_groups: HasGroups | None):
        self._has_groups = has_groups

    def to_builtin(self, has_groups=None):
        has_groups = has_groups if has_groups is not None else self._has_groups
        if has_groups is not None:
            repr_dict = {}
            for k in has_groups.list_groups():
                repr_dict[k] = self.to_builtin(has_groups[k])
            for k in has_groups.list_nodes():
                repr_dict[k] = str(has_groups[k])
            return repr_dict
        else:
            return None

    def _repr_json_(self):
        return self.to_builtin()

    def _repr_html_(self):
        name = self._has_groups.__class__.__name__
        plain = f"{name}({json.dumps(self.to_builtin(), indent=2, default=str)})"
        return "<pre>" + plain + "</pre>"


class NodeBase(Node):
    color = "#ff69b4"  # Add an abrasive default color -- won't crash if you forget to add one, but pops out a bit

    def __init__(self, params):
        super().__init__(params)
        self._call_after_update = []

    def update(self, inp=-1):
        super().update(inp=inp)
        self._after_update(inp)

    def _after_update(self, inp: int):
        for fnc in self._call_after_update:
            fnc(inp)

    def output(self, i):
        return self.outputs[i].val


class NodeWithRepresentation(NodeBase, ABC):
    main_widget_class = RepresentableNodeWidget

    def __init__(self, params):
        super().__init__(params)
        self.representation_updated = False
        self._call_after_update.append(self._representation_update)

    def _representation_update(self, inp):
        self.representation_updated = True

    @property
    def representations(self) -> dict:
        return {
            o.label_str if o.label_str != "" else f"output{i}": o.val
            for i, o in enumerate(self.outputs) if o.type_ == "data"
        }


class Project_Node(NodeWithRepresentation):
    """Create a pyiron project node"""

    # this __doc__ string will be displayed as tooltip in the editor

    title = "Project"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Char(default="."), label="name"),
    ]
    init_outputs = [
        NodeOutputBP(label="project"),
    ]
    color = "#aabb44"

    def place_event(self):
        self.update()

    def update_event(self, inp=-1):
        pr = Project(self.input(0))
        self.set_output_val(0, pr)

    @property
    def _project(self):
        return self.output(0)

    @property
    def representations(self) -> dict:
        return {
            "name": str(self.input(0)),
            # "job_table": self._project.job_table() if self._project is not None else None
            # TODO: Figure out how to display this without breaking the gui size; right now it automatically grows
            # the gui because the table is so wide.
        }


class OutputsOnlyAtoms(NodeWithRepresentation, ABC):
    init_outputs = [
        NodeOutputBP(label="structure"),
    ]
    color = "#aabb44"

    @abstractmethod
    def update_event(self, inp=-1):
        """Must set output 0 to an instance of pyiron_atomistics.atomistics.atoms.Atoms"""
        pass

    @property
    def representations(self) -> dict:
        return {
            "plot3d": self.output(0).plot3d(),
            "print": self.output(0)
        }


class BulkStructure_Node(OutputsOnlyAtoms):
    """Generate a bulk atomic structure"""

    # this __doc__ string will be displayed as tooltip in the editor

    title = "BulkStructure"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Data(size="m"), label="project"),
        NodeInputBP(dtype=dtypes.Char(default="Fe"), label="element"),
        NodeInputBP(dtype=dtypes.Boolean(default=True), label="cubic"),
    ]

    def update_event(self, inp=-1):
        pr = self.input(0)
        self.set_output_val(
            0, pr.create.structure.bulk(self.input(1), cubic=self.input(2))
        )


class Repeat_Node(OutputsOnlyAtoms):
    """Repeat atomic structure supercell"""

    # this __doc__ string will be displayed as tooltip in the editor

    title = "Repeat"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Data(size="m"), label="structure"),
        NodeInputBP(dtype=dtypes.Integer(default=1, bounds=(1, 100)), label="all"),
    ]

    def update_event(self, inp=-1):
        self.set_output_val(0, self.input(0).repeat(self.input(1)))


class ApplyStrain_Node(OutputsOnlyAtoms):
    """
    Apply strain on atomic structure supercell

    Inputs:
        structure (Atoms): The atomic structure to strain.
        strain (float): The isotropic strain to apply.

    Outputs:
        (Atoms): The strained structure.
    """

    title = "ApplyStrain"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Data(size="m"), label="structure"),
        NodeInputBP(dtype=dtypes.Float(default=0, bounds=(-100, 100)), label="strain"),
    ]

    def update_event(self, inp=-1):
        self.set_output_val(0, self.input(0).apply_strain(float(self.input(1)), return_box=True))


class Lammps_Node(NodeWithRepresentation):
    title = "Lammps"
    version = "v0.1"
    init_inputs = [
        NodeInputBP(type_="exec", label="run"),
        NodeInputBP(type_="exec", label="remove"),
        NodeInputBP(dtype=dtypes.Data(size="m"), label="project"),
        NodeInputBP(dtype=dtypes.Char(default="job"), label="name"),
        NodeInputBP(dtype=dtypes.Data(size="m"), label="structure"),
        NodeInputBP(dtype=dtypes.Choice(
            default="Set structure first", items=["Set structure first"]), label="potential"
        )
    ]
    init_outputs = [
        NodeOutputBP(type_="exec"),
        NodeOutputBP(label="job"),
    ]
    color = "#5d95de"

    @property
    def _project(self):
        return self.input(2)

    @property
    def _name(self):
        return self.input(3)

    @property
    def _structure(self):
        return self.input(4)

    @property
    def _potential(self):
        return self.input(5)

    def _run(self):
        job = self._project.create.job.Lammps(self._name)
        job.structure = self._structure
        job.potential = self._potential
        self._job = job
        job.run()
        self.set_output_val(1, job)
        self.exec_output(0)

    def _remove(self):
        try:
            name = self._job.name  # Remove based on the run job, not the input name which might have changed...
            self._project.remove_job(name)
            self.set_output_val(1, None)
        except AttributeError:
            pass

    def _update_potential_choices(self):
        potl_input = self.inputs[5]
        last_potential = potl_input.val
        structure = self.inputs[4].val
        available_potentials = list_potentials(structure)

        if len(available_potentials) == 0:
            potl_input.val = "No valid potential"
            potl_input.dtype.items = ["No valid potential"]
        else:
            if last_potential not in available_potentials:
                potl_input.val = available_potentials[0]
            potl_input.dtype.items = available_potentials

    def update_event(self, inp=-1):
        if inp == 0:
            self._run()
        elif inp == 1:
            self._remove()
        elif inp == 4:
            self._update_potential_choices()

    @property
    def representations(self) -> dict:
        return {'job': BeautifulHasGroups(self.output(1))}


class GenericOutput_Node(NodeWithRepresentation):
    """Select Generic Output item"""

    version = "v0.1"
    title = "GenericOutput"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Data(size="m"), label="job"),
        NodeInputBP(
            dtype=dtypes.Choice(
                default="Input an atomistic job", items=["Input an atomistic job"]
            ),
            label="field",
        ),
    ]
    init_outputs = [
        NodeOutputBP(label="output"),
    ]
    color = "#c69a15"

    def __init__(self, params):
        super().__init__(params)

    @property
    def _job(self):
        return self.input(0)

    def _update_fields(self):
        if isinstance(self._job, AtomisticGenericJob):
            self.inputs[1].dtype.items = self._job["output/generic"].list_nodes()
            self.inputs[1].val = self.inputs[1].dtype.items[0]
        else:
            self.inputs[1].dtype.items = [self.init_inputs[1].dtype.default]
            # Note: It would be sensible to use `self.init_outputs[1].dtype.items` above, but this field gets updated
            # to `self.inputs[1].dtype.items`, probably because of the mutability of lists.
            self.inputs[1].val = self.init_inputs[1].dtype.default

    def _update_value(self):
        if isinstance(self._job, AtomisticGenericJob):
            val = self._job[f"output/generic/{self.input(1)}"]
        else:
            val = None
        self.set_output_val(0, val)

    def update_event(self, inp=-1):
        if inp == 0:
            self._update_fields()
            self._update_value()
        elif inp == 1:
            self._update_value()


class IntRand_Node(NodeWithRepresentation):
    """Generate a random number in a given range"""

    # this __doc__ string will be displayed as tooltip in the editor

    title = "IntRandom"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Integer(default=1, bounds=(10, 100)), label="high"),
        NodeInputBP(dtype=dtypes.Integer(default=1, bounds=(1, 100)), label="length"),
    ]
    init_outputs = [
        NodeOutputBP(label="randint"),
    ]
    color = "#aabb44"

    def update_event(self, inp=-1):
        val = np.random.randint(0, high=self.input(0), size=self.input(1))
        self.set_output_val(0, val)


class JobName_Node(NodeWithRepresentation):
    """Create job name for parameters"""

    title = "JobName"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Char(default="job_"), label="base"),
        NodeInputBP(dtype=dtypes.Float(default=0), label="float"),
    ]
    init_outputs = [
        NodeOutputBP(label="job name"),
    ]
    color = "#aabb44"

    def update_event(self, inp=-1):
        val = self.input(0) + f"{float(self.input(1))}".replace("-", "m").replace(
            ".", "p"
        )
        self.set_output_val(0, val)


class Linspace_Node(NodeWithRepresentation):
    """Generate a linear mesh in a given range using np.linspace"""

    # this __doc__ string will be displayed as tooltip in the editor

    title = "Linspace"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Integer(default=1, bounds=(0, 100)), label="min"),
        NodeInputBP(dtype=dtypes.Integer(default=2, bounds=(0, 100)), label="max"),
        NodeInputBP(dtype=dtypes.Integer(default=10, bounds=(1, 100)), label="steps"),
    ]
    init_outputs = [
        NodeOutputBP(label="linspace"),
    ]
    color = "#aabb44"

    def place_event(self):
        self.update()    

    def update_event(self, inp=-1):
        val = np.linspace(self.input(0), self.input(1), self.input(2))
        self.set_output_val(0, val)


class Plot3d_Node(NodeWithRepresentation):
    title = "Plot3d"
    version = "v0.1"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Data(size="m"), label="structure"),
    ]
    init_outputs = [
        NodeOutputBP(type_="data", label="plot3d"),
        NodeOutputBP(type_="data", label="structure"),
    ]
    color = "#5d95de"

    def update_event(self, inp=-1):
        self.set_output_val(0, self.input(0).plot3d())
        self.set_output_val(1, self.input(0))


class Matplot_Node(NodeWithRepresentation):
    title = "MatPlot"
    version = "v0.1"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Data(size="m"), label="x"),
        NodeInputBP(dtype=dtypes.Data(size="m"), label="y"),
    ]
    init_outputs = [
        NodeOutputBP(type_="data", label="fig"),
    ]
    color = "#5d95de"

    def update_event(self, inp=-1):
        super().update_event()
        plt.ioff()
        fig = plt.figure()
        plt.clf()
        plt.plot(self.input(0), self.input(1))
        self.set_output_val(0, fig)
        plt.ion()


class Sin_Node(NodeWithRepresentation):
    title = "Sin"
    version = "v0.1"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Data(size="m")),
    ]
    init_outputs = [
        NodeOutputBP(label="sin"),
    ]
    color = "#5d95de"

    def update_event(self, inp=-1):
        self.set_output_val(0, np.sin(self.input(0)))


class Result_Node(NodeBase):
    """Simply shows a value converted to str"""

    version = "v0.1"

    title = "Result"
    init_inputs = [
        NodeInputBP(type_="data"),
    ]
    color = "#c69a15"

    def __init__(self, params):
        super().__init__(params)
        self.val = None

    def place_event(self):
        self.update()

    def view_place_event(self):
        self.main_widget().show_val(self.val)

    def update_event(self, inp=-1):
        self.val = self.input(0)
        if self.session.gui:
            self.main_widget().show_val(self.val)


class ForEach_Node(NodeBase):
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
    color = '#b33a27'

    _count = 0

    def update_event(self, inp=-1):
        if inp == 0:
            self._count += 1
            if len(self.input(2)) > self._count:
                e = self.input(2)[self._count]
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


class Click_Node(NodeBase):
    title = "Click"
    version = "v0.1"
    main_widget_class = ButtonNodeWidget
    init_inputs = []
    init_outputs = [NodeOutputBP(type_="exec")]
    color = "#99dd55"

    def update_event(self, inp=-1):
        self.exec_output(0)


nodes = [
    Project_Node,
    BulkStructure_Node,
    Repeat_Node,
    ApplyStrain_Node,
    Lammps_Node,
    JobName_Node,
    GenericOutput_Node,
    Plot3d_Node,
    IntRand_Node,
    Linspace_Node,
    Sin_Node,
    Result_Node,
    ExecCounter_Node,
    Matplot_Node,
    Click_Node,
    ForEach_Node,
]
