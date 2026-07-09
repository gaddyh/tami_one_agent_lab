from __future__ import annotations

import shutil
import sys
from pathlib import Path


TEMPLATE_DIR = Path("features/000-template")
FEATURES_DIR = Path("features")


def slugify(name: str) -> str:
    return name.strip().lower().replace(" ", "-").replace("_", "-")


def next_index() -> int:
    indexes = []
    for path in FEATURES_DIR.iterdir():
        if path.is_dir() and path.name[:3].isdigit():
            indexes.append(int(path.name[:3]))
    return max(indexes, default=0) + 1


def replace_placeholders(path: Path, feature_name: str) -> None:
    for md_file in path.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        content = content.replace("<feature-name>", feature_name)
        md_file.write_text(content, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/new_feature.py <feature-name>")

    name = slugify(sys.argv[1])
    target = FEATURES_DIR / f"{next_index():03d}-{name}"
    if target.exists():
        raise SystemExit(f"Feature already exists: {target}")

    shutil.copytree(TEMPLATE_DIR, target)
    replace_placeholders(target, name)
    print(f"Created {target}")


if __name__ == "__main__":
    main()
