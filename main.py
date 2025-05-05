import os
from supabase import create_client, Client
from dotenv import load_dotenv
from telebot import TeleBot
import psycopg2

from handlers import init_bot

if __name__ == "__main__":
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    else:
        raise Exception("No .env file found")
    try:
        with psycopg2.connect(
            dbname=os.getenv("DATABASE"),
            user=os.getenv("USER"),
            password=os.getenv("PASSWORD"),
            host=os.getenv("HOST"),
            port=os.getenv("PORT"),
        ) as conn:
            with conn.cursor() as sql_cursor:
                app = TeleBot(BOT_TOKEN)
                init_bot(app, sql_cursor, BOT_TOKEN)
    except psycopg2.OperationalError as e:
        print(f"Ошибка при подключение к бд: {e}")
