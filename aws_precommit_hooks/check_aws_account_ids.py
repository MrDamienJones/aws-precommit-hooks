"""Fail if a committed file contains a real-looking AWS account ID.

AWS account IDs are 12-digit numbers. This hook flags any 12-digit number
that isn't a recognised placeholder, so a real account ID doesn't end up
committed to git history by accident.

Always allowed:
  - 123456789012, 111122223333, 444455556666 (AWS's own documentation example
    account IDs - the standard trio used in cross-account tutorials)
  - any 12-digit string of a single repeated digit (000000000000, 111111111111, ...)
  - any 12-digit string where the digits step by a constant +1 or -1 (mod 10)
    from one to the next, e.g. 123456789012 or 210987654321
  - any 12-digit string made of six doubled digits whose values step by a
    constant +1 or -1 (mod 10), e.g. 112233445566, 221100998877

Per-repo exceptions:
  - add the ID to a `.precommit-hooks-allowlist.txt` file at the repo root
    (one ID per line, '#' starts a comment), or
  - append `# allow-account-id` to the offending line.
"""

import re
import sys
from pathlib import Path

ACCOUNT_ID_RE = re.compile(r"(?<!\d)\d{12}(?!\d)")
ALWAYS_ALLOWED = {"123456789012", "111122223333", "444455556666"}
ALLOWLIST_FILENAME = ".precommit-hooks-allowlist.txt"
INLINE_MARKER = "allow-account-id"


def _is_repeated_digit(candidate: str) -> bool:
    return len(set(candidate)) == 1


def _steps_by(digits: list, step: int) -> bool:
    return all((digits[i] + step) % 10 == digits[i + 1] for i in range(len(digits) - 1))


def _is_sequential_digits(candidate: str) -> bool:
    """e.g. 123456789012 or 210987654321 - each digit is +/-1 (mod 10) from the last."""
    digits = [int(c) for c in candidate]
    return _steps_by(digits, 1) or _steps_by(digits, -1)


def _is_sequential_digit_pairs(candidate: str) -> bool:
    """e.g. 112233445566 or 221100998877 - six doubled digits stepping +/-1 (mod 10)."""
    pairs = [candidate[i : i + 2] for i in range(0, 12, 2)]
    if not all(pair[0] == pair[1] for pair in pairs):
        return False
    digits = [int(pair[0]) for pair in pairs]
    return _steps_by(digits, 1) or _steps_by(digits, -1)


def _is_placeholder_pattern(candidate: str) -> bool:
    return (
        _is_repeated_digit(candidate)
        or _is_sequential_digits(candidate)
        or _is_sequential_digit_pairs(candidate)
    )


def _load_repo_allowlist() -> set:
    allowlist_path = Path.cwd() / ALLOWLIST_FILENAME
    if not allowlist_path.exists():
        return set()
    entries = set()
    for line in allowlist_path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            entries.add(line)
    return entries


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    allowlist = ALWAYS_ALLOWED | _load_repo_allowlist()
    failed = False

    for filename in argv:
        path = Path(filename)
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        for lineno, line in enumerate(text.splitlines(), start=1):
            if INLINE_MARKER in line:
                continue
            for match in ACCOUNT_ID_RE.finditer(line):
                candidate = match.group()
                if candidate in allowlist or _is_placeholder_pattern(candidate):
                    continue
                print(
                    f"{filename}:{lineno}: possible real AWS account ID '{candidate}' "
                    f"committed to git. Use a placeholder (e.g. 123456789012), add it to "
                    f"{ALLOWLIST_FILENAME}, or mark the line with '# {INLINE_MARKER}'."
                )
                failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
