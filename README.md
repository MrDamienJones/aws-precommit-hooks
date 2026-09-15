# aws-precommit-hooks

Shared [pre-commit](https://pre-commit.com) hooks for AWS repos, meant to be reused across
unrelated AWS accounts/orgs (not tied to any one of them) rather than copy-pasted into each repo.

## Setup

```bat
py -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements-dev.txt
pre-commit install
```

`requirements-dev.txt` includes `-e .`, so the console scripts (`no-real-aws-account-ids`,
etc.) are on the venv's path - required both for `pip install .` consumers and for this
repo's own `.pre-commit-config.yaml`, which dogfoods its own hooks against itself via
`python -m aws_precommit_hooks.<module>`.

## Hooks

### `no-real-aws-account-ids`

Fails if a committed file contains a 12-digit number shaped like a real AWS account ID
that isn't a recognised placeholder. See
[aws_precommit_hooks/check_aws_account_ids.py](aws_precommit_hooks/check_aws_account_ids.py)
for what counts as a placeholder and how to add a per-repo exception.

### `no-destroy-removal-policy`

Fails if `RemovalPolicy.DESTROY` is committed (Python or TypeScript CDK) without an
explicit `# allow-destroy-policy` marker on that line. Not a ban - DESTROY may be the
right call for a throwaway/sandbox stack - just a requirement that the choice is visible
rather than silent. See
[aws_precommit_hooks/check_destroy_removal_policy.py](aws_precommit_hooks/check_destroy_removal_policy.py).

### `no-committed-iac-state`

Fails if `cdk.context.json` or a Terraform `.tfstate`/`.tfstate.backup` file is committed.
Both hold resolved, account-specific values that are meant to be generated locally/in CI,
not committed - this is a backstop for when `.gitignore` gets bypassed by a `git add -f`.
See
[aws_precommit_hooks/check_committed_iac_state.py](aws_precommit_hooks/check_committed_iac_state.py)
for the per-file exception mechanism.

### `require-cdk-nag-present`

Fails if a file constructs a `cdk.App()` but never mentions `AwsSolutionsChecks`. This is
a cheap, static presence check, **not real verification** - it only proves the string
appears somewhere in the file, not that cdk-nag is actually wired in and passing. Pair it
with a pytest test that actually synthesizes the stack with cdk-nag attached and asserts on
the result (see `tests/test_ai_storage_stack.py::TestCdkNag` in the storage repo, or
`infra/tests/test_garmin_agent_stack.py::TestCdkNag` in garmin_analysis, for the real check).
See
[aws_precommit_hooks/check_cdk_nag_present.py](aws_precommit_hooks/check_cdk_nag_present.py).

### `no-push-from-main`

Fails a `git push` made while checked out on `main`/`master` directly - "everything goes
via a branch and a PR/MR". This is a **local speed bump, not real enforcement**: it only
fires on a machine that ran `pre-commit install` for the `pre-push` hook stage, and
`git push --no-verify` skips it entirely. The actual guarantee is server-side branch
protection on the remote (require a PR before merging, block direct pushes) - set that up
on the repo itself; this hook just catches the common accident before it leaves your
machine. Override the protected-branch list per-repo via `PROTECTED_BRANCHES=` in
`.precommit-hooks-allowlist.txt`. See
[aws_precommit_hooks/check_no_push_from_main.py](aws_precommit_hooks/check_no_push_from_main.py).
Not AWS-specific (unlike the other hooks here) - kept in this repo for now since it's
small and this is where it was first needed; a candidate to move if a general,
non-AWS-scoped hooks repo ever exists.

## Using this from another repo

Add the hooks you want to that repo's `.pre-commit-config.yaml`:

```yaml
default_install_hook_types: [pre-commit, pre-push]

repos:
  - repo: https://github.com/MrDamienJones/aws-precommit-hooks
    rev: v1.0.0
    hooks:
      - id: no-real-aws-account-ids
      - id: no-destroy-removal-policy
      - id: no-committed-iac-state
      - id: require-cdk-nag-present
      - id: no-push-from-main
```

`no-push-from-main` runs at the `pre-push` git hook stage, not the default `commit` stage -
the `default_install_hook_types` line above is what makes a plain `pre-commit install`
enable both (otherwise `pre-push` hooks are silently never installed and never run).

## Tests

Each hook has a matching pytest file under `tests/` covering its positive/negative
cases and exception mechanisms directly (no subprocess involved - `main()` is called
in-process, which is faster and doesn't hit platform-specific process-launching quirks).

```bat
pytest tests/ -v
```

This repo also dogfoods its own hooks (plus generic hygiene, ruff, detect-secrets)
against itself via `.pre-commit-config.yaml`:

```bat
pre-commit run --all-files
```

## Releasing a new version

`main` is protected on GitHub (PR required, no direct pushes, applies to admins too) -
land changes via a branch + PR, then from `main`:

```bat
git tag vX.Y.Z -m "..."
git push origin vX.Y.Z
```

Then bump `rev:` in each consuming repo's `.pre-commit-config.yaml` to that tag (or let
[Renovate's pre-commit manager](https://docs.renovatebot.com/modules/manager/pre-commit/)
do it automatically).
