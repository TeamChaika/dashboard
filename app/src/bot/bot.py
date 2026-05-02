import asyncio
import logging

from aiogram import Bot, types, Dispatcher, F
from aiogram.filters import Command

from env import bot_token
from services import process_register_request, process_waybill, \
    process_writeoff

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = Bot(bot_token)
dp = Dispatcher()

logger.info("Bot initialized")


@dp.message(Command('start'))
async def register(message: types.Message):
    return await message.answer(
        f'Ваш уникальный код для регистрации на сайте: '
        f'<b>{message.from_user.id}</b>\n'
        f'Вставьте его в запрашиваемое поле.\n\n'
        f'Команды:\n'
        f'/pending - показать необработанные накладные и списания',
        parse_mode='HTML'
    )


@dp.message(Command('pending'))
async def show_pending(message: types.Message):
    from services import get_pending_documents
    return await get_pending_documents(message)


@dp.callback_query(
    F.data.startswith('confirmRegister:') |
    F.data.startswith('denyRegister:')
)
async def register_confirmation_handler(query: types.CallbackQuery):
    request_id = int(query.data.split(':')[1])
    return await process_register_request(
        query,
        'confirm' if query.data.startswith('confirm') else 'deny',
        request_id
    )


@dp.callback_query(
    F.data.startswith('confirmWaybill:') |
    F.data.startswith('denyWaybill:')
)
async def confirm_waybill(query: types.CallbackQuery):
    waybill_id = int(query.data.split(':')[1])
    return await process_waybill(
        query,
        'confirm' if query.data.startswith('confirm') else 'deny',
        waybill_id
    )


@dp.callback_query(
    F.data.startswith('confirmwriteoff:') |
    F.data.startswith('denywriteoff:')
)
async def confirm_writeoff(query: types.CallbackQuery):
    logger.info(f"Received writeoff callback: {query.data} from user {query.from_user.id}")
    writeoff_id = int(query.data.split(':')[1])
    action = 'confirm' if query.data.startswith('confirm') else 'deny'
    logger.info(f"Processing writeoff {writeoff_id}, action: {action}")
    return await process_writeoff(query, action, writeoff_id)


async def main():
    logger.info("Starting bot polling...")
    await dp.start_polling(bot)


if __name__ == '__main__':
    logger.info("Bot script started")
    asyncio.run(main())
