#!/usr/bin/env python3
"""Pre-submission sanity checks for CivicPulse. Extend as needed."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def check_env_not_tracked(files: list[str]) -> bool:
    return ".env" not in files


def check_env_example_exists() -> bool:
    return (REPO_ROOT / ".env.example").is_file()


def check_no_large_files(files: list[str]) -> bool:
    ok = True
    for rel_path in files:
        path = REPO_ROOT / rel_path
        if path.is_file() and path.stat().st_size > MAX_FILE_SIZE_BYTES:
            print(f"  - {rel_path} exceeds 5MB")
            ok = False
    return ok


def report(name: str, passed: bool) -> None:
    print(f"[{'PASS' if passed else 'FAIL'}] {name}")


def main() -> int:
    files = tracked_files()

    results = {
        ".env is not tracked by git": check_env_not_tracked(files),
        ".env.example exists": check_env_example_exists(),
        "no tracked file exceeds 5MB": check_no_large_files(files),
    }

    for name, passed in results.items():
        report(name, passed)

    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
