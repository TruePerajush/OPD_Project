from datetime import time, datetime
from typing import Union
from time import sleep


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
        book_id: int,
        title: str,
        description: str,
        year: str,
        rating: float,
        genre: str,
        status: str,
        last_update: datetime,
        author: str,
        cover: str = None,  # ссылка на обложку из бакета covers
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
    def __init__(self, sql_cursor, supabase):
        """
        :param sql_cursor: это функция для запросов к бд, см. документацию по psycopg2
        :param supabase: это клиент для связи с проектом, см. документацию по supabase
        """
        self.__sql_cursor = sql_cursor
        self.__supabase = supabase

    def create_user(self, user: User) -> None:
        """
        Создай пользователя в бд, если такого еще нет
        :param user:
        :return:
        """
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
        print(f"аттрибут {attribute} изменен на {value}")
        pass

    def get_user(self, chat_id: int) -> User:
        """
        Верни юзера из бд. Если нет, верни None
        :param chat_id:
        :return:
        """
        print(f"получен user c chat_id: {chat_id}")
        return None

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
                1,
                "нига",
                "черный",
                1984,
                10,
                "человек",
                "раб",
                datetime(1, 1, 1),
                "белый",
            )
        ]

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


if __name__ == "__main__":
    pass
