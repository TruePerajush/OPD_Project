from datetime import time
from typing import Union

class User:
    def __init__(self, username: str, chat_id: int, daily_goals: int = 0, weekly_goals: int = 0, monthly_goals: int = 0, annual_goals: int = 0, reminder: time = None):
        self.username: str = username
        self.chat_id: int = chat_id
        self.daily_goals: int = daily_goals
        self.weekly_goals: int = weekly_goals
        self.monthly_goals: int = monthly_goals
        self.annual_goals: int = annual_goals
        self.reminder: time = reminder

class TelegramBot:
    def __init__(self, sql_cursor):
        self.sql_cursor = sql_cursor
    def create_user(self, user: User) -> None:
        print("user создан")
        """
        Создай пользователя в бд, если такого еще нет
        :param user:
        :return:
        """
        pass
    def update_user_attribute(self, user: User, attribute: str, value: Union[int, time]) -> None:
        print(f"аттрибут {attribute} изменен на {value}")

        """
        Обнови пользователя только по данному аттрибуту
        :param user:
        :param attribute:
        :param value:
        :return:
        """
        pass
    def get_user(self, chat_id: int) -> User:
        print(f"получен user c chat_id: {chat_id}")
        """
        Верни юзера из бд
        :param chat_id:
        :return:
        """
        return None
if __name__ == '__main__':
    pass
