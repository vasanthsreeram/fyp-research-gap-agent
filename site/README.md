# FYP progress board (fyp.vasanth.my)

Multi-page, passphrase-gated Cloudflare Worker site for async supervisor updates.

## Pages
| Path | Content |
|------|---------|
| `/` | Overview, stats, timeline, checklist |
| `/results.html` | Charts + gap/claim/paper tables |
| `/topics.html` | Topic proposals |
| `/method.html` | Interactive Mermaid diagrams |
| `/docs.html` | STATUS, supervisor brief, run report |

## Deploy
```bash
cd site
# secrets once:
# wrangler secret put SITE_PASSWORD
# wrangler secret put SESSION_SECRET
CLOUDFLARE_API_TOKEN=… wrangler deploy
```

Custom domain: `fyp.vasanth.my` (Workers custom domain).

## Update data
```bash
# from repo root after a pipeline run
python3 - <<'PY'
# or re-run the bundle builder used in site setup
PY
# copy STATUS / draft / latest_run into site/public/data/
wrangler deploy
```

Passphrase lives in macOS Keychain `openclaw/fyp/vasanth-site-passphrase` (account `vasanth`).
