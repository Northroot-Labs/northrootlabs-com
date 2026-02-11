# DNS automation for northrootlabs.com

Cloudflare-first DNS automation for GitHub Pages, with Namecheap retained as registrar.

## Prerequisites

- Cloudflare zone exists for `northrootlabs.com` (or allow script to create it).
- Cloudflare API token scoped to the `northrootlabs.com` zone with DNS edit/read only.
- Optional Namecheap API access for nameserver updates.

Environment variables:

- Cloudflare:
  - `CLOUDFLARE_API_TOKEN`
  - `CLOUDFLARE_ACCOUNT_ID` (only needed for `--create-zone`)
- Namecheap (only for nameserver switch automation):
  - `NAMECHEAP_API_USER`
  - `NAMECHEAP_API_KEY`
  - `NAMECHEAP_USERNAME`
  - `NAMECHEAP_CLIENT_IP`

## Dry run

```bash
python scripts/cloudflare_set_github_pages_dns.py --domain northrootlabs.com
```

## Apply Cloudflare DNS parity

```bash
python scripts/cloudflare_set_github_pages_dns.py --domain northrootlabs.com --apply
```

## Create zone if missing (Cloudflare)

```bash
python scripts/cloudflare_set_github_pages_dns.py --domain northrootlabs.com --create-zone --apply
```

## Switch registrar nameservers (Namecheap -> Cloudflare)

```bash
python scripts/namecheap_set_custom_nameservers.py --domain northrootlabs.com --ns "<cf_ns1>" "<cf_ns2>" --apply
```

## Target records in Cloudflare

- `@` A `185.199.108.153`
- `@` A `185.199.109.153`
- `@` A `185.199.110.153`
- `@` A `185.199.111.153`
- `www` CNAME `northroot-labs.github.io`

## Notes

- Existing Namecheap URL forwarding/parking must be disabled before/at cutover.
- After DNS propagation and certificate issuance, enforce HTTPS on GitHub Pages.
- Approval-gated workflow for cutover is in `.github/workflows/dns-cutover.yml`.
- Ongoing verification workflow is in `.github/workflows/dns-verify.yml`.
- Rollback steps are in `dns/ROLLBACK.md`.
