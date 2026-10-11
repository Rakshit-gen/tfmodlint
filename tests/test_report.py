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


def test_json_rows():
    import json

    from tfmodlint.report import as_json

    rows = json.loads(as_json(FINDINGS[:1]))
    assert rows == [
        {
            "rule": "required-version",
            "level": "error",
            "file": "mod/versions.tf",
            "line": 1,
            "message": "no required_version",
        }
    ]


def test_json_without_findings_is_an_empty_list():
    from tfmodlint.report import as_json

    assert as_json([]) == "[]\n"
