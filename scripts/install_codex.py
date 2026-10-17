#!/usr/bin/env python3
"""Install the complete skill for Codex without overwriting existing files."""
import argparse
import shutil
from pathlib import Path


def install(destination):
    source = Path(__file__).resolve().parents[1] / "youtube-english-study"
    source_files = {
        p.relative_to(source): p for p in source.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    }
    if destination.is_symlink():
        raise SystemExit(f"Refusing symlink destination: {destination}")
    if destination.exists():
        if not destination.is_dir():
            raise SystemExit(f"Destination is not a directory: {destination}")
        existing = {
            p.relative_to(destination): p for p in destination.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
        }
        if (existing.keys() != source_files.keys()
                or any(p.is_symlink() for p in destination.rglob("*"))
                or any(existing[k].read_bytes() != v.read_bytes()
                       for k, v in source_files.items())):
            raise SystemExit(f"Existing skill differs; back it up and move it first: {destination}")
        print(f"Already installed and verified: {destination}")
        return
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print(f"Installed: {destination}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, help="Install under this project's .agents/skills")
    args = parser.parse_args()
    root = args.project.expanduser().resolve() if args.project else Path.home()
    install(root / ".agents" / "skills" / "youtube-english-study")
    print("Reopen Codex, then invoke $youtube-english-study with a YouTube URL.")


if __name__ == "__main__":
    main()
