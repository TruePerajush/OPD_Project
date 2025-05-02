from datetime import time, datetime, timedelta
from datetime import timedelta
from typing import Union
from time import sleep
import psycopg2
from dotenv import load_dotenv
import os
from psycopg2 import sql
import requests
import speech_recognition as sr
import tempfile
from collections import Counter
class Quote:
    def __init__(
        self,
        book_id: int,
        user_id: int,
        page_number: int,
        text: str,
        chat_id: int = None,
    ):
        self.book_id = book_id
        self.user_id = user_id
        self.page_number = page_number
        self.text = text
        self.chat_id = chat_id


class Note:
    def __init__(
        self,
        chat_id: int,
        book_id: int,
        rating: int,
        opinion: str,
    ):
        self.chat_id = chat_id
        self.book_id = book_id
        self.rating = rating
        self.opinion = opinion


class Report:
    def __init__(
        self,
        report_id: int,
        user_id: int,
        books_read: int,
        pages_read: int,
        quotes_added: int,
    ):
        self.report_id = report_id
        self.user_id = user_id
        self.books_read = books_read
        self.pages_read = pages_read
        self.quotes_added = quotes_added


class Book:
    def __init__(
        self,
        title: str = None,
        book_id: int = 0,
        description: str = "описание",
        year: int = 0,
        rating: float = 0,
        genre: str = "жанр",
        status: str = "статус",
        last_update: datetime = None,
        author: str = "автор",
        cover: str = "Обложка",
    ):
        self.book_id = book_id
        self.title = title
        self.description = description
        self.year = year
        self.rating = rating
        self.genre = genre
        self.status = status
        self.last_update = last_update
        self.author = author
        self.cover = cover


class User:
    def __init__(
        self,
        username: str,
        chat_id: int,
        daily_goal: int = -1,
        weekly_goal: int = -1,
        monthly_goal: int = -1,
        annual_goal: int = -1,
        reminder: time = None,
    ):
        self.username: str = username
        self.chat_id: int = chat_id
        self.daily_goal: int = daily_goal
        self.weekly_goal: int = weekly_goal
        self.monthly_goal: int = monthly_goal
        self.annual_goal: int = annual_goal
        self.reminder: time = reminder


class TelegramBot:
 
    def __init__(self, connection):
        """
        :param sql_cursor: это функция для запросов к бд, см. документацию по psycopg2
        """

        self.__connection = connection
    def _get_conn(self):
        return psycopg2.connect(self.__connection)

    def create_user(self, user: User) -> None:
        """
        Создай пользователя в бд, если такого еще нет
        :param user:
        :return:
        """
        conn=self.__sql_cursor.connection
        with conn.cursor() as cur:
            chat_id = user.chat_id
            username = "unknown"
            daily_goal = -1
            weekly_goal = -1,
            monthly_goal = -1,
            annual_goal = -1,
            cur.execute(
                "INSERT INTO Users (chat_id, daily_goal, weekly_goal,monthly_goal,annual_goal) VALUES (%s,%s,%s,%s,%s)",
                (chat_id, daily_goal, weekly_goal,monthly_goal,annual_goal)
            )
        conn.commit()
        print("user создан")
        pass

    def update_user_attribute(
        self, user: User, attribute: str, value: Union[int, time]
    ) -> None:
        """
        Обнови пользователя только по данному аттрибуту
        :param user:
        :param attribute:
        :param value:
        :return:
        """
        conn=self.__sql_cursor.connection
        with conn.cursor() as cursor:
            update_query = sql.SQL("""
            UPDATE Users
            SET {attribute} = %s
            WHERE {chat_id} = {user.chat_id}
            """
        )
            new_attribute = value
            cursor.execute(update_query, (new_attribute))

        print(f"аттрибут {attribute} изменен на {value}")
        pass

    def get_user(self, chat_id: int) -> User | None:
        """
        Верни юзера из бд. Если нет, верни None
        :param chat_id: Идентификатор чата пользователя
        :return: Объект User или None
        """
        conn = self.__sql_cursor.connection
        query = "SELECT * FROM users WHERE chat_id = ?"
        
        try:
            cursor = conn.cursor()
            cursor.execute(query, (chat_id,))
            user_data = cursor.fetchone()  
            
            if user_data:
                
                return User(*user_data)
            else:
                print(f"Пользователь с chat_id {chat_id} не найден")
                return None
        except Exception as e:
            print(f"Ошибка при получении пользователя: {e}")
            return None
        finally:
            cursor.close()  
            
    def create_book(self, book: Book) -> None:
        """
        Добавляет книгу в БД со всеми связями: авторы, жанры, статус, полка (shelf).
        """
        conn = None
        try:
            conn = self._get_conn()
            with conn.cursor() as cur:
            
                cur.execute("""
                    INSERT INTO "Books" (book_id, title, description, year, cover, last_update)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (book.book_id, book.title, book.description, book.year, book.cover, book.last_update))

                parts = book.author.split(maxsplit=2)
                name = parts[0]
                surname = parts[1]
                patronymic = parts[2] if len(parts) > 2 else None
                cur.execute("""
                    INSERT INTO "Authors" (surname, name, patronymic)
                    VALUES (%s, %s, %s)
                    RETURNING author_id
                """, (surname, name, patronymic))
                author_id = cur.fetchone()[0]

                cur.execute("""
                    INSERT INTO books_authors (book_id, author_id)
                    VALUES (%s, %s)
                """, (book.book_id, author_id))

                for genre in book.genres:
                    cur.execute("""SELECT genre_id FROM "Genres" WHERE genre = %s""", (genre,))
                    row = cur.fetchone()
                    if row:
                        genre_id = row[0]
                    else:
                        cur.execute("""INSERT INTO "Genres" (genre) VALUES (%s) RETURNING genre_id""", (genre,))
                        genre_id = cur.fetchone()[0]
                    cur.execute("""INSERT INTO book_genres (book_id, genre_id) VALUES (%s, %s)""", (book.book_id, genre_id))

                cur.execute("""SELECT status_id FROM "Statuses" WHERE status = %s""", (book.status,))
                row = cur.fetchone()
                if row:
                    status_id = row[0]
                else:
                    cur.execute("""INSERT INTO "Statuses" (status) VALUES (%s) RETURNING status_id""", (book.status,))
                    status_id = cur.fetchone()[0]

                cur.execute("""
                    INSERT INTO "Shelfs" (user_id, book_id, status_id, progress)
                    VALUES (%s, %s, %s, %s)
                """, (book.user_id, book.book_id, status_id, book.progress))

                conn.commit()

        except Exception as e:
            print(f"Ошибка при добавлении книги: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()



    def get_books(self, chat_id: int) -> list[Book]:
        """
        Возвращает список книг пользователя с жанром, статусом, датой обновления и рейтингом.
        """
        conn = None
        books = []

        try:
            conn = self._get_conn()
            with conn.cursor() as cur:
                user = self.get_user(chat_id)
                user_id = user.user_id

                cur.execute("""
                    SELECT b.book_id, b.title, b.description, b.year, b.cover,
                        st.status, s.last_update
                    FROM "Shelfs" s
                    JOIN "Books" b ON b.book_id = s.book_id
                    JOIN "Statuses" st ON st.status_id = s.status_id
                    WHERE s.user_id = %s
                """, (user_id,))
                rows = cur.fetchall()

                for row in rows:
                    book_id, title, description, year, cover, status, last_update = row

                    cur.execute("""
                        SELECT g.genre
                        FROM book_genres bg
                        JOIN "Genres" g ON g.genre_id = bg.genre_id
                        WHERE bg.book_id = %s
                    """, (book_id,))
                    genre_rows = cur.fetchall()
                    genre = ", ".join(g[0] for g in genre_rows) if genre_rows else "Без жанра"

                    cur.execute("""
                        SELECT a.name, a.surname, a.patronymic
                        FROM books_authors ba
                        JOIN "Authors" a ON a.author_id = ba.author_id
                        WHERE ba.book_id = %s
                    """, (book_id,))
                    author_row = cur.fetchone()
                    author = " ".join(filter(None, author_row)) if author_row else "Неизвестный автор"

                    cur.execute("""
                        SELECT AVG(rating) FROM "Notes" WHERE book_id = %s AND rating IS NOT NULL
                    """, (book_id,))
                    rating_row = cur.fetchone()
                    rating = float(rating_row[0]) if rating_row and rating_row[0] is not None else 0.0

                    books.append(Book(
                        title=title,
                        book_id=book_id,
                        description=description,
                        year=int(year),
                        rating=rating,
                        genre=genre,
                        status=status,
                        last_update=last_update,
                        author=author,
                        cover=cover
                    ))

            return books

        except Exception as e:
            print(f"Ошибка при получении книг: {e}")
            return []
        finally:
            if conn:
                conn.close()


    import requests

    def get_book_from_side_site(self, book: Book) -> Book:
        """
        Пытается найти книгу через Google Books API по названию и автору.
        Если находит — возвращает заполненный объект Book, иначе возвращает исходный.
        """
        try:
            query = f"{book.title} {book.author}"
            url = f"https://www.googleapis.com/books/v1/volumes?q={query}"
            response = requests.get(url)
            data = response.json()

            if "items" not in data or not data["items"]:
                return book

            item = data["items"][0]["volumeInfo"]

            title = item.get("title", book.title)
            authors = item.get("authors", [book.author])
            published_date = item.get("publishedDate", "0")
            year = int(published_date[:4]) if published_date[:4].isdigit() else book.year
            categories = item.get("categories", ["жанр"])
            genre = categories[0]

            return Book(
                title=title,
                author=", ".join(authors),
                genre=genre,
                year=year,
                book_id=book.book_id,
                description=item.get("description", book.description),
                rating=book.rating,
                status=book.status,
                last_update=book.last_update,
                cover=item.get("imageLinks", {}).get("thumbnail", book.cover),
            )

        except Exception as e:
            print(f"Ошибка при поиске книги: {e}")
            return book



    def get_books_over_year(self, books: list[Book]) -> int:
        """
        Считает количество книг со статусом "прочитано", обновлённых в текущем году.
        :param books: список объектов Book
        :return: количество подходящих книг
        """
        current_year = datetime.now().year
        return sum(
            1 for book in books
            if book.status.lower() == "прочитано" and book.last_update.year == current_year
        )


    def get_books_mid_rating(self, books: list[Book]) -> float:
        """
        Посчитай среднюю оценку по книгам
        :param books:
        :return:
        """
        ratings = [book.rating for book in books if book.rating is not None]
        if not ratings:
            return 0.0
        return sum(ratings) / len(ratings)


    def get_books_popular_genres(self, books: list[Book]) -> list[tuple[str, float]]:
        """
        Верни отсортированный по процентам список. Пример [('Хоррор', 60), ('Роман', 40)]
        :param books:
        :return:
        """
        genres = [book.genre for book in books if book.genre]
        total = len(genres)
        if total == 0:
            return []

        counter = Counter(genres)
        result = [
            (genre, round((count / total) * 100, 2))
            for genre, count in counter.items()
        ]
        return sorted(result, key=lambda x: x[1], reverse=True)

    def generate_reports(self) -> None:
        """
        Бесконечный цикл, запускает отчёты по понедельникам.
        Удаляет старые (старше 2 недель) и создаёт новые.
        """
        while True:
            now = datetime.now()
            print(f"[{now}] Проверка на понедельник...")

            if now.weekday() == 0:  
                try:
                    conn = self._get_conn()
                    with conn.cursor() as cur:
                        cur.execute("""
                            DELETE FROM "Reports"
                            WHERE last_update < now() - interval '14 days'
                        """)
                        cur.execute("""SELECT user_id FROM "Users" """)
                        users = cur.fetchall()
                        for (user_id,) in users:
                            cur.execute("""
                                INSERT INTO "Reports" (user_id, books_read, pages_read)
                                VALUES (%s, 0, 0)
                            """, (user_id,))

                        conn.commit()
                        print(f"[{now}] Отчёты созданы.")
                except Exception as e:
                    print(f"Ошибка при создании отчётов: {e}")
                    if conn:
                        conn.rollback()
                finally:
                    if conn:
                        conn.close()
                time.sleep(86400)
            else:
                time.sleep(21600)

    def get_report(self, chat_id: int) -> tuple[Report, Report]:
        """
        Верни новый и старый репорты из бд соответственно.
        + нужно получить кол-во цитат через user_id
        :param chat_id:
        :return:
        """
        conn = None
        try:
            conn = self._get_conn()
            with conn.cursor() as cur:
            
                cur.execute("""
                    SELECT user_id FROM "Users" WHERE chat_id = %s
                """, (chat_id,))
                result = cur.fetchone()
                if not result:
                    return None, None
                user_id = result[0]

                cur.execute("""
                    SELECT report_id, books_read, pages_read, last_update
                    FROM "Reports"
                    WHERE user_id = %s
                    ORDER BY last_update DESC
                    LIMIT 2
                """, (user_id,))
                reports = cur.fetchall()

                report_objs = []
                for r in reports:
                    report_id, books_read, pages_read, last_update = r

                    cur.execute("""
                        SELECT COUNT(*) FROM "Quotes"
                        WHERE user_id = %s AND DATE(last_update) = DATE(%s)
                    """, (user_id, last_update))
                    quotes_added = cur.fetchone()[0]

                    report_objs.append(Report(report_id, user_id, books_read, pages_read, quotes_added))

                if len(report_objs) == 2:
                    return report_objs[0], report_objs[1]
                elif len(report_objs) == 1:
                    return report_objs[0], None
                else:
                    return None, None
        except Exception as e:
            print(f"Ошибка при получении отчётов: {e}")
            return None, None
        finally:
            if conn:
                conn.close()


    def create_note(self, note: Note) -> None:
            """
            Создай или обнови note.
            :param note:
            :return:
            """
            conn = self.__sql_cursor.connection
            cursor = None
            try:
                cursor = conn.cursor()
                with conn.cursor() as cur:
                    user_id = note.user_id
                    book_id = note.book_id
                    rating = note.rating
                    opinion = note.opinion

                    cur.execute("""
                        INSERT INTO Notes (user_id, book_id, rating, opinion)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (user_id, book_id)
                        DO UPDATE SET rating = EXCLUDED.rating, opinion = EXCLUDED.opinion;
                    """, (user_id, book_id, rating, opinion))

                conn.commit()
            except Exception as e:
                print(f"Ошибка при создании или обновлении note: {e}")
                return None
            finally:
                cursor.close()  
            print("Note создан или обновлён")


    def get_note(self, chat_id: int, book_id: int) -> Union[Note, None]:
            """
            Достань заметку из бд или верни None.
            :param chat_id:
            :param book_id:
            :return:
            """
            conn = self.__sql_cursor.connection
            cursor = None
            try:
                cursor = conn.cursor()
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT user_id, book_id, rating, opinion
                        FROM Notes
                        WHERE user_id = %s AND book_id = %s
                    """, (chat_id, book_id))
                    row = cur.fetchone()
                    if row:
                        user_id, book_id, rating, opinion = row
                        return Note(user_id=user_id, book_id=book_id, rating=rating, opinion=opinion)
                return None
            except Exception as e:
                print(f"Ошибка при получении note: {e}")
                return None
            finally:
                cursor.close()  
    

    def get_quotes(self, book: Book) -> list[Quote]:
        """
        Верни список цитат по book_id.
        :param book:
        :return:
        """
        conn = self.__sql_cursor.connection
        cursor = None
        quotes = []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT quote_id, book_id, user_id, page_number, text
                FROM "Quotes"
                WHERE book_id = %s
            """, (book.book_id,))
            rows = cursor.fetchall()
            for row in rows:
                quote_id, book_id, user_id, page_number, text = row
                quotes.append(Quote(quote_id=quote_id, book_id=book_id, user_id=user_id,
                                    page_number=page_number, text=text))
            return quotes
        except Exception as e:
            print(f"Ошибка при получении цитат: {e}")
            return []
        finally:
            if cursor:
                cursor.close()


    def create_quote(self, quote: Quote) -> None:
        """
        Добавь quote в бд.
        :param quote:
        :return:
        """
        conn = self.__sql_cursor.connection
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO "Quotes" (book_id, user_id, page_number, text)
                VALUES (%s, %s, %s, %s)
            """, (
                quote.book_id,
                quote.user_id,
                quote.page_number,
                quote.text
            ))
            conn.commit()
            print("Quote добавлена")
        except Exception as e:
            print(f"Ошибка при добавлении quote: {e}")
        finally:
            if cursor:
                cursor.close()


    def update_book(self, book: Book):
        """
        Обнови книгу, она точно есть в таблице.
        :param book:
        :return:
        """
        conn = self.__sql_cursor.connection
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE "Books"
                SET title = %s,
                    description = %s,
                    year = %s,
                    cover = %s,
                    last_update = now()
                WHERE book_id = %s
            """, (
                book.title,
                book.description,
                book.year,
                book.cover,
                book.book_id
            ))
            conn.commit()
            print("Книга обновлена")
        except Exception as e:
            print(f"Ошибка при обновлении книги: {e}")
        finally:
            if cursor:
                cursor.close()


    def voice_to_speech(self, file_url: str) -> str:
        """
        Верни текст из гс по url. url точно действительный.
        :param file_url:
        :return:
        """
        try:
            response = requests.get(file_url)
            response.raise_for_status()
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=True) as temp_audio:
                temp_audio.write(response.content)
                temp_audio.flush()
                recognizer = sr.Recognizer()
                with sr.AudioFile(temp_audio.name) as source:
                    audio = recognizer.record(source)
                    text = recognizer.recognize_google(audio, language="ru-RU")
                    return text

        except Exception as e:
            print(f"Ошибка при распознавании речи: {e}")
            return "Ошибка при распознавании речи"


if __name__ == "__main__":
    pass
