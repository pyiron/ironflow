# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Wrapped dtypes to avoid mutable defaults.

Implementation changes in ryvencore v0.4, so this file may be short-lived.
"""

from typing import Optional

from ryvencore.dtypes import DType, Data, Integer, Float, String, Boolean, Char


class Choice(DType):
    def __init__(self, default=None, items: Optional[list] = None, doc: str = "", _load_state=None):
        self.items = items if items is not None else []
        super().__init__(default=default, doc=doc, _load_state=_load_state)
        self.add_data('items')


class List(DType):
    def __init__(self, default: Optional[list] = None, doc: str = "", _load_state=None):
        default = default if default is not None else []
        super().__init__(default=default, doc=doc, _load_state=_load_state)