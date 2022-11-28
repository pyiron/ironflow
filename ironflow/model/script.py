from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from ryvencore import Script as ScriptCore

from ironflow.model.flow import Flow

if TYPE_CHECKING:
    from ironflow.model.session import Session


class Script(ScriptCore):
    """
    Wraps `ryvencore.Script.Script` to build our `Flow` class instead.
    """

    def __init__(
        self,
        session: Session,
        title: Optional[str] = None,
        load_data: Optional[dict] = None,
        create_default_logs: bool = True,
    ):
        super().__init__(
            session=session,
            title=title,
            load_data=load_data,
            create_default_logs=create_default_logs,
        )
        del self.flow  # A little inefficient, but I don't want to reproduce init here
        self.flow = Flow(self.session, self)
