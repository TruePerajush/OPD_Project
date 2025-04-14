from telebot import TeleBot
from telebot.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from bot import TelegramBot, User, time, Book, Report
from typing import Callable
from supabase import Client
import re


def init_bot(app: TeleBot, supabase: Client, sql_cursor):
    bot = TelegramBot(sql_cursor, supabase)

    user_messages = {}

    def delete_previous_messages(user_id, chat_id):
        key = (user_id, chat_id)
        if key not in user_messages:
            return

        for msg_id in user_messages[key]:
            try:
                app.delete_message(chat_id=chat_id, message_id=msg_id)
            except:
                continue

        user_messages[key] = []

    def send_menu(message: Message, command_type: str):
        menu = [
            [
                InlineKeyboardButton("Книги", callback_data="start_books"),
                InlineKeyboardButton("Заметки", callback_data="start_notes"),
                InlineKeyboardButton("Цитаты", callback_data="start_quotes"),
            ],
            [
                InlineKeyboardButton("Цели", callback_data="start_goals"),
                InlineKeyboardButton("Статистика", callback_data="start_statistic"),
                InlineKeyboardButton("Помощь", callback_data="start_help"),
            ],
        ]

        if command_type == "menu":
            text = "Вот мое меню."
        else:
            text = f"Привет, {message.chat.first_name}\n\nДобро пожаловать в ваш персональный читательский дневник! Выберите действие в меню ниже."

        msg = app.send_message(
            chat_id=message.chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(menu),
        )

        bot.create_user(
            User(username=message.from_user.username, chat_id=message.chat.id)
        )

        key = (message.from_user.id, message.chat.id)
        if key not in user_messages:
            user_messages[key] = []
        user_messages[key].append(msg.message_id)

    @app.message_handler(commands=["start"])
    def command_start(message: Message):
        delete_previous_messages(message.from_user.id, message.chat.id)
        send_menu(message, "start")

    @app.message_handler(commands=["menu"])
    def command_menu(message: Message):
        delete_previous_messages(message.from_user.id, message.chat.id)
        send_menu(message, "menu")

    def goals(app: TeleBot, bot: TelegramBot):
        message_to_delete = [0]

        @app.callback_query_handler(func=lambda call: call.data == "start_goals")
        def handle_start_goals(call: CallbackQuery):
            app.answer_callback_query(call.id)
            goals_start(call.message)

        def goals_start(message: Message):
            # if bot.get_user(call.message.chat.id).annual_goal == -1:
            #     msg = app.edit_message_text(
            #         chat_id=call.message.chat.id,
            #         message_id=call.message.message_id,
            #         text="Введите желаемое количество прочитанных книг за год.",
            #         reply_markup=None,
            #     )
            #     app.register_next_step_handler(msg, goals_year)
            # это в продакшн
            if not bot.get_user(message.chat.id):
                print(message.text)

                msg = app.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    text="Введите желаемое количество прочитанных книг за год.",
                    reply_markup=None,
                )
                app.register_next_step_handler(msg, goals_year)
            else:
                app.delete_message(message.chat.id, message.message_id)
                goals_confirmation(message)

        def goals_n(
            message: Message,
            func_next: Callable,
            func_repeat: Callable,
            attribute: str,
            reply: str,
        ):
            try:
                number = int(message.text)
                if number < 0:
                    raise ValueError

                bot.update_user_attribute(
                    User(username=message.from_user.username, chat_id=message.chat.id),
                    attribute,
                    number,
                )

                msg = app.send_message(message.chat.id, reply)
                app.register_next_step_handler(msg, func_next)
            except ValueError:
                msg = app.send_message(message.chat.id, "Это не положительное число.")
                app.register_next_step_handler(msg, func_repeat)

        def goals_year(message: Message):
            goals_n(
                message,
                goals_month,
                goals_year,
                "annual_goal",
                "Введите желаемое количество прочитанных книг за месяц.",
            )

        def goals_month(message: Message):
            goals_n(
                message,
                goals_week,
                goals_month,
                "monthly_goal",
                "Введите желаемое количество прочитанных книг за неделю.",
            )

        def goals_week(message: Message):
            goals_n(
                message,
                goals_day,
                goals_week,
                "weekly_goal",
                "Сколько минут в день вы хотите выделить на чтение?",
            )

        def goals_day(message: Message):
            try:
                number = int(message.text)
                if number < 0:
                    raise ValueError

                bot.update_user_attribute(
                    User(username=message.from_user.username, chat_id=message.chat.id),
                    "daily_goal",
                    number,
                )

                msg = app.send_message(
                    chat_id=message.chat.id,
                    text="Хотите поставить себе напоминание? (y/n)",
                )

                message_to_delete[0] = msg
                app.register_next_step_handler(msg, goals_reminder_check)
            except ValueError:
                msg = app.send_message(message.chat.id, "Это не положительное число.")
                app.register_next_step_handler(msg, goals_day)

        def goals_reminder_check(message: Message):
            if message.text == "y":
                msg = app.send_message(
                    chat_id=message.chat.id,
                    text="Введите в какое время хотите получать уведомление (ЧЧ:ММ)."
                )
                app.register_next_step_handler(msg, goals_reminder_set)
            elif message.text == "n":
                goals_confirmation(message)
            else:
                app.send_message(message.chat.id, "Введено неправильное значение.")
                app.register_next_step_handler(message, goals_reminder_check)

        def goals_reminder_set(message: Message):
            if re.fullmatch(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", message.text):
                bot.update_user_attribute(
                    User(message.from_user.username, message.chat.id),
                    "reminder",
                    time(
                        int(message.text.split(":")[0]),
                        int(message.text.split(":")[1]),
                    ),
                )
                goals_confirmation(message)
            else:
                msg = app.send_message(
                    chat_id=message.chat.id,
                    text="Введенное значение не соответствует требованию.",
                )
                app.register_next_step_handler(msg, goals_reminder_set)

        def goals_confirmation(message: Message):
            user = bot.get_user(message.chat.id)

            if user:
                msg = app.send_message(
                    chat_id=message.chat.id,
                    text=f"Ваши цели:\n"
                    f"-Книг за год: {user.annual_goal}\n"
                    f"-Книг за месяц: {user.monthly_goal}\n"
                    f"-Книг за неделю: {user.weekly_goal}\n"
                    f"-Минут в день: {user.daily_goal}\n\n"
                    f'{f'Напоминания:\n-Каждый день в {user.reminder}' if user.reminder else ''}\n\n'
                    f"Все верно? (y/n)\n",
                )

            else:
                msg = app.send_message(
                    chat_id=message.chat.id,
                    text="Заглушка, пока проверить пользователя нельзя, да - выход в меню, нет - повтор (y/n)",
                )

            app.register_next_step_handler(msg, goals_reminder_confirmation_check)

            message_to_delete[0] = msg

        def goals_reminder_confirmation_check(message: Message):
            if message.text == "y":
                app.send_message(message.chat.id, "Цели успешно сохранены.")
            elif message.text == "n":
                print("тута")
                user = bot.get_user(message.chat.id)
                bot.update_user_attribute(user, "annual_goal", -1)
                msg = app.send_message(message.chat.id, ".")
                goals_start(msg)
            else:
                msg = app.send_message(message.chat.id, "Введено неправильное значение.")
                app.register_next_step_handler(msg, goals_reminder_confirmation_check)

    def help(app: TeleBot):
        @app.callback_query_handler(func=lambda call: call.data == "start_help")
        def handle_start_help(call: CallbackQuery):
            app.answer_callback_query(call.id)
            app.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"Контактные данные и описание: ДОПИСАТЬ."
            )

    def statistic(app: TeleBot, bot: TelegramBot):
        @app.callback_query_handler(func=lambda call: call.data == "start_statistic")
        def handle_start_statistic(call: CallbackQuery):
            app.answer_callback_query(call.id)
            books = bot.get_books(call.message.chat.id)
            statistic_analyse(call.message, books)
            statistic_report(call.message)

        def statistic_analyse(message: Message, books: list[Book]):
            if books:
                text = (
                        f"Ваша статистика.\n"
                        f"1. Прочитанно книг за год: {bot.get_books_over_year(books)}\n"
                        f"2. Средняя оценка: {bot.get_books_mid_rating(books)}\n"
                        f"3. Популярные жанры:\n"
                )

                for key_value in bot.get_books_popular_genres(books):
                    text += f"\t{key_value[0]} - {key_value[1]}\n"

                app.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    text=text
                )
            else:
                app.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    text="Невозможно собрать статистику. Пока нет добавленных книг."
                )

        def statistic_report(message):
            reports: (Report, Report) = bot.get_report(message.chat.id)

            progress = reports[0].pages_read/reports[1].pages_read * 100

            app.send_message(
                chat_id=message.chat.id,
                text=f"Ваши результаты за неделю.\n"
                     f"-Прочитано книг: {reports[0].books_read} ({reports[0].pages_read} стр.)\n"
                     f"-Новые цитаты: {reports[0].quotes_added}\n"
                     f"На {progress if progress < 100 else progress - 100}%{f' менее' if progress < 100 else ''} продуктивнее прошлой недели.\n"
            )

    goals(app, bot)
    statistic(app, bot)
    help(app)

    print("Бот работает.")
    app.polling()


if __name__ == "__main__":
    pass
