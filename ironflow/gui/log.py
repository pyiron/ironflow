# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Control the underlying Ryven logging system, and route logs to a widget.
"""

from __future__ import annotations

import sys
from io import TextIOBase

import ipywidgets as widgets
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ironflow.gui.gui import GUI


class StdOutPut(TextIOBase):
    """Helper class that can be assigned to stdout and/or stderr,  passing string to a widget"""

    def __init__(self):
        self.output = widgets.Output()

    def write(self, s):
        self.output.append_stdout(s)


class LogScreen:
    """
    A class that can redirect stdout and stderr to a widget, and gives controls for both this and toggling the
    Ryven logger.
    """

    def __init__(self, gui: GUI, enable_ryven_log: bool, log_to_display: bool):
        self._gui = gui
        self._stdoutput = StdOutPut()
        self._stdoutput.output.layout.height = "430px"
        self._standard_stdout = sys.stdout
        self._standard_stderr = sys.stderr

        if log_to_display:
            self.log_to_display()

        self.ryven_log_button = widgets.Checkbox(
            value=enable_ryven_log, description="Use Ryven's InfoMsgs system"
        )
        self.display_log_button = widgets.Checkbox(
            value=log_to_display, description="Route stdout to ironflow"
        )

        self.ryven_log_button.observe(self._toggle_ryven_log)
        self.display_log_button.observe(self._toggle_display_log)

    @property
    def box(self):
        return widgets.VBox(
            [
                widgets.HBox(
                    [self.display_log_button, self.ryven_log_button],
                    layout=widgets.Layout(min_height="35px")
                ),
                widgets.HBox([self.output])
            ],
        )

    @property
    def output(self):
        return self._stdoutput.output

    def log_to_display(self):
        sys.stdout = self._stdoutput
        sys.stderr = self._stdoutput

    def log_to_stdout(self):
        sys.stdout = self._standard_stdout
        sys.stderr = self._standard_stderr

    def _toggle_ryven_log(self, change: dict):
        if change["name"] == "value":
            if change["new"]:
                self._gui.session.info_messenger().enable()
            else:
                self._gui.session.info_messenger().disable()

    def _toggle_display_log(self, change: dict):
        if change["name"] == "value":
            if change["new"]:
                self.log_to_display()
            else:
                self.log_to_stdout()
