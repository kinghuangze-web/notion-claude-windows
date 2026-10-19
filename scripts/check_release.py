"""Validate the public file allowlist without printing matched secret values."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "personal_email": re.compile(r"\b[A-Za-z0-9._%+-]+@(?!(?:example\.(?:com|invalid)|users\.noreply\.github\.com)\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", re.I),
    "personal_windows_home": re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+(?!Public(?:[\\/]|\b)|Default(?:[\\/]|\b))[^\s\"'<>]+", re.I),
    "private_source_path": re.compile(r"[A-Za-z]:[\\/]+wenjian[\\/]", re.I),
    "github_token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    "literal_api_key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "literal_cookie": re.compile(r"token_v2\s*[=:]\s*[\"']?[A-Za-z0-9%._-]{24,}", re.I),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "credential_assignment": re.compile(r"(?:api_key|auth_token|admin_password)[\"']?\s*[=:]\s*[\"'][A-Za-z0-9_-]{24,}[\"']", re.I),
}


def release_files():
    entries = (ROOT / "release-files.txt").read_text(encoding="utf-8").splitlines()
    return [x.strip() for x in entries if x.strip() and not x.lstrip().startswith("#")]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-index", action="store_true", help="Require Git tracked paths to equal the allowlist")
    options = parser.parse_args()
    files = release_files()
    issues = []
    if len(files) != len(set(files)):
        issues.append({"file": "release-files.txt", "rule": "duplicate_entry"})
    forbidden = {"runtime", "logs", "evidence", "demo", "_source", "_cache", "_tmp", ".venv", ".git", "_drafts", "dist"}
    for name in files:
        path = ROOT / name
        try:
            resolved = path.resolve(strict=True)
        except OSError:
            issues.append({"file": name, "rule": "missing_file"})
            continue
        if not resolved.is_relative_to(ROOT) or not resolved.is_file() or any(x in forbidden for x in Path(name).parts):
            issues.append({"file": name, "rule": "forbidden_path"})
            continue
        if path.is_symlink() or path.name in ("tools.local.ps1", "config.yaml", "token.txt"):
            issues.append({"file": name, "rule": "private_or_redirected_file"})
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeError:
            issues.append({"file": name, "rule": "non_text_file"})
            continue
        for rule, pattern in PATTERNS.items():
            if pattern.search(text):
                issues.append({"file": name, "rule": rule})
    if options.check_index:
        result = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True)
        if result.returncode:
            issues.append({"file": ".git", "rule": "git_index_unavailable"})
        else:
            tracked = set(result.stdout.decode("utf-8").rstrip("\0").split("\0"))
            for name in sorted(tracked.symmetric_difference(files)):
                issues.append({"file": name, "rule": "index_allowlist_difference"})
    print(json.dumps({"passed": not issues, "public_files": len(files), "issues": issues}, indent=2, ensure_ascii=False))
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
