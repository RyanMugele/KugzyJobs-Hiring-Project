# Release checklist

Prepared: branded README, genuine screenshots, diagrams, production settings, persistent disk configuration, Gunicorn startup, readiness endpoint, hosting tests, CI configuration, and a read-only copy of the existing repository history. Render automatic deployment is off.

Before publication:

- [x] Owner approved publishing the prepared update to the existing GitHub repository on 23 November 2026.
- [ ] Owner approves Render publication and approximately USD 7.25/month before taxes/extras after checking the dashboard total.
- [ ] Connect Render/GitHub and enter billing details directly with the provider if needed.

After publication:

- [ ] First Linux CI run passes.
- [ ] Render build/startup and database readiness pass.
- [ ] HTTPS login, roles and complete demonstration workflow pass.
- [ ] Create private admin credentials; no shared demo accounts.
- [ ] Restart confirms persistent data.
- [ ] Make private off-service backup.
- [ ] Record real commit SHA, live URL and date in README and report.

The owner authorized GitHub publication and completion of deployment on 23 November 2026. Hosting purchase and live verification remain pending.
