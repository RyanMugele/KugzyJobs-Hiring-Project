# Verification report

Date: November 17, 2026. Local macOS x86_64, Python 3.14.0. Source: the user's KugzyJobs-Final-Audit.zip, extracted into a separate working directory. No original database was opened or modified; fictional demonstration data was created in the working copy.

## Repeatable automated suite

**Final result: 30 passed in 47.26 seconds.**

The final test suite is in `tests/test_workflows.py`; exact output is in `test-results.txt`. It uses real Werkzeug password hashing, actual sign-in requests, CSRF tokens, and an isolated in-memory SQLite database. It covers public registration, role-specific pages, the entire creator/editor/admin workflow, and negative authorization cases.

The workflow test posts a job, submits and approves portfolio evidence, applies, selects the applicant, submits a deliverable, completes the job, sends an internal message, rates the editor, creates a payment agreement, and verifies that processing leaves it unpaid while payments are disabled. No gateway is contacted. Separate tests verify CSRF rejection, cross-account restrictions, role-ID collisions, suspension, open redirects, token expiry/reuse, participant ratings, unrelated job messages, approved portfolio edit blocking and verification removal after deletion, and selection of an editor who never applied.

## Page smoke check

91 GET responses were recorded: 71 HTTP 200, 15 expected redirects, 4 HTTP 404 for disabled administrator signup, and 1 HTTP 503 for the disabled provider callback. No unhandled exceptions were recorded. Some redirects deliberately represent unavailable job states. This check used synthetic records and disabled CSRF only for its read-only route inventory; the separate workflow suite tests real CSRF enforcement.

## NLP

The existing 20-case script: 18/20 exact matches (90%), precision 100%, recall 96.30%, F1 98.11%. Style F1 was 92.31%; both exact mismatches concerned “documentary editor” classification. Raw output: `nlp-accuracy.txt`.

The separate supplied CSV evaluation: skills 17 true positives, styles 12, niches 13; no false positives or false negatives for those supplied examples. Raw output: `nlp-evaluation.txt`; detailed rows in `data/evaluation/nlp_evaluation_results.csv`. Curated examples and overlapping vocabulary do not prove generalization; no independent dataset was collected.

## Dependencies

62 resolved runtime packages were checked with pip-audit 2.10.1 against its public advisory service. The final report contains zero reported vulnerabilities. Exact versions are recorded in `requirements-lock.txt`, and machine-readable scan output is `dependency-audit.json`. This is a point-in-time dependency check, not a security certification. `pip check` reported no broken requirements.

## Browser observations

The running local app was checked through the connected browser. Creator and editor sign-in succeeded; the dashboard and extracted job requirements rendered; a fictional editor application was submitted and the resulting application-detail success page was observed. Four genuine viewport screenshots are in `screenshots/`. These captures are not mockups. They use demo data rather than real portfolio evidence.

## Unverified boundaries

Live payments, provider callbacks/reconciliation, email delivery, live MySQL, production hosting, load/concurrency behavior, independent usability, and portfolio authorship verification were not tested. The browser check is a focused sample, not automated coverage of every JavaScript control. Historical standalone scripts may expect a populated development database. No GitHub push was performed and no real payment was initiated.


## Additional selection and matcher verification on 18 November 2026

The prepared GitHub release passed 49 tests in 25.35 s. This includes 11 focused scoring and selection cases, which passed separately in 6.11 s. The original 30-test results above remain the audit baseline. See [detailed selection tests](SELECTION_MATCHER_TESTS.md) and [raw results](selection-matcher-tests.txt). Creator choice remains independent of score rank; the tested creator selected a 75% applicant despite a 100% alternative.
