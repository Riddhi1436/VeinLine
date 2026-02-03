from django.conf import settings
from django.core.mail import send_mail


def send_fallback_email(to_email: str, subject: str, message: str) -> int:
    """
    Backup notification channel.
    In development we default to console email backend.
    """

    if not to_email:
        return 0
    return send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[to_email],
        fail_silently=True,
    )


