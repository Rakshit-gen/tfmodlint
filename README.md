# tfmodlint

Lint Terraform modules for the problems that make them hard to reuse.

## Install

Needs Python 3.11 or newer.

```
pip install git+https://github.com/Rakshit-gen/tfmodlint
```

## Quickstart

```
tfmodlint path/to/module
tfmodlint --recursive modules/
```

Output for `tests/fixtures/messy`:

```
main.tf:1: error: no terraform block sets required_version [required-version]
main.tf:3: error: provider "aws" has no version constraint [provider-version]
main.tf:9: warning: variable "region" belongs in variables.tf [file-layout]
main.tf:9: warning: variable "region" is never used [unused-variable]
main.tf:9: warning: variable "region" has no description [variable-description]
main.tf:9: warning: variable "region" has no type [variable-type]
main.tf:11: error: module "vpc" from the registry has no version [module-version]
main.tf:15: warning: resource name "Logs" should be lower snake_case [naming]
main.tf:16: warning: use var.bucket instead of "${var.bucket}" [interpolation-only]
main.tf:16: error: var.bucket is used but not declared [undeclared-variable]

4 errors, 6 warnings.
```

## Rules

Errors stop a module from being safe to reuse. Warnings are style and
documentation problems.

| Rule | Level | Flags |
|---|---|---|
| `required-version` | error | no `terraform` block sets `required_version` |
| `provider-version` | error | a `required_providers` entry has no `version` |
| `provider-source` | warning | a `required_providers` entry has no `source`, including the old `aws = "~> 5.0"` form |
| `module-ref` | error | a git module source has no `?ref=`, or points at a branch such as `main` |
| `module-version` | error | a registry module (`namespace/name/provider`) has no `version` |
| `undeclared-variable` | error | `var.x` is used but never declared |
| `unused-variable` | warning | a variable is declared but never used. Its own `validation` block does not count |
| `variable-description` | warning | a variable has no description |
| `variable-type` | warning | a variable has no type |
| `output-description` | warning | an output has no description |
| `secret-default` | error | a variable named like a password, token or key has a default value |
| `sensitive-variable` | warning | a variable named like a secret is not `sensitive = true` |
| `sensitive-output` | error | an output uses a sensitive variable without `sensitive = true` |
| `interpolation-only` | warning | `"${var.x}"` where `var.x` would do |
| `naming` | warning | a variable, output, module, resource, data source or local is not lower snake_case |
| `file-layout` | warning | a variable is outside `variables.tf` or an output is outside `outputs.tf` |
| `provider-config` | warning | a `provider` block with settings, which a reusable module should leave to its caller |

`tfmodlint --list-rules` prints the same list.

## Measured vs Claimed

Every number below states what it measures and how. Update this table
instead of writing new numbers straight into prose elsewhere (portfolio site,
resume), so there is one source of truth.

| Claim | Value | How measured | Date |
|---|---|---|---|
| Lint time, 200 modules (52,600 lines of HCL, 4,000 findings) | 4.1 s median of 3 runs | `python scripts/bench.py 200`: find, parse and lint every module in a generated tree. Apple M4, Python 3.12. A profile shows about 97% of the time is spent in python-hcl2 parsing | 2026-10-11 |

## Architecture

_Short description or diagram link._

## Status

Early. Nothing works yet.
