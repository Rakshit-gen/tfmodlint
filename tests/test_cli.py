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


def test_list_rules(capsys):
    assert main(["--list-rules"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].split() == [
        "variable-description",
        "warning",
        "a",
        "variable",
        "has",
        "no",
        "description",
    ]
    assert any(line.startswith("module-ref ") and " error " in line for line in lines)


def test_disable_skips_rules(capsys):
    args = [MESSY, "--disable", "module-version", "--disable", "naming"]
    main(args)
    out = capsys.readouterr().out
    assert "[module-version]" not in out and "[naming]" not in out
    assert "[required-version]" in out


def test_disable_rejects_unknown_rule(capsys):
    with pytest.raises(SystemExit):
        main([MESSY, "--disable", "nope"])
    assert "invalid choice: 'nope'" in capsys.readouterr().err


def test_json_format(capsys):
    import json

    assert main([MESSY, "-f", "json"]) == 1
    rows = json.loads(capsys.readouterr().out)
    assert {r["rule"] for r in rows} >= {"required-version", "naming"}


def test_recursive_lints_every_module(capsys):
    assert main([str(FIXTURES), "--recursive"]) == 1
    out = capsys.readouterr().out
    assert "fixtures/messy/main.tf" in out
    assert "fixtures/good/" not in out


def test_recursive_with_no_modules_exits_2(tmp_path, capsys):
    (tmp_path / "docs").mkdir()
    assert main([str(tmp_path), "-r"]) == 2


def test_config_disables_rules_and_sets_strict(tmp_path, capsys):
    config = tmp_path / "lint.toml"
    config.write_text(
        'disable = ["required-version", "provider-version", "module-version",'
        ' "undeclared-variable"]\n'
    )
    assert main([MESSY, "-c", str(config)]) == 0
    config.write_text(
        'disable = ["required-version", "provider-version", "module-version",'
        ' "undeclared-variable"]\nstrict = true\n'
    )
    assert main([MESSY, "-c", str(config)]) == 1


def test_bad_config_exits_2(tmp_path, capsys):
    config = tmp_path / "lint.toml"
    config.write_text("x = 1\n")
    assert main([MESSY, "-c", str(config)]) == 2
    assert "unknown setting: x" in capsys.readouterr().err
