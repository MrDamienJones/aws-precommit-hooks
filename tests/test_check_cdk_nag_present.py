from aws_precommit_hooks.check_cdk_nag_present import main


def _write(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content)
    return path


def test_flags_app_without_nag(tmp_path):
    path = _write(tmp_path, "app.py", "app = cdk.App()\n")
    assert main([str(path)]) == 1


def test_passes_when_nag_present(tmp_path):
    path = _write(
        tmp_path,
        "app.py",
        "app = cdk.App()\ncdk.Aspects.of(app).add(AwsSolutionsChecks())\n",
    )
    assert main([str(path)]) == 0


def test_ignores_files_without_cdk_app(tmp_path):
    path = _write(tmp_path, "handler.py", "def handler(event, context):\n    return {}\n")
    assert main([str(path)]) == 0


def test_repo_allowlist_suppresses_finding(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".precommit-hooks-allowlist.txt").write_text("app.py\n")
    _write(tmp_path, "app.py", "app = cdk.App()\n")
    assert main(["app.py"]) == 0
