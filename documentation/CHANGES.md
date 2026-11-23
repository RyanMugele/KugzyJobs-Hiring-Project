# Audit changes — November 17, 2026

- Corrected Flask-Login identity loading: session IDs always refer to User, never Creator/Editor/Admin primary keys. Corrected User role property and string IDs.
- Denied suspended accounts at login and when existing sessions reload. Replaced session-role authorization with database-backed user roles in shared helpers.
- Disabled public administrator registration unless a private code is configured; removed the predictable default code. Retained interactive administrator creation.
- Enabled global CSRF validation and supplied tokens to HTML mutation forms and JSON fetch calls.
- Rejected protocol-relative and backslash login redirects; added cookie and response-header defaults, upload size limit, and production secret enforcement.
- Corrected SQLite's in-memory test URI, added missing python-dotenv dependency, and resolved typing_extensions compatibility with Python 3.14/spaCy.
- Corrected password-reset password assignment, secure token generation, one-use handling, expiry, recovery template, and disabled-email messaging. No delivery success is claimed with email disabled.
- Added missing application edit and administrator form templates; fixed optional-proposal rendering and broken administrator error-template paths.
- Corrected false-success AJAX behavior in editor profile and portfolio forms by preserving normal server validation and redirects.
- Reanalyze NLP when job descriptions change. Require an actual pending application before selecting an editor.
- Restrict ratings to the completed job's actual two participants. Validate job-linked message participants and correct quick-contact editor/user ID conversion.
- Resubmit edited portfolio evidence for review and recalculate editor verification on rejection/removal/deletion.
- Disable outbound email/payment gateway requests by default, bound HTTP timeouts, block repeated processing of completed payments, and redirect unpaid success-page requests to status.
- Add shared CSS/favicon, non-destructive database setup, fictional demo seeding, a Mac launcher, setup instructions, automated tests, genuine screenshots, and architecture documentation.
- Replace landing-page scale claims and unimplemented escrow/support promises with accurate prototype descriptions.

This is a local demonstration release. It is not a certification of production security or a completed payment integration.
