"""Fail if a CDK entrypoint doesn't wire in cdk-nag's AwsSolutionsChecks.

This is a cheap, static backstop, not real verification: it only proves the
string `AwsSolutionsChecks` appears somewhere in a file that also constructs
a `cdk.App()` - it can't tell if the wiring is dead code, commented out, or
actually applied via `Aspects.of(app).add(...)`. The real check is a pytest
test that synthesizes the stack with cdk-nag attached and asserts there are
no unsuppressed findings (see e.g. tests/test_ai_storage_stack.py::TestCdkNag
in the storage repo). This hook exists to catch the obvious regression -
someone deletes the two lines that wire cdk-nag in - before that test even
runs.

Only files that construct a CDK App (contain `cdk.App(`) are checked. To
exempt a specific file, add its exact repo-relative path to
`.precommit-hooks-allowlist.txt` at the repo root.
"""

import sys
from pathlib import Path

APP_MARKER = "cdk.App("
NAG_MARKER = "AwsSolutionsChecks"
ALLOWLIST_FILENAME = ".precommit-hooks-allowlist.txt"


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
    allowlist = _load_repo_allowlist()
    failed = False

    for filename in argv:
        normalized = filename.replace("\\", "/")
        if normalized in allowlist:
            continue

        path = Path(filename)
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        if APP_MARKER in text and NAG_MARKER not in text:
            print(
                f"{filename}: constructs a cdk.App() but never mentions "
                f"{NAG_MARKER} - cdk-nag doesn't appear to be wired in. If this "
                f"is deliberate, add this file's path to {ALLOWLIST_FILENAME}."
            )
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
