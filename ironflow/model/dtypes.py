# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Wrapped dtypes to avoid mutable defaults.

Implementation changes in ryvencore v0.4, so this file may be short-lived.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
from ryvencore.dtypes import DType as DTypeCore


class DType(DTypeCore):
    def __init__(
        self,
        default,
        bounds: tuple = None,
        doc: str = "",
        _load_state=None,
        valid_classes=None,
        allow_none=False,
        batched=False,
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
            self.batched = batched
        self.add_data("valid_classes")
        self.add_data("allow_none")
        self.add_data("batched")

    @staticmethod
    def from_str(s):
        # Load local dtypes, not ryven dtypes
        for DTypeClass in [
            Boolean, Choice, Data, Float, Integer, List, String, Untyped
        ]:
            if s == "DType." + DTypeClass.__name__:
                return DTypeClass

        return None

    @staticmethod
    def _other_types_are_subset(other, reference):
        return all(
            [
                any([issubclass(o, ref) for ref in reference])
                for o in other
            ]
        )

    def _dtype_matches(self, val: DType):
        if isinstance(val, Untyped):
            raise ValueError(
                f"Match checks against {Untyped.__class__.__name__} should always be "
                f"done by value, not by dtype"
            )
        elif isinstance(val, self.__class__) and val.batched == self.batched:
            other_is_more_specific = self._other_types_are_subset(
                val.valid_classes, self.valid_classes
            )
            might_get_surprising_none = val.allow_none and not self.allow_none
            return other_is_more_specific and not might_get_surprising_none
        else:
            return False

    def _instance_matches(self, val: Any):
        if self.batched:
            return self._instance_matches_batch(val)
        else:
            return self._instance_matches_classes(val)

    def _instance_matches_classes(self, val: Any):
        return any([isinstance(val, c) for c in self.valid_classes]) or \
               self._matches_none(val)

    def _matches_none(self, val: Any):
        return val is None and self.allow_none

    def _instance_matches_batch(self, val: Any):
        if isinstance(val, (list, np.ndarray)):
            if any([v is None for v in val]) and not self.allow_none:
                return False
            else:
                return self._other_types_are_subset(
                    set([type(v) for v in val if v is not None]), self.valid_classes
                )
        else:
            return False

    def matches(self, val: DType | Any | None):
        if isinstance(val, DType):
            return self._dtype_matches(val)
        else:
            return self._instance_matches(val)


class Untyped(DType):
    """
    Untyped data always performs an instance-check when used as input and when it's
    used as output, other input nodes always perform an instance-check against it.
    That means it can't be used to pre-wire a graph that has missing data.
    """

    def __init__(
        self,
        doc: str = "",
        _load_state=None,
        batched=False,
    ):
        super().__init__(
            default=None,
            bounds=None,
            doc=doc,
            _load_state=_load_state,
            valid_classes=None,
            allow_none=True,
            batched=batched,
        )

    def _dtype_matches(self, val: DType):
        raise ValueError(
            f"Match checks to {self.__class__.__name__} should always be done by "
            f"value, not by dtype"
        )

    def _instance_matches_classes(self, val: Any):
        return True

    def _instance_matches_batch(self, val: Any):
        return isinstance(val, (list, np.ndarray))


class Data(DType):
    """Any kind of data represented by some evaluated text input"""

    def __init__(
        self,
        default=None,
        size: str = "m",
        doc: str = "",
        _load_state=None,
        valid_classes=None,
        allow_none=False,
        batched=False,
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
            allow_none=allow_none,
            batched=batched,
        )
        self.add_data("size")


class Integer(DType):
    def __init__(
        self,
        default: int = 0,
        bounds: tuple = None,
        doc: str = "",
        _load_state=None,
        valid_classes=None,
        allow_none=False,
        batched=False,
    ):
        super().__init__(
            default=default,
            bounds=bounds,
            doc=doc,
            _load_state=_load_state,
            valid_classes=[int, np.integer] if valid_classes is None else valid_classes,
            allow_none=allow_none,
            batched=batched,
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
        allow_none=False,
        batched=False,
    ):
        self.decimals = decimals
        super().__init__(
            default=default,
            bounds=bounds,
            doc=doc,
            _load_state=_load_state,
            valid_classes=[float, np.floating] if valid_classes is None else valid_classes,
            allow_none=allow_none,
            batched=batched,
        )
        self.add_data("decimals")


class Boolean(DType):
    def __init__(
        self,
        default: bool = False,
        doc: str = "",
        _load_state=None,
        valid_classes=None,
        allow_none=False,
        batched=False,
    ):
        super().__init__(
            default=default,
            doc=doc,
            _load_state=_load_state,
            valid_classes=[bool, np.bool_] if valid_classes is None else valid_classes,
            allow_none=allow_none,
            batched=batched,
        )


class String(DType):
    def __init__(
        self,
        default: str = "",
        size: str = "m",
        doc: str = "",
        _load_state=None,
        valid_classes=None,
        allow_none=False,
        batched=False,
    ):
        """
        size: 's' / 'm' / 'l'
        """
        self.size = size
        super().__init__(
            default=default,
            doc=doc,
            _load_state=_load_state,
            valid_classes=[str, np.str_] if valid_classes is None else valid_classes,
            allow_none=allow_none,
            batched=batched,
        )
        self.add_data("size")


class Choice(DType):
    def __init__(
        self,
        default=None,
        items: Optional[list] = None,
        doc: str = "",
        _load_state=None,
        valid_classes=None,
        allow_none=False,
        batched=False,
    ):
        self.items = items if items is not None else []
        super().__init__(
            default=default,
            doc=doc,
            _load_state=_load_state,
            valid_classes=valid_classes,
            allow_none=allow_none,
            batched=batched,
        )
        self.add_data("items")

    def _instance_matches_classes(self, val: Any):
        return val in self.items or self._matches_none(val)

    def _instance_matches_batch(self, val: Any):
        return isinstance(val, (list, np.ndarray)) and \
            all([self._instance_matches_classes(v) for v in val])


class List(DType):
    """
    TODO: List can probably be more like `Choice`, with special matching rules. For
          instance, I would expect a `List` input to accept other output, as long as
          that output was batched and the other `valid_classes` were a subset of the
          `List.valid_classes`.
    """
    def __init__(
        self,
        default: Optional[list] = None,
        doc: str = "",
        _load_state=None,
        valid_classes=None,
        allow_none=False,
        batched=False,
    ):
        default = default if default is not None else []
        super().__init__(
            default=default,
            doc=doc,
            _load_state=_load_state,
            valid_classes=list if valid_classes is None else valid_classes,
            allow_none=allow_none,
            batched=batched,
        )
