"""Lint rules. Each one looks at a whole module and yields findings."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

from tfmodlint.module import Block, Module

ERROR, WARNING = "error", "warning"


@dataclass(frozen=True)
class Finding:
    rule: str
    level: str
    file: Path
    line: int
    message: str


# A rule yields (file, line, message); the registry adds its name and level.
Hit = tuple[Path, int, str]
Rule = Callable[[Module], Iterator[Hit]]


@dataclass(frozen=True)
class RuleInfo:
    fn: Rule
    level: str
    description: str


RULES: dict[str, RuleInfo] = {}


def rule(name: str, level: str, description: str) -> Callable[[Rule], Rule]:
    def register(fn: Rule) -> Rule:
        RULES[name] = RuleInfo(fn, level, description)
        return fn

    return register


def at(block: Block, message: str) -> Hit:
    return block.file, block.line, message


@rule("variable-description", WARNING, "a variable has no description")
def variable_description(module: Module) -> Iterator[Hit]:
    for block in module.of("variable"):
        if not str(block.body.get("description", "")).strip():
            yield at(block, f'variable "{block.name}" has no description')


def lint(module: Module, disabled: frozenset[str] = frozenset()) -> list[Finding]:
    findings = [
        Finding(name, info.level, file, line, message)
        for name, info in RULES.items()
        if name not in disabled
        for file, line, message in info.fn(module)
    ]
    return sorted(findings, key=lambda f: (str(f.file), f.line, f.rule))
