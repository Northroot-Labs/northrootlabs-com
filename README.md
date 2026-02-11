# northrootlabs.com

Public landing site for Northroot Labs.

## Structure

- `index.html` - deployed public landing page.
- `scripts/check_public_content.py` - public safety checks.
- `scripts/cloudflare_set_github_pages_dns.py` - Cloudflare DNS parity automation.
- `scripts/namecheap_set_custom_nameservers.py` - registrar nameserver switch automation.
- `scripts/namecheap_set_github_pages_dns.py` - legacy Namecheap DNS automation fallback.
- `scripts/verify_dns_cutover.py` - DNS/state verification checks.
- `scripts/preflight_auth.py` - auth/tooling readiness checks for GitHub, Cloudflare, GCP, Namecheap.
- `.github/workflows/public-content-checks.yml` - CI checks for public content.
- `.github/workflows/deploy-pages.yml` - GitHub Pages deploy workflow.
- `.github/workflows/dns-cutover.yml` - approval-gated DNS cutover workflow.
- `.github/workflows/dns-verify.yml` - periodic DNS verification workflow.
- `.github/workflows/toolchain-preflight.yml` - manual preflight check for CLI/API auth readiness.
- `DNS_AUTOMATION.md` - DNS workflow and prerequisites.
