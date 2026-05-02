import hashlib
import hmac
import logging
import time
import requests

from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from env import app_host, public_url, bot_secret

logger = logging.getLogger(__name__)


def _sign(user_id: int, timestamp: int) -> str:
    message = f"{timestamp}:{user_id}".encode()
    return hmac.new(bot_secret.encode(), message, hashlib.sha256).hexdigest()


def send_request(url: str, user_id: int):
    timestamp = int(time.time())
    headers = {
        'X-Telegram-User': str(user_id),
        'X-Bot-Timestamp': str(timestamp),
        'X-Bot-Signature': _sign(user_id, timestamp),
    }
    logger.debug(f"Sending request to {url}, user_id={user_id}")
    response = requests.post(url, headers=headers)
    logger.debug(f"Request completed with status: {response.status_code}")
    return response


async def process_register_request(
    query: CallbackQuery, action: str, request_id: int
):
    response = send_request(
        f'{app_host}/register-requests/{request_id}/{action}',
        query.from_user.id
    )
    if response.status_code == 200:
        if action == 'confirm':
            text = 'Пользователь успешно зарегистрирован!'
        else:
            text = 'Заявка на регистрацию успешно отклонена!'
    elif response.status_code == 404:
        text = 'Заявка отсутствует. Она была обработана или удалена.'
    else:
        text = 'Что-то пошло не так, попробуйте позже!'
    
    await query.answer(text, show_alert=True)
    
    # Удаляем кнопки и сообщение (игнорируем ошибки если уже удалено)
    try:
        await query.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    
    try:
        await query.message.delete()
    except Exception:
        pass


async def process_waybill(
    query: CallbackQuery, action: str, waybill_id: int
):
    response = send_request(
        f'{app_host}/waybills/{waybill_id}/{action}',
        query.from_user.id
    )
    if response.status_code == 200:
        if action == 'confirm':
            text = 'Накладная успешно создана!'
        else:
            text = 'Накладная успешно отклонена!'
    elif response.status_code == 400 and 'Already processed' in response.text:
        text = 'Данная накладная уже обработана!'
    else:
        text = 'Что-то пошло не так, попробуйте позже!'
    
    await query.answer(text, show_alert=True)
    
    # Удаляем кнопки и сообщение (игнорируем ошибки если уже удалено)
    try:
        await query.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    
    try:
        await query.message.delete()
    except Exception:
        pass


async def process_writeoff(
    query: CallbackQuery, action: str, writeoff_id: int
):
    url = f'{app_host}/writeoffs/{writeoff_id}/{action}'
    logger.info(f"Processing writeoff {writeoff_id}, action: {action}, user: {query.from_user.id}")
    logger.debug(f"Sending request to: {url}")
    
    response = send_request(url, query.from_user.id)
    
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response text: {response.text[:200]}")
    
    if response.status_code == 200:
        if action == 'confirm':
            text = 'Списание успешно создано!'
        else:
            text = 'Списание успешно отклонено!'
    elif response.status_code == 400 and 'Already processed' in response.text:
        text = 'Данное списание уже обработано!'
    else:
        text = f'Ошибка: {response.status_code} - {response.text[:100]}'
    
    await query.answer(text, show_alert=True)
    
    # Удаляем кнопки и сообщение (игнорируем ошибки если уже удалено)
    try:
        await query.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    
    try:
        await query.message.delete()
    except Exception:
        pass


async def get_pending_documents(message: Message):
    """Получить список необработанных накладных и списаний"""
    from aiogram import Bot
    bot = Bot(token=message.bot.token)
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Удаляем последние 50 сообщений (очистка чата)
    try:
        for i in range(50):
            try:
                await bot.delete_message(chat_id=chat_id, message_id=message.message_id - i)
            except:
                pass
    except:
        pass
    
    timestamp = int(time.time())
    bot_headers = {
        'X-Telegram-User': str(user_id),
        'X-Bot-Timestamp': str(timestamp),
        'X-Bot-Signature': _sign(user_id, timestamp),
    }

    # Запрашиваем необработанные накладные
    waybills_response = requests.get(
        f'{app_host}/waybills/pending',
        headers=bot_headers,
    )

    # Запрашиваем необработанные списания
    writeoffs_response = requests.get(
        f'{app_host}/writeoffs/pending',
        headers=bot_headers,
    )
    
    if waybills_response.status_code != 200 and writeoffs_response.status_code != 200:
        return await message.answer(
            '❌ Ошибка получения данных. Проверьте права доступа.',
            parse_mode='HTML'
        )
    
    waybills = waybills_response.json().get('waybills', []) if waybills_response.status_code == 200 else []
    writeoffs = writeoffs_response.json().get('writeoffs', []) if writeoffs_response.status_code == 200 else []
    
    if not waybills and not writeoffs:
        return await message.answer(
            '✅ Нет необработанных документов!',
            parse_mode='HTML'
        )
    
    # Отправляем накладные с ПОЛНОЙ информацией
    if waybills:
        await message.answer(f'<b>🚚 Накладные ({len(waybills)})</b>', parse_mode='HTML')
        
        for wb in waybills:
            text = f'<b>Накладная #{wb["id"]}</b>\n'
            text += f'От: <b>{wb["from"]}</b>\n'
            text += f'Кому: <b>{wb["to"]}</b>\n'
            if wb.get('comment'):
                text += f'💬 {wb["comment"]}\n'
            
            # Добавляем товары
            if wb.get('items'):
                text += f'\n<b>Товары ({len(wb["items"])}):</b>\n'
                for item in wb['items']:
                    text += f'• {item["name"]} - {item["amount"]}\n'
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text='🌐 Просмотр', url=f'{public_url}/waybills/{wb["id"]}'),
                InlineKeyboardButton(text='✅', callback_data=f'confirmWaybill:{wb["id"]}'),
                InlineKeyboardButton(text='❌', callback_data=f'denyWaybill:{wb["id"]}')
            ]])
            await message.answer(text=text, parse_mode='HTML', reply_markup=keyboard)
    
    # Отправляем списания с ПОЛНОЙ информацией
    if writeoffs:
        await message.answer(f'<b>📝 Списания ({len(writeoffs)})</b>', parse_mode='HTML')
        
        for wo in writeoffs:
            text = f'<b>Списание #{wo["id"]}</b>\n'
            text += f'Склад: <b>{wo["store"]}</b>\n'
            text += f'Причина: <b>{wo["reason"]}</b>\n'
            if wo.get('comment'):
                text += f'💬 {wo["comment"]}\n'
            
            # Добавляем товары
            if wo.get('items'):
                text += f'\n<b>Товары ({len(wo["items"])}):</b>\n'
                for item in wo['items']:
                    text += f'• {item["name"]} - {item["amount"]}\n'
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text='🌐 Просмотр', url=f'{public_url}/writeoffs/{wo["id"]}'),
                InlineKeyboardButton(text='✅', callback_data=f'confirmwriteoff:{wo["id"]}'),
                InlineKeyboardButton(text='❌', callback_data=f'denywriteoff:{wo["id"]}')
            ]])
            await message.answer(text=text, parse_mode='HTML', reply_markup=keyboard)
