from pathlib import Path

import pytest

from tfmodlint.module import ParseError, load_module, parse_file

FIXTURES = Path(__file__).parent / "fixtures"


def blocks(text):
    return parse_file(Path("main.tf"), text)


def test_loads_every_block_with_file_and_line():
    module = load_module(FIXTURES / "good")
    found = [(b.kind, b.name, b.file.name, b.line) for b in module.blocks]
    assert found == [
        ("resource", "aws_instance.web", "main.tf", 1),
        ("output", "instance_ids", "outputs.tf", 1),
        ("variable", "name", "variables.tf", 1),
        ("variable", "instance_count", "variables.tf", 6),
        ("terraform", "", "versions.tf", 1),
    ]


def test_strings_lose_their_quotes():
    (variable,) = blocks('variable "x" {\n  description = "Some text"\n}\n')
    assert variable.body["description"] == "Some text"


def test_repeated_blocks_point_at_their_own_line():
    text = 'provider "aws" {\n  region = "us-east-1"\n}\n\nprovider "aws" {\n  alias = "eu"\n}\n'
    assert [b.line for b in blocks(text)] == [1, 5]


def test_labels_without_quotes_are_found():
    (resource,) = blocks("\n\nresource aws_s3_bucket logs {\n}\n")
    assert (resource.name, resource.line) == ("aws_s3_bucket.logs", 3)


def test_bad_hcl_names_the_file():
    with pytest.raises(ParseError, match=r"^main.tf: cannot parse"):
        blocks('variable "x" {\n')


def test_module_keeps_source_text():
    module = load_module(FIXTURES / "good")
    assert "var.instance_count" in module.sources[FIXTURES / "good" / "main.tf"]


def test_module_dirs_skips_hidden_and_cache_directories(tmp_path):
    for rel in ["main.tf", "modules/a/main.tf", "modules/b/c/x.tf", ".terraform/modules/m/main.tf"]:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("")
    (tmp_path / "docs").mkdir()
    from tfmodlint.module import module_dirs

    found = [str(p.relative_to(tmp_path)) for p in module_dirs(tmp_path)]
    assert found == [".", "modules/a", "modules/b/c"]
