import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Bot, Update
from telegram.ext import Application, CallbackContext, CommandHandler

from ...core.config import settings
from ...core.db import async_session
from ...modules.auth.models import TokenForRegistrationTelegram


# Асинхронная функция для отправки сообщения пользователю по chat_id
async def send_message(chat_id: str, message: str) -> None:
    bot_token = settings.TELEGRAM_BOT_TOKEN
    bot = Bot(token=bot_token)
    await bot.send_message(chat_id=chat_id, text=message)


async def create_token_for_registration(chat_id: str, db: AsyncSession):
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
                chat_id=chat_id, db=db
            )
        message = f"http://localhost:5173/registration?key={token_info.registration_token}"
        await send_message(chat_id, message)
        await update.message.reply_text(
            "Перейдите по ссылке, чтобы зарегистрироваться на сайте!"
        )
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text(
            "Произошла ошибка. Попробуйте ещё раз."
        )


def run_bot():
    bot_token = settings.TELEGRAM_BOT_TOKEN
    # Создаем объект Application для управления ботом, используя предоставленный токен
    application = Application.builder().token(bot_token).build()
    # Добавляем обработчик команды /start: при ее вызове будет запускаться функция start
    application.add_handler(CommandHandler("start", start))
    # Запускаем бот в режиме polling с использованием asyncio
    application.run_polling()


if __name__ == "__main__":
    run_bot()

# class Command(BaseCommand):
#     def handle(self, *args, **kwargs):
#         bot_token = '8199155454:AAFDI6xdgYH81_BNKEjELIuWM72N3-HUFdU'  # Замените на свой токен
#         # Создаем объект Application для управления ботом, используя предоставленный токен
#         application = Application.builder().token(bot_token).build()
#
#         # Асинхронная функция для отправки сообщения пользователю по chat_id
#         async def send_message(bot: Bot, chat_id: str, message: str) -> None:
#             # Создаем объект Bot с использованием токена, чтобы отправить сообщение
#             await bot.send_message(chat_id=chat_id, text=message)
#
#             # Асинхронная функция для обработки команды /start
#         async def start(update: Update, context: CallbackContext) -> None:
#             # Получаем уникальный идентификатор пользователя (chat_id) из объекта update
#             chat_id = str(update.message.chat_id)
#             token_info = TokenForRegistration.objects.create(user_id=chat_id)
#             message = f"http://localhost:8000/api/registration/?key={token_info.registration_token}"
#             # Вызываем функцию send_message, чтобы отправить дополнительное сообщение
#             bot_token = '8199155454:AAFDI6xdgYH81_BNKEjELIuWM72N3-HUFdU'  # Замените на свой токен
#             bot = Bot(token=bot_token)
#             await send_message(bot, chat_id, message)
#
#         # Добавляем обработчик команды /start: при ее вызове будет запускаться функция start
#         application.add_handler(CommandHandler('start', self.start))
#         # Запускаем бот в режиме polling, чтобы он принимал и обрабатывал входящие команды
#         application.run_polling()
#         logger.info("Бот успешно запущен")

# bot_token = '8199155454:AAFDI6xdgYH81_BNKEjELIuWM72N3-HUFdU'  # Замените на свой токен
# # Создаем объект Application для управления ботом, используя предоставленный токен
# application = Application.builder().token(bot_token).build()
#
# # Асинхронная функция для отправки сообщения пользователю по chat_id
# async def send_message(chat_id: str, message: str) -> None:
#     # Создаем объект Bot с использованием токена, чтобы отправить сообщение
#     bot = Bot(token=bot_token)
#     await bot.send_message(chat_id=chat_id, text=message)
#
#
# # Асинхронная функция для обработки команды /start
# async def start(update: Update, context: CallbackContext) -> None:
#     # Получаем уникальный идентификатор пользователя (chat_id) из объекта update
#     chat_id = str(update.message.chat_id)
#     message = 'Hello, do you want to get a token?'
#     # Отправляем ответ пользователю, информируя его о его chat_id
#     await update.message.reply_text(f"Ваш chat_id: {chat_id}")
#     # Вызываем функцию send_message, чтобы отправить дополнительное сообщение
#     await send_message(chat_id, message)
#
#
# # Добавляем обработчик команды /start: при ее вызове будет запускаться функция start
# application.add_handler(CommandHandler('start', start))
# # Запускаем бот в режиме polling, чтобы он принимал и обрабатывал входящие команды
# application.run_polling()
