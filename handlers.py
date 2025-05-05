from telebot import TeleBot
from concurrent.futures import ThreadPoolExecutor
from telebot.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    InputMediaPhoto,
)
from bot import TelegramBot, User, time, Book, Report, Note, Quote, Union, datetime
from typing import Callable, final
from supabase import Client
import re


def init_bot(app: TeleBot, connection, BOT_TOKEN: str):
    bot = TelegramBot(connection)

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
            if bot.get_user(message.chat.id).annual_goal == -1:
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
                    text="Введите в какое время хотите получать уведомление (ЧЧ:ММ).",
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
                reminder_text = f"Напоминания:\n-Каждый день в {user.reminder}" if user.reminder else ""

                msg = app.send_message(
                chat_id=message.chat.id,
                text=f"Ваши цели:\n"
                    f"- Книг за год: {user.annual_goal}\n"
                    f"- Книг за месяц: {user.monthly_goal}\n"
                    f"- Книг за неделю: {user.weekly_goal}\n"
                    f"- Минут в день: {user.daily_goal}\n\n"
                    f"{reminder_text}\n\n"
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
                msg = app.send_message(
                    message.chat.id, "Введено неправильное значение."
                )
                app.register_next_step_handler(msg, goals_reminder_confirmation_check)

    def help(app: TeleBot):
        @app.callback_query_handler(func=lambda call: call.data == "start_help")
        def handle_start_help(call: CallbackQuery):
            app.answer_callback_query(call.id)
            app.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"Контактные данные и описание: ДОПИСАТЬ.",
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
                    chat_id=message.chat.id, message_id=message.message_id, text=text
                )
            else:
                app.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    text="Невозможно собрать статистику. Пока нет добавленных книг.",
                )
        from typing import Tuple
        def statistic_report(message):
            reports: Tuple[Report, Report] = bot.get_report(message.chat.id)
            try:
                progress = reports[0].pages_read / reports[1].pages_read * 100
            except ZeroDivisionError as e:
                progress = 0

            
            app.send_message(
                chat_id=message.chat.id,
                text=f"Ваши результаты за неделю.\n"
                f"-Прочитано книг: {reports[0].books_read} ({reports[0].pages_read} стр.)\n"
                f"-Новые цитаты: {reports[0].quotes_added}\n"
                f"На {progress if progress < 100 else progress - 100}%{f' менее' if progress < 100 else ''} продуктивнее прошлой недели.\n",
            )

    def notes(app: TeleBot, bot: TelegramBot):
        @app.callback_query_handler(func=lambda call: call.data == "start_notes")
        def handle_start_notes(call: CallbackQuery):
            app.answer_callback_query(call.id)
            handle_start_notes_first_message(call.message)

        def handle_start_notes_first_message(message: Message):
            books = bot.get_books(message.chat.id)
            if books:
                text = "Выберите книгу:\n"
                for number, book in enumerate(books):
                    text += f"{number + 1}. {book.author} - {book.title}\n"
                msg = app.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    text=text,
                    reply_markup=None,
                )
                app.register_next_step_handler(
                    msg, lambda message: notes_check_book(message, books)
                )
            else:
                app.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    text="У вас нет книг. Пока что невозможно создать заметку.",
                    reply_markup=None,
                )

        def notes_check_book(message: Message, books: list[Book]):
            try:
                number = int(message.text)
                if number < 1 or number > len(books):
                    msg = app.send_message(
                        chat_id=message.chat.id,
                        text="Книги с таким порядковым номером нет в вашем списке. Введите еще раз.",
                    )
                    app.register_next_step_handler(
                        msg, lambda message: notes_check_book(message, books)
                    )
                else:
                    msg = app.send_message(
                        chat_id=message.chat.id, text="Напишите отзыв к книге."
                    )
                    app.register_next_step_handler(
                        msg,
                        lambda message: notes_get_opinion(message, books[number - 1]),
                    )
            except ValueError:
                msg = app.send_message(
                    chat_id=message.chat.id,
                    text="Введите порядковый номер книги. Введите еще раз.",
                )
                app.register_next_step_handler(
                    msg, lambda message: notes_check_book(message, books)
                )

        def notes_get_opinion(message: Message, book: Book):
            note = Note(message.chat.id, book.book_id, None, message.text)

            msg = app.send_message(
                chat_id=message.chat.id,
                text="Отзыв получен. Поставьте рейтинг прочитанной книге по 10-бальной шкале.",
            )

            app.register_next_step_handler(
                msg, lambda message: notes_check_rating(message, note)
            )

        def notes_check_rating(message: Message, note: Note):
            try:
                rating = int(message.text)
                if rating < 1 or rating > 10:
                    msg = app.send_message(
                        chat_id=message.chat.id,
                        text="Значение не подходит. Введите еще раз.",
                    )
                    app.register_next_step_handler(
                        msg, lambda message: notes_check_rating(message, note)
                    )
                else:
                    note.rating = rating
                    msg = app.send_message(
                        chat_id=message.chat.id,
                        text=f"Подтверждение:\n"
                        f"Отзыв: {note.opinion}\n"
                        f"Рейтинг: {note.rating}/10\n\n"
                        f"Все верно? (y/n)",
                    )
                    app.register_next_step_handler(
                        msg, lambda message: notes_confirmation(message, note)
                    )
            except ValueError:
                msg = app.send_message(
                    chat_id=message.chat.id,
                    text="Значение не подходит. Введите еще раз.",
                )
                app.register_next_step_handler(
                    msg, lambda message: notes_check_rating(message, note)
                )

        def notes_confirmation(message: Message, note: Note):
            if message.text == "y":
                bot.create_note(note)
                app.send_message(
                    chat_id=message.chat.id, text="Заметка успешно сохранена."
                )
            elif message.text == "n":
                msg = app.send_message(
                    chat_id=message.chat.id, text="Повторите ввод данных заметки."
                )
                handle_start_notes_first_message(msg)
            else:
                msg = app.send_message(chat_id=message.chat.id, text="Введите y или n.")
                app.register_next_step_handler(
                    msg, lambda message: notes_confirmation(message, note)
                )

    def quotes(app: TeleBot, bot: TelegramBot):
        @app.callback_query_handler(func=lambda call: call.data == "start_quotes")
        def handle_start_quotes(call: CallbackQuery):

            app.answer_callback_query(call.id)
            handle_start_quotes_first_message(call.message)

        def handle_start_quotes_first_message(message: Message):
            books = bot.get_books(message.chat.id)
            if books:
                text = "Выберите книгу:\n"
                for number, book in enumerate(books):
                    text += f"{number + 1}. {book.author} - {book.title}\n"
                msg = app.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    text=text,
                    reply_markup=None,
                )
                app.register_next_step_handler(
                    msg, lambda message: quotes_check_book(message, books)
                )
            else:
                app.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    text="У вас нет книг. Пока что эта опция недоступна.",
                    reply_markup=None,
                )

        def quotes_check_book(message: Message, books: list[Book]):
            try:
                number = int(message.text)
                if number < 1 or number > len(books):
                    msg = app.send_message(
                        chat_id=message.chat.id,
                        text="Книги с таким порядковым номером нет в вашем списке. Введите еще раз.",
                    )
                    app.register_next_step_handler(
                        msg, lambda message: quotes_check_book(message, books)
                    )
                else:
                    msg = app.send_message(
                        chat_id=message.chat.id,
                        text="1. Добавить цитату.\n" "2. Список цитат.",
                    )
                    app.register_next_step_handler(
                        msg,
                        lambda message: quotes_add_or_list(message, books[number - 1]),
                    )
            except ValueError:
                msg = app.send_message(
                    chat_id=message.chat.id,
                    text="Введите порядковый номер книги. Введите еще раз.",
                )
                app.register_next_step_handler(
                    msg, lambda message: quotes_check_book(message, books)
                )

        def quotes_add_or_list(message: Message, book: Union[Book, Quote]):
            if message.text == "1":
                msg = app.send_message(
                    chat_id=message.chat.id,
                    text="Введите цитату.",
                )
                app.register_next_step_handler(
                    msg, lambda message: quotes_register_text(message, book)
                )
            elif message.text == "2":
                quotes = bot.get_quotes(book)
                text = f"Список цитат:\n"
                for number, quote in enumerate(quotes):
                    text += f'{number+1}. "{quote.text} стр. {quote.page_number}"'
                app.send_message(
                    chat_id=message.chat.id,
                    text=text,
                )
            else:
                msg = app.send_message(
                    chat_id=message.chat.id, text="Такой опции нет. Введите 1 или 2."
                )
                app.register_next_step_handler(
                    msg, lambda message: quotes_add_or_list(message, book)
                )

        def quotes_register_text(message: Message, book: Union[Book, Quote]):
            if isinstance(book, Book):
                quote = Quote(
                    book_id=book.book_id,
                    user_id=None,
                    page_number=None,
                    text=message.text,
                    chat_id=message.chat.id,
                )
            else:
                quote = book
                quote.text = message.text

            msg = app.send_message(chat_id=message.chat.id, text="Укажите страницу.")

            app.register_next_step_handler(
                msg, lambda message: quotes_register_page(message, quote)
            )

        def quotes_register_page(message: Message, quote: Quote):
            try:
                number = int(message.text)
                if number < 1:
                    msg = app.send_message(
                        chat_id=message.chat.id,
                        text="Это не натуральное число. Введите еще раз.",
                    )
                    app.register_next_step_handler(
                        msg, lambda message: quotes_register_page(message, quote)
                    )
                else:
                    quote.page_number = number
                    msg = app.send_message(
                        chat_id=message.chat.id,
                        text=f"Подтверждение:\n"
                        f'"{quote.text}" стр. {quote.page_number}\n\n'
                        f"Все верно? (y/n)",
                    )
                    app.register_next_step_handler(
                        msg, lambda message: quotes_confirmation(message, quote)
                    )
            except ValueError:
                msg = app.send_message(
                    chat_id=message.chat.id, text="Это не число. Введите еще раз."
                )
                app.register_next_step_handler(
                    msg, lambda message: quotes_confirmation(message, quote)
                )

        def quotes_confirmation(message: Message, quote: Quote):
            if message.text == "y":
                bot.create_quote(quote)
                app.send_message(
                    chat_id=message.chat.id, text="Цитата успешно сохранена."
                )
            elif message.text == "n":
                msg = app.send_message(
                    chat_id=message.chat.id,
                    text="Добавьте цитату заново.\n" "Введите цитату.",
                )
                app.register_next_step_handler(
                    msg, lambda message: quotes_register_text(message, quote)
                )
            else:
                msg = app.send_message(chat_id=message.chat.id, text="Введите y или n.")
                app.register_next_step_handler(
                    msg, lambda message: quotes_confirmation(message, quote)
                )

    def books(app: TeleBot, bot: TelegramBot):
        def books_menu(message: Message):
            msg = app.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=f"1. Добавить книгу.\n"
                f"2. Поиск книги\n"
                f"3. Мои книги\n"
                f"4. Редактировать книгу.\n"
                f"5. Назад\n\n"
                f"Выберите номер опции",
            )
            app.register_next_step_handler(msg, books_menu_options)

        @app.callback_query_handler(func=lambda call: call.data == "start_books")
        def handle_start_books(call: CallbackQuery):
            app.answer_callback_query(call.id)
            books_menu(call.message)

        def books_menu_options(message: Message):
            try:
                option = int(message.text)
                match option:
                    case 1:
                        books_add(message)
                    case 2:
                        books_search(message)
                    case 3:
                        books_users_books(message)
                    case 4:
                        books_pick_to_edit(message)
                    case 5:
                        app.send_message(
                            chat_id=message.chat.id,
                            text="Выберите /menu для продолжения.",
                        )
                    case _:
                        msg = app.send_message(
                            chat_id=message.chat.id,
                            text="Такой опции нет. Выберите еще раз.",
                        )
                        app.register_next_step_handler(msg, books_menu_options)
            except ValueError:
                msg = app.send_message(chat_id=message.chat.id, text="Введите номер.")
                app.register_next_step_handler(msg, books_menu_options)

        def books_add(message: Message):
            msg = app.send_message(
                chat_id=message.chat.id,
                text="Введите название книги.(Поддерживается ввод через гс)",
            )
            app.register_next_step_handler(msg, books_add_title)

        def books_add_title(message: Message):
            book = Book()
            try:
                file_info = app.get_file(message.voice.file_id)
                file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
                book.title = bot.voice_to_speech(file_url)
            except AttributeError:
                book.title = message.text
            msg = app.send_message(
                chat_id=message.chat.id, text="Введите автора. (Формат: Фамилия Имя Отчество)"
            )
            app.register_next_step_handler(
                msg, lambda message: books_add_author(message, book)
            )

        def books_add_author(message: Message, book: Book):
            try:
                file_info = app.get_file(message.voice.file_id)
                file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
                book.author = bot.voice_to_speech(file_url)
            except AttributeError:
                author = message.text
                if len(author.split(" ")) != 3:
                    msg = app.send_message(
                        chat_id=message.chat.id,
                        text="В сообщение должно быть три слова."
                    )
                    app.register_next_step_handler(msg, lambda message: books_add_author(message, book))
                    return
                book.author = author
                book = bot.get_book_from_side_site(book)
                msg = app.send_message(
                    chat_id=message.chat.id,
                    text=f"Название: {book.title}\n"
                    f"Автор: {book.author}\n"
                    f"Жанр: {book.genre}\n"
                    f"Год: {book.year}\n\n"
                    f"Это книга, которую вы хотите добавить? (y/n)",
            )
            app.register_next_step_handler(
                msg, lambda message: books_first_confirmation(message, book)
            )

        def books_first_confirmation(message: Message, book: Book):
            if message.text == "y":
                msg = app.send_message(
                    chat_id=message.chat.id, text="Скиньте фото или ссылку обложки."
                )
                app.register_next_step_handler(
                    msg, lambda message: books_cover(message, book)
                )
            elif message.text == "n":
                msg = app.send_message(
                    chat_id=message.chat.id,
                    text="Заполните тогда оставшиеся поля сами.\n"
                    "Выберите жанр:\n"
                    "1. Классика\n"
                    "2. Фантастика\n"
                    "3. Детектив\n"
                    "4. Роман\n"
                    "5. Наука\n"
                    "6. Другое (при выборе этой опции надо будет ввести жанр самому)\n",
                )
                app.register_next_step_handler(
                    msg, lambda message: books_genre_choice(message, book)
                )
            else:
                msg = app.send_message(chat_id=message.chat.id, text="Введите y или n")
                app.register_next_step_handler(
                    msg, lambda message: books_first_confirmation(message, book)
                )

        def books_genre_choice(message: Message, book: Book):
            try:
                number = int(message.text)
                match number:
                    case 1:
                        book.genre = "Классика"
                    case 2:
                        book.genre = "Фантастика"
                    case 3:
                        book.genre = "Детектив"
                    case 4:
                        book.genre = "Роман"
                    case 5:
                        book.genre = "Наука"
                    case 6:
                        msg = app.send_message(
                            chat_id=message.chat.id, text="Введите жанр."
                        )
                        app.register_next_step_handler(
                            msg, lambda message: books_genre_user_input(message, book)
                        )
                    case _:
                        msg = app.send_message(
                            chat_id=message.chat.id, text="Введите число от 1 до 6."
                        )
                        app.register_next_step_handler(
                            msg, lambda message: books_genre_choice(message, book)
                        )
                        return
                msg = app.send_message(
                    chat_id=message.chat.id, text="Введите год издания."
                )
                app.register_next_step_handler(
                    msg, lambda message: books_year(message, book)
                )

            except ValueError:
                msg = app.send_message(chat_id=message.chat.id, text="Введите число")
                app.register_next_step_handler(
                    msg, lambda message: books_genre_choice(message, book)
                )

        def books_genre_user_input(message: Message, book: Book):
            book.genre = message.text
            msg = app.send_message(chat_id=message.chat.id, text="Введите год издания.")
            app.register_next_step_handler(
                msg, lambda message: books_year(message, book)
            )

        def books_year(message: Message, book: Book):
            try:
                year = int(message.text)
                if year < 0 or year > datetime.now().year:
                    msg = app.send_message(
                        chat_id=message.chat.id,
                        text=f"Введите год нашей эры не превышающий {datetime.now().year}",
                    )
                    app.register_next_step_handler(
                        msg, lambda message: books_year(message, book)
                    )
                else:
                    msg = app.send_message(
                        chat_id=message.chat.id, text="Скиньте фото или ссылку обложки."
                    )
                    app.register_next_step_handler(
                        msg, lambda message: books_cover(message, book)
                    )
            except ValueError:
                msg = app.send_message(chat_id=message.chat.id, text="Введите число.")
                app.register_next_step_handler(
                    msg, lambda message: books_year(message, book)
                )

        def books_cover(message: Message, book: Book):
            try:
                if message.text == "0":
                    msg = app.send_message(
                        chat_id=message.chat.id,
                        text="https://img.freepik.com/premium-photo/white-background-with-black-white-image-white-background_796580-1989.jpg?w=1380\nВыберите статус книги: \n"
                             "1. Читаю сейчас\n"
                             "2. Прочитано\n"
                             "3. Отложено\n",
                    )
                else:
                    photo = message.photo[-1]
                    file_id = photo.file_id
                    file_info = app.get_file(file_id)
                    book.cover = file_info
                    msg = app.send_message(
                        chat_id=message.chat.id,
                        text="Выберите статус книги: \n"
                        "1. Читаю сейчас\n"
                        "2. Прочитано\n"
                        "3. Отложено\n",
                    )
                app.register_next_step_handler(
                    msg, lambda message: books_status(message, book)
                )
            except:
                if (
                    re.match(
                        r"^(https?://.*\.(jpg|jpeg))$", message.text, re.IGNORECASE
                    )
                    is not None
                ):
                    book.cover = message.text
                    msg = app.send_message(
                        chat_id=message.chat.id,
                        text="Выберите статус книги: \n"
                        "1. Читаю сейчас\n"
                        "2. Прочитано\n"
                        "3. Отложено\n",
                    )
                    app.register_next_step_handler(
                        msg, lambda message: books_status(message, book)
                    )
                else:
                    msg = app.send_message(
                        chat_id=message.chat.id,
                        text="Вы не скинули фото. Попробуйте еще раз.",
                    )
                    app.register_next_step_handler(
                        msg, lambda message: books_cover(message, book)
                    )
        def books_status(message: Message, book: Book):
            try:
                number = int(message.text)
                match number:
                    case 1:
                        book.status = "Читаю сейчас"
                    case 2:
                        book.status = "Прочитано"
                    case 3:
                        book.status = "Отложено"
                    case _:
                        msg = app.send_message(
                            chat_id=message.chat.id,
                            text="Такой опции нет. Введите от 1 до 3",
                        )
                        app.register_next_step_handler(
                            msg, lambda message: books_status(message, book)
                        )
                        return
                msg = app.send_message(
                    chat_id=message.chat.id,
                    text=f"{book.cover}\n"
                    f"Подтверждение: \n"
                    f"Название: {book.title}\n"
                    f"Автор: {book.author}\n"
                    f"Жанр: {book.genre}\n"
                    f"Год: {book.year}\n"
                    f"Статус: {book.status}\n\n"
                    f"Все верно? (y/n)",
                )
                app.register_next_step_handler(
                    msg, lambda message: books_final_confirmation(message, book)
                )
            except ValueError:
                msg = app.send_message(chat_id=message.chat.id, text="Введите число.")
                app.register_next_step_handler(
                    msg, lambda message: books_status(message, book)
                )

        def books_final_confirmation(message: Message, book: Book):
            if message.text == "y":
                bot.create_book(book, message.chat.id)
                app.send_message(chat_id=message.chat.id, text="Книга создана.")
            elif message.text == "n":
                msg = app.send_message(
                    chat_id=message.chat.id,
                    text="Введиите все данные заново.\n" "Введите название книги.",
                )
                app.register_next_step_handler(msg, books_add_title)
            else:
                msg = app.send_message(chat_id=message.chat.id, text="Введите y или n.")
                app.register_next_step_handler(
                    msg, lambda message: books_final_confirmation(message, book)
                )

        def books_search(message: Message):
            msg = app.send_message(
                chat_id=message.chat.id,
                text="Выберите по какому полю, будет производиться поиск:\n"
                "1. По названию.\n"
                "2. По автору.\n"
                "3. По жанру.\n"
                "4. По году.\n\n"
                "Введите номер опции.",
            )
            app.register_next_step_handler(msg, books_search_get_type)

        def books_search_get_type(message: Message):
            try:
                number = int(message.text)
                if number < 1 or number > 4:
                    msg = app.send_message(
                        chat_id=message.chat.id,
                        text="Такой опции нет. Введите еще раз.",
                    )
                    app.register_next_step_handler(msg, books_search_get_type)
                elif number == 4:
                    msg = app.send_message(
                        chat_id=message.chat.id, text="Введите год для поиска."
                    )
                    app.register_next_step_handler(msg, books_search_return_by_year)
                else:
                    match number:
                        case 1:
                            text = "название."
                            
                        case 2:
                            text = "автора."
                        case 3:
                            text = "жанр."
                    msg = app.send_message(
                        chat_id=message.chat.id,
                        text="Введите " + text,
                    )
                    app.register_next_step_handler(
                        msg, lambda message: books_search_return_by_str(message, number)
                    )
            except ValueError:
                msg = app.send_message(chat_id=message.chat.id, text="Введите число.")
                app.register_next_step_handler(msg, books_search_get_type)

        def books_search_return_by_str(message: Message, type: int):
            books = bot.get_books(message.chat.id)
            to_send_back: list[Book] = []
            for book in books:
                if type == 1:
                    to_send_back.append(book) if book.author == message.text else None
                elif type == 2:
                    to_send_back.append(book) if book.title == message.text else None
                else:
                    to_send_back.append(book) if book.title == message.text else None

            if to_send_back:
                app.send_message(chat_id=message.chat.id, text="Найденные книги:")
                for i in range(len(to_send_back) // 3 + 1):
                    text = ""
                    media = []
                    for j in range(0 + 3 * (i - 1), 3 + 3 * (i - 1)):
                        if j >= len(to_send_back):
                            break
                        media.append(InputMediaPhoto(media=to_send_back[j].cover))
                        note = bot.get_note(message.chat.id, to_send_back[j].book_id)
                        text += (
                           f"Рейтинг: {note.rating if note else 'нет'}\n"
                           f"Заметка: {note.opinion if note else 'нет'}\n\n"

                        )
                    media[0 + 3 * (i - 1)].caption = text
                    app.send_media_group(chat_id=message.chat.id, media=media)
            else:
                app.send_message(chat_id=message.chat.id, text="Книги не найдены.")

        def books_search_return_by_year(message: Message):
            try:
                year = int(message.text)
                if year < 0 or year > datetime.now().year:
                    msg = app.send_message(
                        chat_id=message.chat.id,
                        text="Введите год нашей эры, не превышающий текущий.",
                    )
                    app.register_next_step_handler(msg, books_search_return_by_year)
                else:
                    books = bot.get_books(message.chat.id)
                    to_send_back: list[Book] = []
                    for book in books:
                        to_send_back.append(book) if book.year == year else None

                    if to_send_back:
                        app.send_message(
                            chat_id=message.chat.id,
                            text="Книги, найденные по данному году:",
                        )
                        for i in range(len(to_send_back) // 3 + 1):
                            text = ""
                            media = []
                            for j in range(0 + 3 * (i), 3 + 3 * (i)):
                                if j >= len(to_send_back):
                                    break
                                media.append(
                                    InputMediaPhoto(media=to_send_back[j].cover)
                                )
                                note = bot.get_note(
                                    message.chat.id, to_send_back[j].book_id
                                )
                                text += (
                                    f"{j + 1}. {to_send_back[j].title} - {to_send_back[j].author}\n"
                                    f"Рейтинг: {note.rating if note else 'нет'}\n"
                                    f"Заметка: {note.opinion if note else 'нет'}\n\n"
                                )
                            media[0 + 3 * (i)].caption = text
                            app.send_media_group(chat_id=message.chat.id, media=media)
                    else:
                        app.send_message(
                            chat_id=message.chat.id,
                            text="Книги с таким годом не найдены.",
                        )

            except ValueError:
                msg = app.send_message(chat_id=message.chat.id, text="Введите число.")
                app.register_next_step_handler(msg, books_search_return_by_year)

        def books_users_books(message: Message):
            books = bot.get_books(message.chat.id)

            if len(books):
                print("Тута")
                sorted_by_status = {
                    "Читаю сейчас": 0,
                    "Прочитано": 0,
                    "Отложено": 0,
                }
                for book in books:
                    sorted_by_status[book.status] += 1

                text = "Ваши книги по статусу:\n"
                for key, value in sorted_by_status.items():
                    text += f"{key}: {value}\n"

                app.send_message(chat_id=message.chat.id, text=text)

                text = "Все ваши книги:\n"
                for number, book in enumerate(books):
                    text += f"{number+1}. {book.author} - {book.title}\n"

                app.send_message(chat_id=message.chat.id, text=text)
            else:
                app.send_message(
                    chat_id=message.chat.id,
                    text="У вас нет на данный момент добавленных книг.",
                )

        def books_pick_to_edit(message: Message):
            books = bot.get_books(message.chat.id)
            if books:
                text = "Все ваши книги (выберите номер, чтобы редактировать, 0 чтобы выйти):\n"
                for number, book in enumerate(books):
                    text += f"{number + 1}. {book.author} - {book.title}\n"

                msg = app.send_message(chat_id=message.chat.id, text=text)

                app.register_next_step_handler(
                    msg, lambda message: books_edit_book(message, books)
                )

        def books_edit_book(message: Message, books: list[Book]):
            try:
                number = int(message.text)
                if number < 0 or number > len(books):
                    msg = app.send_message(
                        chat_id=message.chat.id,
                        text="Такой книги нет. Введите еще раз.",
                    )
                    app.register_next_step_handler(
                        msg, lambda message: books_edit_book(message, books)
                    )
                elif number == 0:
                    app.send_message(
                        chat_id=message.chat.id, text="Редактирование отменено."
                    )
                else:
                    book = books[number - 1]
                    text = (
                        f"Данные книги:\n"
                        f"1. Название: {book.title}\n"
                        f"2. Автор: {book.author}\n"
                        f"3. Жанр: {book.genre}\n"
                        f"4. Год: {book.year}\n"
                        f"5. Статус: {book.status}\n\n"
                        f"Какое поле хотите редактировать?"
                    )

                    msg = app.send_message(chat_id=message.chat.id, text=text)

                    app.register_next_step_handler(
                        msg, lambda message: books_attribute_edit(message, book)
                    )
            except ValueError:
                msg = app.send_message(chat_id=message.chat.id, text="Введите номер.")
                app.register_next_step_handler(
                    msg, lambda message: books_edit_book(message, books)
                )

        def books_attribute_edit(message: Message, book: Book):
            try:
                number = int(message.text)
                match number:
                    case 1 | 2 | 3:
                        msg = app.send_message(
                            chat_id=message.chat.id,
                            text=f"Введите новое значение для поля.",
                        )
                        app.register_next_step_handler(
                            msg, lambda message: books_edit_str(message, book, number)
                        )
                    case 4:
                        msg = app.send_message(
                            chat_id=message.chat.id,
                            text=f"Введите новый год выхода книги.",
                        )
                        app.register_next_step_handler(
                            msg, lambda message: books_edit_num(message, book)
                        )
                    case 5:
                        msg = app.send_message(
                            chat_id=message.chat.id,
                            text=f"Введите новый статус книги. Поддерживаются следующие статусы:\n"
                            f"1. Читаю сейчас.\n"
                            f"2. Прочитано.\n"
                            f"3. Отложено.\n\n"
                            f"Выберите номер.",
                        )
                        app.register_next_step_handler(
                            msg, lambda message: books_edit_status(message, book)
                        )
                    case _:
                        msg = app.send_message(
                            chat_id=message.chat.id,
                            text="Такой опции нет. Введите еще раз.",
                        )
                        app.register_next_step_handler(
                            msg, lambda message: books_attribute_edit(message, book)
                        )

            except ValueError:
                msg = app.send_message(chat_id=message.chat.id, text="Введите номер.")
                app.register_next_step_handler(
                    msg, lambda message: books_attribute_edit(message, book)
                )

        def books_edit_status(message: Message, book: Book):
            try:
                number = int(message.text)
                match number:
                    case 1:
                        book.status = "Читаю сейчас"
                    case 2:
                        book.status = "Прочитано"
                    case 3:
                        book.status = "Отложено"
                    case _:
                        msg = app.send_message(
                            chat_id=message.chat.id,
                            text="Такого статуса нет. Введите еще раз.",
                        )
                        app.register_next_step_handler(
                            msg, lambda message: books_edit_status(message, book)
                        )
                        return
                msg = app.send_message(
                    chat_id=message.chat.id,
                    text=f"Поле успешно обновлено.\n"
                    f"Хотите обновить другие поля? (y/n)",
                )
                app.register_next_step_handler(
                    msg, lambda message: books_edit_confirmation(message, book)
                )
            except ValueError:
                msg = app.send_message(chat_id=message.chat.id, text="Введите номер.")
                app.register_next_step_handler(
                    msg, lambda message: books_attribute_edit(message, book)
                )

        def books_edit_num(message: Message, book: Book):
            try:
                number = int(message.text)
                if number < 0 or number > datetime.now().year:
                    msg = app.send_message(
                        chat_id=message.chat.id,
                        text="Введен некорректный год. Введите еще раз.",
                    )
                    app.register_next_step_handler(
                        msg, lambda message: books_edit_num(message, book)
                    )
                else:
                    book.year = number
                    msg = app.send_message(
                        chat_id=message.chat.id,
                        text=f"Поле успешно обновлено.\n"
                        f"Хотите обновить другие поля? (y/n)",
                    )
                    app.register_next_step_handler(
                        msg, lambda message: books_edit_confirmation(message, book)
                    )
            except ValueError:
                msg = app.send_message(chat_id=message.chat.id, text="Введите число.")
                app.register_next_step_handler(
                    msg, lambda message: books_edit_num(message, book)
                )

        def books_edit_str(message: Message, book: Book, choice: int):
            match choice:
                case 1:
                    book.title = message.text
                case 2:
                    book.author = message.text
                case 3:
                    book.genre = message.text
            msg = app.send_message(
                chat_id=message.chat.id,
                text=f"Поле успешно обновлено.\n" f"Хотите обновить другие поля? (y/n)",
            )
            app.register_next_step_handler(
                msg, lambda message: books_edit_confirmation(message, book)
            )

        def books_edit_confirmation(message: Message, book: Book):
            if message.text == "y":
                msg = app.send_message(
                    chat_id=message.chat.id,
                    text=f"Введите вариант заново.\n"
                    f"Данные книги:\n"
                    f"1. Название: {book.title}\n"
                    f"2. Автор: {book.author}\n"
                    f"3. Жанр: {book.genre}\n"
                    f"4. Год: {book.year}\n"
                    f"5. Статус: {book.status}\n\n"
                    f"Какое поле хотите редактировать?",
                )
                app.register_next_step_handler(
                    msg, lambda message: books_attribute_edit(message, book)
                )
            elif message.text == "n":
                bot.update_book(book)
                app.send_message(
                    chat_id=message.chat.id,
                    text=f"Редактирование завершено. Редактированные данные книги:\n"
                    f"Название: {book.title}\n"
                    f"Автор: {book.author}\n"
                    f"Жанр: {book.genre}\n"
                    f"Год: {book.year}\n"
                    f"Статус: {book.status}",
                )
            else:
                msg = app.send_message(chat_id=message.chat.id, text="Введите y или n.")
                app.register_next_step_handler(
                    msg, lambda message: books_attribute_edit(message, book)
                )

    goals(app, bot)
    statistic(app, bot)
    help(app)
    notes(app, bot)
    quotes(app, bot)
    books(app, bot)

    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(bot.generate_reports)
        print("Бот работает.")
        executor.submit(app.polling)


if __name__ == "__main__":
    pass
