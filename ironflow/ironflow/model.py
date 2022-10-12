# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from __future__ import annotations

__author__ = "Joerg Neugebauer, Liam Huber"
__copyright__ = (
    "Copyright 2020, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Liam Huber"
__email__ = "liamhuber@greyhavensolutions.com"
__status__ = "production"
__date__ = "Sep 6, 2022"

from pathlib import Path
import os
import json
from abc import ABC
from ryvencore import Session, Script, Flow
from ironflow.main.utils import import_nodes_package, NodesPackage

from typing import Optional, Type

import ironflow.NENV as NENV

os.environ["RYVEN_MODE"] = "no-gui"
NENV.init_node_env()

ryven_location = Path(__file__).parents[1]
packages = [os.path.join(ryven_location, "nodes", *subloc) for subloc in [
    ("built_in",),
    ("std",),
    ("pyiron",),
]]


class HasSession(ABC):
    """Mixin for an object which has a Ryven session as the underlying model"""

    def __init__(self, session_title: str, session: Optional[Session] = None):
        self._session = session if session is not None else Session()
        self.session_title = session_title
        self._active_script_index = 0

        for package in packages:
            self.session.register_nodes(
                import_nodes_package(NodesPackage(directory=package))
            )

        self._nodes_dict = {}
        for n in self.session.nodes:
            self._register_node(n)

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
            data: Optional[dict] = None
    ) -> None:
        self.session.create_script(
            title=title if title is not None else self.next_auto_script_name,
            create_default_logs=create_default_logs,
            data=data
        )
        self.active_script_index = -1

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

    def _register_node(self, node_class: Type[NENV.Node], node_module: Optional[str] = None):
        node_module = node_module or node_class.__module__  # n.identifier_prefix
        if node_module not in self._nodes_dict.keys():
            self._nodes_dict[node_module] = {}
        self._nodes_dict[node_module][node_class.title] = node_class

    def register_user_node(self, node_class: Type[NENV.Node]):
        """
        Register a custom node class from the gui's current working scope. These nodes are available under the
        'user' module. You will need to (re-)draw your GUI to see the change.

        Note: You can re-register a class to update its functionality, but only *newly placed* nodes will see this
                update. Already-placed nodes are still instances of the old class and need to be deleted.

        Note: You can save the graph as normal, but new gui instances will need to register the same custom nodes before
            loading the saved graph is possible.

        Args:
            node_class Type[NENV.Node]: The new node class to register.

        Example:
            >>> from ironflow.ironflow import GUI, Node, NodeInputBP, NodeOutputBP, dtypes
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
            >>> gui.register_user_node(MyNode)
        """
        if node_class in self.session.nodes:
            self.session.unregister_node(node_class)
        self.session.register_node(node_class)
        self._register_node(node_class, node_module='user')
