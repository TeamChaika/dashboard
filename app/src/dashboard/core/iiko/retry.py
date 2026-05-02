"""
Retry механизм для устойчивых HTTP запросов к внешним API.

Автоматически повторяет запросы при временных сбоях:
- Сетевые ошибки (ConnectionError, Timeout)
- Ошибки передачи данных (ChunkedEncodingError)
- HTTP ошибки сервера (500, 502, 503, 504)
"""

import time
import logging
from functools import wraps
from typing import Callable, Optional, Tuple, Type

from requests.exceptions import (
    RequestException,
    ConnectionError,
    Timeout,
    ChunkedEncodingError,
    HTTPError
)

logger = logging.getLogger(__name__)


# Ошибки, при которых имеет смысл повторять запрос
RETRYABLE_EXCEPTIONS = (
    ConnectionError,      # Проблемы с сетью
    Timeout,             # Таймауты
    ChunkedEncodingError, # Разрыв соединения
    HTTPError,           # HTTP ошибки (проверим код)
)


def is_retryable_http_error(exception: Exception) -> bool:
    """
    Проверяет, стоит ли повторять запрос при HTTP ошибке.
    
    Повторяем только при серверных ошибках (5xx) и некоторых 4xx:
    - 408 Request Timeout
    - 429 Too Many Requests
    - 500 Internal Server Error
    - 502 Bad Gateway
    - 503 Service Unavailable
    - 504 Gateway Timeout
    """
    if isinstance(exception, HTTPError) and exception.response is not None:
        status_code = exception.response.status_code
        return status_code in (408, 429, 500, 502, 503, 504)
    return False


def retry_on_failure(
    max_attempts: int = 3,
    initial_delay: float = 5.0,
    exponential_backoff: bool = True,
    max_delay: float = 60.0,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None
):
    """
    Декоратор для автоматического повтора функции при ошибках.
    
    Args:
        max_attempts: Максимальное количество попыток (по умолчанию 3)
        initial_delay: Начальная задержка между попытками в секундах (по умолчанию 5)
        exponential_backoff: Использовать экспоненциальную задержку (5s → 10s → 20s)
        max_delay: Максимальная задержка между попытками
        retryable_exceptions: Кортеж исключений, при которых повторять запрос
    
    Пример:
        @retry_on_failure(max_attempts=5, initial_delay=10)
        def get_data_from_api(self):
            return requests.get('https://api.example.com/data')
    """
    if retryable_exceptions is None:
        retryable_exceptions = RETRYABLE_EXCEPTIONS
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    # Логируем попытку
                    if attempt > 1:
                        logger.info(
                            f"[Retry] {func.__name__}: попытка {attempt}/{max_attempts}"
                        )
                    
                    # Выполняем функцию
                    result = func(*args, **kwargs)
                    
                    # Если успех после повторных попыток - логируем
                    if attempt > 1:
                        logger.info(
                            f"[Retry] {func.__name__}: успех после {attempt} попыток"
                        )
                    
                    return result
                
                except retryable_exceptions as e:
                    last_exception = e
                    
                    # Проверяем HTTP ошибки - не все стоит повторять
                    if isinstance(e, HTTPError) and not is_retryable_http_error(e):
                        logger.warning(
                            f"[Retry] {func.__name__}: HTTP ошибка {e.response.status_code} "
                            f"(повтор не имеет смысла)"
                        )
                        raise
                    
                    # Если это последняя попытка - выбрасываем ошибку
                    if attempt >= max_attempts:
                        logger.error(
                            f"[Retry] {func.__name__}: все {max_attempts} попыток исчерпаны. "
                            f"Последняя ошибка: {type(e).__name__}: {str(e)}"
                        )
                        raise
                    
                    # Логируем ошибку и ожидание
                    logger.warning(
                        f"[Retry] {func.__name__}: {type(e).__name__}: {str(e)[:100]}. "
                        f"Повтор через {delay:.1f}s..."
                    )
                    
                    # Ждём перед следующей попыткой
                    time.sleep(delay)
                    
                    # Увеличиваем задержку для следующей попытки
                    if exponential_backoff:
                        delay = min(delay * 2, max_delay)
                    
                except Exception as e:
                    # Неожиданная ошибка - логируем и сразу выбрасываем
                    logger.error(
                        f"[Retry] {func.__name__}: неожиданная ошибка "
                        f"{type(e).__name__}: {str(e)}"
                    )
                    raise
            
            # На всякий случай (не должно сюда попасть)
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


# Готовые пресеты для разных сценариев

def retry_quick(func: Callable) -> Callable:
    """Быстрые повторы для лёгких операций (3 попытки с задержкой 2s)"""
    return retry_on_failure(
        max_attempts=3,
        initial_delay=2.0,
        exponential_backoff=False
    )(func)


def retry_standard(func: Callable) -> Callable:
    """Стандартные повторы для обычных API запросов (3 попытки, 5s → 10s → 20s)"""
    return retry_on_failure(
        max_attempts=3,
        initial_delay=5.0,
        exponential_backoff=True
    )(func)


def retry_aggressive(func: Callable) -> Callable:
    """Агрессивные повторы для критичных операций (5 попыток, до 60s)"""
    return retry_on_failure(
        max_attempts=5,
        initial_delay=10.0,
        exponential_backoff=True,
        max_delay=60.0
    )(func)

