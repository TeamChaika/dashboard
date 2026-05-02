from contextlib import suppress
from datetime import datetime, timezone
from time import time

from django.contrib.auth.models import Permission
from django.db.models import Q
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from env import public_url
from authentication.models import User
from core.iiko import iiko_api
from core.telegram import telegram_bot
from .models import Waybill, WaybillItem


def confirm_waybill(waybill: Waybill, user: User):
    waybill_items = WaybillItem.objects.filter(waybill_id=waybill.id)
    waybill.processed_by = user
    response = load_waybill(waybill, waybill_items)
    if response.get('valid'):
        waybill.status = 'Sent'
        waybill.processed_at = datetime.fromtimestamp(time(), tz=timezone.utc)
        waybill.save()


def deny_waybill(waybill: Waybill, user: User):
    waybill.status = 'Denied'
    waybill.processed_by = user
    waybill.processed_at = datetime.fromtimestamp(time(), tz=timezone.utc)
    waybill.save()


def copy_waybill(waybill: Waybill, user: User):
    duplicate = Waybill(
        store=waybill.store,
        counteragent=waybill.counteragent,
        comment=waybill.comment,
        status='Created',
        created_by=user
    )
    duplicate.save()
    waybill_items = WaybillItem.objects.filter(waybill_id=waybill.id)
    items = []
    for item in waybill_items:
        items.append(WaybillItem(
            waybill=duplicate, product_id=item.product_id,
            amount=item.amount
        ))
    WaybillItem.objects.bulk_create(items)
    send_waybill_confirmation(duplicate, items)


def cancel_waybill(waybill: Waybill, user: User):
    waybill.status = 'Cancelled'
    waybill.processed_by = user
    waybill.processed_at = datetime.fromtimestamp(time(), tz=timezone.utc)
    waybill.save()


def load_waybill(waybill: Waybill, waybill_items: list[WaybillItem]):
    comment = f'Отправил: {waybill.created_by.get_full_name()} ' \
        f'[{waybill.created_by.username}] ' \
        f'со склада {waybill.store.name}\n'
    comment += f'Принял: {waybill.processed_by.get_full_name()} ' \
        f'[{waybill.processed_by.username}] ' \
        f'на склад {waybill.counteragent.name}'
    created_at = waybill.created_at if isinstance(waybill.created_at, datetime) else datetime.fromtimestamp(waybill.created_at)
    document = {
        'documentNumber': 'DJ' + '0'*(6-len(str(waybill.id))) +
        str(waybill.id),
        'dateIncoming': created_at.isoformat(timespec='seconds'),
        'useDefaultDocumentTime': True,
        'defaultStoreId': str(waybill.store.id),
        'comment': comment,
        'items':
            [
                {
                    'productId': str(item.product_id),
                    'price': 0.0,
                    'amount': item.amount
                } for item in waybill_items
            ]
    }
    response = iiko_api.load_waybill(document)
    return response


def get_waybill_message(
    waybill: Waybill,
    waybill_items: list[WaybillItem],
    event: str
):
    nomenclature = iiko_api.get_nomenclature()['id']
    waybill_items_string = ''
    for waybill_item in waybill_items:
        waybill_items_string += '–' * 30 + \
            '\nНаименование: ' \
            f'{nomenclature.get(str(waybill_item.product_id))}\n' \
            f'Количество: {waybill_item.amount}\n'

    document_number = 'DJ' + '0'*(6-len(str(waybill.id))) + \
        str(waybill.id)
    created_at = (
        waybill.created_at
        if isinstance(waybill.created_at, datetime)
        else datetime.fromtimestamp(waybill.created_at)
    ).strftime('%d.%m.%Y %H:%M')
    title = 'Новый запрос на создание накладной:' \
        if event == 'created' else 'Запрос на создание накладной обновлён:'

    return f'<b>{title}</b>\n\n' \
        f'<b>Номер:</b> {document_number}\n' \
        f'<b>Время:</b> {created_at}\n' \
        f'<b>Откуда:</b> {waybill.store.name}\n' \
        f'<b>Куда:</b> {waybill.counteragent.name}\n' \
        f'<b>Создал:</b> {waybill.created_by.get_full_name()} ' \
        f'[{waybill.created_by.username}]\n' \
        f'<b>Комментарий:</b> ' \
        f'{waybill.comment if waybill.comment else "Нет"}\n' \
        f'<b>Количество позиций:</b> {len(waybill_items)}\n\n' \
        f'<b>Товары:</b>\n{waybill_items_string}'


def get_waybill_buttons(waybill_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            'Просмотр',
            url=f'{public_url}/waybills/{waybill_id}')
         ],
        [InlineKeyboardButton(
            'Подтвердить',
            callback_data=f'confirmWaybill:{waybill_id}'
        ), InlineKeyboardButton(
            'Отклонить',
            callback_data=f'denyWaybill:{waybill_id}')
        ]]
    )


def send_waybill_confirmation(
    waybill: Waybill,
    waybill_items: list[WaybillItem],
    event: str = 'created'
):
    """Отправка уведомлений в фоновом режиме для ускорения"""
    import threading
    import logging
    
    logger = logging.getLogger(__name__)
    
    def send_notifications():
        try:
            perm = Permission.objects.get(codename='can_add_waybills')
            users = User.objects.filter(
                Q(telegram_id__isnull=False) &
                (
                    Q(user_permissions=perm) |
                    Q(groups__permissions=perm) |
                    Q(is_superuser=True)
                ) &
                Q(stores=waybill.counteragent)
            ).distinct()
            
            message = get_waybill_message(waybill, waybill_items, event)
            buttons = get_waybill_buttons(waybill.id)
            
            sent_count = 0
            for user in users:
                try:
                    telegram_bot.send_message(
                        chat_id=user.telegram_id,
                        text=message,
                        parse_mode='HTML',
                        reply_markup=buttons,
                        disable_web_page_preview=True
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send to {user.telegram_id}: {e}")
            
            logger.info(f"Sent {sent_count} waybill notifications")
        except Exception as e:
            logger.error(f"Error in send_notifications: {e}")
    
    # Запускаем в фоновом потоке
    thread = threading.Thread(target=send_notifications, daemon=False)
    thread.start()
