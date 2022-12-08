from __future__ import annotations

from typing import TYPE_CHECKING

from ryvencore import Flow as FlowCore, InfoMsgs
from ryvencore.NodePort import NodePort

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

    def check_connection_validity(self, p1: NodePort, p2: NodePort) -> bool:
        """Checks whether a considered connect action is legal"""

        # ryvencore.Flow.Flow content
        valid = True

        if p1.node == p2.node:
            valid = False

        if p1.io_pos == p2.io_pos or p1.type_ != p2.type_:
            valid = False

        # ironflow content
        inp, out = (p1, p2) if p1.io_pos == 1 else (p2, p1)
        if inp.dtype is not None:
            if out.dtype is not None:
                valid = inp.dtype.matches(out.dtype)
                InfoMsgs.write(
                    f"{self.batched_or_nothing(inp.dtype)}dtype-"
                    f"{self.batched_or_nothing(out.dtype)}dtype check for "
                    f"{inp.node.title}.{inp.label_str} and "
                    f"{out.node.title}.{out.label_str} returned {valid}"
                )
            else:
                valid = inp.dtype.matches(out.val)
                InfoMsgs.write(
                    f"{self.batched_or_nothing(inp.dtype)}dtype-value check for "
                    f"{inp.node.title}.{inp.label_str} and "
                    f"{out.node.title}.{out.label_str} returned {valid}"
                )

        # ryvencore.Flow.Flow content
        self.connection_request_valid.emit(valid)

        return valid
