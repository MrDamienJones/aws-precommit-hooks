from aws_precommit_hooks.check_committed_iac_state import main


def test_flags_cdk_context_json(tmp_path, capsys):
    path = tmp_path / "cdk.context.json"
    path.write_text("{}")
    assert main([str(path)]) == 1
    assert str(path) in capsys.readouterr().out


def test_flags_tfstate(tmp_path):
    path = tmp_path / "terraform.tfstate"
    path.write_text("{}")
    assert main([str(path)]) == 1


def test_flags_tfstate_backup(tmp_path):
    path = tmp_path / "terraform.tfstate.backup"
    path.write_text("{}")
    assert main([str(path)]) == 1


def test_normal_json_passes(tmp_path):
    path = tmp_path / "cdk.json"
    path.write_text("{}")
    assert main([str(path)]) == 0


def test_nested_path_still_flagged(tmp_path):
    nested = tmp_path / "infra"
    nested.mkdir()
    path = nested / "cdk.context.json"
    path.write_text("{}")
    assert main([str(path)]) == 1


def test_repo_allowlist_suppresses_finding(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".precommit-hooks-allowlist.txt").write_text("cdk.context.json\n")
    path = tmp_path / "cdk.context.json"
    path.write_text("{}")
    assert main(["cdk.context.json"]) == 0
