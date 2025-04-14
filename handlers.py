from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatFullInfo
from bot import TelegramBot, User, time
from typing import Callable
import re

def init_bot(app: TeleBot, conn, sql_cursor):
    bot = TelegramBot(sql_cursor)

    message_to_delete = [0]

    @app.message_handler(commands=['start'])
    def command_start(message: Message):
        start_menu = [
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
        app.send_message(
            chat_id=message.chat.id,
            text=f"Привет, {message.chat.first_name}\n\n"
                 f"Добро пожаловать в ваш персональный читательский дневник! Выберите действие в меню ниже.",
            reply_markup=InlineKeyboardMarkup(start_menu)
        )
        bot.create_user(User(username=message.from_user.username, chat_id=message.chat.id))


    @app.message_handler(commands=['menu'])
    def command_menu(message: Message):
        menu(message)

    def menu(message: Message):
        start_menu = [
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
        app.send_message(
            chat_id=message.chat.id,
            text=f"Вот мое меню.",
            reply_markup=InlineKeyboardMarkup(start_menu)
        )

    @app.callback_query_handler(func=lambda call: call.data == "start_goals")
    def handle_callbacks(call: CallbackQuery):
        app.answer_callback_query(call.id)
        msg = app.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Введите желаемое количество прочитанных книг за год.",
            reply_markup=None,
        )
        app.register_next_step_handler(msg, goals_year)

    def goals_n(message: Message, func_next: Callable, func_repeat: Callable, attribute: str, reply: str):
        try:
            number = int(message.text)
            if number < 0:
                raise ValueError

            bot.update_user_attribute(User(username=message.from_user.username, chat_id=message.chat.id), attribute, number)

            msg = app.send_message(message.chat.id, reply)
            app.register_next_step_handler(msg, func_next)
        except ValueError:
            msg = app.send_message(message.chat.id, "Это не положительное число.")
            app.register_next_step_handler(msg, func_repeat)

    def goals_year(message: Message):
        goals_n(message, goals_month, goals_year, "annual_goal", "Введите желаемое количество прочитанных книг за месяц.")

    def goals_month(message: Message):
        goals_n(message, goals_week, goals_month, "monthly_goal", "Введите желаемое количество прочитанных книг за неделю.")

    def goals_week(message: Message):
        goals_n(message, goals_day, goals_week, "weekly_goal", "Сколько минут в день вы хотите выделить на чтение?")

    def goals_day(message: Message):
        try:
            number = int(message.text)
            if number < 0:
                raise ValueError

            bot.update_user_attribute(User(username=message.from_user.username, chat_id=message.chat.id), 'daily_goal',
                                      number)

            reminder_menu = [
                [InlineKeyboardButton("Да", callback_data="goals_reminder_yes"),
                 InlineKeyboardButton("Нет", callback_data="goals_reminder_no")],
            ]

            msg = app.send_message(
                chat_id=message.chat.id,
                text="Хотите поставить себе напоминание?",
                reply_markup=InlineKeyboardMarkup(reminder_menu)
            )

            message_to_delete[0] = msg

        except ValueError:
            msg = app.send_message(message.chat.id, "Это не положительное число.")
            app.register_next_step_handler(msg, goals_day)

    @app.callback_query_handler(func=lambda call: call.data == "goals_reminder_yes")
    def goals_reminder_yes(call: CallbackQuery):
        app.answer_callback_query(call.id)
        msg = app.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=message_to_delete[0].message_id,
            text="Введите в какое время хотите получать уведомление (ЧЧ:ММ).",
            reply_markup=None,
        )
        app.register_next_step_handler(msg, goals_reminder_set)

    def goals_reminder_set(message: Message):
        if re.fullmatch(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', message.text):
            bot.update_user_attribute(User(message.from_user.username, message.chat.id), 'reminder', time(
                int(message.text.split(":")[0]),
                int(message.text.split(":")[1]),
            ))
            goals_confirmation(message)
        else:
            msg = app.send_message(
                chat_id=message.chat.id,
                text="Введенное значение не соответствует требованию."
            )
            app.register_next_step_handler(msg, goals_reminder_set)

    @app.callback_query_handler(func=lambda call: call.data == "goals_reminder_no")
    def goals_reminder_no(call: CallbackQuery):
        app.answer_callback_query(call.id)
        app.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=message_to_delete[0].message_id,
            text=message_to_delete[0].text,
            reply_markup=None,
        )
        goals_confirmation(call.message)

    def goals_confirmation(message: Message):
        user = bot.get_user(message.chat.id)

        reminder_confirmation_menu = [
            [
                InlineKeyboardButton("Да", callback_data="goals_reminder_confirmation_yes"),
                InlineKeyboardButton("Нет", callback_data="goals_reminder_confirmation_no")
            ]
        ]

        if user:
            msg = app.send_message(
                chat_id=message.chat.id,
                text=f'Ваши цели:\n'
                     f'-Книг за год: {user.annual_goals}\n'
                     f'-Книг за месяц: {user.monthly_goals}\n'
                     f'-Книг за неделю: {user.weekly_goals}\n'
                     f'-Минут в день: {user.daily_goals}\n\n'
                     f'{f'Напоминания:\n-Каждый день в {user.reminder}' if user.reminder else ''}\n\n'
                     f'Все верно?',
                reply_markup=InlineKeyboardMarkup(reminder_confirmation_menu)
            )

            message_to_delete[0] = msg
        else:
            msg = app.send_message(
                chat_id=message.chat.id,
                text='Заглушка, пока проверить пользователя нельзя, да - выход в меню, нет - повтор',
                reply_markup=InlineKeyboardMarkup(reminder_confirmation_menu)
            )

            message_to_delete[0] = msg

    @app.callback_query_handler(func=lambda call: call.data == "goals_reminder_confirmation_yes")
    def goals_reminder_confirmation_yes(call: CallbackQuery):
        app.answer_callback_query(call.id)
        app.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=message_to_delete[0].message_id,
            text=message_to_delete[0].text,
            reply_markup=None,
        )
        menu(call.message)

    @app.callback_query_handler(func=lambda call: call.data == "goals_reminder_confirmation_no")
    def goals_reminder_confirmation_no(call: CallbackQuery):
        app.answer_callback_query(call.id)
        app.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=message_to_delete[0].message_id,
            text=message_to_delete[0].text,
            reply_markup=None,
        )
        call.data = "start_goals"
        app.send_message(call.message.chat.id, "Введите данные повторно.")
        handle_callbacks(call)

    print("Бот работает.")
    app.polling()

if __name__ == "__main__":
    pass