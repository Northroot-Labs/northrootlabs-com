#!/usr/bin/env python3
"""Configure Namecheap DNS records for GitHub Pages.

Defaults to dry-run. Use --apply to execute.
Requires env vars:
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


def build_common_params() -> Dict[str, str]:
    return {
        "ApiUser": required_env("NAMECHEAP_API_USER"),
        "ApiKey": required_env("NAMECHEAP_API_KEY"),
        "UserName": required_env("NAMECHEAP_USERNAME"),
        "ClientIp": required_env("NAMECHEAP_CLIENT_IP"),
    }


def host_payload() -> List[Tuple[str, str, str, str]]:
    # GitHub Pages apex + www pattern.
    return [
        ("@", "A", "185.199.108.153", "300"),
        ("@", "A", "185.199.109.153", "300"),
        ("@", "A", "185.199.110.153", "300"),
        ("@", "A", "185.199.111.153", "300"),
        ("www", "CNAME", "northroot-labs.github.io", "300"),
    ]


def build_sethosts_query(sld: str, tld: str) -> Dict[str, str]:
    params = build_common_params()
    params.update(
        {
            "Command": "namecheap.domains.dns.setHosts",
            "SLD": sld,
            "TLD": tld,
        }
    )
    for idx, (name, record_type, address, ttl) in enumerate(host_payload(), start=1):
        params[f"HostName{idx}"] = name
        params[f"RecordType{idx}"] = record_type
        params[f"Address{idx}"] = address
        params[f"TTL{idx}"] = ttl
    return params


def parse_domain(domain: str) -> Tuple[str, str]:
    parts = domain.split(".")
    if len(parts) < 2:
        raise ValueError(f"Invalid domain: {domain}")
    return parts[-2], parts[-1]


def call_namecheap(params: Dict[str, str]) -> str:
    query = urllib.parse.urlencode(params)
    url = f"{NAMECHEAP_API}?{query}"
    with urllib.request.urlopen(url, timeout=30) as response:  # nosec: B310
        return response.read().decode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Set Namecheap DNS for GitHub Pages.")
    parser.add_argument("--domain", default="northrootlabs.com")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Execute API call. Without this flag, prints the request only.",
    )
    args = parser.parse_args()

    try:
        sld, tld = parse_domain(args.domain)
        params = build_sethosts_query(sld, tld)
    except ValueError as exc:
        print(str(exc))
        return 2

    redacted = dict(params)
    redacted["ApiKey"] = "***"
    print("Prepared Namecheap request:")
    print(urllib.parse.urlencode(redacted))

    if not args.apply:
        print("Dry-run only. Re-run with --apply to execute.")
        return 0

    try:
        result_xml = call_namecheap(params)
    except Exception as exc:
        print(f"Namecheap API call failed: {exc}")
        return 1

    # Keep output concise and avoid parsing dependency for now.
    print("Namecheap API response (first 500 chars):")
    print(result_xml[:500])
    return 0


if __name__ == "__main__":
    sys.exit(main())
