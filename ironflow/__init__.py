# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Combines ryven, ipywidgets/ipycanvas, and pyiron to facilitate visual scripting of pyiron workflows.
"""

import ironflow.custom_nodes
from ironflow.gui.gui import GUI

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
