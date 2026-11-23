# Hosted deployment verification

Verified on 23 November 2026.

- Public HTTPS site: https://kugzyjobs.onrender.com
- Repository: https://github.com/RyanMugele/KugzyJobs-Hiring-Project
- Deployed source: `75a87d8c252d62dca20d48e01136a58cf2013ac1`.
- Render deploy: `dep-dc1u4s3l550s73firb00`, reported **Live**, build/deploy duration 1 minute 31 seconds.
- Service: Starter, Python 3.14, Gunicorn; automatic deploys off.
- Persistent disk: **1 GB**, mounted at **`/var/data`**, confirmed in Render dashboard. SQLite configured at `/var/data/kugzyjobs.db`.
- Expected hosting cost: approximately **USD 7.25/month** before taxes or extra usage, approved by owner.

| Hosted check | Observed result |
| --- | --- |
| Homepage | HTTPS page rendered in browser |
| Login page | HTTP 200; form rendered |
| Database readiness | `/healthz` HTTP 200, `{"status":"ok"}` |
| Protected admin dashboard | Unauthenticated request redirected with HTTP 302 |
| Session cookie | Secure, HttpOnly, SameSite=Lax |
| Response headers | X-Content-Type-Options nosniff; X-Frame-Options SAMEORIGIN |
| Linux CI | All 49 pytest tests passed; NLP and CSV evaluations completed |

[Latest passing Linux CI](https://github.com/RyanMugele/KugzyJobs-Hiring-Project/actions/runs/45126206252).

Private administrator creation, authenticated hosted workflows, restart persistence and an off-service backup remain pending. Local persistence and workflow tests passed previously; they are not presented as hosted results. No shared demonstration accounts or existing local database were copied to the public deployment. Payments and outgoing email remain disabled.
