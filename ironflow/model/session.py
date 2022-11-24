# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A wrapper for `ryvencore.Session` that makes sure our custom flow class gets
instantiated
"""

from __future__ import annotations

from typing import Optional

from ryvencore.Session import Session as SessionCore

from ironflow.model.script import Script


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
