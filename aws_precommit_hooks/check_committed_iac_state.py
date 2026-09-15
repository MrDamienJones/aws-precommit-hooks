"""Fail if CDK/Terraform state or context files are committed.

`cdk.context.json` holds resolved, account-specific lookups (AZs, VPC IDs,
AMI IDs). Terraform state files can hold real secret values in plaintext.
Both are meant to be generated locally/in CI, not committed - `.gitignore`
normally keeps them out, but doesn't stop a deliberate `git add -f`. This
hook is that second line of defense.

To allow a specific file (rare - e.g. an intentionally-committed example),
add its exact repo-relative path to `.precommit-hooks-allowlist.txt` at the
repo root.
"""

import sys
from pathlib import Path

FORBIDDEN_NAMES = {"cdk.context.json"}
FORBIDDEN_SUFFIXES = (".tfstate", ".tfstate.backup")
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


def _is_forbidden(filename: str) -> bool:
    name = Path(filename).name
    return name in FORBIDDEN_NAMES or name.endswith(FORBIDDEN_SUFFIXES)


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    allowlist = _load_repo_allowlist()
    failed = False

    for filename in argv:
        normalized = filename.replace("\\", "/")
        if normalized in allowlist or not _is_forbidden(filename):
            continue
        print(
            f"{filename}: looks like a CDK/Terraform state or context file - these "
            f"hold resolved, account-specific values (and Terraform state can hold "
            f"real secrets). If committing it is deliberate, add its path to "
            f"{ALLOWLIST_FILENAME}."
        )
        failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
