# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A wrapper for `ryvencore.Session` that makes sure our custom flow class gets
instantiated
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from ryvencore.Flow import Flow as FlowCore
from ryvencore.Script import Script as ScriptCore
from ryvencore.Session import Session as SessionCore

if TYPE_CHECKING:
    from ryvencore.NodePort import NodePort


class Session(SessionCore):
    """
    Wraps `ryvencore.Session.Session` to create our `Script` class instead
    """

    def create_script(
            self,
            title: Optional[str] = None,
            create_default_logs: bool =True,
            data: Optional[dict] = None
    ) -> Script:
        """
        Creates and returns a new script.
        If data is provided the title parameter will be ignored.
        """
        # Exactly the content of ScriptCore.create_script,
        # but the `Script` class here is different!

        script = Script(
            session=self, title=title, create_default_logs=create_default_logs,
            load_data=data
        )

        self.scripts.append(script)
        script.load_flow()

        self.new_script_created.emit(script)

        return script


class Script(ScriptCore):
    """
    Wraps `ryvencore.Script.Script` to build our `Flow` class instead.
    """

    def __init__(
            self,
            session: Session,
            title: Optional[str] = None,
            load_data: Optional[dict] = None,
            create_default_logs: bool = True
    ):
        super().__init__(
            session=session,
            title=title,
            load_data=load_data,
            create_default_logs=create_default_logs
        )
        del self.flow  # A little inefficient, but I don't want to reproduce init here
        self.flow = Flow(self.session, self)


class Flow(FlowCore):
    """
    Wraps `ryvencore.Flow.Flow` to overwride the connection validity check, so we can
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
            else:
                valid = inp.dtype.matches(out.val)

        # ryvencore.Flow.Flow content
        self.connection_request_valid.emit(valid)

        return valid
