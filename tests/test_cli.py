import pytest

from tfmodlint.cli import main

from .test_module import FIXTURES

GOOD = str(FIXTURES / "good")
MESSY = str(FIXTURES / "messy")


def test_clean_module_exits_0(capsys):
    assert main([GOOD]) == 0
    assert capsys.readouterr().out == "No problems found.\n"


def test_errors_exit_1(capsys):
    assert main([MESSY]) == 1
    out = capsys.readouterr().out
    assert 'main.tf:11: error: module "vpc" from the registry has no version' in out
    assert out.endswith("4 errors, 6 warnings.\n")


def test_warnings_alone_exit_0_unless_strict(tmp_path, capsys):
    (tmp_path / "versions.tf").write_text('terraform {\n  required_version = ">= 1.5"\n}\n')
    (tmp_path / "variables.tf").write_text('variable "x" {}\n')
    (tmp_path / "main.tf").write_text("locals {\n  y = var.x\n}\n")
    assert main([str(tmp_path)]) == 0
    assert main([str(tmp_path), "--strict"]) == 1


def test_missing_directory_exits_2(capsys):
    assert main(["no/such/dir"]) == 2
    assert "no/such/dir: not a directory" in capsys.readouterr().err


def test_directory_without_tf_files_exits_2(tmp_path, capsys):
    assert main([str(tmp_path)]) == 2
    assert "no .tf files" in capsys.readouterr().err


def test_parse_error_exits_2(tmp_path, capsys):
    (tmp_path / "main.tf").write_text('variable "x" {\n')
    assert main([str(tmp_path)]) == 2
    assert "main.tf: cannot parse" in capsys.readouterr().err


def test_version(capsys):
    with pytest.raises(SystemExit):
        main(["--version"])
    assert capsys.readouterr().out.startswith("tfmodlint ")
