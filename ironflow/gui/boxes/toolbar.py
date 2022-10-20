# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A place to collect all the UI buttons.
"""

from __future__ import annotations

import ipywidgets as widgets

from ironflow.gui.boxes.base import Box


class Buttons:
    def __init__(self):
        """Toolbar buttons, declared in the order they will appear."""
        layout = widgets.Layout(width="50px")
        # Icon source: https://fontawesome.com
        # It looks like I'm stuck on v4, but this might just be a limitation of my jupyter environment -Liam
        # v4 icon search: https://fontawesome.com/v4/icons/
        self.load = widgets.Button(tooltip="Load session from JSON", icon="upload", layout=layout)
        self.save = widgets.Button(tooltip="Save session to JSON", icon="download", layout=layout)
        self.help_node = widgets.Button(
            tooltip="Print docs for new node class", icon="question-circle", layout=layout
        )
        self.add_node = widgets.Button(
            tooltip="Add new node (or double-click on empty space)", icon="plus-circle", layout=layout
        )
        self.delete_node = widgets.Button(
            tooltip="Delete selected node (or double-click on the node)", icon="minus-circle", layout=layout
        )
        self.create_script = widgets.Button(
            tooltip="Create script (or click the '+' tab)", icon="plus-square-o", layout=layout
        )
        self.rename_script = widgets.Button(
            tooltip="Rename script",
            icon="pencil-square-o",  # Todo: Use file-pen once this is available
            layout=layout
        )
        self.delete_script = widgets.Button(
            tooltip="Delete script",
            icon="minus-square-o",  # Todo: Use file-circle-minus once this is available
            layout=layout
        )
        self.zero_location = widgets.Button(
            tooltip="Recenter script canvas at the origin",
            icon="map-marker",  # Todo: Use location-dot once this is available
            layout=layout
        )
        self.zoom_in = widgets.Button(
            tooltip="Zoom canvas in",
            icon="search-plus",
            layout=layout
        )
        self.zoom_out = widgets.Button(
            tooltip="Zoom canvas out",
            icon="search-minus",
            layout=layout
        )

    def __iter__(self):
        """Iterates like a list based on order of attribute declaration"""
        return self.__dict__.values().__iter__()


class Toolbar(Box):
    box_class = widgets.HBox

    def __init__(self):
        super().__init__()
        alg_modes = ["data", "exec"]
        self.alg_mode_dropdown = widgets.Dropdown(
            options=alg_modes,
            value=alg_modes[0],
            disabled=False,
            layout=widgets.Layout(width="80px"),
        )
        self.buttons = Buttons()
        self.box.children = [self.alg_mode_dropdown, *self.buttons]
