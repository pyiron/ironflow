from __future__ import annotations

import pickle
from io import BytesIO

import numpy as np
import seaborn as sns
from matplotlib import pylab as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from nglview import NGLWidget

from ironflow.model import dtypes
from ironflow.model.node import DataNode, Node
from ironflow.model.port import NodeInputBP, NodeOutputBP
from ironflow.node_tools import main_widgets
from ironflow.nodes.std.special_nodes import DualNodeBase
from pyiron_atomistics import Atoms


NUMERIC_TYPES = [int, float, np.number]


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
        return {"sliced": sliced}


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
        NodeInputBP(dtype=dtypes.Data(valid_classes=Atoms), label="structure"),
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
        NodeInputBP(dtype=dtypes.Untyped(), label="x"),
        NodeInputBP(dtype=dtypes.Untyped(), label="y"),
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
        NodeInputBP(dtype=dtypes.Untyped(), label="x"),
        NodeInputBP(dtype=dtypes.Untyped(), label="y"),
        NodeInputBP(
            dtype=dtypes.Choice(
                default="scatter",
                items=list(_seaborn_method_map.keys()),
            ),
            label="type",
        ),
    ]
    init_outputs = [NodeOutputBP(label="plot")]

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
