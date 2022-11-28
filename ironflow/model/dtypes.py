# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Wrapped dtypes to avoid mutable defaults.

Implementation changes in ryvencore v0.4, so this file may be short-lived.
"""

from __future__ import annotations

from typing import Any, Optional

from ryvencore.dtypes import DType as DTypeCore


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
        if _load_state is None:
            if isinstance(valid_classes, list):
                self.valid_classes = list(valid_classes)
            elif valid_classes is not None:
                self.valid_classes = [valid_classes]
            else:
                self.valid_classes = []
            self.allow_none = allow_none
        self.add_data('valid_classes')
        self.add_data('allow_none')

    @staticmethod
    def from_str(s):
        # Load local dtypes, not ryven dtypes
        for DTypeClass in [
            Boolean,
            Char,
            Choice,
            Data,
            Float,
            Integer,
            List,
            String
        ]:
            if s == 'DType.'+DTypeClass.__name__:
                return DTypeClass

        return None

    def _dtype_matches(self, val: DType):
        # val can be *more* specific, but not *less*
        return isinstance(val, self.__class__)

    def _instance_matches(self, val: Any):
        return any([isinstance(val, c) for c in self.valid_classes])

    def matches(self, val: DType | Any | None):
        if isinstance(val, DType):
            return self._dtype_matches(val)
        elif val is not None:
            return self._instance_matches(val)
        else:
            return self.allow_none


class Data(DType):
    """Any kind of data represented by some evaluated text input"""
    def __init__(
            self,
            default=None,
            size: str = 'm',
            doc: str = "",
            _load_state=None,
            valid_classes=None,
            allow_none=False
    ):
        """
        size: 's' / 'm' / 'l'
        """
        self.size = size
        super().__init__(
            default=default,
            doc=doc,
            _load_state=_load_state,
            valid_classes=valid_classes,
            allow_none=allow_none
        )
        self.add_data('size')

    def _dtype_matches(self, val: DType):
        return _other_is_more_specific(self, val)


def _other_is_more_specific(reference: DType, other: DType):
    if reference.__class__ == other.__class__:
        other_is_more_specific = all(
            [
                any(
                    [issubclass(o, ref) for ref in reference.valid_classes]
                )
                for o in other.valid_classes
            ]
        )
        might_get_surprising_none = other.allow_none and not reference.allow_none
        return other_is_more_specific and not might_get_surprising_none
    else:
        return False


class Integer(DType):
    def __init__(
            self,
            default: int = 0,
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
            valid_classes=int if valid_classes is None else valid_classes,
            allow_none=allow_none
        )


class Float(DType):
    def __init__(
            self,
            default: float = 0.0,
            bounds: tuple = None,
            decimals: int = 10,
            doc: str = "",
            _load_state=None,
            valid_classes=None,
            allow_none=False
    ):
        self.decimals = decimals
        super().__init__(
            default=default,
            bounds=bounds,
            doc=doc,
            _load_state=_load_state,
            valid_classes=float if valid_classes is None else valid_classes,
            allow_none=allow_none
        )
        self.add_data('decimals')


class Boolean(DType):
    def __init__(
            self,
            default: bool = False,
            doc: str = "",
            _load_state=None,
            valid_classes=None,
            allow_none=False
    ):
        super().__init__(
            default=default,
            doc=doc,
            _load_state=_load_state,
            valid_classes=bool if valid_classes is None else valid_classes,
            allow_none=allow_none
        )


class Char(DType):
    def __init__(
            self,
            default: chr = '',
            doc: str = "",
            _load_state=None,
            valid_classes=None,
            allow_none=False
    ):
        super().__init__(
            default=default,
            doc=doc,
            _load_state=_load_state,
            valid_classes=chr if valid_classes is None else valid_classes,
            allow_none=allow_none
        )


class String(DType):
    def __init__(
            self,
            default: str = "",
            size: str = 'm',
            doc: str = "",
            _load_state=None,
            valid_classes=None,
            allow_none=False
    ):
        """
        size: 's' / 'm' / 'l'
        """
        self.size = size
        super().__init__(
            default=default,
            doc=doc,
            _load_state=_load_state,
            valid_classes=str if valid_classes is None else valid_classes,
            allow_none=allow_none
        )
        self.add_data('size')


class Choice(DType):
    def __init__(
            self,
            default=None,
            items: Optional[list] = None,
            doc: str = "",
            _load_state=None,
            valid_classes=None,
            allow_none=False
    ):
        self.items = items if items is not None else []
        super().__init__(
            default=default,
            doc=doc,
            _load_state=_load_state,
            valid_classes=valid_classes,
            allow_none=allow_none
        )
        self.add_data("items")

    def _dtype_matches(self, val: DType):
        return _other_is_more_specific(self, val)

    def _instance_matches(self, val: Any):
        return val in self.items


class List(DType):
    def __init__(
            self,
            default: Optional[list] = None,
            doc: str = "",
            _load_state=None,
            valid_classes=None,
            allow_none=False
    ):
        default = default if default is not None else []
        super().__init__(
            default=default,
            doc=doc,
            _load_state=_load_state,
            valid_classes=list if valid_classes is None else valid_classes,
            allow_none=allow_none
        )
