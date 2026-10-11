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
