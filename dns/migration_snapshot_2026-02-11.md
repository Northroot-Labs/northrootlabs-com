# DNS migration snapshot (2026-02-11)

Purpose: baseline before moving DNS authority from Namecheap-managed DNS to Cloudflare.

## Snapshot source checks

Commands used:

```bash
dig +short NS northrootlabs.com
dig +short A northrootlabs.com
dig +short CNAME www.northrootlabs.com
curl -sI http://northrootlabs.com/
```

Observed values:

- NS:
  - `dns1.registrar-servers.com.`
  - `dns2.registrar-servers.com.`
- A (`northrootlabs.com`):
  - `162.255.119.15`
- CNAME (`www.northrootlabs.com`):
  - `parkingpage.namecheap.com.`
- HTTP behavior:
  - `302 Found`
  - `Location: http://www.northrootlabs.com/`
  - `X-Served-By: Namecheap URL Forward`

## Freeze declaration

- Freeze non-essential DNS changes until migration cutover is complete.
- Allowed during freeze:
  - Parity record preparation in Cloudflare.
  - Cutover and rollback operations only.
