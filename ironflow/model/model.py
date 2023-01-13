# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
The back-end model which interfaces with Ryven.
"""

from __future__ import annotations

import importlib.util
import json
import types
from abc import ABC
from inspect import isclass
from pathlib import Path
from types import ModuleType
from typing import Optional, Type

from ironflow.model.node import Node
from ironflow.model.session import Session
from ironflow.model.flow import Flow
from ironflow.model.script import Script


class HasSession(ABC):
    """Mixin for an object which has a Ryven session as the underlying model"""

    def __init__(
        self,
        session_title: str,
        *args,
        extra_nodes_packages: Optional[list] = None,
        enable_ryven_log: bool = True,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._session = Session()
        self.session_title = session_title
        self._active_script_index = 0

        if enable_ryven_log:
            self.session.info_messenger().enable()

        self.nodes_dictionary = {}
        from ironflow.nodes import built_in
        from ironflow.nodes.pyiron import atomistics_nodes
        from ironflow.nodes.std import (
            basic_operators,
            control_structures,
            special_nodes,
        )

        for module in [
            built_in,
            atomistics_nodes,
            basic_operators,
            control_structures,
            special_nodes,
        ]:
            self.register_nodes_from_module(module)

        if extra_nodes_packages is not None:
            for package in extra_nodes_packages:
                # Todo: Figure out how to allow node_group to be passed in in an elegant way here for each package
                self.register_nodes(package)

    @property
    def active_script_index(self) -> int:
        return self._active_script_index

    @active_script_index.setter
    def active_script_index(self, i: int) -> None:
        if i >= len(self.session.scripts):
            raise KeyError(
                f"Attempted to activate script {i}, but there are only {len(self.session.scripts)} available."
            )
        self._active_script_index = i % self.n_scripts

    @property
    def session(self) -> Session:
        return self._session

    @property
    def script(self) -> Script:
        return self.session.scripts[self.active_script_index]

    @property
    def flow(self) -> Flow:
        return self.script.flow

    @property
    def n_scripts(self):
        return len(self.session.scripts)

    @property
    def next_auto_script_name(self):
        i = 0
        titles = [s.title for s in self.session.scripts]
        while f"script_{i}" in titles:
            i += 1
        return f"script_{i}"

    def create_script(
        self,
        title: Optional[str] = None,
        create_default_logs: bool = True,
        data: Optional[dict] = None,
    ) -> None:
        self.session.create_script(
            title=title if title is not None else self.next_auto_script_name,
            create_default_logs=create_default_logs,
            data=data,
        )
        self.active_script_index = self.n_scripts - 1

    def delete_script(self) -> None:
        last_active = self.active_script_index
        self.session.delete_script(self.script)
        if self.n_scripts == 0:
            self.create_script()
        else:
            self.active_script_index = last_active - 1

    def rename_script(self, new_name: str) -> bool:
        return self.session.rename_script(self.script, new_name)

    def save(self, file_path: str) -> None:
        data = self.serialize()

        with open(file_path, "w") as f:
            f.write(json.dumps(data, indent=4))

    def serialize(self) -> dict:
        return self.session.serialize()

    def load(self, file_path: str) -> None:
        with open(file_path, "r") as f:
            data = json.loads(f.read())

        self.load_from_data(data)

    def load_from_data(self, data: dict) -> None:
        for script in self.session.scripts[::-1]:
            self.session.delete_script(script)
        self.session.load(data)
        self.active_script_index = 0

    def register_node(
        self, node_class: Type[Node], node_group: Optional[str] = None
    ) -> None:
        """
        Registers a node class with the ryven session and model, storing it in `nodes_dictionary`. Some node attributes
        (`identifier_prefix` and `type_`) are also set on the Node class.

        Args:
            node_class (Type[Node]): The node class to register.
            node_group (str | None): The sub-collection to which this node belongs. (Default is None, which uses the
                last bit of the module path.)


        Note: The sub-collection in the `nodes_dictionary` to which the node gets added depends only on the *tail* of its
              module path, so it is possible that nodes from two different sources get grouped together. In case this
              leads to a conflict, `node_module` can be explicitly provided and this will be used instead.

        Note: You can re-register a class to update its functionality, but only *newly placed* nodes will see this
                update. Already-placed nodes are still instances of the old class and need to be deleted.

        Note: You can save the graph as normal, but new gui instances will need to register the same custom nodes before
            loading the saved graph is possible.

        Example:
            >>> from ironflow import GUI
            >>> from ironflow.custom_nodes import Node, NodeInputBP, NodeOutputBP, dtypes, input_widgets
            >>> gui = GUI(script_title='foo')
            >>>
            >>> class MyNode(Node):
            >>>     title = "MyUserNode"
            >>>     init_inputs = [
            >>>         NodeInputBP(dtype=dtypes.Integer(default=1), label="foo")
            >>>     ]
            >>>     init_outputs = [
            >>>        NodeOutputBP(label="bar")
            >>>    ]
            >>>    color = 'cyan'
            >>>
            >>>     def update_event(self, inp=-1):
            >>>         self.set_output_val(0, self.input(0) + 42)
            >>>
            >>> gui.register_node(MyNode)
        """
        if node_class in self.session.nodes:
            self.session.unregister_node(node_class)
        self.session.register_node(node_class)

        module = node_class.__module__
        identifier_prefix, _, module_shorthand = module.rpartition(".")
        node_class.identifier_prefix = (
            identifier_prefix if node_class.identifier is None else None
        )
        node_class.type_ = (
            module + node_class.type_ if not node_class.type_ else node_class.type_
        )

        node_group = node_group or module_shorthand
        if node_group not in self.nodes_dictionary.keys():
            self.nodes_dictionary[node_group] = {}
        self.nodes_dictionary[node_group][node_class.title] = node_class

    def register_nodes_from_module(
        self, module: ModuleType, node_group: Optional[str] = None
    ) -> None:
        """
        Search through the provided python module for all subclasses `ironflow.main.node.Node` whose name ends with
        `'_Node'` and register them with the ryven session and the model's `nodes_dictionary`.

        Args:
            module (types.ModuleType): The module to register from.
            node_group (str | None): The sub-collection to which this node belongs. (Default is None, which uses the
                last bit of the module path.)
        """
        for name in [key for key in module.__dir__() if key.endswith("_Node")]:
            node = getattr(module, name)
            if not isclass(node) or not issubclass(node, Node):
                raise TypeError(
                    f"Tried to import {name} from {module}, but it was a {node.__class__} instead of {Node}"
                )
            self.register_node(node_class=node, node_group=node_group)

    def register_nodes_from_file(
        self, file_path: str | Path, node_group: Optional[str] = None
    ) -> None:
        """
        Loads a .py file as a module, then searches through it for all subclasses `ironflow.main.node.Node` whose name
        ends with `'_Node'` and register them with the ryven session and the model's `nodes_dictionary`.

        Args:
            file_path (str | pathlib.Path): The .py file to load.
            node_group (str | None): The sub-collection to which this node belongs. (Default is None, which uses the
                file name stripped of its .py suffix.)
        """
        path = Path(file_path)
        resolved = path.resolve().__str__()
        if not path.is_file():
            raise ValueError(f"No file found at {resolved}")

        spec = importlib.util.spec_from_file_location(
            resolved.replace("/", ".").lstrip(".").rpartition(".")[0], resolved
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.register_nodes_from_module(module, node_group=node_group)

    def register_nodes(
        self,
        source: str | Path | types.ModuleType | list | tuple,
        node_group: Optional[str] = None,
    ) -> None:
        if isinstance(source, (str, Path)):
            self.register_nodes_from_file(source, node_group=node_group)
        elif isinstance(source, types.ModuleType):
            self.register_nodes_from_module(source, node_group=node_group)
        elif isinstance(source, (list, tuple)) and all(
            [issubclass(item, Node) for item in source]
        ):
            for node_class in source:
                self.register_node(node_class, node_group=node_group)
