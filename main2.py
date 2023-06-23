import telebot
import openai
from telebot import types
import requests
from bs4 import BeautifulSoup
import webbrowser
import sqlite3

bot = telebot.TeleBot('6289799568:AAFArEfu7yepVGeseGNzwEdAC8F44H2Aiak')
openai_token = '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'
channel_id = '123'
openai.api_key = openai_token


# Команда "/start"
@bot.message_handler(commands=['start', 'hello'])
def main(message):
    bot.send_message(message.chat.id, "Привет! Это бот, который умеет запоминать твои расходы и доходы, "
                                      "классифицировать их и создавать график по твоим расходам и доходам,"
                                      " а также предлагать советы по улучшению расходов."
                                      'Если хочешь добавить свои расходы, то напиши команду "/add- <сумма расходов>".'
                                      'Если хочешь добавить свои доходы, то напиши команду "/add+ <сумма расходов>".'
                                      'Если хочешь посмотреть свои расходы, то напиши /give-.'
                                      'Если хочешь посмотреть свои доходы, то напиши /give+.'
                                      'Чтобы начать напечатай /start или /hello.')


# @bot.message_handler(func=lambda message: True)
# def handle_buttons(message):
#     if message.text == 'Доход':
#         money = bot.send_message(message.chat.id, 'Сколько вы заработали?')
#     elif message.text == 'Расход':
#         bot.send_message(message.chat.id, 'Сколько вы потратили?')


def create_table():
    with sqlite3.connect('data.db') as cursor:
        command = """
            CREATE TABLE IF NOT EXISTS Users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                expenses INTEGER,
                income INTEGER
            );
        """
        cursor.execute(command)


@bot.message_handler(commands=['add-'])
def expenses(message):
    try:
        income_value = int(str(message.text.split()[1]))
        keyboard = types.ReplyKeyboardMarkup(row_width=2)
        button1 = types.KeyboardButton('Питание')
        button2 = types.KeyboardButton('Транспорт')
        button3 = types.KeyboardButton('Образование')
        button4 = types.KeyboardButton('Спорт')
        button5 = types.KeyboardButton('Одежда')
        button6 = types.KeyboardButton('Квартплата')
        button7 = types.KeyboardButton('Развлечения')
        button8 = types.KeyboardButton('Другое')
        keyboard.add(button1, button2, button3, button4, button5, button6, button7, button8)
        bot.send_message(message.chat.id, "К какой категории относится данный расход?", reply_markup=keyboard)

    except sqlite3.Error as e:
        bot.send_message(message.chat.id, f"Ошибка при добавлении расхода: {e}")


@bot.message_handler(func=lambda message: True)
def button(message):
    if message.text in (
    'Питание', 'Транспорт', 'Образование', 'Спорт', 'Одежда', 'Квартплата', 'Развлечения', 'Другое'):


@bot.message_handler(commands=['add+'])
def income(message):
    with sqlite3.connect('data.db') as cursor:
        command = """
                INSERT INTO Users (income) VALUES (?);
        """
        try:
            income_value = int(str(message.text.split()[1]))
            cursor.execute(command, (income_value,))
            bot.send_message(message.chat.id, "Доход успешно добавлен.")
        except sqlite3.Error as e:
            bot.send_message(message.chat.id, f"Ошибка при добавлении дохода: {e}")


@bot.message_handler(commands=['give-'])
def given_expenses(message):
    with sqlite3.connect('data.db') as cursor:
        commands = """
            SELECT expenses FROM Users WHERE expenses IS NOT NULL;
        """
        result = cursor.execute(commands)
        column_values = result.fetchall()
    bot.send_message(message.chat.id, f'{column_values}')


@bot.message_handler(commands=['give+'])
def given_income(message):
    with sqlite3.connect('data.db') as cursor:
        commands = """
            SELECT income FROM Users WHERE income IS NOT NULL;
        """
        result = cursor.execute(commands)
        column_values = result.fetchall()
    bot.send_message(message.chat.id, f'{column_values}')


if __name__ == '__main__':
    create_table()
    bot.polling(none_stop=True)
