"""Fail if a CDK stack sets a stateful resource's removal policy to DESTROY
without an explicit ack.

Buckets, tables, and databases with their removal policy set to DESTROY get deleted the
moment their CDK stack (or the resource itself) is removed - no snapshot, no
recycle bin. This hook flags every occurrence and requires a deliberate
opt-out per line, so it can't slip in by copy-paste or a default-arg change.

DESTROY may be exactly right for a throwaway/sandbox stack - this isn't a
ban, just a requirement that the choice be visible and intentional rather
than silent. To accept a specific occurrence, append `# allow-destroy-policy`
to that line.
"""

import re
import sys
from pathlib import Path

DESTROY_RE = re.compile(r"RemovalPolicy\.DESTROY")
INLINE_MARKER = "allow-destroy-policy"


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
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
            if DESTROY_RE.search(line):
                print(
                    f"{filename}:{lineno}: RemovalPolicy.DESTROY committed without "  # allow-destroy-policy
                    f"acknowledgement. If this is deliberate (e.g. a throwaway/sandbox "
                    f"stack), mark the line with '# {INLINE_MARKER}'."
                )
                failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
