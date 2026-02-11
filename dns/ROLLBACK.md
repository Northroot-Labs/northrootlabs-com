# DNS rollback procedure

Use this if Cloudflare cutover causes degraded availability.

## Inputs required

- Previous registrar nameservers (from migration snapshot).
- Previous DNS records snapshot.

## Steps

1. At Namecheap registrar, restore prior nameservers.
2. Confirm authoritative NS has reverted:

```bash
dig +short NS northrootlabs.com
```

3. Restore previous DNS records if needed.
4. Validate service:

```bash
python scripts/verify_dns_cutover.py --domain northrootlabs.com
```

5. Record the rollback and rationale in break-glass evidence docs:
   - `northroot-docs/internal/security/BREAK_GLASS_AND_EVIDENCE.md`
