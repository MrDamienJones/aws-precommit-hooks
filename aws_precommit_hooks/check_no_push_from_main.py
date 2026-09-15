"""Fail a `git push` made while checked out on a protected branch directly.

This is a fast, local speed bump for "everything goes via a branch and a
PR/MR" - not real enforcement. It only fires on a machine that ran
`pre-commit install` (which enables this for the `pre-push` git hook stage),
and anyone can bypass it with `git push --no-verify`. The actual guarantee
comes from server-side branch protection on the remote (require a PR before
merging to main, block direct pushes) - set that up on the repo itself; this
hook is just a courtesy that catches the common accident before it leaves
your machine.

Protected branches default to `main` and `master`. Override per-repo with a
`PROTECTED_BRANCHES` line in `.precommit-hooks-allowlist.txt` at the repo
root, e.g. `PROTECTED_BRANCHES=main,release`.
"""

import subprocess
from pathlib import Path

DEFAULT_PROTECTED_BRANCHES = {"main", "master"}
ALLOWLIST_FILENAME = ".precommit-hooks-allowlist.txt"


def _load_protected_branches() -> set:
    allowlist_path = Path.cwd() / ALLOWLIST_FILENAME
    if not allowlist_path.exists():
        return DEFAULT_PROTECTED_BRANCHES

    for line in allowlist_path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line.startswith("PROTECTED_BRANCHES="):
            branches = {b.strip() for b in line.split("=", 1)[1].split(",") if b.strip()}
            return branches or DEFAULT_PROTECTED_BRANCHES

    return DEFAULT_PROTECTED_BRANCHES


def _current_branch() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def main(argv=None) -> int:
    del argv  # pre-push hooks receive no useful filename args; unused here
    branch = _current_branch()
    protected = _load_protected_branches()

    if branch in protected:
        print(
            f"Direct push from '{branch}' is blocked. Push a branch and open a PR/MR "
            f"instead. (Local-only speed bump - the real guarantee is branch "
            f"protection on the remote. Override with PROTECTED_BRANCHES= in "
            f"{ALLOWLIST_FILENAME} if this repo genuinely doesn't use PRs.)"
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
