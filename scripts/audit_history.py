"""Scan all reachable Git blobs and identity metadata; never print matched values."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from check_release import ROOT, PATTERNS


def audit(root=ROOT, private_values=()):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args])
    commits = git("rev-list", "--all").decode().splitlines()
    objects, issues = {}, []
    identities = set()
    for commit in commits:
        # Commit messages are checked too; personal emails in metadata are reported by kind only.
        metadata = git("show", "-s", "--format=%an%n%ae%n%cn%n%ce%n%B", commit).decode("utf-8", errors="replace").splitlines()
        for email in (metadata[1], metadata[3]):
            identities.add(hashlib.sha256(email.encode()).hexdigest())
            if not re.fullmatch(r"[^\s@]+@users\.noreply\.github\.com", email):
                issues.append({"commit": commit, "rule": "non_noreply_identity_email"})
        for name, pattern in PATTERNS.items():
            if pattern.search("\n".join(metadata[4:])):
                issues.append({"commit": commit, "rule": name, "scope": "message"})
        for row in git("ls-tree", "-r", "-z", commit).split(b"\0"):
            if not row:
                continue
            meta, path = row.split(b"\t", 1)
            _, kind, oid = meta.decode().split()
            if kind == "blob":
                objects.setdefault(oid, set()).add(path.decode("utf-8"))
    for oid, paths in objects.items():
        data = git("cat-file", "blob", oid)
        text = data.decode("utf-8", errors="replace")
        for name, pattern in PATTERNS.items():
            if pattern.search(text):
                issues.append({"object": oid, "files": sorted(paths), "rule": name})
        if any(value.encode() in data for value in private_values):
            issues.append({"object": oid, "files": sorted(paths), "rule": "exact_local_private_value"})
    return {"passed": not issues, "commits": len(commits), "unique_blobs": len(objects),
            "identity_count": len(identities), "private_values_compared": len(private_values), "issues": issues}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-values-file", type=Path, help="Ignored local JSON string array; values never printed")
    options = parser.parse_args()
    values = []
    if options.private_values_file:
        path = options.private_values_file.resolve()
        if not path.is_relative_to((ROOT / "runtime/private").resolve()):
            raise RuntimeError("Exact-match values must stay under ignored runtime/private")
        values = json.loads(path.read_text("utf-8"))
        if not isinstance(values, list) or not all(isinstance(v, str) and len(v) >= 5 for v in values):
            raise RuntimeError("Expected a local array of private strings, each at least five characters")
    result = audit(private_values=values)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
