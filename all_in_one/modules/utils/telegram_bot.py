import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Bot, Update
from telegram.ext import Application, CallbackContext, CommandHandler

from ...core.config import settings
from ...core.db import async_session
from ...modules.auth.models import TokenForRegistrationTelegram


async def send_message(chat_id: str, message: str) -> None:
    bot_token = settings.TELEGRAM_BOT_TOKEN
    bot = Bot(token=bot_token)
    await bot.send_message(chat_id=chat_id, text=message)


async def create_token_for_registration(
    update, chat_id: str, db: AsyncSession
):
    try:
        new_user_with_telegram_token = TokenForRegistrationTelegram(
            chat_id=chat_id
        )
        db.add(new_user_with_telegram_token)
        await db.commit()
        await db.refresh(new_user_with_telegram_token)
        return new_user_with_telegram_token
    except IntegrityError:
        await db.rollback()
        result = await db.execute(
            select(TokenForRegistrationTelegram).where(
                TokenForRegistrationTelegram.chat_id == chat_id
            )
        )
        existing_token = result.scalar_one_or_none()
        if existing_token:
            await update.message.reply_text(
                "Вам уже была отправлена ссылка для регистрации на сайте"
            )
            logging.warning(
                f"Пользователь уже имеет токен: {existing_token.registration_token}"
            )
            return existing_token
        return None
    except Exception as e:
        await db.rollback()
        logging.error(
            f"Неожиданная ошибка при создании токена: {str(e)}", exc_info=True
        )
        raise


async def start(update: Update, context: CallbackContext) -> None:
    try:
        # Получаем уникальный идентификатор пользователя (chat_id) из объекта update
        chat_id = str(update.message.chat_id)
        async with async_session() as db:
            token_info = await create_token_for_registration(
                update, chat_id=chat_id, db=db
            )
        message = f"http://localhost:5173/registration?key={token_info.registration_token}"
        await send_message(chat_id, message)
        await update.message.reply_text(
            "Перейдите по ссылке, чтобы зарегистрироваться на сайте"
        )
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text(
            "Произошла ошибка. Попробуйте ещё раз."
        )


bot_token = settings.TELEGRAM_BOT_TOKEN
application = Application.builder().token(bot_token).build()
application.add_handler(CommandHandler("start", start))


async def run_bot():
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    return application


if __name__ == "__main__":
    run_bot()


# main.py
# from fastapi import FastAPI

# app = FastAPI()

# @app.on_event("startup")
# async def startup_event():
#     await run_bot()

# @app.on_event("shutdown")
# async def shutdown_event():
#     await application.updater.stop()
#     await application.stop()
#     await application.shutdown()
