# Testing Guide

This project uses `pytest` for automated verification.

## Prerequisites

1. Open the repository root.
2. Activate the project virtual environment:

```bash
cd /home/slipnut44/git_repo/anykeep
. .venv/bin/activate
```

## Run all tests

```bash
pytest -q
```

## Run a specific test file

```bash
pytest -q tests/test_cli_config.py
```

## Run a single test

```bash
pytest -q tests/test_cli_config.py -k keyring
```

## What the tests cover

The test suite currently verifies:

- CLI help and command output
- auth command behavior without a `--set-key` flag
- default configuration fallback logic
- Takeout ZIP parsing behavior
- OS keyring read/write flow using a sample API key
- missing-key error handling

## Notes

- The keyring tests are intentionally mocked to avoid requiring a live desktop keyring service during CI or local headless runs.
- The sample key used in tests is stored in `tests/sample/sample_api_key.txt`.
- The project root is added to `sys.path` in `tests/conftest.py` so pytest can import `src.*` reliably from any working directory.
