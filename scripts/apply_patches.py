"""Apply the ordered pinned patches, including upgrades from the original toolkit."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def apply(source, patches):
    def git(*args):
        return subprocess.run(["git", "-C", str(source), *map(str, args)], capture_output=True, text=True)

    # The first patch is cumulative against the pinned base; the second upgrades 1.0.x.
    if git("apply", "--reverse", "--check", patches[0]).returncode == 0:
        return "already_applied"
    dirty = git("status", "--porcelain")
    if dirty.returncode:
        raise RuntimeError("Cannot inspect pinned source")
    if not dirty.stdout.strip():
        pending = patches[:1]
    elif git("apply", "--check", patches[1]).returncode == 0:
        pending = patches[1:]
    else:
        raise RuntimeError("Source has incompatible changes; preserve it and use a fresh project copy")
    checked = git("apply", "--check", *pending)
    if checked.returncode:
        raise RuntimeError("Ordered patch compatibility check failed: " + checked.stderr.strip())
    result = git("apply", *pending)
    if result.returncode:
        raise RuntimeError("Patch application failed: " + result.stderr.strip())
    if git("apply", "--reverse", "--check", patches[0]).returncode:
        raise RuntimeError("Final source differs from the cumulative patch; preserve it for inspection")
    return "applied"


if __name__ == "__main__":
    try:
        print(apply(ROOT / "_source", [ROOT / "patches/opus55.patch", ROOT / "patches/full-mode-v2.patch"]))
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
