"""Render findings for a terminal, a script or GitHub Actions."""

from __future__ import annotations

import json

from tfmodlint.rules import ERROR, Finding


def text(findings: list[Finding]) -> str:
    lines = [f"{f.file}:{f.line}: {f.level}: {f.message} [{f.rule}]" for f in findings]
    errors = sum(f.level == ERROR for f in findings)
    warnings = len(findings) - errors
    if findings:
        lines.append("")
        lines.append(f"{_plural(errors, 'error')}, {_plural(warnings, 'warning')}.")
    else:
        lines.append("No problems found.")
    return "\n".join(lines) + "\n"


def _plural(n: int, noun: str) -> str:
    return f"{n} {noun}" if n == 1 else f"{n} {noun}s"


def as_json(findings: list[Finding]) -> str:
    rows = [
        {
            "rule": f.rule,
            "level": f.level,
            "file": str(f.file),
            "line": f.line,
            "message": f.message,
        }
        for f in findings
    ]
    return json.dumps(rows, indent=2) + "\n"


def _escape(value: str, prop: bool = False) -> str:
    value = value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    if prop:
        value = value.replace(":", "%3A").replace(",", "%2C")
    return value


def github(findings: list[Finding]) -> str:
    """Workflow commands that GitHub Actions shows as annotations on the diff."""
    lines = [
        f"::{f.level} file={_escape(str(f.file), True)},line={f.line},"
        f"title={_escape(f.rule, True)}::{_escape(f.message)}"
        for f in findings
    ]
    return "".join(line + "\n" for line in lines)
