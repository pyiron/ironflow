# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Initially wrapped dtypes to avoid mutable defaults, but after that expanded to
facilitate strict type checking when flow connections are made, and to add batching.

Node ports were overridden so that by default they come with an `Untyped` dtype, and
always have a batching flag.

Spec for Data connection cases:
- Typed output / Typed input: output classes must be subset of input classes.
- Batched output / Typed input: Input must be List-type, and output classes must be a
    subset of input classes.
- Typed output / Batched input: Output must be List-type, and output classes must be
    subset of input classes.
- Batched output / Batched input: output classes must be subset of input classes.
- Untyped output / Typed input: value is instance of allowed classes.
- Untyped output / Batched input: value is iterable and each element is an instance of
    allowed classes.
- Untyped output / Untyped input: always allow.

There are also two special dtypes that carry information with a more defined structure:
Choice and List.

Warning:
    Any additional types defined here later need to be added to the list in
    `DType.from_str` to work with (de)serialization.

Implementation of Dtypes changes in ryvencore v0.4, so this file may be short-lived.
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

    def _accepts_dtype(self, other: DType):
        if isinstance(other, Untyped):
            raise ValueError(
                f"Match checks against {Untyped.__class__.__name__} should always be "
                f"done by value, not by dtype. Please contact a package maintainer and "
                f"explain how you got to this error."
            )
        elif isinstance(other, self.__class__) and other.batched == self.batched:
            other_is_more_specific = self._other_types_are_subset(
                other.valid_classes, self.valid_classes
            )
            might_get_surprising_none = other.allow_none and not self.allow_none
            return other_is_more_specific and not might_get_surprising_none
        else:
            return False

    def _accepts_instance(self, val: Any):
        if self.batched:
            return self._batch_accepts_instance(val)
        else:
            return self._accepts_none(val) or self._instance_matches_classes(val)

    def valid_val(self, val: Any):
        return self._accepts_instance(val)

    def _instance_matches_classes(self, val: Any):
        return any([isinstance(val, c) for c in self.valid_classes])

    def _accepts_none(self, val: Any):
        return val is None and self.allow_none

    def _batch_accepts_instance(self, val: Any):
        if isinstance(val, (list, np.ndarray)):
            if any([v is None for v in val]) and not self.allow_none:
                return False
            else:
                return self._other_types_are_subset(
                    set([type(v) for v in val if v is not None]), self.valid_classes
                )
        else:
            return False

    def accepts(self, other: DType | Any | None):
        if isinstance(other, DType):
            return self._accepts_dtype(other)
        else:
            return self._accepts_instance(other)


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

    def _accepts_dtype(self, other: DType):
        raise ValueError(
            f"Match checks to {self.__class__.__name__} should always be done by "
            f"value, not by dtype. Please contact a package maintainer and explain how"
            f"you got to this error."
        )

    def _instance_matches_classes(self, val: Any):
        return True

    def _batch_accepts_instance(self, val: Any):
        return hasattr(val, "__iter__")


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


class Integer(Data):
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
        self.bounds = bounds
        super().__init__(
            default=default,
            doc=doc,
            _load_state=_load_state,
            valid_classes=[int, np.integer] if valid_classes is None else valid_classes,
            allow_none=allow_none,
            batched=batched,
        )
        self.add_data("bounds")


class Float(Data):
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
        self.bounds = bounds
        self.decimals = decimals
        super().__init__(
            default=default,
            doc=doc,
            _load_state=_load_state,
            valid_classes=[float, np.floating] if valid_classes is None else valid_classes,
            allow_none=allow_none,
            batched=batched,
        )
        self.add_data("bounds")
        self.add_data("decimals")


class Boolean(Data):
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


class String(Data):
    def __init__(
        self,
        default: str = "",
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
            valid_classes=[str, np.str_] if valid_classes is None else valid_classes,
            allow_none=allow_none,
            batched=batched,
        )


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
        return val in self.items or self._accepts_none(val)

    def _batch_accepts_instance(self, val: Any):
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
