import hashlib
import hmac as hmac_lib
import logging
import time
from functools import wraps

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect

from .types import HttpRequest

logger = logging.getLogger(__name__)

_SIGNATURE_MAX_AGE = 60  # seconds


def _verify_bot_signature(user_id: str, timestamp_str: str, signature: str) -> bool:
    from env import bot_secret
    try:
        timestamp = int(timestamp_str)
        if abs(time.time() - timestamp) > _SIGNATURE_MAX_AGE:
            logger.warning("[hybrid_login] Bot request rejected: timestamp too old")
            return False
        expected = hmac_lib.new(
            bot_secret.encode(),
            f"{timestamp}:{user_id}".encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac_lib.compare_digest(expected, signature)
    except (ValueError, TypeError):
        return False


def http_methods(methods: list[str]):
    def decorator(view):
        @wraps(view)
        def wrap(request: HttpRequest, *args, **kwargs):
            if request.method not in methods:
                return HttpResponse('Method Not Allowed', status=405)
            return view(request, *args, **kwargs)
        return wrap
    return decorator


def hybrid_login(view):
    @wraps(view)
    def wrap(request: HttpRequest, *args, **kwargs):
        user_id = request.META.get('HTTP_X_TELEGRAM_USER')
        timestamp = request.META.get('HTTP_X_BOT_TIMESTAMP')
        signature = request.META.get('HTTP_X_BOT_SIGNATURE')

        if user_id and timestamp and signature:
            logger.info(f"[hybrid_login] Bot request, user_id={user_id}")
            if not _verify_bot_signature(user_id, timestamp, signature):
                logger.warning(f"[hybrid_login] Invalid HMAC signature for user_id={user_id}")
                return HttpResponse('Forbidden', status=403)
            try:
                from authentication.models import User as UserModel
                request.user = UserModel.objects.get(telegram_id=int(user_id))
                logger.info(f"[hybrid_login] Bot authenticated as {request.user.username}")
                return view(request, *args, **kwargs)
            except UserModel.DoesNotExist:
                logger.error(f"[hybrid_login] User not found for telegram_id={user_id}")
                return HttpResponse(f'User not found', status=404)

        # Обычный веб-запрос
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            logger.warning(f"[hybrid_login] Unauthorized from {request.META.get('REMOTE_ADDR')}")
            return HttpResponse('Unauthorized', status=401)
        return csrf_protect(view)(request, *args, **kwargs)
    return wrap
