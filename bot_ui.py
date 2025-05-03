import os
import re
from pathlib import Path
from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler
)

class Config:
    EMOJI = {
        "books": "📚", "shelves": "🗂", "notes": "✍️", "quotes": "⭐",
        "stats": "📊", "goals": "🎯", "help": "ℹ️", "back": "🔙",
        "add": "➕", "search": "🔍", "tags": "🏷", "year": "📅",
        "quote": "💬", "author": "✍️", "genre": "🏷", "rating": "⭐",
        "characters": "👥", "reminders": "⏰", "confirm": "✅", "cancel": "❌"
    }

class States:
    # Состояния для добавления книг
    ADD_BOOK_TITLE = 0
    ADD_BOOK_AUTHOR = 1
    CONFIRM_API_DATA = 2
    ADD_BOOK_GENRE_MANUALLY = 3
    ADD_BOOK_GENRE = 4
    ADD_BOOK_YEAR = 5
    ADD_BOOK_STATUS = 6
    CONFIRM_BOOK_DATA = 7

    # Состояния поиска
    SEARCH_METHOD = 8
    SEARCH_BY_TITLE = 9
    SEARCH_BY_AUTHOR = 10
    SEARCH_BY_GENRE = 11
    SEARCH_BY_YEAR = 12
    SEARCH_RESULTS = 13
    ADD_BOOK_START = 14

    # Состояния для моих книг
    CONFIRM_AUTHOR = 15
    MY_BOOKS_MENU = 16
    BOOKS_BY_STATUS = 17
    BOOK_DETAILS = 18
    EDIT_BOOK = 19
    BOOKS_MENU = 20

    # Состояния для заметок
    ADD_NOTE_BOOK = 21
    ADD_NOTE_TEXT = 22
    ADD_NOTE_RATING = 23
    CONFIRM_NOTE = 24
    NOTES_MENU = 25
    SELECT_BOOK_FOR_NOTE = 26
    EDIT_EXISTING_NOTE = 27

    # Состояния для цитат
    ADD_QUOTE_BOOK = 28
    ADD_QUOTE_TEXT = 29
    ADD_QUOTE_PAGE = 30
    CONFIRM_QUOTE = 31
    QUOTES_MENU = 32
    SELECT_BOOK_FOR_QUOTE = 33
    LIST_QUOTES = 34
    EDIT_QUOTE = 35
    DELETE_QUOTE = 36
    QUOTE_DETAILS = 37

    # Состояния для целей
    SETUP_GOALS_QUESTION = 38
    SET_YEARLY_GOAL = 39
    SET_MONTHLY_GOAL = 40
    SET_WEEKLY_GOAL = 41
    SET_DAILY_MINUTES = 42
    SET_REMINDER = 43
    SET_REMINDER_TIME = 44
    CONFIRM_GOALS = 45
    EDIT_GOALS = 46

    # Состояния для статистики
    STATS_MENU = 47
    REPORT_SETTINGS = 48
    SET_REPORT_FREQ = 49
    SET_REPORT_TIME = 50


class BookBot:
    def __init__(self):
        self.user_data = {}

    # Главное меню
    def main_menu_keyboard(self):
        return ReplyKeyboardMarkup([
            [f"{Config.EMOJI['books']} Книги", f"{Config.EMOJI['notes']} Заметки", f"{Config.EMOJI['quotes']} Цитаты"],
            [f"{Config.EMOJI['goals']} Цели", f"{Config.EMOJI['stats']} Статистика", f"{Config.EMOJI['help']} Помощь"]
        ], resize_keyboard=True)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_msg = (
            f"{Config.EMOJI['books']} Добро пожаловать в ваш персональный читательский дневник!\n\n"
            "Выберите действие в меню ниже:"
        )
        await update.message.reply_text(welcome_msg, reply_markup=self.main_menu_keyboard())
        return ConversationHandler.END

    def back_button(self):
        return [InlineKeyboardButton(f"{Config.EMOJI['back']} Назад", callback_data="back")]

    # Обработчик главного меню
    async def handle_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text

        if text == f"{Config.EMOJI['books']} Книги":
            await self.books_menu(update, context)
        elif text == f"{Config.EMOJI['notes']} Заметки":
            return await self.notes_menu(update, context)
        elif text == f"{Config.EMOJI['quotes']} Цитаты":
            return await self.quotes_menu(update, context)
        elif text == f"{Config.EMOJI['goals']} Цели":
            return await self.goals_menu(update, context)
        elif text == f"{Config.EMOJI['stats']} Статистика":
            await self.show_stats(update, context)
        elif text == f"{Config.EMOJI['help']} Помощь":
            await self.help_menu(update, context)
        else:
            await update.message.reply_text(
                "Пожалуйста, используйте меню для навигации",
                reply_markup=self.main_menu_keyboard()
            )
        return ConversationHandler.END

    # Раздел книг
    # Меню управления книгами
    async def books_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{Config.EMOJI['add']} Добавить книгу", callback_data="add_book")],
            [InlineKeyboardButton(f"{Config.EMOJI['search']} Поиск книги", callback_data="search_book")],
            [InlineKeyboardButton(f"{Config.EMOJI['books']} Мои книги", callback_data="my_books")]
            # self.back_button()
        ])

        if update.callback_query:
            await update.callback_query.edit_message_text(
                f"{Config.EMOJI['books']} Управление книгами:",
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                f"{Config.EMOJI['books']} Управление книгами:",
                reply_markup=keyboard
            )
        return ConversationHandler.END

    # Процесс добавления книги
    async def add_book_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            f"{Config.EMOJI['books']} Введите название книги:",
            reply_markup=InlineKeyboardMarkup([self.back_button()])
        )
        return States.ADD_BOOK_TITLE

    async def add_book_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.user_data[update.message.from_user.id] = {'title': update.message.text}
        await update.message.reply_text(
            f"{Config.EMOJI['author']} Введите автора (Формат: Фамилия Имя):",
            reply_markup=InlineKeyboardMarkup([self.back_button()])
        )
        return States.ADD_BOOK_AUTHOR

    async def add_book_author(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.user_data[update.message.from_user.id]['author'] = update.message.text

        # Здесь должен быть запрос к API для поиска книги по названию и автору
        # book_data = await self.search_book_api(title, author)
        # Если API вернул данные:
        if False:  # Замените на реальную проверку результата API
            book_data = {}  # Это должны быть данные из API
            self.user_data[update.message.from_user.id].update(book_data)

            confirmation_msg = (
                f"{Config.EMOJI['books']} Данные книги:\n\n"
                f"📖 Название: {book_data.get('title', 'не указано')}\n"
                f"✍️ Автор: {book_data.get('author', 'не указан')}\n"
                f"🏷 Жанр: {book_data.get('genre', 'не указан')}\n"
                f"📅 Год: {book_data.get('year', 'не указан')}\n"
                f"{Config.EMOJI['confirm']} Все верно?"
            )

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(f"{Config.EMOJI['confirm']} Да", callback_data="confirm_api_data_yes"),
                    InlineKeyboardButton(f"{Config.EMOJI['cancel']} Нет", callback_data="confirm_api_data_no")
                ],
                self.back_button()
            ])

            await update.message.reply_text(confirmation_msg, reply_markup=keyboard)
            return States.CONFIRM_API_DATA
        else:
            await update.message.reply_text(
                "Ничего не нашлось по вашему запросу. Введите данные самостоятельно:",
                reply_markup=InlineKeyboardMarkup([self.back_button()])
            )
            return States.ADD_BOOK_GENRE_MANUALLY

    async def confirm_api_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if query.data == "confirm_api_data_no":
            await query.edit_message_text(
                "Введите данные самостоятельно:",
                reply_markup=InlineKeyboardMarkup([self.back_button()])
            )
            return States.ADD_BOOK_GENRE_MANUALLY
        else:
            # Переходим к выбору статуса, если пользователь подтвердил данные из API
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📖 Читаю сейчас", callback_data="status_reading"),
                    InlineKeyboardButton("✅ Прочитано", callback_data="status_finished")
                ],
                [
                    InlineKeyboardButton("💤 Отложено", callback_data="status_paused"),
                    InlineKeyboardButton("📅 Планирую", callback_data="status_planned")
                ],
                self.back_button()
            ])

            await query.edit_message_text(
                f"{Config.EMOJI['books']} Выберите статус книги:",
                reply_markup=keyboard
            )
            return States.ADD_BOOK_STATUS

    async def add_book_genre_manually(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Классика", callback_data="genre_classic"),
                InlineKeyboardButton("Фантастика", callback_data="genre_fantasy")
            ],
            [
                InlineKeyboardButton("Наука", callback_data="genre_science"),
                InlineKeyboardButton("Другое", callback_data="genre_other")
            ],
            self.back_button()
        ])
        await update.message.reply_text(
            f"{Config.EMOJI['genre']} Выберите жанр:",
            reply_markup=keyboard
        )
        return States.ADD_BOOK_GENRE

    async def add_book_genre(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        genre = query.data.replace("genre_", "")
        self.user_data[query.from_user.id]['genre'] = genre
        await query.edit_message_text(
            f"{Config.EMOJI['year']} Введите год издания (например, 2001):\n\nМожно пропустить /skip",
            reply_markup=InlineKeyboardMarkup([self.back_button()])
        )
        return States.ADD_BOOK_YEAR

    async def add_book_year(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.text != '/skip':
            self.user_data[update.message.from_user.id]['year'] = update.message.text

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📖 Читаю сейчас", callback_data="status_reading"),
                InlineKeyboardButton("✅ Прочитано", callback_data="status_finished")
            ],
            [
                InlineKeyboardButton("💤 Отложено", callback_data="status_paused"),
                InlineKeyboardButton("📅 Планирую", callback_data="status_planned")
            ],
            self.back_button()
        ])

        await update.message.reply_text(
            f"{Config.EMOJI['books']} Выберите статус книги:",
            reply_markup=keyboard
        )
        return States.ADD_BOOK_STATUS

    async def update_book_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        _, status, book_id = query.data.split("_", 2)

        # Здесь должен быть запрос к БД для обновления статуса
        # await self.update_book_status_in_db(book_id, status)

        await query.answer(f"Статус изменен на: {self._get_status_name(status)}")
        return await self.show_book_details(update, context)

    async def add_book_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        status = query.data.replace("status_", "")
        self.user_data[query.from_user.id]['status'] = status

        book_data = self.user_data[query.from_user.id]
        confirmation_msg = (
            f"{Config.EMOJI['books']} Данные книги:\n\n"
            f"📖 Название: {book_data['title']}\n"
            f"✍️ Автор: {book_data['author']}\n"
            f"🏷 Жанр: {book_data.get('genre', 'не указан')}\n"
            f"📅 Год: {book_data.get('year', 'не указан')}\n"
            f"📌 Статус: {status}\n\n"
            f"{Config.EMOJI['confirm']} Все верно?"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"{Config.EMOJI['confirm']} Да", callback_data="confirm_book_yes"),
                InlineKeyboardButton(f"{Config.EMOJI['cancel']} Нет", callback_data="confirm_book_no")
            ],
            self.back_button()
        ])

        await query.edit_message_text(confirmation_msg, reply_markup=keyboard)
        return States.CONFIRM_BOOK_DATA

    async def confirm_book_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if query.data == "confirm_book_no":
            await query.edit_message_text(
                "Начнем процесс заново:",
                reply_markup=InlineKeyboardMarkup([self.back_button()])
            )
            return States.ADD_BOOK_START
        else:
            # Здесь должен быть вызов метода для сохранения книги в БД
            # await self.save_book_to_db(query.from_user.id, self.user_data[query.from_user.id])
            await query.edit_message_text(
                f"{Config.EMOJI['success']} Книга успешно добавлена!",
                reply_markup=self.get_main_menu_keyboard()
            )
            return ConversationHandler.END

    # Процесс поиска книги
    async def search_book_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔍 По названию", callback_data="search_title"),
                InlineKeyboardButton("✍️ По автору", callback_data="search_author")
            ],
            [
                InlineKeyboardButton("🏷 По жанру", callback_data="search_genre"),
                InlineKeyboardButton("📅 По году", callback_data="search_year")
            ],
            self.back_button()
        ])

        await update.callback_query.edit_message_text(
            f"{Config.EMOJI['search']} Выберите критерий поиска:",
            reply_markup=keyboard
        )
        return States.SEARCH_METHOD

    async def search_by_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.edit_message_text(
            f"{Config.EMOJI['books']} Введите название книги:",
            reply_markup=InlineKeyboardMarkup([self.back_button()])
        )
        return States.SEARCH_BY_TITLE

    async def search_by_author(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.edit_message_text(
            f"{Config.EMOJI['author']} Введите автора:",
            reply_markup=InlineKeyboardMarkup([self.back_button()])
        )
        return States.SEARCH_BY_AUTHOR

    async def search_by_genre(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Здесь должен быть запрос к БД для получения списка доступных жанров
        # genres = await self.get_available_genres()
        genres = ["Фантастика", "Детектив", "Роман", "Научная литература"]  # Пример

        buttons = [InlineKeyboardButton(genre, callback_data=f"genre_{genre}") for genre in genres]
        keyboard = InlineKeyboardMarkup(self._chunk_buttons(buttons, 2) + [self.back_button()])

        await update.callback_query.edit_message_text(
            f"{Config.EMOJI['genre']} Выберите жанр:",
            reply_markup=keyboard
        )
        return States.SEARCH_BY_GENRE

    async def search_by_year(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.edit_message_text(
            f"{Config.EMOJI['year']} Введите год издания:",
            reply_markup=InlineKeyboardMarkup([self.back_button()])
        )
        return States.SEARCH_BY_YEAR

    async def show_search_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        search_query = update.message.text if update.message else update.callback_query.data.replace("genre_", "")
        search_method = context.user_data.get('search_method')

        # Здесь должен быть запрос к БД/API для поиска книг
        # books, total_count = await self.search_books_in_db(
        #     method=search_method,
        #     query=search_query,
        #     page=context.user_data.get('page', 0),
        #     limit=10
        # )
        books = []  # Это должны быть результаты из БД/API
        total_count = 0  # Общее количество найденных книг

        if not books:
            await update.message.reply_text(
                "Ничего не найдено. Попробуйте изменить критерии поиска.",
                reply_markup=InlineKeyboardMarkup([self.back_button()])
            )
            return States.SEARCH_METHOD

        # Сохраняем текущую страницу
        current_page = context.user_data.get('page', 0)
        context.user_data['search_results'] = books

        # Формируем сообщение с результатами
        message = f"{Config.EMOJI['books']} Найдено книг: {total_count}\n\n"
        for i, book in enumerate(books, 1):
            message += f"{i}. {book.get('title', 'Без названия')} - {book.get('author', 'Неизвестен')} ({book.get('year', 'нет данных')})\n"

            # Создаем клавиатуру с числами
            keyboard_buttons = []
            if total_count > 10 and (current_page + 1) * 10 < total_count:
                keyboard_buttons.append(InlineKeyboardButton("➡️ Следующая страница", callback_data="next_page"))

            keyboard_buttons.append(self.back_button()[0])
            keyboard = InlineKeyboardMarkup([keyboard_buttons])

            # Отправляем обложки (здесь должен быть реальный код отправки фото)
            # for book in books:
            #     if book.get('cover_url'):
            #         await update.message.reply_photo(book['cover_url'])

            await update.message.reply_text(
                message,
                reply_markup=keyboard
            )
            return States.SEARCH_RESULTS

        async def handle_next_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
            context.user_data['page'] = context.user_data.get('page', 0) + 1
            return await self.show_search_results(update, context)

        def _chunk_buttons(self, buttons, chunk_size):
            """Разбивает кнопки на ряды по chunk_size кнопок в каждом"""
            return [buttons[i:i + chunk_size] for i in range(0, len(buttons), chunk_size)]

    # Мои книги
    # Процесс работы с "Мои книги"
    async def show_my_books(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Здесь должен быть запрос к БД для получения количества книг по статусам
        # status_counts = await self.get_books_count_by_status(user_id=update.effective_user.id)
        status_counts = {
            'reading': 5,  # Читаю сейчас
            'finished': 12,  # Прочитано
            'paused': 3,  # Отложено
            'dropped': 2  # Заброшено
        }

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"📖 Читаю сейчас ({status_counts['reading']})",
                                     callback_data="status_reading"),
                InlineKeyboardButton(f"✅ Прочитано ({status_counts['finished']})",
                                     callback_data="status_finished")
            ],
            [
                InlineKeyboardButton(f"💤 Отложено ({status_counts['paused']})",
                                     callback_data="status_paused"),
                InlineKeyboardButton(f"❌ Заброшено ({status_counts['dropped']})",
                                     callback_data="status_dropped")
            ],
            self.back_button()
        ])

        await update.callback_query.edit_message_text(
            "📚 Мои книги по статусам:",
            reply_markup=keyboard
        )
        return States.MY_BOOKS_MENU

    async def show_books_by_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        status = query.data.replace("status_", "")
        context.user_data['current_status'] = status
        context.user_data['page'] = 0

        # Здесь должен быть запрос к БД для получения книг по статусу
        # books, total_count = await self.get_books_by_status(
        #     user_id=query.from_user.id,
        #     status=status,
        #     page=0,
        #     limit=10
        # )
        books = []  # Это должны быть результаты из БД
        total_count = len(books)  # Общее количество

        if not books:
            await query.edit_message_text(
                f"У вас нет книг с статусом '{self._get_status_name(status)}'.",
                reply_markup=InlineKeyboardMarkup([self.back_button()])
            )
            return States.MY_BOOKS_MENU

        # Формируем сообщение
        status_name = self._get_status_name(status)
        message = f"📚 Книги со статусом '{status_name}' ({total_count}):\n\n"

        # Добавляем список книг
        for i, book in enumerate(books, 1):
            message += f"{i}. {book.get('title', 'Без названия')} - {book.get('author', 'Неизвестен')}\n"

        # Создаем клавиатуру
        keyboard_buttons = []
        if total_count > 10:
            keyboard_buttons.append(InlineKeyboardButton("➡️ Следующая страница", callback_data="next_page"))

        keyboard_buttons.append(self.back_button()[0])
        keyboard = InlineKeyboardMarkup([keyboard_buttons])

        # Отправляем обложки (здесь должен быть реальный код отправки фото)
        # for book in books:
        #     if book.get('cover_url'):
        #         await query.message.reply_photo(book['cover_url'])

        await query.edit_message_text(
            message,
            reply_markup=keyboard
        )
        return States.BOOKS_BY_STATUS

    async def show_book_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        book_index = int(update.callback_query.data.replace("book_", ""))
        books = context.user_data.get('current_books', [])

        if not books or book_index >= len(books):
            await update.callback_query.answer("Книга не найдена")
            return States.BOOKS_BY_STATUS

        book = books[book_index]

        # Формируем детальную информацию
        details = (
            f"📖 {book.get('title', 'Без названия')}\n"
            f"✍️ Автор: {book.get('author', 'Неизвестен')}\n"
            f"🏷 Жанр: {book.get('genre', 'не указан')}\n"
            f"📅 Год: {book.get('year', 'не указан')}\n"
            f"⭐ Рейтинг: {book.get('rating', 'не оценена')}\n"
            f"📌 Статус: {self._get_status_name(book.get('status'))}\n"
            f"📝 Заметок: {book.get('notes_count', 0)}\n"
            f"💬 Цитат: {book.get('quotes_count', 0)}"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✏️ Изменить статус", callback_data=f"edit_status_{book['id']}"),
                InlineKeyboardButton("📝 Добавить заметку", callback_data=f"add_note_{book['id']}"),
                InlineKeyboardButton("💬 Добавить цитату", callback_data=f"add_quote_{book['id']}")
            ],
            self.back_button()
        ])

        await update.callback_query.edit_message_text(
            details,
            reply_markup=keyboard
        )
        return States.BOOK_DETAILS

    async def handle_next_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['page'] += 1
        return await self.show_books_by_status(update, context)

    def _get_status_name(self, status):
        status_names = {
            'reading': 'Читаю сейчас',
            'finished': 'Прочитано',
            'paused': 'Отложено',
            'dropped': 'Заброшено',
            'planned': 'Планирую'
        }
        return status_names.get(status, 'Неизвестен')

    async def edit_book_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик изменения статуса книги"""
        query = update.callback_query
        book_id = query.data.replace("edit_status_", "")
        context.user_data['current_book_id'] = book_id

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📖 Читаю сейчас", callback_data="status_reading"),
                InlineKeyboardButton("✅ Прочитано", callback_data="status_finished")
            ],
            [
                InlineKeyboardButton("💤 Отложено", callback_data="status_paused"),
                InlineKeyboardButton("📅 Планирую", callback_data="status_planned")
            ],
            self.back_button()
        ])

        await query.edit_message_text(
            "Выберите новый статус книги:",
            reply_markup=keyboard
        )
        return States.EDIT_BOOK

    # Раздел заметок
    async def notes_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.callback_query:
            await update.callback_query.answer()
            reply_method = update.callback_query.edit_message_text
        else:
            reply_method = update.message.reply_text

        # Здесь должен быть запрос к БД для получения книг пользователя
        # books = await self.get_user_books(update.effective_user.id)
        books = []  # Это должны быть результаты из БД

        if not books:
            await update.message.reply_text(
                "У вас пока нет добавленных книг.",
                reply_markup=self.main_menu_keyboard()
            )
            return ConversationHandler.END

        # Формируем сообщение со списком книг (первые 10)
        message = "📚 Выберите книгу для заметки:\n\n"
        for i, book in enumerate(books[:10], 1):
            message += f"{i}. {book.get('title', 'Без названия')} - {book.get('author', 'Неизвестен')}\n"

        # Создаем клавиатуру
        keyboard_buttons = []

        # Кнопки для выбора книги
        for i, book in enumerate(books[:10], 1):
            keyboard_buttons.append(InlineKeyboardButton(
                f"{i}. {book.get('title', 'Без названия')}",
                callback_data=f"book_{book['id']}"
            ))

        # Кнопка следующей страницы если книг больше 10
        if len(books) > 10:
            keyboard_buttons.append(InlineKeyboardButton("➡️ Следующая страница", callback_data="next_page"))

        keyboard_buttons.append(self.back_button()[0])
        keyboard = InlineKeyboardMarkup(self._chunk_buttons(keyboard_buttons, 2))

        # Отправляем обложки (здесь должен быть реальный код отправки фото)
        # for book in books[:10]:
        #     if book.get('cover_url'):
        #         await update.message.reply_photo(book['cover_url'])

        await update.message.reply_text(
            message,
            reply_markup=keyboard
        )
        return States.SELECT_BOOK_FOR_NOTE

    async def select_book_for_note(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        book_id = query.data.replace("book_", "")

        # Здесь должен быть запрос к БД для проверки существующей заметки
        # existing_note = await self.get_book_note(update.effective_user.id, book_id)
        existing_note = None  # Это должны быть данные из БД

        if existing_note:
            context.user_data['existing_note'] = existing_note
            context.user_data['book_id'] = book_id

            confirmation_msg = (
                f"📝 У вас уже есть заметка для этой книги:\n\n"
                f"✍️ Отзыв: {existing_note.get('text', 'нет текста')}\n"
                f"⭐ Рейтинг: {existing_note.get('rating', 'не оценена')}/10\n\n"
                f"Хотите изменить заметку?"
            )

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(f"{Config.EMOJI['confirm']} Да", callback_data="edit_note_yes"),
                    InlineKeyboardButton(f"{Config.EMOJI['cancel']} Нет", callback_data="edit_note_no")
                ],
                self.back_button()
            ])

            await query.edit_message_text(
                confirmation_msg,
                reply_markup=keyboard
            )
            return States.EDIT_EXISTING_NOTE
        else:
            context.user_data['book_id'] = book_id
            await query.edit_message_text(
                f"{Config.EMOJI['notes']} Напишите отзыв или заметки по этой книге:",
                reply_markup=InlineKeyboardMarkup([self.back_button()])
            )
            return States.ADD_NOTE_TEXT

    async def add_note_to_book(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик добавления заметки к книге"""
        book_id = update.callback_query.data.replace("add_note_", "")
        context.user_data['current_book_id'] = book_id
        await update.callback_query.edit_message_text(
            "Введите текст заметки:",
            reply_markup=InlineKeyboardMarkup([self.back_button()])
        )
        return States.ADD_NOTE_TEXT

    async def handle_edit_note_decision(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if query.data == "edit_note_yes":
            await query.edit_message_text(
                f"{Config.EMOJI['notes']} Напишите новый отзыв:",
                reply_markup=InlineKeyboardMarkup([self.back_button()])
            )
            return States.ADD_NOTE_TEXT
        else:
            await query.edit_message_text(
                "Заметка осталась без изменений.",
                reply_markup=self.main_menu_keyboard()
            )
            return ConversationHandler.END

    async def add_note_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.user_data[update.message.from_user.id]['note'] = update.message.text

        # Создаем клавиатуру с рейтингом
        rating_buttons = [InlineKeyboardButton(str(i), callback_data=f"rating_{i}") for i in range(1, 11)]
        keyboard = InlineKeyboardMarkup(
            self._chunk_buttons(rating_buttons, 5) +
            [self.back_button()]
        )

        await update.message.reply_text(
            f"{Config.EMOJI['rating']} Поставьте рейтинг книге (по 10-балльной шкале):",
            reply_markup=keyboard
        )
        return States.ADD_NOTE_RATING

    async def add_note_rating(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        rating = query.data.replace("rating_", "")
        self.user_data[query.from_user.id]['rating'] = rating

        # Здесь должен быть запрос к БД для получения информации о книге
        # book = await self.get_book_info(context.user_data['book_id'])
        book = {'title': 'Название книги', 'author': 'Автор'}  # Заглушка

        note_data = self.user_data[query.from_user.id]
        confirmation_msg = (
            f"{Config.EMOJI['notes']} Ваша заметка:\n\n"
            f"📖 Книга: {book.get('title', 'не указана')} - {book.get('author', 'не указан')}\n"
            f"✍️ Отзыв: {note_data['note']}\n"
            f"⭐ Рейтинг: {note_data['rating']}/10\n\n"
            f"{Config.EMOJI['confirm']} Все верно?"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"{Config.EMOJI['confirm']} Да", callback_data="confirm_note_yes"),
                InlineKeyboardButton(f"{Config.EMOJI['cancel']} Нет", callback_data="confirm_note_no")
            ],
            self.back_button()
        ])

        await query.edit_message_text(
            confirmation_msg,
            reply_markup=keyboard
        )
        return States.CONFIRM_NOTE

    async def confirm_note(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if query.data == "confirm_note_yes":
            # Здесь должен быть запрос к БД для сохранения/обновления заметки
            # await self.save_note(
            #     user_id=update.effective_user.id,
            #     book_id=context.user_data['book_id'],
            #     text=context.user_data[update.effective_user.id]['note'],
            #     rating=context.user_data[update.effective_user.id]['rating']
            # )
            await query.edit_message_text(
                f"{Config.EMOJI['success']} Заметка успешно сохранена!",
                reply_markup=self.main_menu_keyboard()
            )
        else:
            await query.edit_message_text(
                "Давайте попробуем еще раз:",
                reply_markup=InlineKeyboardMarkup([self.back_button()])
            )
            return States.ADD_NOTE_TEXT

        return ConversationHandler.END

    async def handle_next_page_notes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['page'] = context.user_data.get('page', 0) + 1
        return await self.notes_menu(update, context)

    # Раздел цитат
    async def quotes_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Здесь должен быть запрос к БД для получения книг пользователя
        # books = await self.get_user_books(update.effective_user.id)
        books = []  # Это должны быть результаты из БД

        if not books:
            await update.message.reply_text(
                "У вас пока нет добавленных книг.",
                reply_markup=self.main_menu_keyboard()
            )
            return ConversationHandler.END

        # Формируем сообщение со списком книг (первые 10)
        message = "📚 Выберите книгу для работы с цитатами:\n\n"
        for i, book in enumerate(books[:10], 1):
            message += f"{i}. {book.get('title', 'Без названия')} - {book.get('author', 'Неизвестен')}\n"

        # Создаем клавиатуру
        keyboard_buttons = []

        # Кнопки для выбора книги
        for i, book in enumerate(books[:10], 1):
            keyboard_buttons.append(InlineKeyboardButton(
                f"{i}. {book.get('title', 'Без названия')}",
                callback_data=f"quote_book_{book['id']}"
            ))

        # Кнопка следующей страницы если книг больше 10
        if len(books) > 10:
            keyboard_buttons.append(InlineKeyboardButton("➡️ Следующая страница", callback_data="next_quote_page"))

        keyboard_buttons.append(self.back_button()[0])
        keyboard = InlineKeyboardMarkup(self._chunk_buttons(keyboard_buttons, 2))

        # Отправляем обложки (здесь должен быть реальный код отправки фото)
        # for book in books[:10]:
        #     if book.get('cover_url'):
        #         await update.message.reply_photo(book['cover_url'])

        await update.message.reply_text(
            message,
            reply_markup=keyboard
        )
        return States.SELECT_BOOK_FOR_QUOTE

    async def select_book_for_quote(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        book_id = query.data.replace("quote_book_", "")
        context.user_data['current_book_id'] = book_id

        # Здесь должен быть запрос к БД для получения информации о книге
        # book = await self.get_book_info(book_id)
        book = {'title': 'Название книги', 'author': 'Автор'}  # Заглушка

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"{Config.EMOJI['add']} Добавить цитату", callback_data="add_quote"),
                InlineKeyboardButton(f"{Config.EMOJI['quotes']} Список цитат", callback_data="list_quotes")
            ],
            self.back_button()
        ])

        await query.edit_message_text(
            f"📖 Выбрана книга: {book.get('title', 'Без названия')}\n"
            f"✍️ Автор: {book.get('author', 'Неизвестен')}\n\n"
            f"Выберите действие:",
            reply_markup=keyboard
        )
        return States.QUOTES_MENU

    async def add_quote_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.edit_message_text(
            f"{Config.EMOJI['quote']} Введите цитату:",
            reply_markup=InlineKeyboardMarkup([self.back_button()])
        )
        return States.ADD_QUOTE_TEXT

    async def add_quote_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.text.lower() == 'назад':
            return await self.back_to_previous_state(update, context)

        self.user_data[update.message.from_user.id]['quote'] = update.message.text
        await update.message.reply_text(
            f"{Config.EMOJI['quote']} Укажите страницу цитаты (только число):",
            reply_markup=InlineKeyboardMarkup([self.back_button()])
        )
        return States.ADD_QUOTE_PAGE

    async def add_quote_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message.text.isdigit():
            await update.message.reply_text(
                "Пожалуйста, введите только число для страницы:",
                reply_markup=InlineKeyboardMarkup([self.back_button()])
            )
            return States.ADD_QUOTE_PAGE

        self.user_data[update.message.from_user.id]['page'] = update.message.text

        # Здесь должен быть запрос к БД для получения информации о книге
        # book = await self.get_book_info(context.user_data['current_book_id'])
        book = {'title': 'Название книги', 'author': 'Автор'}  # пока что

        quote_data = self.user_data[update.message.from_user.id]
        confirmation_msg = (
            f"{Config.EMOJI['quote']} Ваша цитата:\n\n"
            f"📖 Книга: {book.get('title', 'не указана')}\n"
            f"💬 Цитата: {quote_data['quote']}\n"
            f"📌 Страница: {quote_data['page']}\n\n"
            f"{Config.EMOJI['confirm']} Все верно?"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"{Config.EMOJI['confirm']} Да", callback_data="confirm_quote_yes"),
                InlineKeyboardButton(f"{Config.EMOJI['cancel']} Нет", callback_data="confirm_quote_no")
            ],
            self.back_button()
        ])

        await update.message.reply_text(confirmation_msg, reply_markup=keyboard)
        return States.CONFIRM_QUOTE

    async def list_quotes_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Здесь должен быть запрос к БД для получения цитат по книге
        # quotes = await self.get_book_quotes(context.user_data['current_book_id'])
        quotes = []  # Это должны быть результаты из БД

        if not quotes:
            await update.callback_query.edit_message_text(
                "Для этой книги пока нет цитат.",
                reply_markup=InlineKeyboardMarkup([self.back_button()])
            )
            return States.QUOTES_MENU

        # Формируем сообщение со списком цитат (первые 10)
        message = "📚 Цитаты по выбранной книге:\n\n"
        for i, quote in enumerate(quotes[:10], 1):
            message += f"{i}. {quote.get('text', 'Без текста')} (стр. {quote.get('page', '?')})\n"

        # Создаем клавиатуру
        keyboard_buttons = []

        # Кнопки для выбора цитаты
        for i, quote in enumerate(quotes[:10], 1):
            keyboard_buttons.append(InlineKeyboardButton(
                f"{i}. Цитата",
                callback_data=f"quote_{quote['id']}"
            ))

        # Кнопка следующей страницы если цитат больше 10
        if len(quotes) > 10:
            keyboard_buttons.append(InlineKeyboardButton("➡️ Следующая страница", callback_data="next_quote_list_page"))

        keyboard_buttons.append(self.back_button()[0])
        keyboard = InlineKeyboardMarkup(self._chunk_buttons(keyboard_buttons, 2))

        await update.callback_query.edit_message_text(
            message,
            reply_markup=keyboard
        )
        return States.LIST_QUOTES

    async def show_quote_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        quote_id = update.callback_query.data.replace("quote_", "")
        context.user_data['current_quote_id'] = quote_id

        # Здесь должен быть запрос к БД для получения информации о цитате
        # quote = await self.get_quote_info(quote_id)
        quote = {'text': 'Текст цитаты', 'page': '123'}  # пока что

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✏️ Изменить цитату", callback_data="edit_quote"),
                InlineKeyboardButton("❌ Удалить цитату", callback_data="delete_quote")
            ],
            self.back_button()
        ])

        await update.callback_query.edit_message_text(
            f"💬 Цитата:\n\n{quote.get('text', 'Без текста')}\n\n"
            f"📌 Страница: {quote.get('page', '?')}\n\n"
            f"Выберите действие:",
            reply_markup=keyboard
        )
        return States.QUOTE_DETAILS

    async def edit_quote_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.edit_message_text(
            "Введите новый текст цитаты:",
            reply_markup=InlineKeyboardMarkup([self.back_button()])
        )
        return States.EDIT_QUOTE

    async def delete_quote_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"{Config.EMOJI['confirm']} Да, удалить", callback_data="confirm_delete_yes"),
                InlineKeyboardButton(f"{Config.EMOJI['cancel']} Нет, оставить", callback_data="confirm_delete_no")
            ],
            self.back_button()
        ])

        await update.callback_query.edit_message_text(
            "Вы уверены, что хотите удалить эту цитату?",
            reply_markup=keyboard
        )
        return States.DELETE_QUOTE

    async def add_quote_to_book(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == "confirm_quote_yes":
            user_id = update.effective_user.id
            book_id = context.user_data['current_book_id']
            quote_data = self.user_data[user_id]

            # Здесь должен быть запрос к БД для сохранения цитаты
            # Например:
            # quote_id = await self.db.add_quote(
            #     user_id=user_id,
            #     book_id=book_id,
            #     text=quote_data['quote'],
            #     page=quote_data['page']
            # )

            await query.edit_message_text(
                f"{Config.EMOJI['success']} Цитата успешно сохранена!",
                reply_markup=InlineKeyboardMarkup([self.back_button()])
            )

            # Очищаем временные данные
            if user_id in self.user_data:
                del self.user_data[user_id]['quote']
                del self.user_data[user_id]['page']

            return await self.select_book_for_quote(update, context)
        else:
            return await self.add_quote_start(update, context)

    async def confirm_quote(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == "confirm_quote_yes":
            user_data = context.user_data
            # Логика сохранения цитаты
            await query.edit_message_text("✅ Цитата сохранена!")
            return await self.select_book_for_quote(update, context)
        else:
            return await self.add_quote_start(update, context)

    async def handle_next_quote_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['quote_page'] = context.user_data.get('quote_page', 0) + 1
        return await self.quotes_menu(update, context)

    async def handle_next_quote_list_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['quote_list_page'] = context.user_data.get('quote_list_page', 0) + 1
        return await self.list_quotes_start(update, context)

    # Раздел целей
    async def goals_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Здесь должен быть запрос к БД для получения текущих целей пользователя
        # goals = await self.get_user_goals(update.effective_user.id)
        goals = None  # Это должны быть данные из БД

        if goals:
            # Если цели уже существуют, показываем их и предлагаем изменить
            confirmation_msg = (
                f"{Config.EMOJI['goals']} Ваши текущие цели:\n\n"
                f"📅 Книг за год: {goals.get('yearly_goal', 'не указано')}\n"
                f"📅 Книг за месяц: {goals.get('monthly_goal', 'не указано')}\n"
                f"📅 Книг за неделю: {goals.get('weekly_goal', 'не указано')}\n"
                f"⏱ Минут в день: {goals.get('daily_minutes', 'не указано')}\n"
                f"⏰ Напоминание: {goals.get('reminder_time', 'не установлено')}\n\n"
                "Хотите изменить цели?"
            )

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(f"{Config.EMOJI['confirm']} Да", callback_data="edit_goals_yes"),
                    InlineKeyboardButton(f"{Config.EMOJI['cancel']} Нет", callback_data="edit_goals_no")
                ]
                # self.back_button()
            ])

            await update.message.reply_text(
                confirmation_msg,
                reply_markup=keyboard
            )
            return States.EDIT_GOALS
        else:
            # Если целей нет, сначала спрашиваем, хочет ли пользователь их установить
            keyboard = [
                [InlineKeyboardButton(f"{Config.EMOJI['confirm']} Да", callback_data="setup_goals_yes"),
                 InlineKeyboardButton(f"{Config.EMOJI['cancel']} Нет", callback_data="setup_goals_no")]
            ]
            await update.message.reply_text(
                f"{Config.EMOJI['goals']} Хотите установить цели для чтения?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return States.SETUP_GOALS_QUESTION

    async def handle_setup_goals_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == "setup_goals_yes":
            await query.edit_message_text(
                f"{Config.EMOJI['goals']} Введите желаемое количество прочитанных книг за год: (можно пропустить /skip)"
            )
            return States.SET_YEARLY_GOAL
        else:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Обязательно попробуйте в следующий раз, это может помочь с мотивацией!",
                reply_markup=self.main_menu_keyboard()
            )
            return ConversationHandler.END

    async def set_yearly_goal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.text != '/skip':
            if not update.message.text.isdigit():
                await update.message.reply_text(
                    "Пожалуйста, введите число. Попробуйте еще раз:"
                )
                return States.SET_YEARLY_GOAL

            self.user_data[update.message.from_user.id]['yearly_goal'] = update.message.text

        await update.message.reply_text(
            f"{Config.EMOJI['goals']} Введите желаемое количество прочитанных книг за месяц: (можно пропустить /skip)"
        )
        return States.SET_MONTHLY_GOAL

    async def set_monthly_goal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.text != '/skip':
            if not update.message.text.isdigit():
                await update.message.reply_text(
                    "Пожалуйста, введите число. Попробуйте еще раз:"
                )
                return States.SET_MONTHLY_GOAL

            self.user_data[update.message.from_user.id]['monthly_goal'] = update.message.text

        await update.message.reply_text(
            f"{Config.EMOJI['goals']} Введите желаемое количество прочитанных книг за неделю: (можно пропустить /skip)"
        )
        return States.SET_WEEKLY_GOAL

    async def set_weekly_goal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.text != '/skip':
            if not update.message.text.isdigit():
                await update.message.reply_text(
                    "Пожалуйста, введите число. Попробуйте еще раз:"
                )
                return States.SET_WEEKLY_GOAL

            self.user_data[update.message.from_user.id]['weekly_goal'] = update.message.text

        await update.message.reply_text(
            f"{Config.EMOJI['goals']} Сколько минут в день вы хотите выделить на чтение? (можно пропустить /skip)"
        )
        return States.SET_DAILY_MINUTES

    async def set_daily_minutes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.text != '/skip':
            if not update.message.text.isdigit():
                await update.message.reply_text(
                    "Пожалуйста, введите число. Попробуйте еще раз:"
                )
                return States.SET_DAILY_MINUTES

            self.user_data[update.message.from_user.id]['daily_minutes'] = update.message.text

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"{Config.EMOJI['confirm']} Да", callback_data="set_reminder_yes"),
                InlineKeyboardButton(f"{Config.EMOJI['cancel']} Нет", callback_data="set_reminder_no")
            ]
        ])

        await update.message.reply_text(
            f"{Config.EMOJI['reminders']} Хотите поставить себе напоминание?",
            reply_markup=keyboard
        )
        return States.SET_REMINDER

    async def set_reminder(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if query.data == "set_reminder_yes":
            await query.edit_message_text(
                f"{Config.EMOJI['reminders']} Введите в какое время хотите получать уведомление (например, 20:00):"
            )
            return States.SET_REMINDER_TIME
        else:
            return await self.confirm_goals(query)

    async def set_reminder_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Здесь должна быть проверка формата времени
        self.user_data[update.message.from_user.id]['reminder_time'] = update.message.text
        return await self.confirm_goals(update)

    async def confirm_goals(self, update: Update):
        confirmation_msg = (
            f"{Config.EMOJI['goals']} Ваши цели:\n\n"
            f"📅 Книг за год: {goals_data.get('yearly_goal', 'не указано')}\n"
            f"📅 Книг за месяц: {goals_data.get('monthly_goal', 'не указано')}\n"
            f"📅 Книг за неделю: {goals_data.get('weekly_goal', 'не указано')}\n"
            f"⏱ Минут в день: {goals_data.get('daily_minutes', 'не указано')}\n"
            f"⏰ Напоминание: {goals_data.get('reminder_time', 'не установлено')}\n\n"
            f"{Config.EMOJI['confirm']} Все верно?"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"{Config.EMOJI['confirm']} Да", callback_data="confirm_goals_yes"),
                InlineKeyboardButton(f"{Config.EMOJI['cancel']} Нет", callback_data="confirm_goals_no")
            ]
        ])

        if hasattr(update, 'edit_message_text'):
            await update.edit_message_text(confirmation_msg, reply_markup=keyboard)
        else:
            await update.message.reply_text(confirmation_msg, reply_markup=keyboard)

        return States.CONFIRM_GOALS

    async def handle_edit_goals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if query.data == "edit_goals_yes":
            # Очищаем старые цели и начинаем процесс ввода заново
            self.user_data[query.from_user.id] = {}
            await query.edit_message_text(
                f"{Config.EMOJI['goals']} Введите желаемое количество прочитанных книг за год: (можно пропустить /skip)"
            )
            return States.SET_YEARLY_GOAL
        else:
            await query.edit_message_text(
                "Цели остались без изменений."
            )
            return ConversationHandler.END

    # Раздел статистики
    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.callback_query:
            await update.callback_query.answer()
            reply_method = update.callback_query.edit_message_text
        else:
            reply_method = update.message.reply_text

        # Здесь должен быть запрос к БД для получения статистики
        # stats = await self.get_user_stats(update.effective_user.id)
        stats = {  # это должны быть данные из БД
            'yearly_books': 15,
            'genres': [
                {'name': 'Фантастика', 'percent': 40},
                {'name': 'Классика', 'percent': 25},
                {'name': 'Научная литература', 'percent': 20},
                {'name': 'Детективы', 'percent': 15}
            ],
            'avg_rating': 7.2,
            'weekly_report': {
                'books_read': 3,
                'books_added': 2,
                'quotes_added': 5,
                'productivity_change': 15
            }
        }

        # Формируем сообщение со статистикой
        stats_msg = (
            f"{Config.EMOJI['stats']} <b>Ваша статистика:</b>\n\n"
            f"1. 📅 Прочитано за год: {stats['yearly_books']} книг\n\n"
            f"2. 🏷 Популярные жанры:\n"
        )

        # Добавляем жанры
        for genre in stats['genres']:
            stats_msg += f"   - {genre['name']} ({genre['percent']}%)\n"

        stats_msg += (
            f"\n3. ⭐ Средняя оценка: {stats['avg_rating']:.1f}/10\n\n"
            f"{Config.EMOJI['report']} <b>Еженедельный отчет:</b>\n"
            f"   - Прочитано: {stats['weekly_report']['books_read']} книг\n"
            f"   - Добавлено: {stats['weekly_report']['books_added']} новых книг\n"
            f"   - Новых цитат: {stats['weekly_report']['quotes_added']}\n"
            f"   - На {stats['weekly_report']['productivity_change']}% продуктивнее прошлой недели!"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"{Config.EMOJI['report']} Полный отчет", callback_data="full_report"),
                InlineKeyboardButton(f"{Config.EMOJI['chart']} Графики", callback_data="show_charts")
            ],
            [
                InlineKeyboardButton(f"{Config.EMOJI['reminders']} Настройка отчетов", callback_data="setup_reports")
            ],
            self.back_button()
        ])

        await update.message.reply_text(
            stats_msg,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return States.STATS_MENU

    async def show_full_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        # Здесь должен быть запрос к БД для получения полного отчета
        # full_report = await self.get_full_report(query.from_user.id)
        full_report = "Полный отчет будет здесь..."  # Заглушка

        await query.edit_message_text(
            f"{Config.EMOJI['report']} <b>Полный отчет по чтению:</b>\n\n{full_report}",
            parse_mode='HTML'
        )
        return States.STATS_MENU

    async def show_charts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        # Здесь должен быть запрос к БД и генерация графиков
        # charts = await self.generate_charts(query.from_user.id)
        charts = []  # пока что

        if charts:
            # Отправляем графики (заглушка - здесь должен быть реальный код отправки фото)
            # for chart in charts:
            #     await query.message.reply_photo(chart)
            pass

        await query.edit_message_text(
            f"{Config.EMOJI['chart']} Ваши графики чтения:",
            reply_markup=InlineKeyboardMarkup([self.back_button()])
        )
        return States.STATS_MENU

    async def setup_reports(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        # Здесь должен быть запрос к БД для получения текущих настроек отчетов
        # report_settings = await self.get_report_settings(query.from_user.id)
        report_settings = {'frequency': 'weekly', 'day': 'Monday', 'time': '20:00'}  # Заглушка

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📅 Частота отчетов", callback_data="set_report_freq"),
                InlineKeyboardButton("🕒 Время отправки", callback_data="set_report_time")
            ],
            self.back_button()
        ])

        await query.edit_message_text(
            f"{Config.EMOJI['reminders']} <b>Настройка отчетов:</b>\n\n"
            f"Текущие настройки:\n"
            f"- Частота: {report_settings['frequency']}\n"
            f"- День недели: {report_settings['day']}\n"
            f"- Время: {report_settings['time']}\n\n"
            "Выберите параметр для изменения:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return States.REPORT_SETTINGS

    async def set_report_frequency(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Еженедельно", callback_data="freq_weekly"),
                InlineKeyboardButton("Ежемесячно", callback_data="freq_monthly")
            ],
            [
                InlineKeyboardButton("Ежедневно", callback_data="freq_daily"),
                InlineKeyboardButton("Отключить", callback_data="freq_off")
            ],
            self.back_button()
        ])

        await query.edit_message_text(
            f"{Config.EMOJI['reminders']} Выберите частоту получения отчетов:",
            reply_markup=keyboard
        )
        return States.SET_REPORT_FREQ

    async def set_report_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            f"{Config.EMOJI['reminders']} Введите время для отправки отчетов (например, 20:00):",
            reply_markup=InlineKeyboardMarkup([self.back_button()])
        )
        return States.SET_REPORT_TIME

    async def handle_report_frequency(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора частоты отчетов"""
        query = update.callback_query
        await query.answer()

        freq_map = {
            'freq_weekly': 'еженедельно',
            'freq_monthly': 'ежемесячно',
            'freq_daily': 'ежедневно',
            'freq_off': 'отключены'
        }

        frequency = freq_map.get(query.data, 'еженедельно')
        context.user_data['report_frequency'] = frequency

        # Здесь должен быть код сохранения в БД
        # await self.db.save_report_frequency(update.effective_user.id, frequency)

        await query.edit_message_text(
            f"✅ Частота отчетов установлена: {frequency}",
            reply_markup=self.main_menu_keyboard()
        )
        return ConversationHandler.END

    async def handle_report_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ввода времени отчетов"""
        # Простая проверка формата времени
        if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', update.message.text):
            await update.message.reply_text(
                "Пожалуйста, введите время в формате ЧЧ:ММ (например, 20:00):",
                reply_markup=InlineKeyboardMarkup([self.back_button()])
            )
            return States.SET_REPORT_TIME

        time_str = update.message.text
        context.user_data['report_time'] = time_str

        # Здесь должен быть код сохранения в БД
        # await self.db.save_report_time(update.effective_user.id, time_str)

        await update.message.reply_text(
            f"✅ Время отчетов установлено: {time_str}",
            reply_markup=self.main_menu_keyboard()
        )
        return ConversationHandler.END

    # Раздел помощи
    async def help_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_msg = (
            f"{Config.EMOJI['help']} Читательский дневник - ваш персональный помощник в мире книг!\n\n"
            "📚 Основные функции:\n"
            "- Добавление книг с подробной информацией\n"
            "- Ведение заметок и цитат\n"
            "- Постановка целей по чтению\n"
            "- Анализ вашей читательской активности\n\n"
            "Используйте меню для навигации по функциям."
        )
        await update.message.reply_text(help_msg)

    def books_menu_keyboard(self):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{Config.EMOJI['add']} Добавить книгу", callback_data="add_book")],
            [InlineKeyboardButton(f"{Config.EMOJI['search']} Поиск", callback_data="search_book")],
            [InlineKeyboardButton("Назад", callback_data="main_menu")]
        ])

    def notes_menu_keyboard(self):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{Config.EMOJI['add']} Добавить заметку", callback_data="add_note")],
            [InlineKeyboardButton("Назад", callback_data="main_menu")]
        ])

    # Обработка кнопок
    async def cancel_operation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик отмены текущей операции"""
        await update.message.reply_text(
            "Операция отменена. Возврат в главное меню.",
            reply_markup=self.main_menu_keyboard()
        )
        return ConversationHandler.END

    # Обработка кнопки Назад до меню раздела
    async def back_to_book_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик кнопки 'Назад' для возврата в главное меню"""
        query = update.callback_query
        await query.answer()

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{Config.EMOJI['add']} Добавить книгу", callback_data="add_book")],
            [InlineKeyboardButton(f"{Config.EMOJI['search']} Поиск книги", callback_data="search_book")],
            [InlineKeyboardButton(f"{Config.EMOJI['books']} Мои книги", callback_data="my_books")],
        ])

        await query.edit_message_text(
            "📚 Управление книгами:",
            reply_markup=keyboard
        )
        return States.BOOKS_MENU

    async def back_to_notes_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Возврат в меню заметок"""
        query = update.callback_query
        await query.answer()

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{Config.EMOJI['add']} Добавить заметку", callback_data="add_note")],
            [InlineKeyboardButton(f"{Config.EMOJI['search']} Просмотреть заметки", callback_data="view_notes")],
        ])

        await query.edit_message_text(
            "📝 Управление заметками:",
            reply_markup=keyboard
        )
        return States.NOTES_MENU

    async def back_to_quotes_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Возврат в меню цитат"""
        query = update.callback_query
        await query.answer()

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{Config.EMOJI['add']} Добавить цитату", callback_data="add_quote")],
            [InlineKeyboardButton(f"{Config.EMOJI['search']} Просмотреть цитаты", callback_data="view_quotes")],
        ])

        await query.edit_message_text(
            "💬 Управление цитатами:",
            reply_markup=keyboard
        )
        return States.QUOTES_MENU

    async def back_to_stats_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Возврат в меню статистики"""
        query = update.callback_query
        await query.answer()

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{Config.EMOJI['report']} Полный отчет", callback_data="full_report")],
            [InlineKeyboardButton(f"{Config.EMOJI['chart']} Графики", callback_data="show_charts")],
            [InlineKeyboardButton(f"{Config.EMOJI['reminders']} Настройка отчетов", callback_data="setup_reports")],
        ])

        await query.edit_message_text(
            f"{Config.EMOJI['stats']} Статистика и отчеты:",
            reply_markup=keyboard
        )
        return States.STATS_MENU

    async def back_to_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "Главное меню:",
            reply_markup=self.main_menu_keyboard()
        )
        return ConversationHandler.END

# ==================== ЗАПУСК БОТА ==================== #
def setup_conversation_handlers(bot_instance):
    """Настройка всех обработчиков с передачей экземпляра бота"""

    # 1. Обработчик добавления книги
    book_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(bot_instance.add_book_start, pattern="^add_book$")],
        states={
            States.ADD_BOOK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_instance.add_book_title)],
            States.ADD_BOOK_AUTHOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_instance.add_book_author)],
            States.CONFIRM_API_DATA: [
                CallbackQueryHandler(bot_instance.confirm_api_data, pattern="^confirm_api_data_")],
            States.ADD_BOOK_GENRE: [CallbackQueryHandler(bot_instance.add_book_genre, pattern="^genre_")],
            States.ADD_BOOK_YEAR: [MessageHandler(filters.TEXT | filters.COMMAND, bot_instance.add_book_year)],
            States.ADD_BOOK_STATUS: [CallbackQueryHandler(bot_instance.add_book_status, pattern="^status_")],
            States.CONFIRM_BOOK_DATA: [CallbackQueryHandler(bot_instance.confirm_book_data, pattern="^confirm_book_")]
        },
        fallbacks=[
            CallbackQueryHandler(bot_instance.back_to_book_menu, pattern="^back$"),
            CommandHandler('cancel', bot_instance.cancel_operation)
        ],
        per_message=False
    )

    # 2. Обработчик поиска книг (без skip)
    search_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(bot_instance.search_book_start, pattern="^search_book$")],
        states={
            States.SEARCH_METHOD: [
                CallbackQueryHandler(bot_instance.search_by_title, pattern="^search_title$"),
                CallbackQueryHandler(bot_instance.search_by_author, pattern="^search_author$"),
                CallbackQueryHandler(bot_instance.search_by_genre, pattern="^search_genre$"),
                CallbackQueryHandler(bot_instance.search_by_year, pattern="^search_year$")
            ],
            States.SEARCH_BY_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_instance.show_search_results)],
            States.SEARCH_BY_AUTHOR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot_instance.show_search_results)],
            States.SEARCH_BY_GENRE: [CallbackQueryHandler(bot_instance.show_search_results, pattern="^genre_")],
            States.SEARCH_BY_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_instance.show_search_results)]
        },
        fallbacks=[
            CallbackQueryHandler(bot_instance.back_to_book_menu, pattern="^back$"),
            CommandHandler('cancel', bot_instance.cancel_operation)
        ],
        per_message=True
    )

    # 3. Обработчик для моих книг (без skip)
    my_books_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(bot_instance.show_my_books, pattern="^my_books$")],
        states={
            States.MY_BOOKS_MENU: [
                CallbackQueryHandler(bot_instance.show_books_by_status, pattern="^status_"),
            ],
            States.BOOKS_BY_STATUS: [
                CallbackQueryHandler(bot_instance.show_book_details, pattern="^book_"),
                CallbackQueryHandler(bot_instance.handle_next_page, pattern="^next_page$"),
                CallbackQueryHandler(bot_instance.back_to_previous_state, pattern="^back$")
            ],
            States.BOOK_DETAILS: [
                CallbackQueryHandler(bot_instance.edit_book_status, pattern="^edit_status_"),
                CallbackQueryHandler(bot_instance.add_note_to_book, pattern="^add_note_"),
                CallbackQueryHandler(bot_instance.add_quote_to_book, pattern="^add_quote_"),
                CallbackQueryHandler(bot_instance.back_to_previous_state, pattern="^back$")
            ],
            States.EDIT_BOOK: [
                # Обработчики для изменения статуса книги
            ]
        },
        fallbacks=[
            CallbackQueryHandler(bot_instance.back_to_book_menu, pattern="^back$"),
            CommandHandler('cancel', bot_instance.cancel_operation)
        ],
        per_message=False
    )

    # 4. Обработчик заметок (без skip)
    notes_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Text([f"{Config.EMOJI['notes']} Заметки"]), bot_instance.notes_menu)],
        states={
            States.SELECT_BOOK_FOR_NOTE: [
                CallbackQueryHandler(bot_instance.select_book_for_note, pattern="^book_"),
                CallbackQueryHandler(bot_instance.handle_next_page_notes, pattern="^next_page$")
            ],
            States.ADD_NOTE_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_instance.add_note_text)],
            States.ADD_NOTE_RATING: [CallbackQueryHandler(bot_instance.add_note_rating, pattern="^rating_")],
            States.CONFIRM_NOTE: [CallbackQueryHandler(bot_instance.confirm_note, pattern="^confirm_note_")]
        },
        fallbacks=[
            CallbackQueryHandler(bot_instance.back_to_notes_menu, pattern="^back$"),
            CommandHandler('cancel', bot_instance.cancel_operation)
        ],
        per_message=True
    )

    # 5. Обработчик целей (со skip)
    goals_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Text([f"{Config.EMOJI['goals']} Цели"]), bot_instance.goals_menu)],
        states={
            States.SETUP_GOALS_QUESTION: [
                CallbackQueryHandler(bot_instance.handle_setup_goals_question, pattern="^setup_goals_")
            ],
            States.EDIT_GOALS: [
                CallbackQueryHandler(bot_instance.handle_edit_goals, pattern="^edit_goals_")
            ],
            States.SET_YEARLY_GOAL: [MessageHandler(filters.TEXT | filters.COMMAND, bot_instance.set_yearly_goal)],
            States.SET_MONTHLY_GOAL: [MessageHandler(filters.TEXT | filters.COMMAND, bot_instance.set_monthly_goal)],
            States.SET_WEEKLY_GOAL: [MessageHandler(filters.TEXT | filters.COMMAND, bot_instance.set_weekly_goal)],
            States.SET_DAILY_MINUTES: [MessageHandler(filters.TEXT | filters.COMMAND, bot_instance.set_daily_minutes)],
            States.SET_REMINDER: [CallbackQueryHandler(bot_instance.set_reminder, pattern="^set_reminder_")],
            States.SET_REMINDER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_instance.set_reminder_time)],
            States.CONFIRM_GOALS: [CallbackQueryHandler(bot_instance.confirm_goals, pattern="^confirm_goals_")]
        },
        fallbacks=[
            CommandHandler('cancel', bot_instance.cancel_operation),
            CallbackQueryHandler(bot_instance.back_to_main_menu, pattern="^back$")

        ],
        per_message=False
    )

    # 6. Обработчик статистики (без skip)
    stats_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Text([f"{Config.EMOJI['stats']} Статистика"]), bot_instance.show_stats)],
        states={
            States.STATS_MENU: [
                CallbackQueryHandler(bot_instance.show_full_report, pattern="^full_report$"),
                CallbackQueryHandler(bot_instance.show_charts, pattern="^show_charts$"),
                CallbackQueryHandler(bot_instance.setup_reports, pattern="^setup_reports$")
            ],
            States.REPORT_SETTINGS: [
                CallbackQueryHandler(bot_instance.set_report_frequency, pattern="^set_report_freq$"),
                CallbackQueryHandler(bot_instance.set_report_time, pattern="^set_report_time$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(bot_instance.back_to_stats_menu, pattern="^back$"),
            CommandHandler('cancel', bot_instance.cancel_operation)
        ],
        per_message=False
    )

    return book_conv, search_conv, my_books_conv, notes_conv, goals_conv, stats_conv

def main():
    env_path = Path(__file__).parent / '.env'
    load_dotenv(env_path)

    bot = BookBot()
    application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

    handlers = setup_conversation_handlers(bot)

    application.add_handler(CommandHandler("start", bot.start))

    application.add_handler(handlers[0])  # book_conv
    application.add_handler(handlers[1])  # search_conv
    application.add_handler(handlers[2])  # my_books_conv
    application.add_handler(handlers[3])  # notes_conv
    application.add_handler(handlers[4])  # goals_conv
    application.add_handler(handlers[5])  # stats_conv

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_main_menu))

    application.run_polling()

if __name__ == "__main__":
    main()
