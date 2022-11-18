# Ironflow

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/pyiron/ironflow/HEAD?labpath=example.ipynb)
[![License](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/f21027e6a1fd40bd8ff93b0314a64725)](https://app.codacy.com/gh/pyiron/ironflow/dashboard)
[![Coverage Status](https://coveralls.io/repos/github/pyiron/ironflow/badge.svg?branch=main)](https://coveralls.io/github/pyiron/ironflow?branch=main)
[![Documentation Status](https://readthedocs.org/projects/ironflow/badge/?version=latest)](https://ironflow.readthedocs.io/en/latest/)

[![Anaconda](https://anaconda.org/conda-forge/ironflow/badges/version.svg)](https://anaconda.org/conda-forge/ironflow)
[![Last Updated](https://anaconda.org/conda-forge/ironflow/badges/latest_release_date.svg
)](https://anaconda.org/conda-forge/ironflow)
[![Platform](https://anaconda.org/conda-forge/ironflow/badges/platforms.svg)](https://anaconda.org/conda-forge/ironflow)
[![Downloads](https://anaconda.org/conda-forge/ironflow/badges/downloads.svg)](https://anaconda.org/conda-forge/ironflow)

Ironflow combines [ryven](https://ryven.org), [ipycanvas](https://ipycanvas.readthedocs.io/) and [ipywidgets](https://ipywidgets.readthedocs.io/en/stable/) to provide a Jupyter-based visual scripting gui for running [pyiron](https://pyiron.org) workflow graphs.
This project is under active development, and in particular the set of nodes available for the workflow graphs is still limited. 
If there is a particular use-case you'd like to see, or if one of our nodes is not working as expected, please raise an issue!

![](docs/_static/screenshot.png)

## Usage

The main gui can be imported directly from `ironflow`.

The gui takes a session title at instantiation, and will automatically try to load any saved session (a JSON file) with the same name present.
To visualize the gui, call the `draw` method.
E.g.:
```python
from ironflow import GUI
gui = GUI('example')
gui.draw()
```

The main screen for ironflow is used to build/run/save/load graphical pyiron workflows. 
In addition to manipulating the gui with buttons in the toolbar (hover the cursor over buttons for more info), you can:
- Look at a node's IO values by clicking on it (which selects it)
- Deselect things by clicking on empty space
- See a richer representation of the node by clicking its `SHOW` button
- Connect the IO (input/output) of a node by clicking on its port and then clicking on another node's OI port
- Move a node around by clicking and dragging it
- Pan the entire camera around by clicking and dragging empty space
- Add a new node of the selected type by double-clicking on empty space
- Delete a node by double-clicking on it
- Collapse or expand a node by clicking on the little triangle on its body (has no effect on functionality, just makes it take less space)

In the default `data` execution mode (we don't currently do anything with the `exec` mode, so don't worry about it), nodes will update their output whenever their input data changes.
You'll see the node body change color when it's performing this update.
Some nodes have input (or output) ports that are of the execution rather than data type.
These can be triggered by a signal from another node's exec-type output port, or by manually clicking the button associated with that port right there in the node widget.

In addition to the workflows screen, ironflow also incorporates the browser from [`pyiron_gui`](https://github.com/pyiron/pyiron_gui), as well as a log tab that allows you to turn the underlying ryven logger on/off and choose whether stdout gets routed to ironflow or its original context.

### Adding custom nodes

The tools needed for extending your graphs with new custom nodes can be imported from `ironflow.custom_nodes`.
New nodes can be registered either from a list of nodes, or from a python module or .py file.
In the latter two cases, only those nodes that inherit from `Node` *and* have a class name ending in `_Node` will be registered (this allows you to have your own node class templates and avoid loading the template itself by simply using regular python CamelCase naming conventions and avoiding ending in `_Node`). 

A new node should have a `title` and may optionally have input and/or output channels specified.
If you want your node to actually *do* something, you'll also need to define an `update_event` method.
E.g.:

```python
from ironflow.custom_nodes import Node, NodeInputBP, NodeOutputBP, dtypes, input_widgets

class My_Node(Node):
    title = "MyUserNode"
    init_inputs = [
        NodeInputBP(dtype=dtypes.Integer(default=1), label="foo")
    ]
    init_outputs = [
       NodeOutputBP(label="bar")
    ]
    color = 'cyan'

    def update_event(self, inp=-1):
        self.set_output_val(0, self.input(0) + 42)

gui.register_node(My_Node)
```

Ironflow nodes differ from standard ryven (version 0.3.1.1) nodes in four ways:
- There is a new helper method `output` analogous to the existing `input` method that lets you more easily access output values, i.e. just a quality-of-life difference.
- Input/output ports and the port values are directly accessible as attributes *if* those ports were labeled, e.g. `node.inputs.ports.foo` or `node.outputs.values.bar`.
- They have a `representation` dictionary, which is used by the IPython gui front-end to give a richer look at nodes. By default, this includes all the outputs and the source code for the node, but you can append to or overwrite these values by specifying an `extra_representations` dictionary on your custom nodes.
- They have two new events: `before_update` and `after_update`, to which you can connect (e.g. `node.after_update.connect`) or disconnect (`...disconnect`) methods to fire before and/or after updates occur -- such methods must take the node instance itself as the first argument, and the canonical input integer (specifying which input value it is that's updating) as the second argument. (You can see an example of this in our base `Node` class, where we use it to force an update of the `representation` attribute after each node update.)

Otherwise, they are just standard ryven nodes, and all the ryven documentation applies.

## Structure

The code is broken into three main submodules:
- `model`, which provides and interface to and extensions of the ryven back-end
- `gui`, which has all the code for driving the back-end from the IPython visual interface
- `nodes`, which stores all the nodes that get included by default when you instantiate the gui/model

There is also a `custom_nodes` submodule, but this just exposes other parts of the code base in one easy-to-improt-from spot.

The model itself, `HasSession`, is just a driver for a single ryven `Session`, with some helpful tools like the ability to easily register new nodes.
The only ryven element we currently extend is the `Node` class, as discussed above; other components are just imported directly from `ryvencore` in `ironflow.model.__init__`.

The gui inherits from and drives the model, and is broken down into three screens: workflows (which allow you to manipulate the model), browser (which wraps the project browser from `pyiron_gui`), and a log.
Inside the workflows screen, visual elements of the gui are broken down into subcomponents like the toolbar, a panel with a visual representation of the graph, a place to show the node representations, etc.
We avoid listing them all here because what's included and how it's laid out is still in flux.
The key conceptual bit is that these various sub-components do not rely directly on each other's internal implementation, they go through the workflow screen as an intermediary where necessary.