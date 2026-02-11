# DNS automation for northrootlabs.com

Programmatic DNS setup for GitHub Pages via Namecheap API.

## Prerequisites

- Namecheap API access enabled.
- Client IP allowlisted in Namecheap API settings.
- Environment variables set:
  - `NAMECHEAP_API_USER`
  - `NAMECHEAP_API_KEY`
  - `NAMECHEAP_USERNAME`
  - `NAMECHEAP_CLIENT_IP`

## Dry run

```bash
python scripts/namecheap_set_github_pages_dns.py --domain northrootlabs.com
```

## Apply DNS records

```bash
python scripts/namecheap_set_github_pages_dns.py --domain northrootlabs.com --apply
```

## Records applied

- `@` A `185.199.108.153`
- `@` A `185.199.109.153`
- `@` A `185.199.110.153`
- `@` A `185.199.111.153`
- `www` CNAME `northroot-labs.github.io`

## Notes

- Existing URL forwarding/parking must be disabled in Namecheap.
- After DNS propagation and certificate issuance, enforce HTTPS on GitHub Pages.
