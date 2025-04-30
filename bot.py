from datetime import time, datetime
from typing import Union
from time import sleep
import psycopg2
from dotenv import load_dotenv
import os
from psycopg2 import sql
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
    def __init__(self, sql_cursor):
        """
        :param sql_cursor: это функция для запросов к бд, см. документацию по psycopg2
        """

        self.__sql_cursor = sql_cursor


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
        Закинь все данные, что есть в книге в бд
        :param book:
        :return:
        """

    def get_books(self, chat_id: int) -> list[Book]:
        """
        Найди юзера в бд и собери все книги в список, преобразовав каждую в объект Book
        надо будет дополнительно подтянуть из бд жанр, рейтинг, статус и последнее обновление
        :param chat_id:
        :return:
        """
        print("книги получены")
        return [
            Book(
                "нига",
                1,
                "черный",
                1984,
                10,
                "человек",
                "Читаю сейчас",
                datetime(1, 1, 1),
                "белый",
                cover="https://i.pinimg.com/236x/c8/cc/24/c8cc24bba37a25c009647b8875aae0e3.jpg",
            )
        ]

    def get_book_from_side_site(self, book: Book) -> Book:
        """
        Найди в инете через сторонний сайт и верни книгу по автору и названию.
        Она должна содержать название, автора, жанр, год
        Если не нашлось -> верни книгу, которую получил
        :param book:
        :return:
        """
        return book

    def get_books_over_year(self, books: list[Book]) -> int:
        """
        Посчитай кол-во книг, у которых статус - прочитано и последний апдейт от текущего года
        :param books:
        :return:
        """
        return 0

    def get_books_mid_rating(self, books: list[Book]) -> float:
        """
        Посчитай среднюю оценку по книгам
        :param books:
        :return:
        """
        return 0

    def get_books_popular_genres(self, books: list[Book]) -> list[tuple[str, float]]:
        """
        Верни отсортированный по процентам список. Пример [('Хоррор', 60), ('Роман', 40)]
        :param books:
        :return:
        """

    def generate_reports(self) -> None:
        """
        Поставь бесконечный цикл, если понедельник, то входит в тело, иначе ждет сутки или как поставишь.
        Там нужно соответственно пройтись по бд и создать новые репорты.
        Удалять старые, которым больше 2х недель.
        То есть должны храниться новые и с прошлой недели.
        :return:
        """
        while True:
            print(datetime.now())
            sleep(5)

    def get_report(self, chat_id: int) -> tuple[Report, Report]:
        """
        Верни новый и старый репорты из бд соответственно.
        + нужно получить кол-во новых репортов через user_id
        :param chat_id:
        :return:
        """
        return (Report(1, 1, 1, 1, 1), Report(1, 1, 1, 1, 1))

    def create_note(self, note: Note) -> None:
        """
        Создай или обнови note.
        :param note:
        :return:
        """

    def get_note(self, chat_id: int, book_id: int) -> Union[Note, None]:
        """
        Достань заметку из бд или верни None
        :param chat_id:
        :param book_id:
        :return:
        """
        return None

    def get_quotes(self, book: Book) -> list[Quote]:
        """
        Верни список цитат по book_id
        :param book:
        :return:
        """
        return [Quote(1, 1, 1, "wasap")]

    def create_quote(self, quote: Quote) -> None:
        """
        Добавь quote в бд
        :param quote:
        :return:
        """

    def update_book(self, book: Book):
        """
        Обнови книгу, она точно есть в таблице
        :param book:
        :return:
        """

    def voice_to_speech(self, file_url: str) -> str:
        """
        Верни текст из гс по url. url точно действительный.
        :param file_url:
        :return:
        """
        return "текст"


if __name__ == "__main__":
    pass
