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


def test_github_annotations():
    from tfmodlint.report import github

    assert github(FINDINGS[:2]) == (
        "::error file=mod/versions.tf,line=1,title=required-version::no required_version\n"
        '::warning file=mod/variables.tf,line=4,title=variable-type::variable "a" has no type\n'
    )


def test_github_escapes_special_characters():
    from tfmodlint.report import github

    finding = Finding("r", "error", Path("a,b:c.tf"), 2, "50% done\nnext")
    assert github([finding]) == "::error file=a%2Cb%3Ac.tf,line=2,title=r::50%25 done%0Anext\n"
