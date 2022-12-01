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
from typing import TYPE_CHECKING

import matplotlib.pylab as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from nglview import NGLWidget
from pandas import DataFrame
from ryvencore.InfoMsgs import InfoMsgs

import pyiron_base
from pyiron_atomistics import Project, Atoms
from pyiron_atomistics.atomistics.structure.factory import StructureFactory
from pyiron_atomistics.atomistics.job.atomistic import AtomisticGenericJob
from pyiron_atomistics.lammps import list_potentials
from pyiron_atomistics.lammps.lammps import Lammps
from pyiron_atomistics.table.datamining import TableJob  # Triggers the function list

from ironflow.node_tools import dtypes, main_widgets, Node, NodeInputBP, NodeOutputBP
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
            "job_table": self.outputs.values.project.job_table(all_columns=False)
        }


class JobTable_Node(Node):
    title = "JobTable"
    init_inputs = [
        NodeInputBP(type_="exec", label="refresh"),
        NodeInputBP(dtype=dtypes.Data(valid_classes=Project), label="project")
    ]
    init_outputs = [
       NodeOutputBP(label="Table")
    ]
    color = "#aabb44"

    def update_event(self, inp=-1):
        if self.inputs.ports.project.valid_val:
            self.set_output_val(
                0,
                self.inputs.values.project.job_table(all_columns=False)
            )


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
        try:
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
        except RuntimeError as e:
            self.set_output_val(0, None)
            raise e

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


class JobRunner(Node, ABC):
    """
    A parent class for nodes that run a pyiron job.

    Child classes are required to specify a `_generate_job` method, which produces
    a `pyiron_base.GenericJob` object, and a `_run` method which can access this job
    at the `.job` attribute, in addition to whatever input is necessary to accomplish
    this. They can optionally override the `_set_output` method, which by default
    assumes there is an output field labeled `"job"` and sends the executed job there.

    The node has `run` and `remove` input exec ports and a `ran` output exec port.
    Once the node has been run, all inputs get locked and remain locked until the
    removal process is triggered. Remove clears all the outputs and sets them to `None`.

    The tricky thing is that we can't easily pre-define the available inputs *and* have
    them be sufficiently detailed in their dtype without running into awkwardness, so
    assumptions get made about what IO fields are available, and these assumptions
    must be satisfied by child classes.
    """

    color = "#c4473f"
    init_inputs = [
        NodeInputBP(type_="exec", label="run"),
        NodeInputBP(type_="exec", label="remove"),
        NodeInputBP(dtype=dtypes.String(default="calc"), label="name")
    ]
    init_outputs = [
        NodeOutputBP(type_="exec", label="ran"),
    ]

    @property
    def job(self):
        try:
            return self._job
        except AttributeError:
            return None

    def update_event(self, inp=-1):
        if inp == 0 and (not self.block_updates) and self.all_input_is_valid:
            self._on_run_signal()

    def update(self, inp=-1):
        if inp == 1:
            # Bypass the `lock_updates` to delete the executed job and unlock updates
            self._on_remove_signal()
        else:
            super().update(inp=inp)

    def _on_run_signal(self):
        self.block_updates = True
        self._job = self._raise_error_if_not_initialized(self._generate_job())
        self._run()
        self._set_output()
        self.exec_output(0)

    def _on_remove_signal(self):
        try:
            self.job.remove()
        except AttributeError:
            InfoMsgs.write("No attribute job, no job removed")
        for i in range(1, len(self.outputs)):
            self.set_output_val(i, None)
        self.block_updates = False
        self.update(-1)

    def _raise_error_if_not_initialized(
            self, job: pyiron_base.GenericJob
    ) -> pyiron_base.GenericJob:
        if job.status == "initialized":
            return job
        else:
            self.block_updates = False
            raise RuntimeError(
                f"The job {self.inputs.values.name} already exists. Delete it first or"
                f"choose a different name."
            )

    @abstractmethod
    def _generate_job(self) -> pyiron_base.GenericJob:
        """
        Return the job to be executed.

        Should use the `self.inputs.values.name` job name and whatever other input is
        necessary and specified in child classes.
        """

        pass

    @abstractmethod
    def _run(self):
        """
        Manipulates `self.job` and adds anything necessary to the output beyond the job
        itself
        """

        pass

    def _set_output(self):
        """
        With the executed `self.job` available, set output fields.
        """

        self.set_output_val(1, self.job)


class TakesJob(JobRunner):
    """
    Parent class for job running nodes that take the job as input and copy it.

    Assumes that this job is input with the label `"job"` and the appropriate dtype.
    """

    def _generate_job(self):
        return self.inputs.values.job.copy_to(
            new_job_name=self.inputs.values.name,
            delete_existing_job=False  # TODO: Make this input?
        )


class MakesJob(JobRunner):
    """
    Parent class for job running nodes that take the project as input and generate a
    new job from scratch.

    Project input should be used in `_generate_job` to produce a job of the correct
    type.
    """

    init_inputs = JobRunner.init_inputs + [
        NodeInputBP(dtype=dtypes.Data(valid_classes=Project), label="project")
    ]


class CalcStatic_Node(TakesJob):
    """
    Execute a static atomistic engine evaluation.
    """

    title = "CalcStatic"
    init_inputs = TakesJob.init_inputs + [
        NodeInputBP(dtype=dtypes.Data(valid_classes=[Lammps]), label="job")
    ]
    init_outputs = TakesJob.init_outputs + [
        NodeOutputBP(dtype=dtypes.Data(valid_classes=[Lammps]), label="job")
    ]

    def _run(self):
        self.job.run()

    @property
    def extra_representations(self) -> dict:
        return {"job": BeautifulHasGroups(self.outputs.values.job)}


def pressure_input():
    return NodeInputBP(
            dtype=dtypes.Data(
                default=None, allow_none=True, valid_classes=[float, list, np.ndarray]
            ),
            label="pressure"
        )


class CalcMinimize_Node(TakesJob):
    """
    Execute a static atomistic engine evaluation.
    """

    title = "CalcMinimize"
    init_inputs = TakesJob.init_inputs + [
        NodeInputBP(dtype=dtypes.Data(valid_classes=[Lammps]), label="job"),
        NodeInputBP(dtype=dtypes.Float(default=0.), label="ionic_energy_tolerance"),
        NodeInputBP(dtype=dtypes.Float(default=1e-4), label="ionic_force_tolerance"),
        NodeInputBP(dtype=dtypes.Integer(default=100000), label="max_iter"),
        pressure_input(),
        NodeInputBP(dtype=dtypes.Integer(default=100), label="n_print"),
        NodeInputBP(dtype=dtypes.Choice(default="cg", items=["cg"]), label="style"),
    ]
    init_outputs = TakesJob.init_outputs + [
        NodeOutputBP(dtype=dtypes.Data(valid_classes=[Lammps]), label="job"),
    ]

    def _run(self):
        self.job.calc_minimize(
            ionic_energy_tolerance=self.inputs.values.ionic_energy_tolerance,
            ionic_force_tolerance=self.inputs.values.ionic_force_tolerance,
            max_iter=self.inputs.values.max_iter,
            pressure=self.inputs.values.pressure,
            n_print=self.inputs.values.n_print,
            style=self.inputs.values.style,
        )
        self.job.run()

    @property
    def extra_representations(self) -> dict:
        return {"job": BeautifulHasGroups(self.outputs.values.job)}


class CalcMD_Node(TakesJob):
    """
    Execute a static atomistic engine evaluation.
    """

    title = "CalcMD"
    init_inputs = TakesJob.init_inputs + [
        NodeInputBP(dtype=dtypes.Data(valid_classes=[Lammps]), label="job"),
        NodeInputBP(
            dtype=dtypes.Float(default=None, allow_none=True), label="temperature"
        ),
        pressure_input(),
        NodeInputBP(dtype=dtypes.Integer(default=1000), label="n_ionic_steps"),
        NodeInputBP(dtype=dtypes.Float(default=1.), label="time_step"),
        NodeInputBP(dtype=dtypes.Integer(default=100), label="n_print"),
        NodeInputBP(
            dtype=dtypes.Float(default=100.), label="temperature_damping_timescale"
        ),
        NodeInputBP(
            dtype=dtypes.Float(default=1000.), label="pressure_damping_timescale"
        ),
        NodeInputBP(dtype=dtypes.Integer(default=None, allow_none=True), label="seed"),
        NodeInputBP(
            dtype=dtypes.Float(default=None, allow_none=True),
            label="initial_temperature"
        ),
        NodeInputBP(
            dtype=dtypes.Choice(default="langevin", items=["langevin", "nose-hoover"]),
            label="dynamics"
        ),
    ]
    init_outputs = TakesJob.init_outputs + [
        NodeOutputBP(dtype=dtypes.Data(valid_classes=[Lammps]), label="job")
    ]

    def _run(self):
        self.job.calc_md(
            temperature=self.inputs.values.temperature,
            pressure=self.inputs.values.pressure,
            n_ionic_steps=self.inputs.values.n_ionic_steps,
            time_step=self.inputs.values.time_step,
            n_print=self.inputs.values.n_print,
            temperature_damping_timescale=self.inputs.values.temperature_damping_timescale,
            pressure_damping_timescale=self.inputs.values.pressure_damping_timescale,
            seed=self.inputs.values.seed,
            initial_temperature=self.inputs.values.initial_temperature,
            langevin=self.inputs.values.dynamics == "langevin",
        )
        self.job.run()

    @property
    def extra_representations(self) -> dict:
        return {"job": BeautifulHasGroups(self.outputs.values.job)}


class PyironTable_Node(MakesJob):
    title = "PyironTable"

    init_inputs = list(MakesJob.init_inputs)
    n_fixed_input_cols = len(init_inputs)
    n_table_cols = 2  # TODO: allow user to change number of cols
    for n in np.arange(n_table_cols):
        init_inputs.append(
            NodeInputBP(
                dtype=dtypes.Choice(
                    default="get_job_name",
                    items=[
                        f.__name__ for f in pyiron_base.TableJob._system_function_lst
                    ]
                ),
                label=f"Col_{n + 1}"
            )
        )
    init_outputs = MakesJob.init_outputs + [
        NodeOutputBP(
            dtype=dtypes.Data(valid_classes=pyiron_base.TableJob), label="job"
        ),
        NodeOutputBP(dtype=dtypes.Data(valid_classes=DataFrame), label="dataframe")
    ]
    n_fixed_output_cols = len(init_outputs)
    for n in np.arange(n_table_cols):
        init_outputs.append(NodeOutputBP(label=f"Col_{n + 1}"))

    def _generate_job(self) -> pyiron_base.TableJob:
        return self.inputs.values.project.base.job.TableJob(self.inputs.values.name)

    def _run(self):
        for n in np.arange(self.n_table_cols):
            getattr(self.job.add, self.inputs[n + self.n_fixed_input_cols].val)
        self.job.run()

    def _set_output(self):
        super()._set_output()
        df = self.job.get_dataframe()
        self.set_output_val(2, df)
        for n in range(self.n_table_cols):
            self.set_output_val(n + self.n_fixed_output_cols, df.iloc[:, n + 1].values)
            # n + 1 because somehow job_id is always a column, and we don't care


class Engine(Node):
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

    def _update_potential_choices(self):
        last_potential = self.inputs.values.potential
        available_potentials = list_potentials(self.inputs.values.structure)

        if len(available_potentials) == 0:
            self.inputs.ports.potential.val = None
            self.inputs.ports.potential.dtype.items = ["No valid potential"]
        else:
            if last_potential not in available_potentials:
                self.inputs.ports.potential.val = available_potentials[0]
            self.inputs.ports.potential.dtype.items = available_potentials

    def update_event(self, inp=-1):
        if inp == 1 and self.inputs.ports.structure.valid_val:
            self._update_potential_choices()
        if self.all_input_is_valid:
            job = self.inputs.values.project.create.job.Lammps(
                "_Lammps_Engine", delete_existing_job=True
            )
            job.structure = self.inputs.values.structure
            job.potential = self.inputs.values.potential
            self.set_output_val(0, job)

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
                valid_classes=str,
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
        NodeInputBP(dtype=dtypes.Float(default=0.0), label="float"),
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
        NodeInputBP(dtype=dtypes.Float(default=1.), label="min"),
        NodeInputBP(dtype=dtypes.Float(default=2.), label="max"),
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
        NodeInputBP(dtype=dtypes.Data(valid_classes=[list, np.ndarray]), label="x"),
        NodeInputBP(dtype=dtypes.Data(valid_classes=[list, np.ndarray]), label="y"),
        NodeInputBP(
            dtype=dtypes.Data(valid_classes=Figure, allow_none=True), label="fig"
        ),
        NodeInputBP(
            dtype=dtypes.Choice(
                default="o",
                items=[
                    "none", ".", ",", "o", "v", "^", "<", ">", "1", "2", "3", "4", "8",
                    "s", "p", "P", "*", "h", "H", "+", "x", "X", "d", "D", "|", "_"
                ],
            ),
            label="marker"
        ),
        NodeInputBP(
            dtype=dtypes.Choice(
                default="none",
                items=["none", "solid", "dotted", "dashed", "dashdot"],
            ),
            label="linestyle"
        ),
        NodeInputBP(dtype=dtypes.String(default=None, allow_none=True), label="color"),
        NodeInputBP(dtype=dtypes.Float(default=1.0, bounds=(0., 1.)), label="alpha"),
        NodeInputBP(dtype=dtypes.String(default=None, allow_none=True), label="label"),
        NodeInputBP(dtype=dtypes.String(default=None, allow_none=True), label="xlabel"),
        NodeInputBP(dtype=dtypes.String(default=None, allow_none=True), label="ylabel"),
        NodeInputBP(dtype=dtypes.String(default=None, allow_none=True), label="title"),
        NodeInputBP(dtype=dtypes.Boolean(default=False), label="legend"),
        NodeInputBP(dtype=dtypes.Boolean(default=True), label="tight_layout"),
    ]
    init_outputs = [
        NodeOutputBP(
            type_="data", label="fig", dtype=dtypes.Data(valid_classes=Figure)
        ),
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

    def deepcopy_matplot(self, fig: Figure) -> tuple[Figure, Axes]:
        # Courtesty of StackOverflow @ImportanceOfBeingErnest
        # https://stackoverflow.com/questions/45810557/pyplot-copy-an-axes-content-and-show-it-in-a-new-figure
        buf = BytesIO()
        pickle.dump(fig, buf)
        buf.seek(0)
        fig_copy = pickle.load(buf)
        return fig_copy, fig_copy.axes[0]


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
            label="x",
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
    main_widget_class = main_widgets.ButtonNodeWidget
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
