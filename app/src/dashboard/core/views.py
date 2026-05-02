"""
Core views and API endpoints
"""

import time
import logging
from datetime import datetime, timezone
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.db.models import Model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.cache import cache

from .iiko import iiko_api
from .types import HttpRequest

logger = logging.getLogger(__name__)


# ============================================================================
# ORIGINAL DocumentView class (используется в waybills/writeoffs)
# ============================================================================

class DocumentView(View):
    model: Model
    item_model: Model
    rel: str

    def render(self, request: HttpRequest) -> HttpResponse:
        pass

    def before_dispatch(self, request: HttpRequest):
        pass

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        if not request.user.stores.all():
            self.context = {'have_store': False}
            return self.render(request)
        self.nomenclature = iiko_api.get_nomenclature()
        self.before_dispatch(request)
        return super(DocumentView, self).dispatch(
            request, *args, **kwargs
        )

    def get(self, request: HttpRequest, *args, **kwargs):
        return self.render(request)

    def collect_items(self, request: HttpRequest):
        names = request.POST.getlist('products_names[]', [])
        amounts = request.POST.getlist('products_counts[]', [])
        if len(names) == 0 or len(amounts) == 0 or len(names) != len(amounts):
            self.context['error_message'] = \
                'Пожалуйста, заполните поля корректно!'
            return self.render(request)
        return zip(names, amounts)

    def create_items(self, request: HttpRequest, items: list[tuple]):
        created = []
        for name, amount in items:
            if not name:
                self.context['error_message'] = 'Пожалуйста, заполните поля корректно!'
                return self.render(request)
            try:
                amount_val = float(amount)
            except (TypeError, ValueError):
                self.context['error_message'] = 'Пожалуйста, заполните поля корректно!'
                return self.render(request)
            if amount_val <= 0:
                self.context['error_message'] = 'Количество должно быть больше нуля!'
                return self.render(request)
            if name not in self.nomenclature['name']:
                self.context['error_message'] = \
                    'Пожалуйста, используйте предлагаемые наименования!'
                return self.render(request)
            created.append(self.item_model(
                product_id=self.nomenclature['name'].get(name),
                amount=amount_val,
            ))
        return created

    def create_document(self, request: HttpRequest, *args, **kwargs):
        document = self.model(*args, **kwargs)
        # Normalize datetime fields to match DB columns that expect timestamps
        if hasattr(document, 'created_at'):
            created = document.created_at
            if isinstance(created, (int, float)):
                document.created_at = datetime.fromtimestamp(created, tz=timezone.utc)
            elif created is None:
                document.created_at = datetime.now(timezone.utc)
        if hasattr(document, 'processed_at') and document.processed_at:
            processed = document.processed_at
            if isinstance(processed, (int, float)):
                document.processed_at = datetime.fromtimestamp(processed, tz=timezone.utc)
        collected = self.collect_items(request)
        if isinstance(collected, HttpResponse):
            return collected
        created = self.create_items(request, collected)
        if isinstance(created, HttpResponse):
            return created
        document.save()
        for item in created:
            setattr(item, self.rel, document)
        self.item_model.objects.bulk_create(created)
        return document, created


# ============================================================================
# NEW: API endpoints для оптимизации номенклатуры
# ============================================================================

@require_http_methods(['GET'])
@login_required(login_url='/login')
def get_nomenclature_api(request):
    """
    API для получения полной номенклатуры.
    
    Возвращает список всех товаров для кэширования на клиенте.
    Используется для уменьшения размера HTML и ускорения загрузки страниц.
    
    Response:
        {
            "products": ["Авокадо", "Ананас", ...],
            "count": 7119,
            "timestamp": 1698765432.123
        }
    """
    try:
        nomenclature_data = iiko_api.get_nomenclature()
        
        # Проверяем структуру данных
        if not nomenclature_data or not isinstance(nomenclature_data, dict):
            return JsonResponse({
                'error': 'Invalid nomenclature data structure',
                'products': [],
                'count': 0,
                'timestamp': time.time()
            }, status=500)
        
        # Получаем словарь name -> id
        name_dict = nomenclature_data.get('name', {})
        products = sorted(name_dict.keys())
        
        return JsonResponse({
            'products': products,
            'count': len(products),
            'timestamp': time.time()
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_nomenclature_api: {e}")
        
        return JsonResponse({
            'error': str(e),
            'products': [],
            'count': 0,
            'timestamp': time.time()
        }, status=500)


@require_http_methods(['GET'])
@login_required(login_url='/login')
def search_nomenclature_api(request):
    """
    API для поиска по номенклатуре с пагинацией.
    
    Query параметры:
        q: поисковый запрос (обязательный)
        page: номер страницы (по умолчанию 1)
        size: размер страницы (по умолчанию 30)
    
    Response:
        {
            "results": [
                {"id": "product_name", "text": "product_name"},
                ...
            ],
            "total_count": 150,
            "page": 1,
            "has_more": true
        }
    """
    try:
        query = request.GET.get('q', '').lower().strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('size', 30))
        
        # Минимум 2 символа для поиска
        if len(query) < 2:
            return JsonResponse({
                'results': [],
                'total_count': 0,
                'page': page,
                'has_more': False
            })
        
        nomenclature_data = iiko_api.get_nomenclature()
        
        # Проверяем структуру данных
        if not nomenclature_data or not isinstance(nomenclature_data, dict):
            return JsonResponse({
                'error': 'Invalid nomenclature data structure',
                'results': [],
                'total_count': 0,
                'page': page,
                'has_more': False
            }, status=500)
        
        name_dict = nomenclature_data.get('name', {})
        
        # Фильтруем по запросу
        filtered = [
            {'id': name, 'text': name}
            for name in name_dict.keys()
            if query in name.lower()
        ]
        
        # Сортируем по релевантности:
        # 1. Точное совпадение
        # 2. Начинается с запроса
        # 3. Содержит запрос
        # 4. Алфавитный порядок
        filtered.sort(key=lambda x: (
            x['text'].lower() != query,  # точное совпадение - выше всех
            not x['text'].lower().startswith(query),  # начинается с запроса
            x['text'].lower()  # алфавитный порядок
        ))
        
        # Пагинация
        start = (page - 1) * page_size
        end = start + page_size
        
        return JsonResponse({
            'results': filtered[start:end],
            'total_count': len(filtered),
            'page': page,
            'has_more': end < len(filtered)
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in search_nomenclature_api: {e}")
        
        return JsonResponse({
            'error': str(e),
            'results': [],
            'total_count': 0,
            'page': page if 'page' in locals() else 1,
            'has_more': False
        }, status=500)


_SYNC_COOLDOWN = 600  # 10 минут


@require_http_methods(['POST'])
@login_required(login_url='/login')
def sync_nomenclature_api(request):
    user_id = request.user.id
    lock_key = f'sync_nomenclature_lock:{user_id}'
    ts_key = f'sync_nomenclature_ts:{user_id}'

    # cache.add() — атомарная операция: устанавливает ключ только если он не существует.
    # Предотвращает race condition при одновременных запросах.
    if not cache.add(lock_key, True, _SYNC_COOLDOWN):
        last_ts = cache.get(ts_key, time.time())
        remaining = max(0, _SYNC_COOLDOWN - (time.time() - last_ts))
        logger.info(f"Sync rate-limited for user {user_id}, {remaining:.0f}s remaining")
        return JsonResponse({
            'success': False,
            'error': 'Синхронизация возможна не чаще одного раза в 10 минут',
            'wait_seconds': int(remaining),
            'wait_minutes': round(remaining / 60, 1),
        }, status=429)

    try:
        logger.info(f"Начало синхронизации номенклатуры для пользователя {user_id}")
        nomenclature = iiko_api._request_nomenclature()
        count = len(nomenclature.get('name', {}))
        now = time.time()
        cache.set(ts_key, now, _SYNC_COOLDOWN + 10)
        logger.info(f"Синхронизация завершена для пользователя {user_id}, товаров: {count}")
        return JsonResponse({
            'success': True,
            'message': 'Номенклатура успешно синхронизирована',
            'count': count,
            'timestamp': now,
        })
    except Exception as e:
        # При ошибке снимаем блокировку чтобы пользователь мог повторить сразу
        cache.delete(lock_key)
        logger.error(f"Ошибка синхронизации для пользователя {user_id}: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': time.time(),
        }, status=500)
