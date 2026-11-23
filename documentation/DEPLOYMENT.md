# Deploy KugzyJobs on Render

Prepared for review. Applying the Blueprint creates a **paid service**. Obtain owner approval for the push, publication and displayed cost first.

## Proposed service

Render Starter, one instance and one Gunicorn worker, Python 3.14.0, and a 1 GB persistent disk at `/var/data`. Database: `/var/data/kugzyjobs.db`. Legacy role-image directories link to `/var/data/uploads/editors` and `/var/data/uploads/creators`. Current profile forms do not expose a complete upload workflow; persistence preparation does not add one.

HTTPS is provided by Render. Production cookies are secure; `/healthz` checks database connectivity. Payments remain disabled. Password-reset email is opt-in through private SMTP settings; see [email setup](PASSWORD_RESET_EMAIL.md). Automatic deployment is **off**.

On November 18, 2026, listed compute was USD 7/month and disk USD 0.25/GB/month: approximately **USD 7.25/month** before taxes or extras. Confirm the dashboard total before purchase. No paid workspace upgrade or custom domain is proposed.

Sources: [pricing](https://render.com/pricing), [persistent disks](https://render.com/docs/disks), [Flask deployment](https://render.com/docs/deploy-flask), [Blueprint specification](https://render.com/docs/blueprint-spec).

## Publish after approval

1. Review the diff against `main` in `RyanMugele/KugzyJobs-Hiring-Project`. Preserve existing commits. Exclude secrets, databases, environments and uploaded role images.
2. Push only after approval. Check the first GitHub Actions run on Linux before claiming CI passes.
3. Connect the repository in Render. Create a Blueprint from root `render.yaml`. Review Starter and the 1 GB disk; approve billing only after confirming the total.
4. Render generates a private `SECRET_KEY`; keep it stable. Check all other variables against the Blueprint. Never commit credentials.
5. Deploy manually. The startup command creates missing tables and runs Gunicorn. The disk is available at runtime, not during build.
6. Check the assigned HTTPS URL, `/healthz`, public pages and registration.
7. In the paid service's Shell, run `python create_admin.py`. Enter private credentials; the script refuses an existing email. Public admin signup is disabled. Do not run `seed_demo.py` publicly.
8. Create private fictional creator/editor accounts and test job posting, extraction, portfolio review, application, selection, delivery, rating and agreement. Confirm payments remain blocked.
9. Restart and verify the same accounts/job remain. Record actual URL, SHA and date, then update README and report with observed results.

## Existing data and backup

Deployment starts with a new empty database; no private local accounts or database are uploaded. A migration of local data needs separate review, a consistent snapshot, secure transfer, schema compatibility checks and a stopped writer. Never commit a database.

Create a consistent snapshot in Render Shell:

```sh
python - <<'PY'
import sqlite3
from pathlib import Path
backup = Path('/var/data/backups')
backup.mkdir(exist_ok=True)
with sqlite3.connect('/var/data/kugzyjobs.db') as source:
    with sqlite3.connect(str(backup / 'kugzyjobs-backup.db')) as destination:
        source.backup(destination)
PY
```

Privately download the snapshot and uploads using Render's documented SSH/SCP. Keep a dated off-service backup; a copy on the same disk cannot protect against disk deletion. Before restoring, stop writes, preserve the current database, replace with the verified snapshot, restore uploads, restart and check workflows. Do not replace a database while Gunicorn is writing.

## Limits

One small SQLite service suits a limited academic demonstration; load capacity is unverified. A disk restricts scaling and changes deployment downtime. Monitor memory with spaCy loaded; request approval before a paid upgrade. `init-db` does not migrate existing columns: prepare and test migrations before schema changes.

`TRUST_PROXY_HEADERS=1` trusts one forwarded protocol header, not forwarded host or IP headers. Use only behind the documented HTTPS proxy. [Flask guidance](https://flask.palletsprojects.com/en/stable/deploying/proxy_fix/).
