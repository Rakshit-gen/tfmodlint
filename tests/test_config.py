import pytest

from tfmodlint.config import Config, ConfigError, load_config, parse_config


def test_empty_config():
    assert parse_config("") == Config()


def test_reads_disable_and_strict():
    config = parse_config('disable = ["naming"]\nstrict = true\n')
    assert config == Config(disable=["naming"], strict=True)


@pytest.mark.parametrize(
    "text, error",
    [
        ("colour = 1", "unknown setting: colour"),
        ('disable = "naming"', "disable must be a list of strings"),
        ('disable = ["namng"]', "disable names unknown rule: namng"),
        ('strict = "yes"', "strict must be true or false"),
        ("disable = [", "invalid TOML"),
    ],
)
def test_rejects_bad_settings(text, error):
    with pytest.raises(ConfigError, match=error):
        parse_config(text)


def test_default_file_in_current_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert load_config(None) == Config()
    (tmp_path / ".tfmodlint.toml").write_text('disable = ["file-layout"]')
    assert load_config(None).disable == ["file-layout"]


def test_missing_explicit_file(tmp_path):
    with pytest.raises(ConfigError, match="cannot read config"):
        load_config(str(tmp_path / "nope.toml"))


def test_example_config_parses():
    from pathlib import Path

    example = Path(__file__).parent.parent / "examples" / "tfmodlint.toml"
    assert parse_config(example.read_text()) == Config(disable=["provider-config"])
