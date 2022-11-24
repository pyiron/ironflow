# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Ryven nodes specifc to pyiron (or with ironflow improvements like an ipywidgets representation).
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import matplotlib.pylab as plt
import numpy as np
from matplotlib.figure import Figure
from nglview import NGLWidget
from pyiron_atomistics import Project, Atoms
from pyiron_atomistics.atomistics.structure.factory import StructureFactory
from pyiron_atomistics.atomistics.job.atomistic import AtomisticGenericJob
from pyiron_atomistics.lammps import list_potentials
from pyiron_atomistics.lammps.lammps import Lammps

from ironflow.gui.workflows.canvas_widgets.nodes import ButtonNodeWidget
from ironflow.model import dtypes, NodeInputBP
from ironflow.model.node import Node
from ironflow.model.port import NodeOutputBP
from ironflow.nodes.std.special_nodes import DualNodeBase

if TYPE_CHECKING:
    from pyiron_base import HasGroups

STRUCTURE_FACTORY = StructureFactory()


class BeautifulHasGroups:
    """
    A helper class for giving classes that inherit from `pyiron_base.HasGroups` a more appealing representation in
    ipywidgets.
    """

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


class Project_Node(Node):
    """
    Create a pyiron project.

    Inputs:
        name (str): The name of the project. Will access existing project data under that name. (Default is ".".)

    Outputs:
        project (pyiron_atomistics.Project): The project object.
    """

    # this __doc__ string will be displayed as tooltip in the editor

    title = "Project"
    init_inputs = [
        NodeInputBP(dtype=dtypes.String(default="."), label="name"),
    ]
    init_outputs = [
        NodeOutputBP(label="project", dtype=dtypes.Data(valid_classes=Project)),
    ]
    color = "#aabb44"

    def place_event(self):
        super().place_event()
        self.update()

    def update_event(self, inp=-1):
        pr = Project(self.inputs.values.name)
        self.set_output_val(0, pr)

    @property
    def extra_representations(self) -> dict:
        return {
            "name": str(self.inputs.values.name),
            # "job_table": self._project.job_table() if self._project is not None else None
            # Todo: Figure out how to display this without breaking the gui size; right now it automatically grows
            # the gui because the table is so wide.
        }


class OutputsOnlyAtoms(Node, ABC):
    """
    A helper class that manages representations for nodes whose only output is a `pyiron_atomistics.Atoms` object.

    Outputs:
        structure (pyiron_atomistics.Atoms): An atomic structure.
    """

    init_outputs = [
        NodeOutputBP(label="structure", dtype=dtypes.Data(valid_classes=Atoms)),
    ]
    color = "#aabb44"

    @abstractmethod
    def update_event(self, inp=-1):
        """Must set output 0 to an instance of pyiron_atomistics.atomistics.atoms.Atoms"""
        pass

    @property
    def extra_representations(self) -> dict:
        return {
            "plot3d": self.outputs.values.structure.plot3d(),
        }


class BulkStructure_Node(OutputsOnlyAtoms):
    """
    Generate a bulk atomic structure.

    Inputs:
        element (str): The atomic symbol for the desired atoms. (Default is "Fe".)
        crystal_structure (str | None): Must be one of sc, fcc, bcc, hcp, diamond, zincblende,
                                rocksalt, cesiumchloride, fluorite or wurtzite.
        a (float | None): Lattice constant.
        c (float | None): Lattice constant.
        c_over_a (float | None): c/a ratio used for hcp.  Default is ideal ratio: sqrt(8/3).
        u (float | None): Internal coordinate for Wurtzite structure.
        orthorhombic (bool): Construct orthorhombic unit cell instead of primitive cell. (Takes precedence over cubic
            flag when both are true.)
        cubic (bool): Construct cubic unit cell if possible.

    Outputs:
        structure (pyiron_atomistics.Atoms): A mono-species bulk structure.
    """

    # this __doc__ string will be displayed as tooltip in the editor

    title = "BulkStructure"
    init_inputs = [
        NodeInputBP(dtype=dtypes.String(default="Fe"), label="element"),
        NodeInputBP(
            dtype=dtypes.Choice(
                default=None,
                items=[
                    None,
                    "sc",
                    "fcc",
                    "bcc",
                    "hcp",
                    "diamond",
                    "zincblende",
                    "rocksalt",
                    "cesiumchloride",
                    "fluorite",
                    "wurtzite",
                ],
                allow_none=True,
            ),
            label="crystal_structure",
        ),
        NodeInputBP(dtype=dtypes.Float(default=None, allow_none=True), label="a"),
        NodeInputBP(dtype=dtypes.Float(default=None, allow_none=True), label="c"),
        NodeInputBP(
            dtype=dtypes.Float(default=None, allow_none=True), label="c_over_a"
        ),
        NodeInputBP(dtype=dtypes.Float(default=None, allow_none=True), label="u"),
        NodeInputBP(dtype=dtypes.Boolean(default=False), label="orthorhombic"),
        NodeInputBP(dtype=dtypes.Boolean(default=False), label="cubic"),
    ]

    def update_event(self, inp=-1):
        self.set_output_val(
            0,
            STRUCTURE_FACTORY.bulk(
                self.inputs.values.element,
                crystalstructure=self.inputs.values.crystal_structure,
                a=self.inputs.values.a,
                c=self.inputs.values.c,
                covera=self.inputs.values.c_over_a,
                u=self.inputs.values.u,
                orthorhombic=self.inputs.values.orthorhombic,
                cubic=self.inputs.values.cubic,
            ),
        )

    def place_event(self):
        super().place_event()
        self.update()


class Repeat_Node(OutputsOnlyAtoms):
    """
    Repeat atomic structure supercell.

    Inputs:
        structure (pyiron_atomistics.Atoms): The structure to repeat periodically.
        all (int): The number of times to repeat it in each of the three bravais lattice directions.

    Outputs:
        structure (pyiron_atomistics.Atoms): A repeated copy of the input structure.
    """

    # this __doc__ string will be displayed as tooltip in the editor

    title = "Repeat"
    init_inputs = [
        NodeInputBP(
            dtype=dtypes.Data(size="m", valid_classes=Atoms), label="structure"
        ),
        NodeInputBP(dtype=dtypes.Integer(default=1, bounds=(1, 100)), label="all"),
    ]

    def update_event(self, inp=-1):
        self.set_output_val(
            0, self.inputs.values.structure.repeat(self.inputs.values.all)
        )


class ApplyStrain_Node(OutputsOnlyAtoms):
    """
    Apply strain on atomic structure supercell.

    Inputs:
        structure (pyiron_atomistics.Atoms): The atomic structure to strain.
        strain (float): The isotropic strain to apply, where 0 is unstrained. (Default is 0.)

    Outputs:
        (pyiron_atomistics.Atoms): A strained copy of the input structure.
    """

    title = "ApplyStrain"
    init_inputs = [
        NodeInputBP(
            dtype=dtypes.Data(size="m", valid_classes=Atoms), label="structure"
        ),
        NodeInputBP(dtype=dtypes.Float(default=0, bounds=(-100, 100)), label="strain"),
    ]

    def update_event(self, inp=-1):
        self.set_output_val(
            0,
            self.inputs.values.structure.apply_strain(
                float(self.inputs.values.strain), return_box=True
            ),
        )


class Lammps_Node(Node):
    """
    WIP.
    """

    title = "Lammps"
    version = "v0.1"
    init_inputs = [
        NodeInputBP(type_="exec", label="run"),
        NodeInputBP(type_="exec", label="remove"),
        NodeInputBP(
            dtype=dtypes.Data(size="m", valid_classes=Project), label="project"
        ),
        NodeInputBP(dtype=dtypes.String(default="job"), label="name"),
        NodeInputBP(
            dtype=dtypes.Data(size="m", valid_classes=Atoms), label="structure"
        ),
        NodeInputBP(
            dtype=dtypes.Choice(
                default="Set structure first",
                items=["Set structure first"],
                valid_classes=str
            ),
            label="potential",
        ),
    ]
    init_outputs = [
        NodeOutputBP(type_="exec", label="ran"),
        NodeOutputBP(label="job", dtype=dtypes.Data(valid_classes=Lammps)),
    ]
    color = "#5d95de"

    def _run(self):
        job = self.inputs.values.project.create.job.Lammps(
            self.inputs.values.name,
            delete_existing_job=True
        )
        job.structure = self.inputs.values.structure
        job.potential = self.inputs.values.potential
        self._job = job
        job.run()
        self.set_output_val(1, job)
        self.exec_output(0)

    def _remove(self):
        try:
            name = (
                self._job.name
            )  # Remove based on the run job, not the input name which might have changed...
            self.inputs.values.project.remove_job(name)
            self.set_output_val(1, None)
        except AttributeError:
            pass

    def _update_potential_choices(self):
        last_potential = self.inputs.values.potential
        available_potentials = list_potentials(self.inputs.values.structure)

        if len(available_potentials) == 0:
            self.inputs.ports.potential.val = "No valid potential"
            self.inputs.ports.potential.dtype.items = ["No valid potential"]
        else:
            if last_potential not in available_potentials:
                self.inputs.ports.potential.val = available_potentials[0]
            self.inputs.ports.potential.dtype.items = available_potentials

    def update_event(self, inp=-1):
        if inp == 0 and self.all_input_is_valid:
            self._run()
        elif inp == 1:
            self._remove()
        elif inp == 4 and self.inputs.ports.structure.valid_val:
            self._update_potential_choices()

    @property
    def extra_representations(self) -> dict:
        return {"job": BeautifulHasGroups(self.outputs.values.job)}


class GenericOutput_Node(Node):
    """
    Select Generic Output item.

    Inputs:
        job (AtomisticGenericJob): A job with an `output` attribute of type
            `pyiron_atomistics.atomistics.job.atomistic.GenericOutput`.
        field (dtypes.Choice): Which output field to look at. Automatically populates once the job is valid.

    Outputs:
        output (numpy.ndarray): The selected output field.
    """

    version = "v0.1"
    title = "GenericOutput"
    init_inputs = [
        NodeInputBP(
            dtype=dtypes.Data(size="m", valid_classes=AtomisticGenericJob), label="job"
        ),
        NodeInputBP(
            dtype=dtypes.Choice(
                default="Input an atomistic job",
                items=["Input an atomistic job"],
                valid_classes=str
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

    def _update_fields(self):
        if isinstance(self.inputs.values.job, AtomisticGenericJob):
            self.inputs.ports.field.dtype.items = self.inputs.values.job[
                "output/generic"
            ].list_nodes()
            self.inputs.ports.field.val = self.inputs.ports.field.dtype.items[0]
        else:
            self.inputs.ports.field.dtype.items = [self.init_inputs[1].dtype.default]
            # Note: It would be sensible to use `self.init_outputs[1].dtype.items` above, but this field gets updated
            # to `self.inputs[1].dtype.items`, probably because of the mutability of lists.
            self.inputs.ports.field.val = self.init_inputs[1].dtype.default

    def _update_value(self):
        if isinstance(self.inputs.values.job, AtomisticGenericJob):
            val = self.inputs.values.job[f"output/generic/{self.inputs.values.field}"]
        else:
            val = None
        self.set_output_val(0, val)

    def update_event(self, inp=-1):
        if inp == 0:
            self._update_fields()
            self._update_value()
        elif inp == 1:
            self._update_value()


class IntRand_Node(Node):
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
        NodeInputBP(dtype=dtypes.Integer(default=1, bounds=(10, 100)), label="high"),
        NodeInputBP(dtype=dtypes.Integer(default=1, bounds=(1, 100)), label="length"),
    ]
    init_outputs = [
        NodeOutputBP(label="randint"),
    ]
    color = "#aabb44"

    def update_event(self, inp=-1):
        val = np.random.randint(
            0, high=self.inputs.values.high, size=self.inputs.values.length
        )
        self.set_output_val(0, val)


class JobName_Node(Node):
    """
    Create job name for parameters.

    Inputs:
        base (str): The stem for the final name. (Default is "job_".)
        float (float): The parameter value to add to the name.

    Outputs:
        job_name (str): The base plus float sanitized into a valid job name.

    Todo:
        There has been some work in pyiron_base on getting a cleaner job name sanitizer, so lean on that.
    """

    title = "JobName"
    init_inputs = [
        NodeInputBP(dtype=dtypes.String(default="job_"), label="base"),
        NodeInputBP(dtype=dtypes.Float(default=0.), label="float"),
    ]
    init_outputs = [
        NodeOutputBP(label="job_name", dtype=dtypes.String()),
    ]
    color = "#aabb44"

    def update_event(self, inp=-1):
        val = self.inputs.values.base + f"{float(self.inputs.values.float)}".replace(
            "-", "m"
        ).replace(".", "p")
        self.set_output_val(0, val)


class Linspace_Node(Node):
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
        NodeInputBP(dtype=dtypes.Integer(default=1, bounds=(0, 100)), label="min"),
        NodeInputBP(dtype=dtypes.Integer(default=2, bounds=(0, 100)), label="max"),
        NodeInputBP(dtype=dtypes.Integer(default=10, bounds=(1, 100)), label="steps"),
    ]
    init_outputs = [
        NodeOutputBP(label="linspace"),
    ]
    color = "#aabb44"

    def place_event(self):
        super().place_event()
        self.update()

    def update_event(self, inp=-1):
        val = np.linspace(
            self.inputs.values.min, self.inputs.values.max, self.inputs.values.steps
        )
        self.set_output_val(0, val)


class Plot3d_Node(Node):
    """
    Plot a structure with NGLView.

    Inputs:
        structure (pyiron_atomistics.Atoms): The structure to plot.

    Outputs:
        plot3d (nglview.widget.NGLWidget): The plot object.
        structure (pyiron_atomistics.Atoms): The raw structure object passed in.
    """

    title = "Plot3d"
    version = "v0.1"
    init_inputs = [
        NodeInputBP(
            dtype=dtypes.Data(size="m", valid_classes=Atoms), label="structure"
        ),
    ]
    init_outputs = [
        NodeOutputBP(
            type_="data", label="plot3d", dtype=dtypes.Data(valid_classes=NGLWidget)
        ),
        NodeOutputBP(
            type_="data", label="structure", dtype=dtypes.Data(valid_classes=Atoms)
        ),
    ]
    color = "#5d95de"

    def update_event(self, inp=-1):
        self.set_output_val(0, self.inputs.values.structure.plot3d())
        self.set_output_val(1, self.inputs.values.structure)


class Matplot_Node(Node):
    """
    A 2D matplotlib plot.

    Inputs:
        x (list|numpy.ndarray|...): Data for the x-axis.
        y (list|numpy.ndarray|...): Data for the y-axis.

    Outputs:
        fig (matplotlib.figure.Figure): The resulting figure after a `matplotlib.pyplot.plot` call on x and y.
    """

    title = "MatPlot"
    version = "v0.1"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Data(valid_classes=[list, np.ndarray]), label="x"),
        NodeInputBP(dtype=dtypes.Data(valid_classes=[list, np.ndarray]), label="y"),
    ]
    init_outputs = [
        NodeOutputBP(type_="data", label="fig", dtype=dtypes.Data(valid_classes=Figure))
    ]
    color = "#5d95de"

    def update_event(self, inp=-1):
        super().update_event()
        plt.ioff()
        fig = plt.figure()
        plt.clf()
        plt.plot(self.inputs.values.x, self.inputs.values.y)
        self.set_output_val(0, fig)
        plt.ion()


class Sin_Node(Node):
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
        NodeInputBP(
            dtype=dtypes.Data(size="m", valid_classes=[int, float, list, np.ndarray]),
            label="x"
        ),
    ]
    init_outputs = [
        NodeOutputBP(label="sin"),
    ]
    color = "#5d95de"

    def update_event(self, inp=-1):
        self.set_output_val(0, np.sin(self.inputs.values.x))


class Result_Node(Node):
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
        super().place_event()
        self.update()

    def view_place_event(self):
        self.main_widget().show_val(self.val)

    def update_event(self, inp=-1):
        self.val = self.inputs.data.val
        if self.session.gui:
            self.main_widget().show_val(self.val)


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
