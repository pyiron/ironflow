# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Wrapped dtypes to avoid mutable defaults.

Implementation changes in ryvencore v0.4, so this file may be short-lived.
"""

from __future__ import annotations

from typing import Any, Optional

from ryvencore.dtypes import (
    DType as DTypeCore, Data, Integer, Float, String, Boolean, Char
)


class DType(DTypeCore):
    def __init__(
            self,
            default,
            bounds: tuple = None,
            doc: str = "",
            _load_state=None,
            valid_classes=None,
            allow_none=False
    ):
        super().__init__(
            default=default,
            bounds=bounds,
            doc=doc,
            _load_state=_load_state,
        )
        if isinstance(valid_classes, list):
            self.valid_classes = valid_classes
        elif valid_classes is not None:
            self.valid_classes = [valid_classes]
        else:
            self.valid_classes = None
        self.allow_none = allow_none

    def _dtype_matches(self, val: DType):
        # val can be *more* specific, but not *less*
        return isinstance(val, self.__class__)

    def _instance_matches(self, val: Any):
        if self.valid_classes is not None:
            return any([isinstance(val, c) for c in self.valid_classes])
        else:
            return False

    def matches(self, val: DType | Any | None):
        if isinstance(val, DType):
            return self._dtype_matches(val)
        elif val is not None:
            return self._instance_matches(val)
        else:
            return self.allow_none


class Choice(DType):
    def __init__(
        self,
        default=None,
        items: Optional[list] = None,
        doc: str = "",
        _load_state=None,
    ):
        self.items = items if items is not None else []
        super().__init__(default=default, doc=doc, _load_state=_load_state)
        self.add_data("items")


class List(DType):
    def __init__(self, default: Optional[list] = None, doc: str = "", _load_state=None):
        default = default if default is not None else []
        super().__init__(default=default, doc=doc, _load_state=_load_state)
