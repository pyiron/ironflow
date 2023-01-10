# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Ryven nodes specific to pyiron (or with ironflow improvements like an ipywidgets
representation).
"""

from __future__ import annotations

import json
import pickle
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Type, TYPE_CHECKING

import matplotlib.pylab as plt
import numpy as np
import seaborn as sns
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from nglview import NGLWidget
from pandas import DataFrame
from ryvencore.InfoMsgs import InfoMsgs

import pyiron_base
from pyiron_atomistics import Project, Atoms
from pyiron_atomistics.atomistics.structure.factory import StructureFactory
from pyiron_atomistics.atomistics.job.atomistic import (
    AtomisticGenericJob,
    GenericOutput,
)
from pyiron_atomistics.lammps import list_potentials
from pyiron_atomistics.lammps.lammps import Lammps
from pyiron_atomistics.table.datamining import TableJob  # Triggers the function list
from pyiron_base.jobs.job.util import _get_safe_job_name

from ironflow.node_tools import (
    DataNode,
    dtypes,
    JobMaker,
    JobTaker,
    main_widgets,
    Node,
    NodeInputBP,
    NodeOutputBP,
    PortList,
)
from ironflow.nodes.std.special_nodes import DualNodeBase

if TYPE_CHECKING:
    from pyiron_base import HasGroups

STRUCTURE_FACTORY = StructureFactory()
NUMERIC_TYPES = [int, float, np.number]


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


class Project_Node(DataNode):
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

    def node_function(self, name, **kwargs) -> dict:
        return {"project": Project(name)}

    @property
    def extra_representations(self) -> dict:
        return {
            "name": str(self.inputs.values.name),
            **self.batched_representation(
                "job_table", self._job_table, self.outputs.values.project
            )
        }

    @staticmethod
    def _job_table(project: Project):
        return project.job_table(all_columns=False)


class JobTable_Node(Node):
    title = "JobTable"
    init_inputs = [
        NodeInputBP(type_="exec", label="refresh"),
        NodeInputBP(dtype=dtypes.Data(valid_classes=Project), label="project"),
    ]
    init_outputs = [NodeOutputBP(label="Table")]
    color = "#aabb44"

    def node_function(self, project, **kwargs) -> dict:
        return {"Table": self.outputs.values.project.job_table(all_columns=False)}


class OutputsOnlyAtoms(DataNode, ABC):
    """
    A helper class that manages representations for nodes whose only output is a `pyiron_atomistics.Atoms` object.

    Outputs:
        structure (pyiron_atomistics.Atoms): An atomic structure.
    """

    init_outputs = [
        NodeOutputBP(label="structure", dtype=dtypes.Data(valid_classes=Atoms)),
    ]
    color = "#aabb44"

    @property
    def extra_representations(self) -> dict:
        return {
            **self.batched_representation(
                "plot3d", self._plot3d, self.outputs.values.structure
            ),
        }

    @staticmethod
    def _plot3d(structure):
        return structure.plot3d()


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

    def node_function(
            self,
            element,
            crystal_structure,
            a,
            c,
            c_over_a,
            u,
            orthorhombic,
            cubic,
            **kwargs
    ) -> dict:
        return {
            "structure": STRUCTURE_FACTORY.bulk(
                element,
                crystalstructure=crystal_structure,
                a=a,
                c=c,
                covera=c_over_a,
                u=u,
                orthorhombic=orthorhombic,
                cubic=cubic
            )
        }


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
            dtype=dtypes.Data(valid_classes=Atoms), label="structure"
        ),
        NodeInputBP(dtype=dtypes.Integer(default=1, bounds=(1, 100)), label="all"),
    ]

    def node_function(self, structure, all, **kwargs) -> dict:
        return {"structure": structure.repeat(all)}


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
            dtype=dtypes.Data(valid_classes=Atoms), label="structure"
        ),
        NodeInputBP(dtype=dtypes.Float(default=0, bounds=(-100, 100)), label="strain"),
    ]

    def node_function(self, structure, strain, **kwargs) -> dict:
        return {"structure": structure.apply_strain(float(strain), return_box=True)}


class AtomisticTaker(JobTaker, ABC):

    valid_job_classes = [Lammps]
    init_outputs = JobTaker.init_outputs + [
        NodeOutputBP(
            dtype=dtypes.List(valid_classes=[float, np.floating]), label="energy_pot"
        ),
        NodeOutputBP(
            dtype=dtypes.List(valid_classes=[float, np.floating]), label="forces"
        ),
    ]

    def _get_output_from_job(self, finished_job: Lammps, **kwargs):
        return {
            "energy_pot": finished_job.output.energy_pot,
            "forces": finished_job.output.forces
        }

    @property
    def extra_representations(self) -> dict:
        return {
            **self.batched_representation(
                "job", BeautifulHasGroups, self.outputs.values.job
            ),
        }


class CalcStatic_Node(AtomisticTaker):
    """
    Execute a static atomistic engine evaluation.
    """

    title = "CalcStatic"

    def _modify_job(self, copied_job: Lammps, **kwargs) -> Lammps:
        copied_job.calc_static()
        return copied_job


def pressure_input():
    return NodeInputBP(
        dtype=dtypes.Data(
            default=None, allow_none=True, valid_classes=[float, list, np.ndarray]
        ),
        label="pressure",
    )


class CalcMinimize_Node(AtomisticTaker):
    """
    Execute a static atomistic engine evaluation.
    """

    title = "CalcMinimize"
    init_inputs = AtomisticTaker.init_inputs + [
        NodeInputBP(dtype=dtypes.Float(default=0.0), label="ionic_energy_tolerance"),
        NodeInputBP(dtype=dtypes.Float(default=1e-4), label="ionic_force_tolerance"),
        NodeInputBP(dtype=dtypes.Integer(default=100000), label="max_iter"),
        pressure_input(),
        NodeInputBP(dtype=dtypes.Integer(default=100), label="n_print"),
        NodeInputBP(dtype=dtypes.Choice(default="cg", items=["cg"]), label="style"),
    ]

    def _modify_job(
            self,
            copied_job: Lammps,
            ionic_energy_tolerance,
            ionic_force_tolerance,
            max_iter,
            pressure,
            n_print,
            style,
            **kwargs
    ) -> Lammps:
        copied_job.calc_minimize(
            ionic_energy_tolerance=ionic_energy_tolerance,
            ionic_force_tolerance=ionic_force_tolerance,
            max_iter=max_iter,
            pressure=pressure,
            n_print=n_print,
            style=style,
        )
        return copied_job


class CalcMD_Node(AtomisticTaker):
    """
    Execute a static atomistic engine evaluation.
    """

    title = "CalcMD"
    init_inputs = AtomisticTaker.init_inputs + [
        NodeInputBP(
            dtype=dtypes.Float(default=None, allow_none=True), label="temperature"
        ),
        pressure_input(),
        NodeInputBP(dtype=dtypes.Integer(default=1000), label="n_ionic_steps"),
        NodeInputBP(dtype=dtypes.Float(default=1.0), label="time_step"),
        NodeInputBP(dtype=dtypes.Integer(default=100), label="n_print"),
        NodeInputBP(
            dtype=dtypes.Float(default=100.0), label="temperature_damping_timescale"
        ),
        NodeInputBP(
            dtype=dtypes.Float(default=1000.0), label="pressure_damping_timescale"
        ),
        NodeInputBP(dtype=dtypes.Integer(default=None, allow_none=True), label="seed"),
        NodeInputBP(
            dtype=dtypes.Float(default=None, allow_none=True),
            label="initial_temperature",
        ),
        NodeInputBP(
            dtype=dtypes.Choice(default="langevin", items=["langevin", "nose-hoover"]),
            label="dynamics",
        ),
    ]

    def _modify_job(
            self,
            copied_job: Lammps,
            temperature,
            pressure,
            n_ionic_steps,
            time_step,
            n_print,
            temperature_damping_timescale,
            pressure_damping_timescale,
            seed,
            initial_temperature,
            dynamics,
            **kwargs
    ) -> Lammps:
        copied_job.calc_md(
            temperature=temperature,
            pressure=pressure,
            n_ionic_steps=n_ionic_steps,
            time_step=time_step,
            n_print=n_print,
            temperature_damping_timescale=temperature_damping_timescale,
            pressure_damping_timescale=pressure_damping_timescale,
            seed=seed,
            initial_temperature=initial_temperature,
            langevin=dynamics == "langevin",
        )
        return copied_job


class PyironTable_Node(JobMaker):
    title = "PyironTable"
    valid_job_classes = [pyiron_base.TableJob]

    init_inputs = list(JobMaker.init_inputs)
    n_fixed_input_cols = len(init_inputs)
    n_table_cols = 2  # TODO: allow user to change number of cols
    for n in np.arange(n_table_cols):
        init_inputs.append(
            NodeInputBP(
                dtype=dtypes.Choice(
                    default="get_job_name",
                    items=[
                        f.__name__ for f in pyiron_base.TableJob._system_function_lst
                    ],
                ),
                label=f"Col_{n + 1}",
            )
        )
    init_outputs = JobMaker.init_outputs + [
        NodeOutputBP(dtype=dtypes.Data(valid_classes=DataFrame), label="dataframe"),
    ]
    n_fixed_output_cols = len(init_outputs)
    for n in np.arange(n_table_cols):
        init_outputs.append(NodeOutputBP(label=f"Col_{n + 1}"))

    def _generate_job(self, name, project, **kwargs) -> pyiron_base.TableJob:
        job = project.base.job.TableJob(name)
        for n in np.arange(self.n_table_cols):
            getattr(job.add, self.inputs[n + self.n_fixed_input_cols].val)
        return job

    def _get_output_from_job(self, finished_job: pyiron_base.TableJob, **kwargs):
        df = finished_job.get_dataframe()
        return {
            f"Col_{n + 1}": df.iloc[:, n + 1].values for n in range(self.n_table_cols)
            # iloc n + 1 because somehow job_id is always a column, and we don't care
        }


class Engine(DataNode):
    """
    A parent class for engines (jobs).
    """

    color = "#5d95de"


class Lammps_Node(Engine):
    """
    Creates a Lammps engine (job) object for use by a calculator
    """

    title = "Lammps"
    version = "v0.2"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Data(valid_classes=Project), label="project"),
        NodeInputBP(dtype=dtypes.Data(valid_classes=Atoms), label="structure"),
        NodeInputBP(
            dtype=dtypes.Choice(
                default=None,
                items=["Set structure first"],
                valid_classes=str,
            ),
            label="potential",
        ),
    ]
    init_outputs = [
        NodeOutputBP(label="engine", dtype=dtypes.Data(valid_classes=Lammps)),
    ]

    def _get_potentials(self):
        # TODO: This is terribly inefficient for very large structures or long batches
        if self.inputs.ports.structure.dtype.batched:
            structure = self.inputs.values.structure[0].copy()
            for other in self.inputs.values.structure[1:]:
                structure += other
        else:
            structure = self.inputs.values.structure
        return list_potentials(structure)

    def _update_potential_choices(self):
        last_potential = self.inputs.values.potential
        available_potentials = self._get_potentials()

        if len(available_potentials) == 0:
            self.inputs.ports.potential.val = None
            self.inputs.ports.potential.dtype.items = ["No valid potential"]
        else:
            if last_potential not in available_potentials and \
                    len(self.inputs.ports.potential.connections) == 0:
                if self.inputs.ports.potential.dtype.batched:
                    self.inputs.ports.potential.val = available_potentials
                else:
                    self.inputs.ports.potential.val = available_potentials[0]
            self.inputs.ports.potential.dtype.items = available_potentials

    def update_event(self, inp=-1):
        if inp == 1 and self.inputs.ports.structure.valid_val:
            self._update_potential_choices()
        super().update_event(inp=inp)

    def node_function(self, project, structure, potential, **kwargs) -> dict:
        job = project.create.job.Lammps("_Lammps_Engine", delete_existing_job=True)
        job.structure = structure
        job.potential = potential
        return {"engine": job}

    @property
    def extra_representations(self) -> dict:
        return {
            **self.batched_representation(
                "job", BeautifulHasGroups, self.outputs.values.engine
            ),
        }


class LammpsPotentials_Node(DataNode):
    """
    Given a structure, returns the available compatible Lammps potential names.
    """

    title = "LammpsPotentials"
    color = "#aabb44"

    init_inputs = [
        NodeInputBP(dtype=dtypes.Data(valid_classes=Atoms), label="structure"),
    ]
    init_outputs = [
        NodeOutputBP(dtype=dtypes.List(valid_classes=str), label="potentials"),
    ]

    def node_function(self, structure, **kwargs) -> dict:
        return {
            "potentials": list_potentials(structure),
        }


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
        NodeInputBP(
            dtype=dtypes.List(valid_classes=object), label="array"
        ),
        NodeInputBP(dtype=dtypes.Integer(default=None, allow_none=True), label="i"),
        NodeInputBP(dtype=dtypes.Integer(default=None, allow_none=True), label="j"),
    ]
    init_outputs = [
        NodeOutputBP(label="sliced", dtype=dtypes.List(valid_classes=object)),
    ]
    color = "#aabb44"

    def node_function(self, array, i, j, **kwargs) -> dict:
        converted = np.array(array)
        if i is None and j is None:
            sliced = converted
        elif i is not None and j is None:
            sliced = converted[i:]
        elif i is None and j is not None:
            sliced = converted[:j]
        else:
            sliced = converted[i:j]
        return {'sliced': sliced}


class AtomisticOutput_Node(DataNode):
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
    title = "AtomisticOutput"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Data(valid_classes=AtomisticGenericJob), label="job"),
        NodeInputBP(
            dtype=dtypes.Choice(
                default="steps",
                items={
                    k for k in GenericOutput.__dict__.keys() if not k.startswith("__")
                },
                valid_classes=str,
            ),
            label="field",
        ),
    ]
    init_outputs = [
        NodeOutputBP(
            dtype=dtypes.List(valid_classes=[int, float, np.number]), label="output"
        ),
    ]
    color = "#c69a15"

    def node_function(self, job, field, **kwargs) -> dict:
        return {
            "output": job[f"output/generic/{field}"]
        }


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


class JobName_Node(DataNode):
    """
    Create a sanitized job name, optionally with a floating point parameter.

    Inputs:
        name_base (str): The stem for the final name. (Default is "job".)
        parameter (float|None): The parameter value to add to the name.
        ndigits (int|None): How many digits to keep from floating point values.
            (Default 8. Use None to not round at all.)
        special_symbols (dict|None): Not documented, sorry. (Default is None.)

    Outputs:
        job_name (str): The base plus float sanitized into a valid job name.
    """

    title = "JobName"
    init_inputs = [
        NodeInputBP(dtype=dtypes.String(default="job"), label="name_base"),
        NodeInputBP(
            dtype=dtypes.Float(default=None, allow_none=True), label="parameter"
        ),
        NodeInputBP(dtype=dtypes.Integer(default=8, allow_none=True), label="ndigits"),
        NodeInputBP(
            dtype=dtypes.Data(
                default=None,
                valid_classes=dict,
                allow_none=True),
            label="special_symbols"
        ),
    ]
    init_outputs = [
        NodeOutputBP(label="job_name", dtype=dtypes.String()),
    ]
    color = "#aabb44"

    def node_function(self, name_base, parameter, ndigits, special_symbols, **kwargs):
        name = (name_base, parameter) if parameter is not None else name_base
        return {
            "job_name": _get_safe_job_name(
                name,
                ndigits=ndigits,
                special_symbols=special_symbols
            )
        }


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
        return {'linspace': np.linspace(min, max, steps)}


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
            dtype=dtypes.Data(valid_classes=Atoms), label="structure"
        ),
    ]
    init_outputs = [
        NodeOutputBP(dtype=dtypes.Data(valid_classes=NGLWidget), label="plot3d"),
        NodeOutputBP(dtype=dtypes.Data(valid_classes=Atoms), label="structure"),
    ]
    color = "#5d95de"

    def update_event(self, inp=-1):
        self.set_output_val(0, self.inputs.values.structure.plot3d())
        self.set_output_val(1, self.inputs.values.structure)


class Matplot_Node(Node):
    """
    A 2D matplotlib plot.

    Inputs:
        x (list | numpy.ndarray): Data for the x-axis.
        y (list | numpy.ndarray): Data for the y-axis.
        fig (Figure | None): The figure to plot to.
        marker (matplotlib marker choice | None): Marker style.
        linestyle (matplotlib linestyle choice | None): Line style.
        color (str): HTML or hex color name.
        alpha (float): Transparency.
        label (str | None): Legend.
        xlabel (str | None): X-axis label.
        ylabel (str | None): Y-axis label.
        title (str | None): Figure title.
        legend (bool): Whether to add the legend.
        tight_layout (bool): Call matplotlib `tight_layout` command.

    Outputs:
        fig (matplotlib.figure.Figure): The resulting figure after a
        `matplotlib.pyplot.plot` call on x and y.
    """

    title = "MatPlot"
    version = "v0.1"
    init_inputs = [
        NodeInputBP(
            dtype=dtypes.List(valid_classes=object, default=None, allow_none=True),
            label="x"
        ),
        NodeInputBP(
            dtype=dtypes.List(valid_classes=object, default=None, allow_none=True),
            label="y"
        ),
        NodeInputBP(
            dtype=dtypes.Data(valid_classes=Figure, allow_none=True), label="fig"
        ),
        NodeInputBP(
            dtype=dtypes.Choice(
                default="o",
                items=[
                    "none",
                    ".",
                    ",",
                    "o",
                    "v",
                    "^",
                    "<",
                    ">",
                    "1",
                    "2",
                    "3",
                    "4",
                    "8",
                    "s",
                    "p",
                    "P",
                    "*",
                    "h",
                    "H",
                    "+",
                    "x",
                    "X",
                    "d",
                    "D",
                    "|",
                    "_",
                ],
            ),
            label="marker",
        ),
        NodeInputBP(
            dtype=dtypes.Choice(
                default="none",
                items=["none", "solid", "dotted", "dashed", "dashdot"],
            ),
            label="linestyle",
        ),
        NodeInputBP(dtype=dtypes.String(default=None, allow_none=True), label="color"),
        NodeInputBP(dtype=dtypes.Float(default=1.0, bounds=(0.0, 1.0)), label="alpha"),
        NodeInputBP(dtype=dtypes.String(default=None, allow_none=True), label="label"),
        NodeInputBP(dtype=dtypes.String(default=None, allow_none=True), label="xlabel"),
        NodeInputBP(dtype=dtypes.String(default=None, allow_none=True), label="ylabel"),
        NodeInputBP(dtype=dtypes.String(default=None, allow_none=True), label="title"),
        NodeInputBP(dtype=dtypes.Boolean(default=False), label="legend"),
        NodeInputBP(dtype=dtypes.Boolean(default=True), label="tight_layout"),
    ]
    init_outputs = [
        NodeOutputBP(dtype=dtypes.Data(valid_classes=Figure), label="fig"),
    ]
    color = "#5d95de"

    def update_event(self, inp=-1):
        super().update_event()
        plt.ioff()
        if self.all_input_is_valid:
            try:
                if self.inputs.values.fig is None:
                    fig, ax = plt.subplots()
                else:
                    fig, ax = self.deepcopy_matplot(self.inputs.values.fig)
                ax.plot(
                    self.inputs.values.x,
                    self.inputs.values.y,
                    marker=self.inputs.values.marker,
                    linestyle=self.inputs.values.linestyle,
                    color=self.inputs.values.color,
                    alpha=self.inputs.values.alpha,
                    label=self.inputs.values.label,
                )
                if self.inputs.values.xlabel is not None:
                    ax.set_xlabel(self.inputs.values.xlabel)
                if self.inputs.values.ylabel is not None:
                    ax.set_ylabel(self.inputs.values.ylabel)
                if self.inputs.values.title is not None:
                    ax.set_title(self.inputs.values.title)
                if self.inputs.values.legend:
                    fig.legend()
                if self.inputs.values.tight_layout:
                    fig.tight_layout()
                self.set_output_val(0, fig)
                plt.ion()
            except Exception as e:
                self.set_all_outputs_to_none()
                plt.ion()
                raise e

    @staticmethod
    def deepcopy_matplot(fig: Figure) -> tuple[Figure, Axes]:
        # Courtesty of StackOverflow @ImportanceOfBeingErnest
        # https://stackoverflow.com/questions/45810557/pyplot-copy-an-axes-content-and-show-it-in-a-new-figure
        buf = BytesIO()
        pickle.dump(fig, buf)
        buf.seek(0)
        fig_copy = pickle.load(buf)
        return fig_copy, fig_copy.axes[0]


_seaborn_method_map = {
        "scatter": sns.scatterplot,
        "hist": sns.histplot,
        "joint": sns.jointplot,
    }


class QuickPlot_Node(Node):
    """
    Make a variety of quick and dirty plots with Seaborn.
    """

    title = "QuickPlot"
    color = "#5d95de"

    init_inputs = [
        NodeInputBP(
            dtype=dtypes.List(valid_classes=NUMERIC_TYPES, default=None, allow_none=True),
            label="x"
        ),
        NodeInputBP(
            dtype=dtypes.List(valid_classes=NUMERIC_TYPES, default=None, allow_none=True),
            label="y"
        ),
        NodeInputBP(
            dtype=dtypes.Choice(
                default="scatter",
                items=list(_seaborn_method_map.keys()),
            ),
            label="type"
        )
    ]
    init_outputs = [
        NodeOutputBP(label="plot")
    ]

    def update_event(self, inp=-1):
        super().update_event()
        plt.ioff()
        if self.all_input_is_valid:
            try:
                plt.clf()
                plot_function = _seaborn_method_map[self.inputs.values.type]
                out = plot_function(x=self.inputs.values.x, y=self.inputs.values.y)
                self.set_output_val(0, out.figure)
                plt.ion()
            except Exception as e:
                self.set_all_outputs_to_none()
                plt.ion()
                raise e


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
    main_widget_class = main_widgets.ButtonNodeWidget
    init_inputs = []
    init_outputs = [NodeOutputBP(type_="exec")]
    color = "#99dd55"

    def update_event(self, inp=-1):
        self.exec_output(0)


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
        return {'transposed': np.array(array).T}


nodes = [
    Project_Node,
    BulkStructure_Node,
    Repeat_Node,
    ApplyStrain_Node,
    Lammps_Node,
    JobName_Node,
    AtomisticOutput_Node,
    Plot3d_Node,
    IntRand_Node,
    Linspace_Node,
    Sin_Node,
    ExecCounter_Node,
    Matplot_Node,
    Click_Node,
    ForEach_Node,
    Transpose_Node,
    Slice_Node,
]
