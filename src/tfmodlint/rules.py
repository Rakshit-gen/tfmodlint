"""Lint rules. Each one looks at a whole module and yields findings."""

from __future__ import annotations

import re
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


def line_in(module: Module, block: Block, pattern: str) -> int:
    """Line of the first match of pattern at or after the start of block."""
    lines = module.sources.get(block.file, "").splitlines()
    regex = re.compile(pattern)
    for number in range(block.line, len(lines) + 1):
        if regex.search(lines[number - 1]):
            return number
    return block.line


def required_providers(module: Module) -> Iterator[tuple[Block, str, object]]:
    for block in module.of("terraform"):
        for entry in block.body.get("required_providers", []):
            for name, spec in entry.items():
                yield block, name, spec


@rule("variable-description", WARNING, "a variable has no description")
def variable_description(module: Module) -> Iterator[Hit]:
    for block in module.of("variable"):
        if not str(block.body.get("description", "")).strip():
            yield at(block, f'variable "{block.name}" has no description')


@rule("variable-type", WARNING, "a variable has no type constraint")
def variable_type(module: Module) -> Iterator[Hit]:
    for block in module.of("variable"):
        if "type" not in block.body:
            yield at(block, f'variable "{block.name}" has no type')


@rule("output-description", WARNING, "an output has no description")
def output_description(module: Module) -> Iterator[Hit]:
    for block in module.of("output"):
        if not str(block.body.get("description", "")).strip():
            yield at(block, f'output "{block.name}" has no description')


@rule("required-version", ERROR, "no terraform block sets required_version")
def required_version(module: Module) -> Iterator[Hit]:
    settings = module.of("terraform")
    if any("required_version" in b.body for b in settings) or not module.sources:
        return
    message = "no terraform block sets required_version"
    if settings:
        yield at(settings[0], message)
    else:
        yield min(module.sources), 1, message


@rule("provider-version", ERROR, "a required provider has no version constraint")
def provider_version(module: Module) -> Iterator[Hit]:
    for block, name, spec in required_providers(module):
        if isinstance(spec, dict) and not spec.get("version"):
            line = line_in(module, block, rf"^\s*{re.escape(name)}\s*=")
            yield block.file, line, f'provider "{name}" has no version constraint'


@rule("provider-source", WARNING, "a required provider has no source address")
def provider_source(module: Module) -> Iterator[Hit]:
    for block, name, spec in required_providers(module):
        if isinstance(spec, dict) and spec.get("source"):
            continue
        line = line_in(module, block, rf"^\s*{re.escape(name)}\s*=")
        yield (
            block.file,
            line,
            f'provider "{name}" has no source, add source = "<namespace>/{name}"',
        )


GIT_PREFIXES = ("git::", "git@", "github.com/", "bitbucket.org/")
BRANCHES = frozenset({"main", "master", "develop", "dev", "trunk", "HEAD"})


def _ref(source: str) -> str | None:
    match = re.search(r"[?&]ref=([^&]+)", source)
    return match.group(1) if match else None


@rule("module-ref", ERROR, "a git module source is not pinned to a tag or commit")
def module_ref(module: Module) -> Iterator[Hit]:
    for block in module.of("module"):
        source = str(block.body.get("source", ""))
        if not source.startswith(GIT_PREFIXES):
            continue
        ref = _ref(source)
        if ref is None:
            yield at(block, f'module "{block.name}" source has no ?ref=, pin a tag or commit')
        elif ref in BRANCHES:
            yield at(
                block, f'module "{block.name}" is pinned to branch "{ref}", use a tag or commit'
            )


# namespace/name/provider, optionally behind a registry host.
REGISTRY_SOURCE = re.compile(r"^([\w.-]+\.[a-z]{2,}/)?[\w-]+/[\w-]+/[\w-]+$")


@rule("module-version", ERROR, "a registry module has no version constraint")
def module_version(module: Module) -> Iterator[Hit]:
    for block in module.of("module"):
        source = str(block.body.get("source", ""))
        if REGISTRY_SOURCE.match(source) and not block.body.get("version"):
            yield at(block, f'module "{block.name}" from the registry has no version')


def lint(module: Module, disabled: frozenset[str] = frozenset()) -> list[Finding]:
    findings = [
        Finding(name, info.level, file, line, message)
        for name, info in RULES.items()
        if name not in disabled
        for file, line, message in info.fn(module)
    ]
    return sorted(findings, key=lambda f: (str(f.file), f.line, f.rule))
