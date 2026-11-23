# Hosted deployment verification

Verified on 23 November 2026.

- Public HTTPS site: https://kugzyjobs.onrender.com
- Repository: https://github.com/RyanMugele/KugzyJobs-Hiring-Project
- Original deployed source: `75a87d8c252d62dca20d48e01136a58cf2013ac1`.
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

Private administrator creation and successful hosted sign-in were confirmed by the owner and the administrator dashboard was observed. At that initial deployment, hosted workflows, restart persistence and an off-service backup remained pending; later checks are recorded below. Local persistence and workflow tests passed previously; they are not presented as hosted results. No shared demonstration accounts or existing local database were copied to the public deployment. Payments remain disabled. Email was disabled at the initial deployment; the later email update is recorded below.

## Live workflow and email update on 23 November

The complete fictional workflow passed: creator/editor registration and sign-in, job extraction, test portfolio approval, application, a 100% match, browser selection, accepted application, deliverable URL, job completion, job-linked messaging, synthetic rating and local agreement. This used placeholder media, not an actual hiring engagement or assessment of editing quality. Test records are clearly labelled.

Email source `dd015d6ffd1182c9c5c43b915d74e26dbac033a9` deployed successfully as `dep-dc1uscl9fdbs73burqt0` at 10:42:52 EAT. Render reported Live after 1 minute 13 seconds. Private SMTP settings were entered by the owner. One reset email was requested to an owner-controlled Gmail alias; the owner confirmed receipt. The owner then completed the reset and confirmed successful sign-in with the new password. The original test password was separately rejected by the live login form.

After this redeployment, the existing completed job, accepted application, deliverable link, message and agreement remained visible through the authenticated live application. This verifies those records survived this release change; backup restoration and load capacity remain untested.
