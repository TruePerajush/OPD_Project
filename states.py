from telebot.handler_backends import StatesGroup, State
class States(StatesGroup):
    YEAR=State()
    MONTH=State()