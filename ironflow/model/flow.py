from __future__ import annotations

from ryvencore import Flow as FlowCore, InfoMsgs
from ryvencore.NodePort import NodePort


class Flow(FlowCore):
    """
    Wraps `ryvencore.Flow.Flow` to override the connection validity check, so we can
    add type checking.
    """

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
            if hasattr(out, 'dtype') and out.dtype is not None:
                valid = inp.dtype.matches(out.dtype)
                InfoMsgs.write(
                    f"dtype-dtype check for {inp.node.title}.{inp.label_str} and "
                    f"{out.node.title}.{out.label_str} returned {valid}"
                )
            else:
                valid = inp.dtype.matches(out.val)
                InfoMsgs.write(
                    f"dtype-value check for {inp.node.title}.{inp.label_str} and "
                    f"{out.node.title}.{out.label_str} returned {valid}"
                )

        # ryvencore.Flow.Flow content
        self.connection_request_valid.emit(valid)

        return valid
