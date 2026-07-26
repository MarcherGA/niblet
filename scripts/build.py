#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from niblet.publisher import build_site


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the released Niblet site")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--secret", default="soft-orbit-47")
    parser.add_argument("--output", type=Path, default=ROOT / "public")
    args = parser.parse_args()
    result = build_site(ROOT / "content", args.output, as_of=args.as_of, secret=args.secret)
    (args.output / ".nojekyll").write_text("", encoding="utf-8")
    print(result)


if __name__ == "__main__":
    main()
