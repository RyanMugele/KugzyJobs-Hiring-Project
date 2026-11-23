# Password reset email

Email delivery is opt-in. The owner chose an existing Gmail account for the sender. Private SMTP settings were supplied by the owner on 23 November 2026. The updated service deployed successfully and the owner confirmed receipt of a test reset email. The owner completed the reset and confirmed new-password sign-in. A separate HTTPS check confirmed the original test password was rejected.

Set these values privately in Render Environment:

```
EMAIL_ENABLED=true
PUBLIC_BASE_URL=https://kugzyjobs.onrender.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=465
MAIL_USE_SSL=true
MAIL_USE_TLS=false
MAIL_USERNAME=<your Gmail address>
MAIL_PASSWORD=<Google app password, not the normal account password>
MAIL_DEFAULT_SENDER=KugzyJobs <your Gmail address>
```

The owner must enable Google two-step verification and create the app password privately. Do not commit it or place it in screenshots/logs. Google app passwords grant account access; a dedicated sending account is preferable as usage grows. The current owner explicitly chose their existing Gmail account.

Deploy the tested source before enabling email. Production startup validates the public HTTPS origin, SMTP credentials, sender and encryption choice. SMTP submission has a 15-second timeout. The response does not expose whether an account exists. A stored 60-second per-account cooldown limits repeated email requests. Links expire after one hour, are single-use and use the configured public origin. Failed submission invalidates the generated token and records only a generic error.

Automated verification: `python -m pytest`. Seven added tests exercise multipart delivery submission, canonical links, successful password change/login, single-use links, disabled email, provider failure, cooldown and replacement requests. The complete local suite passed **56 tests in 66.79 seconds** on 23 November 2026. SMTP is mocked in those tests; this does not prove inbox delivery.

Live verification must confirm inbox receipt (including spam), the HTTPS link, setting a new password, old-password rejection, new-password login and rejection of the used link. The owner should enter their chosen new password privately. Do not use their personal account for an automatic password change.

Payments remain disabled. SMTP acceptance is not a guarantee of inbox delivery. Gmail has sending limits and is suitable only for the project's low-volume use; monitor failures and move to a transactional provider if usage grows.
