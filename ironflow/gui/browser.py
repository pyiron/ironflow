# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Provide access to the `pyiron_gui`
"""

from __future__ import annotations

import ipywidgets as widgets

from pyiron_atomistics import Project
from pyiron_gui import ProjectBrowser


class Browser:
    def __init__(self):
        self.top_level_project = Project(".")
        self._box = widgets.VBox([], layout=widgets.Layout(height="470px"))
        self.project_browser = ProjectBrowser(self.top_level_project, Vbox=self._box)
        self.project_browser.refresh()

    @property
    def box(self):
        return self._box
