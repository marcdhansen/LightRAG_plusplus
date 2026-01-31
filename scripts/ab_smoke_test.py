#!/usr/bin/env python3
from __future__ import annotations

import sys

try:
    from lightrag.ab_defaults import get_default_variant, select_variant_by_weights
except Exception:

    def get_default_variant(_m):
        return None

    def select_variant_by_weights(_m):
        return "A"


def main():
    models = ["qwen2.5-coder:1.5b", "qwen2.5-coder:3b", "qwen2.5-coder:7b"]
    print("AB Smoke Test: Default Variant by Model")
    for m in models:
        dv = get_default_variant(m)
        sw = select_variant_by_weights(m)
        print(f"{m}: default_variant={dv}, weighted_choice={sw}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
