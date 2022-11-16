"""
Stuff that doesn't fit anywhere yet.
"""
from __future__ import annotations

from IPython.core.display import HTML


def display_string(string):
    """
    Format a python string to look nice in an IPython.display.display context.

    If we just pass a string, `display` doesn't resolve newlines.
    If we pass a `print`ed string, `display` also shows the `None` value returned by `print`
    So we use this ugly hack.
    """
    return HTML(
        string.replace("\n", "<br>").replace("\t", "&emsp;").replace(" ", "&nbsp;")
    )
