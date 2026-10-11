"""Settings read from a .tfmodlint.toml file."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from tfmodlint.rules import RULES

DEFAULT_PATH = ".tfmodlint.toml"


class ConfigError(ValueError):
    pass


@dataclass
class Config:
    disable: list[str] = field(default_factory=list)
    strict: bool = False


def parse_config(text: str) -> Config:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid TOML: {exc}") from exc
    unknown = set(data) - {"disable", "strict"}
    if unknown:
        raise ConfigError("unknown setting: " + ", ".join(sorted(unknown)))
    disable = data.get("disable", [])
    if not isinstance(disable, list) or not all(isinstance(v, str) for v in disable):
        raise ConfigError("disable must be a list of strings")
    typos = [name for name in disable if name not in RULES]
    if typos:
        raise ConfigError("disable names unknown rule: " + ", ".join(typos))
    strict = data.get("strict", False)
    if not isinstance(strict, bool):
        raise ConfigError("strict must be true or false")
    return Config(disable=disable, strict=strict)


def load_config(path: str | None) -> Config:
    """Read the given file, or .tfmodlint.toml in the current directory if it exists."""
    if path is None:
        if not Path(DEFAULT_PATH).is_file():
            return Config()
        path = DEFAULT_PATH
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"cannot read config {path}: {exc.strerror}") from exc
    try:
        return parse_config(text)
    except ConfigError as exc:
        raise ConfigError(f"{path}: {exc}") from exc
