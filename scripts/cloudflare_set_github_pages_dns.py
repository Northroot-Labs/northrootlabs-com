#!/usr/bin/env python3
"""Configure Cloudflare DNS records for GitHub Pages.

Dry-run by default. Use --apply to make API changes.

Required env vars:
  CLOUDFLARE_API_TOKEN
Optional:
  CLOUDFLARE_ACCOUNT_ID (used when creating a zone)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

API_BASE = "https://api.cloudflare.com/client/v4"


@dataclass
class DesiredRecord:
    record_type: str
    name: str
    content: str
    ttl: int = 300
    proxied: bool = False


DESIRED: List[DesiredRecord] = [
    DesiredRecord("A", "@", "185.199.108.153"),
    DesiredRecord("A", "@", "185.199.109.153"),
    DesiredRecord("A", "@", "185.199.110.153"),
    DesiredRecord("A", "@", "185.199.111.153"),
    DesiredRecord("CNAME", "www", "northroot-labs.github.io"),
]


def required_env(name: str) -> str:
    val = os.getenv(name, "").strip()
    if not val:
        raise ValueError(f"Missing required environment variable: {name}")
    return val


def cf_request(
    method: str,
    path: str,
    token: str,
    payload: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    data = None
    headers = {"Authorization": f"Bearer {token}"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        url=f"{API_BASE}{path}",
        method=method,
        headers=headers,
        data=data,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # nosec: B310
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Cloudflare API error {exc.code}: {body}") from exc


def get_zone_id(token: str, domain: str) -> Optional[str]:
    q = urllib.parse.urlencode({"name": domain})
    data = cf_request("GET", f"/zones?{q}", token)
    result = data.get("result", [])
    if not result:
        return None
    return str(result[0]["id"])


def create_zone(token: str, domain: str, account_id: str) -> Tuple[str, List[str]]:
    payload = {"name": domain, "account": {"id": account_id}, "type": "full"}
    data = cf_request("POST", "/zones", token, payload)
    if not data.get("success"):
        errs = data.get("errors", [])
        raise RuntimeError(f"Failed creating zone: {errs}")
    zone = data.get("result", {})
    zone_id = str(zone.get("id"))
    ns = [str(n) for n in zone.get("name_servers", [])]
    return zone_id, ns


def list_records(token: str, zone_id: str) -> List[Dict[str, object]]:
    data = cf_request("GET", f"/zones/{zone_id}/dns_records?per_page=100", token)
    return list(data.get("result", []))


def fqdn_for(label: str, domain: str) -> str:
    return domain if label == "@" else f"{label}.{domain}"


def find_record(
    records: List[Dict[str, object]],
    record_type: str,
    fqdn: str,
    content: str,
) -> Optional[Dict[str, object]]:
    for rec in records:
        if (
            rec.get("type") == record_type
            and rec.get("name") == fqdn
            and str(rec.get("content", "")).rstrip(".") == content.rstrip(".")
        ):
            return rec
    return None


def upsert_record(token: str, zone_id: str, record: DesiredRecord, domain: str) -> str:
    fqdn = fqdn_for(record.name, domain)
    existing = list_records(token, zone_id)
    match = find_record(existing, record.record_type, fqdn, record.content)
    if match:
        return f"exists: {record.record_type} {fqdn} -> {record.content}"
    payload = {
        "type": record.record_type,
        "name": fqdn,
        "content": record.content,
        "ttl": record.ttl,
        "proxied": record.proxied,
    }
    cf_request("POST", f"/zones/{zone_id}/dns_records", token, payload)
    return f"created: {record.record_type} {fqdn} -> {record.content}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Set Cloudflare DNS for GitHub Pages")
    parser.add_argument("--domain", default="northrootlabs.com")
    parser.add_argument("--apply", action="store_true", help="Apply DNS changes")
    parser.add_argument(
        "--create-zone",
        action="store_true",
        help="Create zone if missing (requires CLOUDFLARE_ACCOUNT_ID)",
    )
    args = parser.parse_args()

    token = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
    if not token:
        if args.apply:
            print("Missing required environment variable: CLOUDFLARE_API_TOKEN")
            return 2
        print("No CLOUDFLARE_API_TOKEN found; dry-run plan only.")
        for r in DESIRED:
            print(f"would upsert: {r.record_type} {fqdn_for(r.name, args.domain)} -> {r.content}")
        if args.create_zone:
            print("would create zone if missing (requires CLOUDFLARE_ACCOUNT_ID + API token).")
        return 0

    zone_id = get_zone_id(token, args.domain)
    nameservers: List[str] = []
    if zone_id is None:
        print(f"Zone not found for {args.domain}.")
        if not args.create_zone:
            print("Re-run with --create-zone to create it.")
            return 1
        try:
            account_id = required_env("CLOUDFLARE_ACCOUNT_ID")
        except ValueError as exc:
            print(str(exc))
            return 2
        if not args.apply:
            print("Dry-run: would create zone.")
            return 0
        zone_id, nameservers = create_zone(token, args.domain, account_id)
        print(f"Zone created: {zone_id}")
        if nameservers:
            print("Assigned nameservers:")
            for ns in nameservers:
                print(f"- {ns}")

    assert zone_id is not None

    if not args.apply:
        print(f"Dry-run: zone {zone_id}")
        for r in DESIRED:
            print(f"would upsert: {r.record_type} {fqdn_for(r.name, args.domain)} -> {r.content}")
        return 0

    for r in DESIRED:
        msg = upsert_record(token, zone_id, r, args.domain)
        print(msg)

    print("Cloudflare DNS parity ensured.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
