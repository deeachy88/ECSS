"""
Token helpers for securing ECSS payment webhook endpoints.

Flow:
  1. Caller POSTs credentials to /ecss_payment_token
  2. Caller uses returned Bearer token on /ecss_payment_update
"""
from django.conf import settings
from django.core import signing


class PaymentWebhookAuthError(Exception):
    """Raised when payment webhook token validation fails."""


def _signer():
    return signing.TimestampSigner(salt='ecss-payment-webhook-v1')


def validate_client_credentials(client_id, client_secret):
    expected_id = getattr(settings, 'PAYMENT_WEBHOOK_CLIENT_ID', '')
    expected_secret = getattr(settings, 'PAYMENT_WEBHOOK_CLIENT_SECRET', '')
    if not expected_id or not expected_secret:
        return False
    return (
        client_id == expected_id
        and secrets_compare(client_secret, expected_secret)
    )


def secrets_compare(provided, expected):
    import hmac
    return hmac.compare_digest(str(provided or ''), str(expected or ''))


def generate_payment_access_token():
    max_age = int(getattr(settings, 'PAYMENT_WEBHOOK_TOKEN_MAX_AGE', 3600))
    token = _signer().sign('ecss-payment-update')
    return token, max_age


def validate_payment_access_token(token):
    if not token:
        raise PaymentWebhookAuthError('Missing access token')
    max_age = int(getattr(settings, 'PAYMENT_WEBHOOK_TOKEN_MAX_AGE', 3600))
    try:
        _signer().unsign(token, max_age=max_age)
    except signing.BadSignature as exc:
        raise PaymentWebhookAuthError('Invalid or expired access token') from exc


def extract_bearer_token(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Bearer '):
        return None
    return auth_header[7:].strip() or None
