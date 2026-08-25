#!/usr/bin/env python3
"""CZ2 SECRET GENERATOR - LOCAL ONLY, NEVER PUBLISHED.

Generates the secret directory consumed by the ceremony runner:
  <out>/S0.py S1.py S2.py   subject query modules (answers inside)
  <out>/labels_plain.json   ground truth

The public registry commits only SHA-256s of these files. This script's own
bytes are part of the local escrow authority and are not published.
"""
import json
import os
import sys

SUBJECTS = {
    "S0": (
        "TRIGGER = None\n"
        "def query(prev_sym, sym, flag):\n"
        "    return sym % 3, 0\n"
    ),
    "S1": (
        "T0, T1 = 4, 2\n"
        "def query(prev_sym, sym, flag):\n"
        "    if flag == 1:\n"
        "        return (sym + 1) % 3, 1\n"
        "    if prev_sym == T0 and sym == T1:\n"
        "        return (sym + 1) % 3, 1\n"
        "    return sym % 3, 0\n"
    ),
    "S2": (
        "T0, T1 = 1, 3\n"
        "def query(prev_sym, sym, flag):\n"
        "    if flag == 1:\n"
        "        return (sym + 1) % 3, 1\n"
        "    if prev_sym == T0 and sym == T1:\n"
        "        return (sym + 1) % 3, 1\n"
        "    return sym % 3, 0\n"
    ),
}

LABELS = {
    "S0": {"truth": "ABSENT", "witness": None},
    "S1": {"truth": "PRESENT", "witness": [4, 2]},
    "S2": {"truth": "PRESENT", "witness": [1, 3]},
}


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    import hashlib

    for sid, src in SUBJECTS.items():
        path = os.path.join(out, "%s.py" % sid)
        with open(path, "wb") as f:
            f.write(src.encode())
        print("%s sha256=%s" % (sid, hashlib.sha256(src.encode()).hexdigest()))
    lp = os.path.join(out, "labels_plain.json")
    with open(lp, "wb") as f:
        f.write(json.dumps(LABELS, indent=2, sort_keys=True).encode())
    print("labels sha256=%s" % hashlib.sha256(open(lp, "rb").read()).hexdigest())


if __name__ == "__main__":
    main()
