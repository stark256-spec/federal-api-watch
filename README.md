# federal-api-watch

Public uptime and changelog tracker for U.S. federal government APIs.

Every developer who builds on government APIs has been burned by silent changes with no notice. This project fixes that — open monitoring, transparent history, embeddable badges.

**[→ Live status page](https://stark256-spec.github.io/federal-api-watch/)**
&nbsp;·&nbsp;
**[→ RSS changelog feed](https://stark256-spec.github.io/federal-api-watch/feed.xml)**

![Federal APIs](https://img.shields.io/endpoint?url=https://stark256-spec.github.io/federal-api-watch/badge/summary.json)

---

## APIs monitored

| API | Agency | Category |
|---|---|---|
| Data.gov Catalog | GSA | Open Data |
| Federal Register | OFR / GPO | Regulations |
| eCFR | OFR / GPO | Regulations |
| Grants.gov Search | HHS | Grants |
| USASpending | Treasury / OMB | Spending |
| SAM.gov Entity | GSA | Procurement |
| FEC | FEC | Elections |
| Census ACS | Census Bureau | Demographics |
| BLS Public Data | DOL | Labor |
| FRED Economic Data | Federal Reserve | Economics |
| NASA APIs | NASA | Science |
| NOAA Climate Data | NOAA | Climate |
| Regulations.gov | EPA / GSA | Regulations |
| openFDA | FDA / HHS | Health |
| CMS Open Payments | CMS / HHS | Health |

---

## What it tracks

- **Uptime** — polls every 15 minutes via GitHub Actions, records status and latency
- **Schema changes** — detects when the top-level JSON keys of a response change
- **Status transitions** — records every `up → down` and `down → up` event
- **7-day uptime %** — rolling window across the last 672 polls

---

## Embed a badge in your README

Every monitored API has a shields.io-compatible badge endpoint:

```markdown
<!-- Summary badge (all APIs) -->
![Federal APIs](https://img.shields.io/endpoint?url=https://stark256-spec.github.io/federal-api-watch/badge/summary.json)

<!-- Per-API badge -->
![Federal Register](https://img.shields.io/endpoint?url=https://stark256-spec.github.io/federal-api-watch/badge/federal-register.json)
![Grants.gov](https://img.shields.io/endpoint?url=https://stark256-spec.github.io/federal-api-watch/badge/grants-gov-search.json)
![USASpending](https://img.shields.io/endpoint?url=https://stark256-spec.github.io/federal-api-watch/badge/usaspending.json)
![openFDA](https://img.shields.io/endpoint?url=https://stark256-spec.github.io/federal-api-watch/badge/open-fda.json)
```

Badge slugs match the `slug` field in [`src/federal_api_watch/registry.py`](src/federal_api_watch/registry.py).

---

## Subscribe to the changelog

**RSS:** `https://stark256-spec.github.io/federal-api-watch/feed.xml`

The feed publishes an item every time an API changes status or its response schema changes. Subscribe in any RSS reader or wire it to Slack/email via Zapier, n8n, or IFTTT.

---

## How it works

```
GitHub Actions cron (every 15 min)
  └─ federal-api-watch poll
       ├─ concurrent httpx probes to all 15 APIs
       ├─ records status, latency, body hash, schema fingerprint
       └─ writes data/status/<slug>.json

  └─ federal-api-watch render
       ├─ generates docs/index.html  (status page → GitHub Pages)
       ├─ generates docs/feed.xml    (RSS changelog)
       └─ generates docs/badge/*.json (shields.io endpoint per API)

  └─ git commit + push (data/ and docs/ only)

GitHub Pages auto-deploys docs/ on push
```

The repo itself is the database — `data/status/<slug>.json` holds 7 days of history (672 polls) and a changelog of every schema or status event.

---

## Add an API

Edit [`src/federal_api_watch/registry.py`](src/federal_api_watch/registry.py) and add an `ApiEndpoint` entry:

```python
ApiEndpoint(
    slug="my-new-api",
    name="My New API",
    url="https://api.example.gov/v1/endpoint",
    description="What this API does.",
    agency="Agency Name",
    category="Category",
)
```

Open a PR — if the endpoint is a real public federal API, it will be merged.

---

## Run locally

```bash
git clone https://github.com/stark256-spec/federal-api-watch
cd federal-api-watch
pip install -e ".[dev]"

# Poll all APIs and render output
federal-api-watch

# Poll only
federal-api-watch poll

# Render from existing data
federal-api-watch render

# Run tests
pytest tests/ -v
```

---

## Data sources

All probes target free, public U.S. government API endpoints — no auth required for health checks. Some endpoints use `DEMO_KEY` which is rate-limited; production monitoring is anonymous probing of the root endpoints.

---

## License

MIT
