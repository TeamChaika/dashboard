from contextlib import suppress
from datetime import datetime, timezone
from time import time

from django.contrib.auth.models import Permission
from django.db.models import Q
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from env import public_url
from core.iiko import iiko_api
from core.telegram import telegram_bot
from authentication.models import User
from .models import Writeoff, WriteoffItem


def confirm_writeoff(writeoff: Writeoff, user: User):
    writeoff_items = WriteoffItem.objects.filter(
        writeoff_id=writeoff.id
    )
    response = load_writeoff(writeoff, writeoff_items)
    if response == 'SUCCESS':
        writeoff.processed_by = user
        writeoff.processed_at = datetime.fromtimestamp(time(), tz=timezone.utc)
        writeoff.status = 'Sent'
        writeoff.save()


def deny_writeoff(writeoff: Writeoff, user: User):
    writeoff.processed_by = user
    writeoff.processed_at = datetime.fromtimestamp(time(), tz=timezone.utc)
    writeoff.status = 'Denied'
    writeoff.save()


def load_writeoff(writeoff: Writeoff, writeoff_items: list[WriteoffItem]):
    created_at = (
        writeoff.created_at
        if isinstance(writeoff.created_at, datetime)
        else datetime.fromtimestamp(writeoff.created_at)
    )
    # API iiko v2 ожидает формат без timezone offset
    date_incoming = created_at.replace(tzinfo=None).isoformat(timespec='seconds')
    document = {
        'documentNumber': 'DJ' + '0'*(
            6-len(str(writeoff.id))
        ) + str(writeoff.id),
        'dateIncoming': date_incoming,
        'status': 'NEW',
        'storeId': str(writeoff.store.id),
        'accountId': str(writeoff.reason.account_id),
        'comment': f'СПИСАНИЕ\n{writeoff.reason or ""}\n{writeoff.comment}',
        'items':
            [
                {'productId': str(item.product_id), 'amount': item.amount}
                for item in writeoff_items
            ]
    }
    response = iiko_api.load_writeoff(document)
    return response


def get_writeoff_message(
    writeoff: Writeoff,
    writeoff_items: list[WriteoffItem]
):
    nomenclature = iiko_api.get_nomenclature()['id']
    writeoff_items_string = ''
    comment = writeoff.comment if writeoff.comment else "Нет"
    document_number = 'DJ' + '0'*(6-len(str(writeoff.id))) + \
        str(writeoff.id)
    created_at = (
        writeoff.created_at
        if isinstance(writeoff.created_at, datetime)
        else datetime.fromtimestamp(writeoff.created_at)
    ).strftime('%d.%m.%Y %H:%M')
    for writeoff_item in writeoff_items:
        writeoff_items_string += '–' * 30 + \
            '\nНаименование: ' \
            f'{nomenclature.get(writeoff_item.product_id)}\n' \
            f'Количество: {writeoff_item.amount}\n'
    return f'<b>Новый запрос на создание списания:</b>\n\n' \
        f'<b>Номер:</b> {document_number}\n' \
        f'<b>Время:</b> {created_at}\n' \
        f'<b>Склад:</b> {writeoff.store.name}\n' \
        f'<b>Создал:</b> {writeoff.created_by.get_full_name()} ' \
        f'[{writeoff.created_by.username}]\n' \
        f'<b>Причина:</b> {writeoff.reason or "Нет"}\n' \
        f'<b>Комментарий:</b> {comment}\n' \
        f'<b>Количество позиций:</b> {len(writeoff_items)}\n\n' \
        f'<b>Товары:</b>\n{writeoff_items_string}'


def get_writeoff_keyboard(
    writeoff: Writeoff
):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            'Просмотр',
            url=f'{public_url}/writeoffs/{writeoff.id}'
        )],
        [InlineKeyboardButton(
            'Подтвердить',
            callback_data=f'confirmwriteoff:{writeoff.id}'
        ), InlineKeyboardButton(
            'Отклонить',
            callback_data=f'denywriteoff:{writeoff.id}'
        )]
    ])


def send_writeoff_confirmation(
    writeoff: Writeoff,
    writeoff_items: list[WriteoffItem]
):
    """Отправка уведомлений в фоновом режиме для ускорения"""
    import threading
    import logging
    
    logger = logging.getLogger(__name__)
    
    def send_notifications():
        try:
            perm = Permission.objects.get(codename='is_disposer')
            users = User.objects.filter(
                Q(telegram_id__isnull=False) &
                (
                    Q(user_permissions=perm) |
                    Q(groups__permissions=perm) |
                    Q(is_superuser=True)
                ) & Q(stores=writeoff.store)
            ).distinct()
            
            message = get_writeoff_message(writeoff, writeoff_items)
            keyboard = get_writeoff_keyboard(writeoff)
            
            sent_count = 0
            for user in users:
                try:
                    telegram_bot.send_message(
                        chat_id=user.telegram_id,
                        text=message,
                        parse_mode='HTML',
                        reply_markup=keyboard,
                        disable_web_page_preview=True
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send to {user.telegram_id}: {e}")
            
            logger.info(f"Sent {sent_count} writeoff notifications")
        except Exception as e:
            logger.error(f"Error in send_notifications: {e}")
    
    # Запускаем в фоновом потоке
    thread = threading.Thread(target=send_notifications, daemon=False)
    thread.start()
