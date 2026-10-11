from pathlib import Path

from tfmodlint.module import Module, parse_file
from tfmodlint.rules import lint

from .test_module import FIXTURES


def module(**files):
    """Build a module from file name -> HCL text, e.g. module(main_tf='...')."""
    m = Module(Path("."))
    for name, text in files.items():
        path = Path(name.replace("_tf", ".tf"))
        m.sources[path] = text
        m.blocks += parse_file(path, text)
    return m


def hits(m, rule=None):
    return [(f.rule, f.line, f.message) for f in lint(m) if rule in (None, f.rule)]


def test_good_module_is_clean():
    from tfmodlint.module import load_module

    assert lint(load_module(FIXTURES / "good")) == []


def test_variable_without_description():
    m = module(
        variables_tf='variable "a" {\n  type = string\n}\n\n'
        'variable "b" {\n  description = " "\n}\n'
    )
    assert hits(m, "variable-description") == [
        ("variable-description", 1, 'variable "a" has no description'),
        ("variable-description", 5, 'variable "b" has no description'),
    ]


def test_disabled_rules_are_skipped():
    m = module(variables_tf='variable "a" {}\n')
    assert hits(m) and not [
        f for f in lint(m, frozenset({"variable-description"})) if f.rule == "variable-description"
    ]


def test_variable_without_type():
    m = module(variables_tf='variable "a" {\n  description = "A."\n  default = 1\n}\n')
    assert hits(m) == [("variable-type", 1, 'variable "a" has no type')]
