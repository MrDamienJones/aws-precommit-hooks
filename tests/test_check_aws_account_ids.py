from aws_precommit_hooks.check_aws_account_ids import main


def _write(tmp_path, content):
    path = tmp_path / "sample.py"
    path.write_text(content)
    return path


class TestAlwaysAllowedPlaceholders:
    def test_aws_official_placeholders_pass(self, tmp_path, capsys):
        path = _write(
            tmp_path,
            'a = "123456789012"\nb = "111122223333"\nc = "444455556666"\n',
        )
        assert main([str(path)]) == 0
        assert capsys.readouterr().out == ""


class TestSequentialDigitPlaceholders:
    def test_ascending_sequence_passes(self, tmp_path, capsys):
        path = _write(tmp_path, 'a = "234567890123"\n')
        assert main([str(path)]) == 0

    def test_descending_sequence_passes(self, tmp_path, capsys):
        path = _write(tmp_path, 'a = "210987654321"\n')
        assert main([str(path)]) == 0


class TestSequentialDigitPairPlaceholders:
    def test_ascending_pairs_pass(self, tmp_path):
        path = _write(tmp_path, 'a = "112233445566"\n')
        assert main([str(path)]) == 0

    def test_descending_pairs_pass(self, tmp_path):
        path = _write(tmp_path, 'a = "665544332211"\n')
        assert main([str(path)]) == 0

    def test_ascending_pairs_with_wrap_pass(self, tmp_path):
        path = _write(tmp_path, 'a = "778899001122"\n')
        assert main([str(path)]) == 0

    def test_descending_pairs_with_wrap_pass(self, tmp_path):
        path = _write(tmp_path, 'a = "221100998877"\n')
        assert main([str(path)]) == 0

    def test_non_doubled_pairs_still_flagged(self, tmp_path):
        # "12" "34" "56" ... are ascending pairs but not *doubled* digits -
        # this must not be mistaken for the doubled-digit placeholder pattern.
        path = _write(tmp_path, 'a = "123456789098"\n')  # allow-account-id
        assert main([str(path)]) == 1


class TestRepeatedDigit:
    def test_all_zeros_passes(self, tmp_path):
        path = _write(tmp_path, 'a = "000000000000"\n')
        assert main([str(path)]) == 0

    def test_all_nines_passes(self, tmp_path):
        path = _write(tmp_path, 'a = "999999999999"\n')
        assert main([str(path)]) == 0


class TestRealLookingIdsAreFlagged:
    def test_flags_real_looking_id(self, tmp_path, capsys):
        path = _write(tmp_path, 'account = "575958560150"\n')  # allow-account-id
        assert main([str(path)]) == 1
        out = capsys.readouterr().out
        assert "575958560150" in out  # allow-account-id
        assert str(path) in out

    def test_flags_alternating_digits(self, tmp_path):
        path = _write(tmp_path, 'a = "121212121212"\n')  # allow-account-id
        assert main([str(path)]) == 1

    def test_reports_correct_line_number(self, tmp_path, capsys):
        path = _write(tmp_path, '# comment\n# comment\naccount = "575958560150"\n')  # allow-account-id
        main([str(path)])
        assert f"{path}:3:" in capsys.readouterr().out


class TestExceptions:
    def test_inline_marker_suppresses_finding(self, tmp_path):
        path = _write(tmp_path, 'account = "575958560150"  # allow-account-id\n')
        assert main([str(path)]) == 0

    def test_repo_allowlist_file_suppresses_finding(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".precommit-hooks-allowlist.txt").write_text("575958560150\n")  # allow-account-id
        path = _write(tmp_path, 'account = "575958560150"\n')  # allow-account-id
        assert main([str(path)]) == 0

    def test_allowlist_comments_are_ignored(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".precommit-hooks-allowlist.txt").write_text(
            "# our sandbox account\n575958560150\n"  # allow-account-id
        )
        path = _write(tmp_path, 'account = "575958560150"\n')  # allow-account-id
        assert main([str(path)]) == 0


class TestBoundaries:
    def test_ignores_binary_files(self, tmp_path):
        path = tmp_path / "binary.dat"
        path.write_bytes(bytes([0xFF, 0xFE, 0x00, 0x01]) * 4)
        assert main([str(path)]) == 0

    def test_ignores_11_and_13_digit_numbers(self, tmp_path):
        path = _write(tmp_path, 'a = "5759585601501"\nb = "57595856015"\n')
        assert main([str(path)]) == 0
