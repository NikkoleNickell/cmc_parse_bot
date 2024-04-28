from create_bot import dp, scheduler, bot, os
from db.sql import Psql
import sys
import logging
import asyncio
from handlers.user_handlers import start_schedule_jobs


async def on_startup() -> None:
    pg = await Psql.connect_postgres()
    await pg.create_db(os.getenv("POSTGRES_DATABASE"))
    await pg.close_pool()

    db = await Psql.connect()
    await db.create_users_table()
    await db.close_pool()

    await start_schedule_jobs()


async def main() -> None:
    dp.startup.register(on_startup)
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
    