# Hermes FMV Partial-Write Fix

A standalone, applyable patch for a Hermes Agent file-mutation-verifier (FMV) edge case: a multi-file V4A patch can modify some files and then fail on a later operation, while FMV reports every requested file as unmodified.

This repository is **not an upstream fork** and does not modify the local Hermes installation. It is a small patch kit that can be fetched on another machine, reviewed, and applied to a compatible Hermes checkout.

## Behavior corrected

When a patch result has `success: false` but reports non-empty `files_modified`, `files_created`, or `files_deleted` lists:

- those paths are treated as landed mutations;
- move results record both source and destination paths;
- only targets not reported as landed remain in the FMV failure state;
- a complete failure with no landed paths remains a failure.

The verifier remains enabled and fail-loud. This does not suppress FMV warnings or weaken verification.

## Baseline

- Upstream repository: <https://github.com/NousResearch/hermes-agent>
- Tested baseline commit: `b6bcb3e791c673e63974029bbab40cc9326803ff`
- Patch: `patches/hermes-fmv-partial-write-fix.patch`
- Patch SHA-256: `51dd143d79b3ab4e53e8081bb1c454f97f79f9a53f62da53bca418e33c87bde2`

## Apply on another machine

```bash
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
git checkout b6bcb3e791c673e63974029bbab40cc9326803ff

git apply --check /path/to/hermes-fmv-partial-write-fix.patch
git apply /path/to/hermes-fmv-partial-write-fix.patch
```

Then run the focused verification using the checkout's supported Python environment:

```bash
python -m pytest \
  tests/agent/test_tool_result_classification.py \
  tests/agent/test_tool_dispatch_helpers.py \
  tests/run_agent/test_file_mutation_verifier.py \
  tests/tools/test_patch_failure_tracking.py \
  tests/tools/test_patch_parser.py \
  -q
```

If the upstream files have changed, do not force-apply the patch. Rebase the five-file change manually and rerun the same tests.

## Verification performed

TDD was used:

1. Added two focused regressions and observed the expected failures.
2. Implemented the minimal partial-write classification/state fix.
3. Expanded coverage across update, add, delete, move, and no-write failure cases.
4. Focused modules passed: `35 passed`.
5. Adjacent blast-radius suite passed: `102 passed`.

The one pytest warning observed was `PytestAssertRewriteWarning` for an already-imported `anyio` module caused by using the existing Hermes virtual environment; it was not a test failure.

See `provenance.json` for machine-readable hashes and scope.

## Files changed in Hermes

- `agent/tool_result_classification.py`
- `agent/tool_dispatch_helpers.py`
- `run_agent.py`
- `tests/agent/test_tool_result_classification.py`
- `tests/run_agent/test_file_mutation_verifier.py`

## Scope and non-goals

- No automatic retry or overwrite behavior is added.
- No FMV configuration is disabled.
- No verification-evidence ledger behavior is changed.
- No upstream repository, branch, issue, or pull request is created or modified.
- No organization-specific data, credentials, runtime logs, or machine-specific paths are included.

## License

The patch modifies MIT-licensed Hermes Agent source. The upstream MIT license is reproduced in `LICENSE`.
