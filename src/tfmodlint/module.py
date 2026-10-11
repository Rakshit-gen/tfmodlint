"""Read the .tf files of one module directory into blocks."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import hcl2
from hcl2.utils import SerializationOptions

OPTIONS = SerializationOptions(
    with_comments=False,
    explicit_blocks=False,
    strip_string_quotes=True,
    preserve_heredocs=False,
)

# How many labels each block type takes: resource "aws_instance" "web" has two.
LABELS = {"resource": 2, "data": 2, "variable": 1, "output": 1, "module": 1, "provider": 1}


class ParseError(ValueError):
    pass


@dataclass(frozen=True)
class Block:
    kind: str
    labels: tuple[str, ...]
    body: dict[str, Any]
    file: Path
    line: int

    @property
    def name(self) -> str:
        return ".".join(self.labels)


@dataclass
class Module:
    path: Path
    blocks: list[Block] = field(default_factory=list)
    sources: dict[Path, str] = field(default_factory=dict)

    def of(self, kind: str) -> list[Block]:
        return [b for b in self.blocks if b.kind == kind]


def _unwrap(kind: str, item: dict[str, Any]) -> list[tuple[tuple[str, ...], dict[str, Any]]]:
    out = [((), item)]
    for _ in range(LABELS.get(kind, 0)):
        out = [(labels + (k,), v) for labels, body in out for k, v in body.items()]
    return out


def _header(kind: str, labels: tuple[str, ...]) -> re.Pattern[str]:
    parts = "".join(rf'[ \t]+"?{re.escape(label)}"?' for label in labels)
    return re.compile(rf"^[ \t]*{kind}{parts}[ \t]*\{{", re.M)


def _line(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def parse_file(path: Path, text: str) -> list[Block]:
    try:
        data = hcl2.loads(text, serialization_options=OPTIONS)
    except Exception as exc:  # lark raises several unrelated exception types
        raise ParseError(f"{path}: cannot parse: {exc}".splitlines()[0]) from exc
    blocks = []
    seen: dict[tuple[str, tuple[str, ...]], int] = {}
    for kind, items in data.items():
        for item in items:
            for labels, body in _unwrap(kind, item):
                # Point at the nth header for blocks that appear more than once,
                # such as several provider "aws" blocks with aliases.
                key = (kind, labels)
                matches = list(_header(kind, labels).finditer(text))
                n = seen.get(key, 0)
                seen[key] = n + 1
                line = _line(text, matches[n].start()) if n < len(matches) else 1
                blocks.append(Block(kind, labels, body, path, line))
    return sorted(blocks, key=lambda b: b.line)


def load_module(path: Path) -> Module:
    module = Module(path)
    for file in sorted(path.glob("*.tf")):
        text = file.read_text(encoding="utf-8")
        module.sources[file] = text
        module.blocks += parse_file(file, text)
    return module
