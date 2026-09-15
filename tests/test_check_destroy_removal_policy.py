from aws_precommit_hooks.check_destroy_removal_policy import main


def _write(tmp_path, content):
    path = tmp_path / "stack.py"
    path.write_text(content)
    return path


def test_flags_unacknowledged_destroy(tmp_path, capsys):
    path = _write(
        tmp_path,
        'bucket = s3.Bucket(self, "B", removal_policy=RemovalPolicy.DESTROY)\n',  # allow-destroy-policy
    )
    assert main([str(path)]) == 1
    out = capsys.readouterr().out
    assert "RemovalPolicy.DESTROY" in out  # allow-destroy-policy
    assert f"{path}:1:" in out


def test_inline_marker_suppresses_finding(tmp_path):
    path = _write(
        tmp_path,
        'table = dynamodb.Table(self, "T", removal_policy=RemovalPolicy.DESTROY)  '  # allow-destroy-policy
        "# allow-destroy-policy\n",
    )
    assert main([str(path)]) == 0


def test_retain_is_not_flagged(tmp_path):
    path = _write(
        tmp_path,
        'kept = s3.Bucket(self, "K", removal_policy=RemovalPolicy.RETAIN)\n',
    )
    assert main([str(path)]) == 0


def test_flags_every_unacknowledged_occurrence(tmp_path, capsys):
    path = _write(
        tmp_path,
        "a = RemovalPolicy.DESTROY\n"  # allow-destroy-policy
        "b = RemovalPolicy.DESTROY  # allow-destroy-policy\n"
        "c = RemovalPolicy.DESTROY\n",  # allow-destroy-policy
    )
    assert main([str(path)]) == 1
    out = capsys.readouterr().out
    assert f"{path}:1:" in out
    assert f"{path}:2:" not in out
    assert f"{path}:3:" in out


def test_ignores_binary_files(tmp_path):
    path = tmp_path / "binary.dat"
    path.write_bytes(bytes([0xFF, 0xFE, 0x00, 0x01]) * 4)
    assert main([str(path)]) == 0
