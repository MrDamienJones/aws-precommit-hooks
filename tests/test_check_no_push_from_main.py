import aws_precommit_hooks.check_no_push_from_main as module


def test_blocks_push_from_main(monkeypatch, capsys):
    monkeypatch.setattr(module, "_current_branch", lambda: "main")
    assert module.main([]) == 1
    assert "main" in capsys.readouterr().out


def test_blocks_push_from_master(monkeypatch):
    monkeypatch.setattr(module, "_current_branch", lambda: "master")
    assert module.main([]) == 1


def test_allows_push_from_feature_branch(monkeypatch):
    monkeypatch.setattr(module, "_current_branch", lambda: "feature/add-thing")
    assert module.main([]) == 0


def test_custom_protected_branches_override_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module, "_current_branch", lambda: "release")
    (tmp_path / ".precommit-hooks-allowlist.txt").write_text("PROTECTED_BRANCHES=release,main\n")
    assert module.main([]) == 1


def test_custom_protected_branches_allows_default_main_if_overridden(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module, "_current_branch", lambda: "main")
    (tmp_path / ".precommit-hooks-allowlist.txt").write_text("PROTECTED_BRANCHES=release\n")
    assert module.main([]) == 0
