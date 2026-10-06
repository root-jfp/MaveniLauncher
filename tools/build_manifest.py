from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Maveni per-file update manifest")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--news-file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"Client root does not exist: {root}")
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if path.name.startswith("."):
            continue
        files.append({
            "path": relative,
            "sha256": digest(path),
            "size": path.stat().st_size,
        })
    news = args.news_file.read_text(encoding="utf-8") if args.news_file and args.news_file.exists() else ""
    manifest = {
        "version": args.version,
        "base_url": args.base_url.rstrip("/"),
        "news": news,
        "files": files,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"manifest: {len(files)} files -> {args.output}")


if __name__ == "__main__":
    main()
