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


def test_git_module_without_ref():
    text = (
        'module "vpc" {\n  source = "git::https://example.com/vpc.git"\n}\n\n'
        'module "dns" {\n  source = "github.com/org/dns?ref=main"\n}\n\n'
        'module "ok" {\n  source = "git::ssh://git@example.com/ok.git?ref=v1.2.0"\n}\n\n'
        'module "local" {\n  source = "./modules/local"\n}\n'
    )
    assert hits(module(main_tf=text), "module-ref") == [
        ("module-ref", 1, 'module "vpc" source has no ?ref=, pin a tag or commit'),
        ("module-ref", 5, 'module "dns" is pinned to branch "main", use a tag or commit'),
    ]


def test_ref_inside_a_subdirectory_source():
    text = 'module "x" {\n  source = "git::https://e.com/m.git//sub?depth=1&ref=abc123"\n}\n'
    assert hits(module(main_tf=text), "module-ref") == []


def test_registry_module_without_version():
    text = (
        'module "vpc" {\n  source = "terraform-aws-modules/vpc/aws"\n}\n\n'
        'module "priv" {\n  source = "app.terraform.io/acme/net/aws"\n}\n\n'
        'module "ok" {\n  source  = "terraform-aws-modules/vpc/aws"\n  version = "5.1.0"\n}\n\n'
        'module "local" {\n  source = "./a/b/c"\n}\n\n'
        'module "gh" {\n  source = "github.com/org/repo?ref=v1"\n}\n'
    )
    assert hits(module(main_tf=text), "module-version") == [
        ("module-version", 1, 'module "vpc" from the registry has no version'),
        ("module-version", 5, 'module "priv" from the registry has no version'),
    ]


def test_unused_variable():
    m = module(
        variables_tf=(
            'variable "used" {}\n\nvariable "unused" {\n  validation {\n'
            '    condition     = length(var.unused) > 0\n    error_message = "Empty."\n  }\n}\n'
        ),
        main_tf='# var.unused is mentioned only here\nlocals {\n  x = "${var.used}-y"\n}\n',
    )
    assert hits(m, "unused-variable") == [("unused-variable", 3, 'variable "unused" is never used')]


def test_undeclared_variable_points_at_the_use():
    m = module(
        variables_tf='variable "region" {}\n',
        main_tf='resource "aws_instance" "web" {\n  ami = var.ami\n  az  = var.region\n}\n',
    )
    assert hits(m, "undeclared-variable") == [
        ("undeclared-variable", 2, "var.ami is used but not declared")
    ]


def test_secret_with_default():
    m = module(
        variables_tf=(
            'variable "db_password" {\n  default = "hunter2"\n}\n\n'
            'variable "api_token" {\n  default = null\n}\n\n'
            'variable "region" {\n  default = "us-east-1"\n}\n'
        )
    )
    assert hits(m, "secret-default") == [
        ("secret-default", 1, 'variable "db_password" looks like a secret but has a default')
    ]


def test_secret_not_marked_sensitive():
    m = module(
        variables_tf=(
            'variable "db_password" {\n  type = string\n}\n\n'
            'variable "api_token" {\n  sensitive = true\n}\n'
        )
    )
    assert hits(m, "sensitive-variable") == [
        (
            "sensitive-variable",
            1,
            'variable "db_password" looks like a secret, set sensitive = true',
        )
    ]


def test_interpolation_only():
    m = module(
        main_tf=(
            "locals {\n"
            '  a = "${var.name}"\n'
            '  b = "${var.name}-suffix"\n'
            "  c = var.name\n"
            '  d = "${local.x}" # old style\n'
            "}\n"
        )
    )
    assert hits(m, "interpolation-only") == [
        ("interpolation-only", 2, 'use var.name instead of "${var.name}"'),
        ("interpolation-only", 5, 'use local.x instead of "${local.x}"'),
    ]


def test_names_must_be_snake_case():
    m = module(
        main_tf=(
            'resource "aws_instance" "webServer" {}\n'
            'variable "instance-count" {}\n'
            'output "id" {}\n'
            "locals {\n  okName = 1\n  fine = 2\n}\n"
        )
    )
    assert hits(m, "naming") == [
        ("naming", 1, 'resource name "webServer" should be lower snake_case'),
        ("naming", 2, 'variable name "instance-count" should be lower snake_case'),
        ("naming", 5, 'local name "okName" should be lower snake_case'),
    ]


def test_blocks_outside_their_standard_file():
    m = module(
        main_tf='variable "a" {}\n\noutput "b" {}\n',
        variables_tf='variable "c" {}\n',
        outputs_tf='output "d" {}\n',
    )
    assert hits(m, "file-layout") == [
        ("file-layout", 1, 'variable "a" belongs in variables.tf'),
        ("file-layout", 3, 'output "b" belongs in outputs.tf'),
    ]


def test_provider_configured_in_module():
    m = module(main_tf='provider "aws" {\n  region = "us-east-1"\n}\n\nprovider "random" {}\n')
    assert hits(m, "provider-config") == [
        ("provider-config", 1, 'provider "aws" is configured here, pass it in from the caller')
    ]


def test_ignore_comment_on_the_line_above():
    m = module(
        variables_tf=(
            "# tfmodlint-ignore: variable-type, unused-variable\n"
            'variable "a" {\n  description = "A."\n}\n'
        )
    )
    assert hits(m, "variable-type") == [] and hits(m, "unused-variable") == []
    assert hits(m, "variable-description") == []


def test_ignore_comment_for_another_rule_does_not_hide_the_finding():
    m = module(variables_tf='variable "a" { # tfmodlint-ignore: naming\n}\n')
    assert hits(m, "variable-type") == [("variable-type", 1, 'variable "a" has no type')]


def test_bare_ignore_comment_hides_everything_on_the_line():
    m = module(main_tf='locals {\n  a = "${var.x}" // tfmodlint-ignore\n}\n')
    assert [r for r, _, _ in hits(m) if r in ("interpolation-only", "undeclared-variable")] == []


def test_output_exposing_a_sensitive_variable():
    m = module(
        variables_tf='variable "token" {\n  sensitive = true\n}\n',
        outputs_tf=(
            'output "url" {\n  value = "https://x/?t=${var.token}"\n}\n\n'
            'output "hidden" {\n  value     = var.token\n  sensitive = true\n}\n'
        ),
    )
    assert hits(m, "sensitive-output") == [
        ("sensitive-output", 1, 'output "url" exposes sensitive var.token, set sensitive = true')
    ]
