from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from shared.public_urls import build_frontend_url


def send_html_email(
    subject: str,
    template_name: str,
    context: dict,
    recipient: str,
    fail_silently: bool = True,
) -> None:
    """Send a branded HTML email with plain-text fallback.

    Uses Django's template engine — templates live in backend/templates/emails/.
    Set fail_silently=False in Celery tasks so failures propagate for retry.
    """
    ctx = {"frontend_url": build_frontend_url("/"), **context}
    html_body = render_to_string(f"emails/{template_name}.html", ctx)

    # Minimal plain-text fallback — avoids spam filters that reject HTML-only mail
    text_body = (
        render_to_string(f"emails/{template_name}.txt", ctx)
        if _template_exists(f"emails/{template_name}.txt")
        else _strip_html(html_body)
    )

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=fail_silently)


def _template_exists(template_name: str) -> bool:
    from django.template import TemplateDoesNotExist
    from django.template.loader import get_template

    try:
        get_template(template_name)
        return True
    except TemplateDoesNotExist:
        return False


def _strip_html(html: str) -> str:
    import re

    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s{2,}", " ", text).strip()
