# KugzyJobs architecture

Flask's application factory creates the app and registers five blueprints: main, authentication, creator, editor, and admin. Flask-Login resolves the base User primary key on every request; role-specific records link back through userId. Database role values control authorization. Flask-WTF protects state-changing HTTP requests with CSRF tokens.

SQLAlchemy manages User, Creator, Editor, Admin, Job, Portfolio, JobApplication, Message, Rating, Payment, PaymentInterim, Report, and PasswordResetToken. SQLite is the verified local backend. The prepared production configuration requires an explicit database URL and persistent data directory. Render is configured to use SQLite on a persistent disk; live hosting remains pending. `flask init-db` creates missing tables; it does not migrate an existing schema.

A creator posts a job. The spaCy blank-English tokenizer and PhraseMatcher extract canonical skills, editing styles, and niches. JSON arrays are stored in the job record and refreshed on edits. Applicant compatibility uses normalized intersections weighted 50% skills, 25% styles, and 25% niches, renormalizing when a category has no requirements. This is a rule-based system, not a trained machine-learning model. Approved portfolio evidence supplements editor profile skills.

Editors submit portfolio links for manual administrator review and apply to posted jobs. Selecting a pending applicant accepts that application, declines competing pending applications, assigns the editor, and changes job status to in_progress. The selected editor submits a deliverable URL. The creator completes the job, after which the two participants may rate each other and create a payment agreement.

Messages are persisted in the local database. Job-linked messages require the creator and an applicant to be the participants. No outbound messages or email were sent during testing. Email and payment gateway requests are disabled in the delivered configuration. Payment agreements are records only and do not transfer money. Re-enabling gateway code requires a separate provider integration review, reconciliation checks, sandbox testing, and explicit authorization for real transactions.

The frontend uses Jinja templates, inline page CSS/JavaScript, a shared CSS file, and externally hosted fonts/icons. Some decorative links remain placeholders. Internet access may be needed for external visual resources; core server workflows work without payment or email services.
