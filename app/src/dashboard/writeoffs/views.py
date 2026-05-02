from datetime import datetime

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q, Subquery

from core.views import DocumentView
from core.decorators import http_methods, hybrid_login
from core.iiko import iiko_api
from core.iiko.decorators import hook_iiko_fail
from core.types import HttpRequest
from core.utils import get_pagination
from .models import Store, Writeoff, WriteoffItem, WriteoffReason
from .services import (
    confirm_writeoff,
    deny_writeoff,
    send_writeoff_confirmation
)


@method_decorator(
    [
        login_required(login_url="/login"),
        permission_required('authentication.can_add_writeoffs'),
        hook_iiko_fail
    ],
    name='dispatch')
class CreateWriteoffView(DocumentView):
    model = Writeoff
    item_model = WriteoffItem
    rel = 'writeoff'

    def before_dispatch(self, request: HttpRequest):
        self.context = {
            'user_stores': [store.name for store in request.user.stores.all()],
            'reasons': WriteoffReason.objects.all(),
            'nomenclature': self.nomenclature['name'],
            'have_store': True
        }

    def render(self, request: HttpRequest):
        return render(request, 'writeoffs/create.html', context=self.context)

    def extract_store(self, request: HttpRequest):
        user_store_name = request.POST.get('user_store_name')
        try:
            user_store = Store.objects.get(name=user_store_name)
        except Store.DoesNotExist:
            self.context['error_message'] = \
                'Пожалуйста, используйте предлагаемые наименования!'
            return self.render(request)
        return user_store

    def extract_reason(self, request: HttpRequest):
        reason_id = request.POST.get('reason')
        if not reason_id:
            self.context['error_message'] = \
                'Пожалуйста, заполните поля корректно!'
            return self.render(request)
        try:
            reason = WriteoffReason.objects.get(id=reason_id)
        except WriteoffReason.DoesNotExist:
            self.context['error_message'] = \
                'Пожалуйста, используйте предлагаемые наименования!'
            return self.render(request)
        return reason

    def post(self, request: HttpRequest):
        extracted = self.extract_store(request)
        if isinstance(extracted, HttpResponse):
            return extracted
        store = extracted
        extracted = self.extract_reason(request)
        if isinstance(extracted, HttpResponse):
            return extracted
        reason = extracted
        created = self.create_document(
            request,
            store=store,
            reason=reason,
            comment=request.POST.get('comment'),
            created_by=request.user
        )
        if isinstance(created, HttpResponse):
            return created
        writeoff, writeoff_items = created
        send_writeoff_confirmation(writeoff, writeoff_items)
        self.context['success_message'] = \
            'Списание успешно создано и отправлено на подтверждение!'
        return self.render(request)


@http_methods(['GET'])
@login_required(login_url='/login')
@permission_required('authentication.can_view_writeoffs')
def writeoff_view_api(request: HttpRequest, pk: int):
    """API endpoint для получения данных списания в JSON формате"""
    user_stores = set(
        request.user.stores.all().values_list('id', flat=True)
    )
    if not user_stores:
        return JsonResponse({'error': 'No stores assigned'}, status=403)
    
    writeoff = get_object_or_404(
        Writeoff.objects.select_related('store', 'created_by', 'processed_by', 'reason')
        .prefetch_related('writeoffitem_set'),
        id=pk
    )
    
    if writeoff.store.id not in user_stores:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    nomenclature = iiko_api.get_nomenclature()['id']
    
    # Форматируем данные для JSON
    data = {
        'id': writeoff.id,
        'store': writeoff.store.name,
        'created_by': writeoff.created_by.get_full_name() or writeoff.created_by.username,
        'processed_by': writeoff.processed_by.get_full_name() or writeoff.processed_by.username if writeoff.processed_by else None,
        'comment': writeoff.comment or '',
        'status': writeoff.status,
        'created_at': (writeoff.created_at if isinstance(writeoff.created_at, datetime) else datetime.fromtimestamp(writeoff.created_at)).strftime('%d.%m.%Y %H:%M'),
        'processed_at': (writeoff.processed_at if isinstance(writeoff.processed_at, datetime) else datetime.fromtimestamp(writeoff.processed_at)).strftime('%d.%m.%Y %H:%M') if writeoff.processed_at else None,
        'items': [
            {
                'name': nomenclature.get(str(item.product_id), 'Неизвестный товар'),
                'amount': float(item.amount)
            }
            for item in writeoff.writeoffitem_set.all()
        ],
        'actions': []
    }
    
    # Определяем доступные действия
    if writeoff.status == 'Created' and request.user.has_perm('authentication.is_disposer'):
        data['actions'].extend(['confirm', 'deny'])
    
    return JsonResponse(data)


@http_methods(['GET'])
@login_required(login_url='/login')
@permission_required('authentication.can_view_writeoffs')
def writeoff_view(request: HttpRequest, pk: int):
    user_stores = set(
        request.user.stores.all().values_list('id', flat=True)
    )
    if not user_stores:
        raise PermissionDenied()
    writeoff = get_object_or_404(
        Writeoff.objects.select_related('store', 'created_by', 'processed_by', 'reason')
        .prefetch_related('writeoffitem_set'),
        id=pk
    )
    if writeoff.store.id not in user_stores:
        raise PermissionDenied()
    nomenclature = iiko_api.get_nomenclature()['id']
    return render(
        request,
        'writeoffs/item.html',
        context={
            'writeoff': writeoff,
            'created_at': writeoff.created_at if isinstance(writeoff.created_at, datetime) else datetime.fromtimestamp(writeoff.created_at),
            'processed_at': (writeoff.processed_at if isinstance(writeoff.processed_at, datetime) else datetime.fromtimestamp(writeoff.processed_at))
            if writeoff.processed_at else None,
            'items': (
                (nomenclature.get(str(item.product_id)), item.amount)
                for item in writeoff.writeoffitem_set.all()
            )
        }
    )


@http_methods(['GET'])
@login_required(login_url="/login")
@permission_required('authentication.can_view_writeoffs')
def writeoffs_view(request: HttpRequest):
    if not request.user.stores.all():
        return render(
            request,
            'writeoffs/index.html',
            context={'have_store': False}
        )
    nomenclature = iiko_api.get_nomenclature()['name']
    status = request.GET.get('status', 'all').capitalize()
    page = int(request.GET.get('page', '1'))
    search = request.GET.get('search')
    search_product = nomenclature.get(search)

    query = Q(store__in=request.user.stores.all())
    if status and status in {'Created', 'Sent', 'Denied'}:
        query &= Q(status=status)
    if search_product:
        query &= Q(id__in=Subquery(
            WriteoffItem.objects.filter(
                product_id=search_product
            ).distinct(
                'writeoff_id'
            ).values_list('writeoff_id', flat=True)
        ))
    writeoffs = Writeoff.objects.filter(
        query
    ).select_related('store', 'created_by', 'processed_by', 'reason').order_by('-id')

    paginator = Paginator(writeoffs, 30)
    pagination = get_pagination(page, paginator.num_pages)

    return render(
        request,
        'writeoffs/index.html',
        context={
            'have_store': bool(request.user.stores.all()),
            'status': status.lower(),
            'search': search if search_product else None,
            'writeoffs': [
                (
                    writeoff,
                    writeoff.created_at if isinstance(writeoff.created_at, datetime) else datetime.fromtimestamp(writeoff.created_at)
                )
                for writeoff in paginator.get_page(page)
            ],
            'nomenclature': nomenclature,
            'pages': paginator.num_pages,
            'page': page,
            'pagination': pagination
        }
    )


@http_methods(['POST'])
@csrf_exempt
@hybrid_login
@permission_required('authentication.is_disposer')
@hook_iiko_fail
def process_writeoff(request: HttpRequest, pk: int, action: str):
    writeoff = get_object_or_404(
        Writeoff.objects.select_related('store', 'created_by', 'processed_by', 'reason'),
        id=pk
    )
    if writeoff.status != 'Created':
        return HttpResponse('Bad Request: Already processed', status=400)
    if writeoff.store not in request.user.stores.all():
        return HttpResponse(status=403)
    if action == 'confirm':
        confirm_writeoff(writeoff, request.user)
        return HttpResponse(status=200)
    elif action == 'deny':
        deny_writeoff(writeoff, request.user)
        return HttpResponse(status=200)
    return HttpResponse('Bad Request', status=400)


@http_methods(['GET'])
@csrf_exempt
@hybrid_login
@permission_required('authentication.is_disposer')
def get_pending_writeoffs(request: HttpRequest):
    """API для получения необработанных списаний для пользователя"""
    user_stores = request.user.stores.all()
    
    # Получаем необработанные списания пользователя
    pending_writeoffs = Writeoff.objects.filter(
        status='Created',
        store__in=user_stores
    ).select_related('store', 'reason').prefetch_related('writeoffitem_set').order_by('-created_at')[:10]
    
    nomenclature = iiko_api.get_nomenclature()
    
    data = []
    for writeoff in pending_writeoffs:
        # Получаем товары
        items = []
        for item in writeoff.writeoffitem_set.all():
            # nomenclature['id'] = {'uuid': 'name_string', ...}
            product_name = nomenclature.get('id', {}).get(str(item.product_id), 'Неизвестный товар')
            items.append({
                'name': product_name,
                'amount': float(item.amount)
            })
        
        data.append({
            'id': writeoff.id,
            'type': 'writeoff',
            'store': writeoff.store.name,
            'reason': writeoff.reason.name if writeoff.reason else '',
            'comment': writeoff.comment or '',
            'created_at': writeoff.created_at,
            'items': items
        })
    
    return JsonResponse({'writeoffs': data})
