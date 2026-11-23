# Deployment preparation verification

Date: November 18, 2026. Platform: macOS, Python 3.14.0. This is local release verification, not a claim of successful hosting.

| Check | Observed result |
| --- | --- |
| Workflow, hosting and focused matcher/selection cases | **49 passed in 25.35s** |
| Production configuration | Missing secret, database URL and absolute data directory rejected |
| Profile-image storage | Test file survived a release-directory change; existing images protected from overwrite |
| Database readiness | Healthy response 200; simulated unavailable database returned generic 503 |
| HTTPS production login | Real CSRF token, creator login/dashboard and secure HttpOnly cookie passed |
| Gunicorn process | Two starts passed health, homepage and login checks |
| SQLite persistence | Test account remained present across both server starts |
| NLP regression | 18/20 exact cases; precision 100%, recall 96.30%, F1 98.11% |
| Included CSV evaluation | 15 descriptions; same extraction results as original audit |
| Hosting YAML | Parsed locally; manual deployment configured |

Logs: [pytest](deployment-tests.txt), [production smoke](production-smoke.txt), [NLP cases](release-nlp-accuracy.txt), [CSV](release-nlp-evaluation.txt).

The Gunicorn test used an isolated database and fictional account under the private local work directory. It did not copy the user's running database or credentials. No real payment or email occurred.

Pending: first GitHub Actions run on Linux, Render build/startup, public HTTPS workflow, hosted restart/persistence, performance and capacity checks. Docker-based Linux verification was unavailable because the local Docker daemon was not running. No GitHub push, hosting purchase or public deployment has occurred.

Render configuration also passed validation against Render’s official JSON schema. README local links and banner XML passed structural checks.

Focused applicant selection and matching: 11 passed in 6.11 s, included within the 49-test total. See [selection evidence](SELECTION_MATCHER_TESTS.md).
