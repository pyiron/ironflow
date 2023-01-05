from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from ryvencore import Flow as FlowCore, InfoMsgs
from ryvencore.NodePort import NodePort

from ironflow.model.dtypes import Untyped

if TYPE_CHECKING:
    from ironflow.model.dtypes import DType


class Flow(FlowCore):
    """
    Wraps `ryvencore.Flow.Flow` to override the connection validity check, so we can
    add type checking.
    """

    @staticmethod
    def batched_or_nothing(dtype: DType) -> str:
        return "batched " if dtype.batched else ""

    @staticmethod
    def _ports_are_connected(p1: NodePort, p2: NodePort) -> bool:
        for c in p1.connections:
            if c in p2.connections:
                return True
        return False

    def check_connection_validity(self, p1: NodePort, p2: NodePort) -> bool:
        """Checks whether a considered connect action is legal"""

        # ryvencore.Flow.Flow content
        valid = True

        if p1.node == p2.node:
            valid = False

        if p1.io_pos == p2.io_pos or p1.type_ != p2.type_:
            valid = False

        # ironflow content
        if not self._ports_are_connected(p1, p2):
        # Only validate connections, not disconnections
            inp, out = (p1, p2) if p1.io_pos == 1 else (p2, p1)
            if isinstance(inp.dtype, Untyped) or isinstance(out.dtype, Untyped) or (
                inp.dtype.batched != out.dtype.batched and
                isinstance(out.val, (list, np.ndarray))
            ):
                type_valid = inp.dtype.matches(out.val)
                check_type = "value"
            else:
                type_valid = inp.dtype.matches(out.dtype)
                check_type = "dtype"
            InfoMsgs.write(
                f"{inp.node.title}.{inp.label_str} input "
                f"{self.batched_or_nothing(inp.dtype)}{inp.dtype.__class__.__name__} "
                f"made a {check_type} check to receive "
                f"{out.node.title}.{out.label_str} output "
                f"{self.batched_or_nothing(out.dtype)}{out.dtype.__class__.__name__} "
                f"and returned {type_valid}"
            )
            valid = valid and type_valid


        # ryvencore.Flow.Flow content
        self.connection_request_valid.emit(valid)

        return valid
