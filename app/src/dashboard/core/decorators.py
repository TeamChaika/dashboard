from functools import wraps
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_protect

from .types import HttpRequest
from authentication.models import User


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
        import logging
        logger = logging.getLogger(__name__)
        
        # Проверяем заголовок от Telegram бота (для Docker и локального окружения)
        if 'HTTP_TELEGRAM_USER' in request.META:
            telegram_user_id = request.META.get('HTTP_TELEGRAM_USER')
            remote_addr = request.META.get('REMOTE_ADDR', '')
            
            logger.info(f"[hybrid_login] Telegram request from {remote_addr}, user_id: {telegram_user_id}")
            
            # Разрешаем запросы от локалхоста или из Docker-сети
            if remote_addr.startswith('127.') or remote_addr.startswith('172.') or remote_addr.startswith('192.168.'):
                try:
                    from authentication.models import User as UserModel
                    request.user = UserModel.objects.get(telegram_id=int(telegram_user_id))
                    logger.info(f"[hybrid_login] User found: {request.user.username}")
                    return view(request, *args, **kwargs)
                except UserModel.DoesNotExist:
                    logger.error(f"[hybrid_login] User not found for telegram_id={telegram_user_id}")
                    return HttpResponse(f'User not found for telegram_id={telegram_user_id}', status=404)
        # Для обычных веб-запросов проверяем аутентификацию
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            logger.warning(f"[hybrid_login] Unauthorized request from {request.META.get('REMOTE_ADDR')}")
            return HttpResponse('Unauthorized', status=401)
        return csrf_protect(view)(request, *args, **kwargs)
    return wrap
