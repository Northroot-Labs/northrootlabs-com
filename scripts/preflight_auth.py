#!/usr/bin/env python3
"""Auth/toolchain preflight for GitHub, Cloudflare, Google Cloud, Namecheap.

Default behavior is non-fatal with actionable guidance.
Use --strict to fail when required providers are not ready.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class CheckResult:
    ok: bool
    summary: str
    details: List[str]


def run(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


def has_cmd(name: str) -> bool:
    return shutil.which(name) is not None


def check_github() -> CheckResult:
    details: List[str] = []
    if not has_cmd("gh"):
        return CheckResult(
            False,
            "GitHub CLI missing",
            ["Install gh and run: gh auth login"],
        )
    r = run(["gh", "auth", "status"])
    if r.returncode == 0:
        return CheckResult(True, "GitHub auth ready", [])
    details.append("gh found but not authenticated.")
    details.append("Run: gh auth login")
    return CheckResult(False, "GitHub auth missing", details)


def check_cloudflare() -> CheckResult:
    token = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
    if token:
        return CheckResult(True, "Cloudflare token present", [])
    return CheckResult(
        False,
        "Cloudflare token missing",
        [
            "Set CLOUDFLARE_API_TOKEN (and CLOUDFLARE_ACCOUNT_ID if creating zones).",
            "For CI, put these in protected environment secrets.",
        ],
    )


def check_gcloud() -> CheckResult:
    details: List[str] = []
    if not has_cmd("gcloud"):
        return CheckResult(
            False,
            "gcloud CLI missing",
            ["Install gcloud SDK and run: gcloud auth login"],
        )

    # Accept either active user auth or explicit workload/service account env wiring.
    active = run(
        ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"]
    )
    account = (active.stdout or "").strip()
    project = run(["gcloud", "config", "get-value", "project"]).stdout.strip()

    wid = os.getenv("GCP_WORKLOAD_IDENTITY_PROVIDER", "").strip()
    sa = os.getenv("GCP_SERVICE_ACCOUNT", "").strip()
    sa_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON", "").strip()

    if account:
        return CheckResult(
            True,
            "gcloud auth ready",
            [f"active_account={account}", f"project={project or '(unset)'}"],
        )
    if wid and sa:
        return CheckResult(
            True,
            "GCP workload identity wiring present",
            ["Using workload identity provider + service account env vars."],
        )
    if sa_json:
        return CheckResult(
            True,
            "GCP service account JSON secret present",
            ["Prefer workload identity over long-lived key JSON when possible."],
        )

    details.append("No active gcloud auth account found.")
    details.append("Local: gcloud auth login && gcloud config set project <project_id>")
    details.append(
        "CI preferred: set GCP_WORKLOAD_IDENTITY_PROVIDER + GCP_SERVICE_ACCOUNT."
    )
    return CheckResult(False, "Google Cloud auth missing", details)


def check_namecheap() -> CheckResult:
    required = [
        "NAMECHEAP_API_USER",
        "NAMECHEAP_API_KEY",
        "NAMECHEAP_USERNAME",
        "NAMECHEAP_CLIENT_IP",
    ]
    missing = [k for k in required if not os.getenv(k, "").strip()]
    if not missing:
        return CheckResult(True, "Namecheap fallback creds present", [])
    return CheckResult(
        False,
        "Namecheap fallback creds missing",
        [
            "Missing: " + ", ".join(missing),
            "Fallback only: prefer Cloudflare DNS authority for routine operations.",
        ],
    )


CHECKERS = {
    "github": check_github,
    "cloudflare": check_cloudflare,
    "gcloud": check_gcloud,
    "namecheap": check_namecheap,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Auth/toolchain preflight checks")
    parser.add_argument(
        "--require",
        nargs="*",
        default=[],
        choices=sorted(CHECKERS.keys()),
        help="Providers that must be ready",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if any required check is not ready",
    )
    parser.add_argument("--context", default="local", choices=["local", "ci"])
    args = parser.parse_args()

    required = set(args.require)
    results: Dict[str, CheckResult] = {}
    for name, fn in CHECKERS.items():
        results[name] = fn()

    print(f"preflight context: {args.context}")
    for name in ["github", "cloudflare", "gcloud", "namecheap"]:
        res = results[name]
        state = "OK" if res.ok else "WARN"
        required_marker = " (required)" if name in required else ""
        print(f"[{state}] {name}{required_marker}: {res.summary}")
        for d in res.details:
            print(f"  - {d}")

    missing_required = [n for n in required if not results[n].ok]
    if args.strict and missing_required:
        print("FAIL: required providers not ready: " + ", ".join(sorted(missing_required)))
        return 1

    if missing_required:
        print(
            "INFO: required providers missing but strict mode disabled; "
            "continuing with guidance above."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
