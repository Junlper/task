import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from config import TOKEN
from database import init_db
from handlers import router

logging.basicConfig(level=logging.INFO)

session = AiohttpSession(proxy="socks5://127.0.0.1:9150", timeout=30)
bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()


async def main():
    await init_db()
    dp.include_router(router)
    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())