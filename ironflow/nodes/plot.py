from __future__ import annotations

import pickle
from io import BytesIO

import seaborn as sns
from matplotlib import pylab as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from nglview import NGLWidget

from ironflow.model import dtypes
from ironflow.model.node import Node
from ironflow.model.port import NodeInputBP, NodeOutputBP
from pyiron_atomistics import Atoms


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
