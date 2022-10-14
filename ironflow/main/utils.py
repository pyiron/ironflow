import inspect
import os
from os.path import basename
import importlib.util

from ironflow.main.node import Node
from ironflow.main.nodes_package import NodesPackage


def load_from_file(file: str = None, components_list: [str] = []) -> tuple:
    """
    Imports the specified components from a python module with given file path.
    """

    name = basename(file).split('.')[0]
    spec = importlib.util.spec_from_file_location(name, file)

    importlib.util.module_from_spec(spec)

    mod = spec.loader.load_module(name)
    # using load_module(name) instead of exec_module(mod) here,
    # because exec_module() somehow then registers it as "built-in"
    # which is wrong and prevents inspect from parsing the source

    comps = tuple([getattr(mod, c) for c in components_list])

    return comps


def import_nodes_package(package: NodesPackage = None, directory: str = None) -> list:
    """
    This function is an interface to the node packages system in Ryven.
    It loads nodes from a Ryven nodes package and returns them in a list.
    You can either pass a NodesPackage object or a path to the directory where the nodes.py file is located.
    """

    if package is None:
        package = NodesPackage(directory)
        print ('package: ', package)

    load_from_file(package.file_path)

    nodes = NodesRegistry.exported_nodes[-1]

    # -----------

    # add package name to identifiers and define custom types

    for n in nodes:
        n.identifier_prefix = package.name if n.identifier is None else None
        n.type_ = package.name if not n.type_ else package.name+f'[{n.type_}]'

    return nodes


def import_widgets(origin_file: str, rel_file_path='widgets.py'):
    """
    Import all exported widgets from 'widgets.py' with respect to the origin_file location.
    Returns an object with all exported widgets as attributes for direct access.
    """

    caller_location = os.path.dirname(origin_file)

    # alternative solution without __file__ argument; does not work with debugging, so it's not the best idea
    #   caller_location = os.path.dirname(stack()[1].filename)  # getting caller file path from stack frame

    # in non-gui mode, return an object that just returns None for all accessed attributes
    # so widgets.MyWidget in the nodes file just returns None then
    class PlaceholderWidgetsContainer:
        def __getattr__(self, item):
            return None
    widgets_container = PlaceholderWidgetsContainer()

    return widgets_container


class NodesRegistry:
    """
    Stores the nodes exported via export_nodes on import of a nodes package.
    After running the imported nodes.py module (which causes export_nodes() to run),
    Ryven can find the exported nodes in exported_nodes.
    """
    exported_nodes: [[Node]] = []
    exported_node_sources: [[str]] = []


def export_nodes(*args):
    """
    Exports/exposes the specified nodes to Ryven for use in flows.
    """

    if not isinstance(args, tuple):
        if issubclass(args, Node):
            nodes = tuple(args)
        else:
            return
    else:
        nodes = list(args)

    NodesRegistry.exported_nodes.append(nodes)

    # get sources
    node_sources = [inspect.getsource(n) for n in nodes]
    NodesRegistry.exported_node_sources.append(node_sources)
