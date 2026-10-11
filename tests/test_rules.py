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
    assert hits(m, "variable-type") == [("variable-type", 1, 'variable "a" has no type')]


def test_output_without_description():
    m = module(outputs_tf='output "id" {\n  value = 1\n}\n')
    assert hits(m, "output-description") == [
        ("output-description", 1, 'output "id" has no description')
    ]


def test_missing_required_version_points_at_terraform_block():
    m = module(
        main_tf="locals {}\n",
        versions_tf='\nterraform {\n  backend "s3" {}\n}\n',
    )
    assert hits(m, "required-version") == [
        ("required-version", 2, "no terraform block sets required_version")
    ]


def test_missing_required_version_without_terraform_block():
    m = module(variables_tf="", main_tf="locals {}\n")
    (finding,) = [f for f in lint(m) if f.rule == "required-version"]
    assert (finding.file, finding.line) == (Path("main.tf"), 1)


VERSIONS = """terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source = "hashicorp/random"
    }
  }
}
"""


def test_provider_without_version():
    assert hits(module(versions_tf=VERSIONS), "provider-version") == [
        ("provider-version", 8, 'provider "random" has no version constraint')
    ]


def test_provider_in_old_string_form_has_no_source():
    text = 'terraform {\n  required_providers {\n    aws = "~> 5.0"\n  }\n}\n'
    assert hits(module(versions_tf=text), "provider-source") == [
        ("provider-source", 3, 'provider "aws" has no source, add source = "<namespace>/aws"')
    ]


def test_old_string_form_counts_as_a_version():
    text = 'terraform {\n  required_providers {\n    aws = "~> 5.0"\n  }\n}\n'
    assert hits(module(versions_tf=text), "provider-version") == []
