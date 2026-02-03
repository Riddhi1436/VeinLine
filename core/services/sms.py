from __future__ import annotations

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class SMSDeliveryError(Exception):
    pass


def send_sms(phone_e164: str, message: str) -> dict:
    """
    Sends an SMS using the configured provider.

    This contains real HTTP calls, but requires a valid API key in `.env`.
    In development, you can keep the key empty; the function will log and no-op.
    """

    api_key = getattr(settings, "VEINLINE_SMS_API_KEY", "")
    provider = getattr(settings, "VEINLINE_SMS_PROVIDER", "fast2sms")

    if not api_key:
        logger.warning("SMS not sent (missing SMS_API_KEY). To enable, set SMS_API_KEY in .env.")
        return {"ok": False, "skipped": True, "reason": "missing_api_key", "phone": phone_e164}

    # Normalize phone number
    if not phone_e164 or not isinstance(phone_e164, str):
        logger.error(f"Invalid phone number: {phone_e164}")
        return {"ok": False, "skipped": True, "reason": "invalid_phone", "phone": phone_e164}

    try:
        if provider == "fast2sms":
            # Fast2SMS quick send endpoint (example; verify params per your Fast2SMS plan)
            url = "https://www.fast2sms.com/dev/bulkV2"
            headers = {"authorization": api_key}
            payload = {
                "route": "v3",
                "numbers": phone_e164.lstrip("+"),  # Fast2SMS typically expects digits without '+'
                "message": message,
                "sender_id": getattr(settings, "VEINLINE_SMS_SENDER", "VEINLN"),
            }
            resp = requests.post(url, data=payload, headers=headers, timeout=20)
        elif provider == "textlocal":
            # Textlocal API
            url = "https://api.textlocal.in/send/"
            payload = {
                "apikey": api_key,
                "numbers": phone_e164.lstrip("+"),
                "message": message,
                "sender": getattr(settings, "VEINLINE_SMS_SENDER", "VEINLN"),
            }
            resp = requests.post(url, data=payload, timeout=20)
        else:
            error_msg = f"Unsupported SMS_PROVIDER: {provider}"
            logger.error(error_msg)
            return {"ok": False, "skipped": True, "reason": "unsupported_provider"}

        if resp.status_code >= 400:
            error_msg = f"SMS provider error {resp.status_code}: {resp.text[:300]}"
            logger.error(error_msg)
            return {"ok": False, "skipped": True, "reason": "provider_error", "status": resp.status_code}

        try:
            response_data = resp.json()
            logger.info(f"SMS sent successfully to {phone_e164} via {provider}")
            return {"ok": True, "provider": provider, "response": response_data, "phone": phone_e164}
        except Exception as e:
            logger.info(f"SMS sent to {phone_e164} via {provider} (response parsing failed)")
            return {"ok": True, "provider": provider, "response_text": resp.text, "phone": phone_e164}
    
    except requests.exceptions.Timeout:
        error_msg = f"SMS timeout for {phone_e164}"
        logger.error(error_msg)
        return {"ok": False, "skipped": True, "reason": "timeout", "phone": phone_e164}
    except requests.exceptions.RequestException as e:
        error_msg = f"SMS request error for {phone_e164}: {str(e)}"
        logger.error(error_msg)
        return {"ok": False, "skipped": True, "reason": "request_error", "phone": phone_e164}
    except Exception as e:
        error_msg = f"Unexpected SMS error for {phone_e164}: {str(e)}"
        logger.error(error_msg)
        return {"ok": False, "skipped": True, "reason": "unexpected_error", "phone": phone_e164}


