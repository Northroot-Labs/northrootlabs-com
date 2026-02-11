#!/usr/bin/env python3
"""Verify DNS cutover and site reachability for northrootlabs.com."""

from __future__ import annotations

import argparse
import subprocess
import sys
from typing import List

EXPECTED_A = {
    "185.199.108.153",
    "185.199.109.153",
    "185.199.110.153",
    "185.199.111.153",
}


def run(cmd: List[str]) -> str:
    out = subprocess.check_output(cmd, text=True).strip()
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify DNS cutover for GitHub Pages.")
    parser.add_argument("--domain", default="northrootlabs.com")
    args = parser.parse_args()

    domain = args.domain
    www = f"www.{domain}"

    ns = sorted([x for x in run(["dig", "+short", "NS", domain]).splitlines() if x])
    a_records = sorted([x for x in run(["dig", "+short", "A", domain]).splitlines() if x])
    www_cname = run(["dig", "+short", "CNAME", www])
    headers = run(["curl", "-sI", f"http://{domain}/"])

    ok = True
    print("NS:")
    for x in ns:
        print(f"- {x}")
    print("A:")
    for x in a_records:
        print(f"- {x}")
    print(f"CNAME www: {www_cname or '(none)'}")

    if not set(a_records).intersection(EXPECTED_A):
        print("FAIL: apex A records do not include GitHub Pages IPs")
        ok = False

    if "github.io" not in www_cname and "northroot-labs.github.io" not in www_cname:
        print("FAIL: www CNAME is not pointing to northroot-labs.github.io")
        ok = False

    if "Namecheap URL Forward" in headers or "parking" in headers.lower():
        print("FAIL: domain still appears to use Namecheap forwarding/parking")
        ok = False

    if ok:
        print("PASS: DNS cutover checks look good.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
