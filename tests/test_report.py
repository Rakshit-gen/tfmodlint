from pathlib import Path

from tfmodlint.report import text
from tfmodlint.rules import Finding

FINDINGS = [
    Finding("required-version", "error", Path("mod/versions.tf"), 1, "no required_version"),
    Finding("variable-type", "warning", Path("mod/variables.tf"), 4, 'variable "a" has no type'),
    Finding("naming", "warning", Path("mod/main.tf"), 9, 'name "B" should be snake_case'),
]


def test_text_lists_findings_and_totals():
    assert text(FINDINGS) == (
        "mod/versions.tf:1: error: no required_version [required-version]\n"
        'mod/variables.tf:4: warning: variable "a" has no type [variable-type]\n'
        'mod/main.tf:9: warning: name "B" should be snake_case [naming]\n'
        "\n"
        "1 error, 2 warnings.\n"
    )


def test_text_without_findings():
    assert text([]) == "No problems found.\n"
