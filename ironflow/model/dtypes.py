# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Initially wrapped dtypes to avoid mutable defaults, but after that expanded to
facilitate strict type checking when flow connections are made, and to add batching.

Node ports were overridden so that by default they come with an `Untyped` dtype, and
always have a batching flag.

Further, the dtypes are broken down into broad categories of `Data`, `List`, and
`Choice` with different behaviours under regular and batched conditions.

Warning:
    Any additional types defined here later need to be added to the list in
    `DType.from_str` to work with (de)serialization.

Implementation of Dtypes changes in ryvencore v0.4, so this file may be short-lived.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

import numpy as np
from ryvencore.dtypes import DType as DTypeCore


def isiterable(obj):
    try:
        iter(obj)
        return True
    except TypeError:
        return False


def other_classes_are_subset(other, reference):
    return all(any(issubclass(o, ref) for ref in reference) for o in other)


class DType(DTypeCore, ABC):
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
            Boolean,
            Choice,
            Data,
            Float,
            Integer,
            List,
            String,
            Untyped,
        ]:
            if s == "DType." + DTypeClass.__name__:
                return DTypeClass

        return None

    def _classes_are_subset(self, other_classes):
        return other_classes_are_subset(other_classes, self.valid_classes)

    def accepts(self, other: DType | Any | None):
        if isinstance(other, DType):
            return self._accepts_dtype(other)
        else:
            return self._accepts_instance(other)

    @abstractmethod
    def _accepts_dtype(self, other: DType):
        pass

    def _accepts_instance(self, val: Any):
        if self.batched:
            return self._batch_accepts_instance(val)
        else:
            return self._accepts_none(val) or self._accepts_non_none_instance(val)

    @abstractmethod
    def _batch_accepts_instance(self, val: Any):
        pass

    def _accepts_none(self, val: Any):
        return val is None and self.allow_none

    @abstractmethod
    def _accepts_non_none_instance(self, val: Any):
        pass

    def valid_val(self, val: Any):
        return self._accepts_instance(val)

    def _surprise_none_possible(self, other: DType):
        return other.allow_none and not self.allow_none


class Untyped(DType):
    """
    Untyped data always performs an instance-check when used as input and when it's
    used as output, other input nodes always perform an instance-check against it.
    That means it can't be used to pre-wire a graph that has missing data.

    When Untyped as an input receives output connections...
    Normally:
        - Accept anything.
    When batched:
        - Accept any value that is iterable.

    Untyped is always valid unless the value is None and None is not allowed.
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

    def _accepts_non_none_instance(self, val: Any):
        return True

    def _batch_accepts_instance(self, val: Any):
        return hasattr(val, "__iter__")


class Data(DType):
    """
    For most types of data.

    When Data as an input receives output connections...
    Normally:
        - Data output: output valid classes must be a subset of input valid classes, and
            one of input or output classes must inherit from the other (or be the same).
        - Untyped output: output value must be an instance of valid classes
        - All else: Fail.
    When batched:
        - Batched Data output: same as the unbatched case, but now both are batched.
        - Untyped output: output value must be iterable and each element must be an
            instance of valid classes.
        - List output: output valid classes must be a subset of input valid classes.
        - All else: Fail.

    Data is valid when the value is an instance of the valid classes, or is None and
    None is allowed.
    """

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

    def _accepts_dtype(self, other: DType):
        if isinstance(other, Untyped):
            raise ValueError(
                f"Match checks against {Untyped.__class__.__name__} should always be "
                f"done by value, not by dtype. Please contact a package maintainer and "
                f"explain how you got to this error."
            )
        elif (
            isinstance(other, self.__class__) or isinstance(self, other.__class__)
        ) and other.batched == self.batched:
            return self._classes_are_subset(
                other.valid_classes
            ) and not self._surprise_none_possible(other)
        elif self.batched and isinstance(other, List) and not other.batched:
            return self._classes_are_subset(other.valid_classes)
        else:
            return False

    def _accepts_non_none_instance(self, val: Any):
        return any(isinstance(val, c) for c in self.valid_classes)

    def _batch_accepts_instance(self, val: Any):
        if hasattr(val, "__iter__"):
            if any(v is None for v in val) and not self.allow_none:
                return False
            else:
                return self._classes_are_subset(
                    set([type(v) for v in val if v is not None])
                )
        else:
            return False


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
            valid_classes=[float, np.floating]
            if valid_classes is None
            else valid_classes,
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
    """
    Data that must be chosen from among a list of items.

    When Choice as an input receives output connections...
    Normally:
        - Data output: output valid classes must be a subset.
        - Untyped output: output value must be in the items list.
        - All else: Fail.
    When batched:
        - Batched Data output: output valid classes must be a subset.
        - List output: output valid classes must be a subset.
        - Untyped: output value must be iterable, and each element must be in the items
            list.
        - All else: Fail.

    Choice is valid when the value is in the items list, or value is None and None is
    allowed.

    Note that when making Data (or List) connections, the connection may be allowed
    but still result in an invalid value state (in cases where the output value does
    not match the input items list).
    """

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

    def _accepts_dtype(self, other: DType):
        # TODO: Temporary code duplication while splitting Data and Choice
        if isinstance(other, Untyped):
            raise ValueError(
                f"Match checks against {Untyped.__class__.__name__} should always be "
                f"done by value, not by dtype. Please contact a package maintainer and "
                f"explain how you got to this error."
            )
        if self.batched:
            dtype_ok = (isinstance(other, List) and not other.batched) or (
                isinstance(other, Data) and other.batched
            )
            classes_ok = self._classes_are_subset(other.valid_classes)
            return dtype_ok and classes_ok and not self._surprise_none_possible(other)
        elif isinstance(other, Data) and not other.batched:
            return self._classes_are_subset(
                other.valid_classes
            ) and not self._surprise_none_possible(other)
        else:
            return False

    def _accepts_non_none_instance(self, val: Any):
        return val in self.items

    def _batch_accepts_instance(self, val: Any):
        return isinstance(val, (list, np.ndarray)) and all(
            self._accepts_non_none_instance(v) for v in val
        )


class List(DType):
    """
    Data that is explicitly iterable.

    When List as an input receives output connections...
    Normally:
        - List output: output valid classes must be a subset.
        - Batched Data output: output valid classes must be a subset.
        - Untyped output: output value must be iterable and each element must be an
            instance of valid classes.
        - All else: Fail.
    When batched:
        - Batched List output: output valid classes must be a subset.
        - Untyped: output value must be iterable, each element must be iterable, and
            each element's element must be an instance of a valid class.
        - All else: Fail.

    List is valid when the value is iterable and all elements are instances of the
    valid classes, or the value is None and None is allowed.

    Note: `allow_none` in this case determines whether the _entire dtype value_ may be
        `None`. If you want to specify that the list-like object itself may _contain_
        `None` values, add `type(None)` to the `valid_classes`.
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
        super().__init__(
            default=default,
            doc=doc,
            _load_state=_load_state,
            valid_classes=list if valid_classes is None else valid_classes,
            allow_none=allow_none,
            batched=batched,
        )

    def _accepts_dtype(self, other: DType):
        if self.batched:
            return (
                isinstance(other, List)
                and other.batched
                and self._classes_are_subset(other.valid_classes)
            )
        elif isinstance(other, List) or (isinstance(other, Data) and other.batched):
            # TODO: Only other unbatched lists should be accepted to conform to spec
            #       At the moment, this is a very useful bug, since it lets us pass
            #       batched data to the `Transpose` and `Slice` nodes to modify them
            #       The correct fix is to introduce a new Matrix DType, of which
            #       List is a special case
            return self._classes_are_subset(other.valid_classes)
        else:
            return False

    def _accepts_non_none_instance(self, val: Any):
        return isiterable(val) and all(
            any(isinstance(v, c) for c in self.valid_classes) for v in val
        )

    def _batch_accepts_instance(self, val: Any):
        return isiterable(val) and all(
            self._accepts_none(v) or self._accepts_non_none_instance(v) for v in val
        )
