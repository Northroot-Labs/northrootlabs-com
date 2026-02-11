#!/usr/bin/env python3
"""Set Namecheap custom nameservers (Cloudflare) for a domain.

Dry-run by default. Use --apply to execute.
Required env vars:
  NAMECHEAP_API_USER
  NAMECHEAP_API_KEY
  NAMECHEAP_USERNAME
  NAMECHEAP_CLIENT_IP
"""

from __future__ import annotations

import argparse
import os
import sys
import urllib.parse
import urllib.request
from typing import Dict, List, Tuple

NAMECHEAP_API = "https://api.namecheap.com/xml.response"


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def parse_domain(domain: str) -> Tuple[str, str]:
    parts = domain.split(".")
    if len(parts) < 2:
        raise ValueError(f"Invalid domain: {domain}")
    return parts[-2], parts[-1]


def build_query(sld: str, tld: str, nameservers: List[str]) -> Dict[str, str]:
    params = {
        "ApiUser": required_env("NAMECHEAP_API_USER"),
        "ApiKey": required_env("NAMECHEAP_API_KEY"),
        "UserName": required_env("NAMECHEAP_USERNAME"),
        "ClientIp": required_env("NAMECHEAP_CLIENT_IP"),
        "Command": "namecheap.domains.dns.setCustom",
        "SLD": sld,
        "TLD": tld,
        "Nameservers": ",".join(nameservers),
    }
    return params


def call_namecheap(params: Dict[str, str]) -> str:
    query = urllib.parse.urlencode(params)
    url = f"{NAMECHEAP_API}?{query}"
    with urllib.request.urlopen(url, timeout=30) as response:  # nosec: B310
        return response.read().decode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Set Namecheap custom nameservers")
    parser.add_argument("--domain", default="northrootlabs.com")
    parser.add_argument("--ns", nargs=2, required=True, help="Two nameservers")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    try:
        sld, tld = parse_domain(args.domain)
        params = build_query(sld, tld, args.ns)
    except ValueError as exc:
        print(str(exc))
        return 2

    redacted = dict(params)
    redacted["ApiKey"] = "***"
    print("Prepared Namecheap setCustom request:")
    print(urllib.parse.urlencode(redacted))

    if not args.apply:
        print("Dry-run only. Re-run with --apply to execute.")
        return 0

    try:
        result = call_namecheap(params)
    except Exception as exc:
        print(f"Namecheap API call failed: {exc}")
        return 1

    print("Namecheap API response (first 500 chars):")
    print(result[:500])
    return 0


if __name__ == "__main__":
    sys.exit(main())
