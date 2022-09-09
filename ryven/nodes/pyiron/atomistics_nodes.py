# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

import matplotlib.pylab as plt
import numpy as np
from pyiron_atomistics import Project
from ryven.NENV import Node, NodeInputBP, NodeOutputBP, dtypes

from abc import ABC, abstractmethod
from ryven.nodes.std.special_nodes import DualNodeBase


__author__ = "Joerg Neugebauer"
__copyright__ = (
    "Copyright 2020, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Liam Huber"
__email__ = "liamhuber@greyhavensolutions.com"
__status__ = "production"
__date__ = "May 10, 2022"


class NodeBase(Node):
    color = "#ff69b4"  # Add an abrasive default color -- won't crash if you forget to add one, but pops out a bit

    def __init__(self, params):
        super().__init__(params)

    # here we could add some stuff for all nodes below...


class NodeWithDisplay(NodeBase, ABC):
    main_widget_class = "DisplayableNodeWidget"

    def __init__(self, params):
        super().__init__(params)
        self._representation = None
        self.representation_updated = False
        self.displayed = False

    def update_event(self, inp=-1):
        self.representation_updated = True

    @property
    def representations(self) -> tuple:
        return tuple(o.val for o in self.outputs)

    def output(self, i):
        return self.outputs[i].val


class Project_Node(NodeWithDisplay):
    """Create a pyiron project node"""

    # this __doc__ string will be displayed as tooltip in the editor

    title = "Project"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Char(default="."), label="name"),
    ]
    init_outputs = [
        NodeOutputBP(),
    ]
    color = "#aabb44"

    def place_event(self):
        self.update()

    def update_event(self, inp=-1):
        super().update_event(inp=inp)
        pr = Project(self.input(0))
        self.set_output_val(0, pr)

    @property
    def representations(self) -> tuple:
        return str(self.input(0)),


class OutputsOnlyAtoms(NodeWithDisplay, ABC):
    init_outputs = [
        NodeOutputBP(),
    ]
    color = "#aabb44"

    @abstractmethod
    def update_event(self, inp=-1):
        """Must set output 0 to an instance of pyiron_atomistics.atomistics.atoms.Atoms"""
        super().update_event(inp=inp)

    @property
    def representations(self) -> tuple:
        return self.output(0).plot3d(), self.output(0)


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
        super().update_event(inp=inp)
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
        super().update_event(inp=inp)
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
        super().update_event(inp=inp)
        self.set_output_val(0, self.input(0).apply_strain(float(self.input(1)), return_box=True))


class Lammps_Node(NodeWithDisplay):
    title = "Lammps"
    version = "v0.1"
    init_inputs = [
        NodeInputBP(type_="exec", label="run"),
        NodeInputBP(dtype=dtypes.Data(size="m"), label="project"),
        NodeInputBP(dtype=dtypes.Char(default="job"), label="name"),
        NodeInputBP(dtype=dtypes.Data(size="m"), label="structure"),
        NodeInputBP(dtype=dtypes.Char(default="Al_Mg_Mendelev_eam"), label="potential"),
    ]
    init_outputs = [
        NodeOutputBP(type_="exec"),
        NodeOutputBP(),
    ]
    color = "#5d95de"

    def _run(self):
        pr = self.input(1)
        job = pr.create.job.Lammps(self.input(2))
        job.structure = self.input(3)
        job.potential = self.input(4)
        self._job = job
        job.run()
        self.set_output_val(1, job)
        self.exec_output(0)

    def update_event(self, inp=-1):
        if inp == 0:
            self._run()

    @property
    def representations(self) -> tuple:
        return self.output(1),


class GenericOutput_Node(NodeWithDisplay):
    """Select Generic Output item"""

    version = "v0.1"

    title = "GenericOutput"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Data(size="m"), label="job"),
        NodeInputBP(
            dtype=dtypes.Choice(
                default="energy_tot", items=["energy_tot", "energy_pot"]
            ),
            label="Var",
        ),
    ]
    init_outputs = [
        NodeOutputBP(),
    ]

    # main_widget_class = widgets.Result_Node_MainWidget
    # main_widget_pos = 'between ports'
    color = "#c69a15"

    def __init__(self, params):
        super().__init__(params)

    def update_event(self, inp=-1):
        super().update_event(inp=inp)
        self.inputs[1].dtype.items = self.input(0)["output/generic"].list_nodes()
        val = self.input(0)[f"output/generic/{self.input(1)}"]
        self.set_output_val(0, val)


class IntRand_Node(NodeWithDisplay):
    """Generate a random number in a given range"""

    # this __doc__ string will be displayed as tooltip in the editor

    title = "IntRandom"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Integer(default=1, bounds=(10, 100)), label="high"),
        NodeInputBP(dtype=dtypes.Integer(default=1, bounds=(1, 100)), label="length"),
    ]
    init_outputs = [
        NodeOutputBP(),
    ]
    color = "#aabb44"

    def update_event(self, inp=-1):
        super().update_event(inp=inp)
        val = np.random.randint(0, high=self.input(0), size=self.input(1))
        self.set_output_val(0, val)


class JobName_Node(NodeWithDisplay):
    """Create job name for parameters"""

    title = "JobName"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Char(default="job_"), label="base"),
        NodeInputBP(dtype=dtypes.Float(default=0), label="float"),
    ]
    init_outputs = [
        NodeOutputBP(),
    ]
    color = "#aabb44"

    def update_event(self, inp=-1):
        super().update_event(inp=inp)
        val = self.input(0) + f"{float(self.input(1))}".replace("-", "m").replace(
            ".", "p"
        )
        self.set_output_val(0, val)


class Linspace_Node(NodeWithDisplay):
    """Generate a linear mesh in a given range using np.linspace"""

    # this __doc__ string will be displayed as tooltip in the editor

    title = "Linspace"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Integer(default=1, bounds=(0, 100)), label="min"),
        NodeInputBP(dtype=dtypes.Integer(default=2, bounds=(0, 100)), label="max"),
        NodeInputBP(dtype=dtypes.Integer(default=10, bounds=(1, 100)), label="steps"),
    ]
    init_outputs = [
        NodeOutputBP(),
    ]
    color = "#aabb44"

    def place_event(self):
        self.update()    

    def update_event(self, inp=-1):
        super().update_event(inp=inp)
        val = np.linspace(self.input(0), self.input(1), self.input(2))
        # val = 10
        self.set_output_val(0, val)


class Plot3d_Node(NodeWithDisplay):
    title = "Plot3d"
    version = "v0.1"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Data(size="m"), label="structure"),
        NodeInputBP(dtype=dtypes.Boolean(default=False), label="print")
    ]
    init_outputs = [
        NodeOutputBP(type_="data"),
        NodeOutputBP(type_="data"),
    ]
    color = "#5d95de"

    def update_event(self, inp=-1):
        super().update_event(inp=inp)
        self.set_output_val(0, self.input(0).plot3d())
        self.set_output_val(1, self.input(0))

    @property
    def representations(self) -> tuple:
        if self.input(1):
            return self.output(0), self.output(1)
        else:
            return self.output(0),


class Matplot_Node(NodeWithDisplay):
    title = "MatPlot"
    version = "v0.1"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Data(size="m"), label="x"),
        NodeInputBP(dtype=dtypes.Data(size="m"), label="y"),
    ]
    init_outputs = [
        NodeOutputBP(type_="data"),
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


class Sin_Node(NodeWithDisplay):
    title = "Sin"
    version = "v0.1"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Data(size="m")),
    ]
    init_outputs = [
        NodeOutputBP(),
    ]
    color = "#5d95de"

    def update_event(self, inp=-1):
        super().update_event(inp=inp)
        self.set_output_val(0, np.sin(self.input(0)))


class Result_Node(NodeBase):
    """Simply shows a value converted to str"""

    version = "v0.1"

    title = "Result"
    init_inputs = [
        NodeInputBP(type_="data"),
    ]
    # main_widget_class = widgets.Result_Node_MainWidget
    # main_widget_pos = 'between ports'
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
        NodeOutputBP("loop", type_="exec"),
        NodeOutputBP("e", type_="data"),
        NodeOutputBP("finished", type_="exec"),
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
        # for e in self.input(0):
        #     self.set_output_val(1, e)
        #     self.exec_output(0)

        # self.exec_output(2)


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
    main_widget_class = "ButtonNodeWidget"
    main_widget_pos = "between ports"
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
