import os
from supabase import create_client, Client
from dotenv import load_dotenv
from telebot import TeleBot
import psycopg2

from handlers import init_bot

if __name__ == "__main__":
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    else:
        raise Exception("No .env file found")
    connection = f"{os.getenv("DRIVER")}://{os.getenv("USER")}:{os.getenv("PASSWORD")}@{os.getenv("HOST")}:{os.getenv("PORT")}/{os.getenv('DATABASE')}"
    try:
        with psycopg2.connect(
            connection
        ) as conn:
            pass
        app = TeleBot(BOT_TOKEN)
        init_bot(app, connection, BOT_TOKEN)

    except psycopg2.OperationalError as e:
        print(f"Ошибка при подключение к бд: {e}")
