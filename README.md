# tfmodlint

Lint Terraform modules for the problems that make them hard to reuse.

## Quickstart

```
tfmodlint path/to/module
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
