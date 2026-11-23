from flask import current_app, render_template
from flask_mailman import EmailMultiAlternatives
from jinja2 import TemplateNotFound
from markupsafe import Markup


def send_email(to, subject, template, **kwargs):
    """Submit a multipart message with a bounded SMTP timeout.

    Return True only when SMTP accepted the message. Provider acceptance is not
    a claim that a recipient received it. Never log credentials or reset links.
    """
    if not current_app.config.get("EMAIL_ENABLED"):
        return False
    html = render_template(template + ".html", **kwargs)
    try:
        plain = render_template(template + ".txt", **kwargs)
    except TemplateNotFound:
        plain = Markup(html).striptags()
    message = EmailMultiAlternatives(
        subject=subject, body=plain, to=to,
        from_email=current_app.config["MAIL_DEFAULT_SENDER"],
    )
    message.attach_alternative(html, "text/html")
    try:
        accepted = message.send() == 1
    except Exception:
        current_app.logger.error("Email submission failed; check provider configuration and availability.")
        return False
    if not accepted:
        current_app.logger.error("Email provider did not accept the message.")
    return accepted
