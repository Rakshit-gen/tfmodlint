"""Time tfmodlint on a generated tree of modules.

uv run python scripts/bench.py 200
"""

from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path

from tfmodlint.module import load_module, module_dirs
from tfmodlint.rules import lint

VARIABLES = """variable "name_{i}" {{
  description = "Name {i}."
  type        = string
}}

"""
RESOURCE = """resource "aws_instance" "web_{i}" {{
  ami           = "ami-0123456789abcdef0"
  instance_type = "t3.micro"
  tags = {{
    Name = "${{var.name_{i}}}"
  }}
}}

"""


def write_tree(root: Path, modules: int, per_module: int = 20) -> int:
    lines = 0
    for m in range(modules):
        directory = root / f"mod{m}"
        directory.mkdir()
        files = {
            "versions.tf": 'terraform {\n  required_version = ">= 1.5"\n}\n',
            "variables.tf": "".join(VARIABLES.format(i=i) for i in range(per_module)),
            "main.tf": "".join(RESOURCE.format(i=i) for i in range(per_module)),
        }
        for name, text in files.items():
            (directory / name).write_text(text)
            lines += text.count("\n")
    return lines


def main() -> None:
    modules = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        lines = write_tree(root, modules)
        runs = []
        for _ in range(3):
            start = time.perf_counter()
            findings = [f for d in module_dirs(root) for f in lint(load_module(d))]
            runs.append(time.perf_counter() - start)
    runs.sort()
    print(
        f"{modules} modules, {lines} lines of HCL, {len(findings)} findings: "
        f"median {runs[1]:.2f} s over 3 runs"
    )


if __name__ == "__main__":
    main()
