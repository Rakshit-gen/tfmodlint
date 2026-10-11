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
