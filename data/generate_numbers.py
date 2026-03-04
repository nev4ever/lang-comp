#!/usr/bin/env python3
import argparse
import random
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic random numbers")
    parser.add_argument("--count", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min", dest="min_value", type=int, default=0)
    parser.add_argument("--max", dest="max_value", type=int, default=100000)
    parser.add_argument("--output", type=Path, default=Path("data/numbers.txt"))
    args = parser.parse_args()

    random.seed(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8") as f:
        for _ in range(args.count):
            f.write(f"{random.randint(args.min_value, args.max_value)}\n")

    print(f"Generated {args.count} numbers at {args.output}")


if __name__ == "__main__":
    main()
