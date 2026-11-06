"""Shared helpers for the notebook section templates."""

from __future__ import annotations

import textwrap
from typing import Any


def dedent(source: str) -> str:
    return textwrap.dedent(source).strip("\n") + "\n"


def section(
    key: str,
    title: str,
    markdown: str,
    code: list[str],
    *,
    llm_editable: bool = False,
    icon: str = "",
) -> dict[str, Any]:
    return {
        "key": key,
        "title": title,
        "markdown": textwrap.dedent(markdown).strip(),
        "code": [dedent(cell) for cell in code],
        "llm_editable": llm_editable,
        "icon": icon,
    }
