import telebot
import openai
from telebot import types
import sqlite3
import re

# Состояния пользователя
states = None
# Предыдущее сообщение
pre_com = None
# Тип расхода
type_expenses = None
# message_id_inline = None
bot = telebot.TeleBot('6289799568:AAFArEfu7yepVGeseGNzwEdAC8F44H2Aiak')
openai_token = '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'
channel_id = '123'
openai.api_key = openai_token


# Команда "/start"
@bot.message_handler(commands=['start'])
def main(message):
    global states
    states = 'STARTED'
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button1 = types.KeyboardButton('Доход')
    button2 = types.KeyboardButton('Расход')
    button3 = types.KeyboardButton('Узнать расход')
    button4 = types.KeyboardButton('Узнать доход')
    keyboard.add(button1, button2, button3, button4)
    bot.send_message(message.chat.id, """
    Привет!\n
    Это бот, который умеет запоминать твои расходы и доходы, классифицировать их и создавать график по твоим расходам и
доходам, а также предлагать советы по улучшению расходов.\n
    Если хочешь добавить свои расходы, то нажми на кнопку <u><b>Доход</b></u> и сумму.\n
    Если хочешь добавить свои доходы, то нажми на кнопку <u><b>Расход</b></u>, его тип и сумму.\n
    Если хочешь посмотреть свои расходы, то нажми на кнопку <u><b>Узнать расход</b></u>.\n
    Если хочешь посмотреть свои доходы, то нажми на кнопку <u><b>Узнать Доход</b></u>.\n
    """, reply_markup=keyboard, parse_mode='html')

    # Проверяем, есть ли пользователь в нашей БД
    with sqlite3.connect('data.db') as cursor:
        commands = """
                SELECT user_id FROM Users;
        """
        result = [row[0] for row in cursor.execute(commands).fetchall()]
        if message.from_user.id not in result:

            command = """
                        INSERT INTO Users (user_id) VALUES (?);
                    """
            cursor.execute(command, (message.from_user.id, ))


@bot.message_handler(func=lambda message: "узнать" in message.text.lower() and "доход" in message.text.lower())
def find_income(message):
    """Пользователь нажал кнопку узнать доход"""
    global pre_com
    pre_com = "Узнать доход"
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    # i - income, цифра - это количество дней
    button1 = types.InlineKeyboardButton('Сегодня', callback_data='i0')
    button2 = types.InlineKeyboardButton('Вчера', callback_data='i1')
    button3 = types.InlineKeyboardButton('Неделю', callback_data='i7')
    button4 = types.InlineKeyboardButton('Месяц', callback_data='i30')
    button5 = types.InlineKeyboardButton('Три месяца', callback_data='i91')
    button6 = types.InlineKeyboardButton('Пол года', callback_data='i183')
    button7 = types.InlineKeyboardButton('Год', callback_data='i365')
    # button8 = types.InlineKeyboardButton('Всё время', callback_data='all')
    # button9 = types.InlineKeyboardButton('Другое', callback_data='other')
    keyboard.add(button1, button2, button3, button4, button5, button6, button7)
    bot.send_message(message.chat.id, "За какой период вы хотите узнать доход?", reply_markup=keyboard)


@bot.message_handler(func=lambda message: "узнать" in message.text.lower() and "расход" in message.text.lower())
def find_expense(message):
    """Пользователь нажал кнопку узнать расход"""
    global pre_com
    pre_com = "Узнать расход"
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    # i - expense, цифра - это количество дней
    button1 = types.InlineKeyboardButton('Сегодня', callback_data='e0')
    button2 = types.InlineKeyboardButton('Вчера', callback_data='e1')
    button3 = types.InlineKeyboardButton('Неделю', callback_data='e7')
    button4 = types.InlineKeyboardButton('Месяц', callback_data='e30')
    button5 = types.InlineKeyboardButton('Три месяца', callback_data='e91')
    button6 = types.InlineKeyboardButton('Пол года', callback_data='e183')
    button7 = types.InlineKeyboardButton('Год', callback_data='e365')
    # button8 = types.InlineKeyboardButton('Всё время', callback_data='all')
    # button9 = types.InlineKeyboardButton('Другое', callback_data='other')
    keyboard.add(button1, button2, button3, button4, button5, button6, button7)
    bot.send_message(message.chat.id, "За какой период вы хотите узнать расход?", reply_markup=keyboard)


@bot.message_handler(func=lambda message: re.compile(r'\b\w*доход\w*\b').search(message.text.lower()))
def button_income(message):
    global pre_com
    pre_com = 'Доход'
    bot.send_message(message.chat.id, "Сколько вы заработали?")


@bot.message_handler(func=lambda message: re.compile(r'\b\w*расход\w*\b').search(message.text.lower()))
def button_income(message):
    """Пользователь нажал кнопку Расхода"""
    global pre_com
    pre_com = 'Расход'
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    button1 = types.InlineKeyboardButton('Питание', callback_data='Питание')
    button2 = types.InlineKeyboardButton('Одежда', callback_data='Одежда')
    button3 = types.InlineKeyboardButton('Транспорт', callback_data='Транспорт')
    button4 = types.InlineKeyboardButton('Спорт', callback_data='Спорт')
    button5 = types.InlineKeyboardButton('Квартплата', callback_data='Квартплата')
    button6 = types.InlineKeyboardButton('Образование', callback_data='Образование')
    button7 = types.InlineKeyboardButton('Развлечения', callback_data='Развлечения')
    button8 = types.InlineKeyboardButton('Другое', callback_data='Другое')
    keyboard.add(button1, button2, button3, button4, button5, button6, button7, button8)
    bot.send_message(message.chat.id, "К какой категории относится данный расход?", reply_markup=keyboard)


@bot.message_handler(func=lambda message: True)
def button(message):
    global states
    global pre_com
    # Предполагается, что пользователь нажал кнопку из обычной клавиатуры
    states = 'BUTTON_MAIN'

    try:
        money = float(message.text)

        if pre_com == 'Доход':
            with sqlite3.connect('data.db') as cursor:

                cursor.execute("INSERT INTO Income (user_id, income_amount, income_date) "
                               "VALUES (?, ?, STRFTIME('%Y-%m-%d', datetime('now')));",
                               (message.from_user.id, money))

            bot.send_message(message.chat.id, "Доход успешно добавлен.")

        elif pre_com == 'Расход':
            with sqlite3.connect('data.db') as cursor:

                cursor.execute("INSERT INTO Expenses (user_id, expense_amount, expense_date, expense_type)"
                               " VALUES (?, ?, STRFTIME('%Y-%m-%d', datetime('now')), ?);",
                               (message.from_user.id, money, type_expenses))

            bot.send_message(message.chat.id, "Расход успешно добавлен.")

    except ValueError:
        bot.send_message(message.chat.id, 'Вы неправильно ввели число.\nПожалуйста, следуйте инструкции :)')


@bot.callback_query_handler(func=lambda message: message.data in ('Питание', 'Одежда', 'Другое', 'Развлечения',
                                                                  'Образование', 'Квартплата', 'Спорт', 'Транспорт'))
def button_inline_type_expense(message):
    """Пользователь нажал кнопку типа расхода"""
    global states, type_expenses
    # Пользователь нажал кнопку INLINE клавиатуры
    # bot.delete_message(message.message.chat.id, message_id_inline)
    states = 'INLINE'
    type_expenses = message.data
    bot.send_message(message.message.chat.id, 'Сколько вы потратили?')


@bot.callback_query_handler(func=lambda message: message.data in ('i365', 'i183', 'i91', 'i30', 'i7', 'i1', 'i0'))
def button_inline_time(message):
    """Пользователь нажал кнопку периода доходов"""
    with sqlite3.connect('data.db') as cursor:
        commands = """
             SELECT Income.income_amount, Income.income_date FROM Users INNER JOIN Income
             ON Users.user_id = Income.user_id
             WHERE Users.user_id = (?) AND 
             CAST(JULIANDAY(STRFTIME('%Y-%m-%d', datetime('now'))) - JULIANDAY(income_date) AS INTEGER) = (?);
        """
        result = cursor.execute(commands, (message.from_user.id, int(message.data[1:])))
        column_values = result.fetchall()
        # Если есть расходы за указанный период
        if column_values:
            bot.send_message(message.message.chat.id, f'{column_values}')
        else:
            bot.send_message(message.message.chat.id, 'У вас нет доходов за данный период')


@bot.callback_query_handler(func=lambda message: message.data in ('e365', 'e183', 'e91', 'e30', 'e7', 'e1', 'e0'))
def button_expense_time(message):
    """Пользователь нажал кнопку периода расходов"""
    with sqlite3.connect('data.db') as cursor:
        commands = """
                SELECT Expenses.expense_amount, Expenses.expense_type, Expenses.expense_date 
                FROM Users INNER JOIN Expenses
                ON Users.user_id = Expenses.user_id
                WHERE Users.user_id = (?) AND
                CAST(JULIANDAY(STRFTIME('%Y-%m-%d', datetime('now'))) - JULIANDAY(expense_date) AS INTEGER) = (?);
            """
        result = cursor.execute(commands, (message.from_user.id, int(message.data[1:])))
        column_values = result.fetchall()
        # Если есть расходы за указанный период
        if column_values:
            bot.send_message(message.message.chat.id, f'{column_values}')
        else:
            bot.send_message(message.message.chat.id, 'У вас нет расходов за данный период')


def create_tables():
    with sqlite3.connect('data.db') as cursor:
        command1 = """
                CREATE TABLE IF NOT EXISTS Expenses (
                    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    expense_amount DECIMAL(100, 2),
                    expense_date DATE,
                    expense_type VARCHAR(20)
                );
        """
        command2 = """
                CREATE TABLE IF NOT EXISTS Income (
                    income_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    income_amount DECIMAL(100, 2),
                    income_date DATE
                );
        """
        command3 = """
                CREATE TABLE IF NOT EXISTS Users(
                    user_id INTEGER PRIMARY KEY,
                    name VARCHAR(50)
            );
        """
        cursor.execute(command1)
        cursor.execute(command2)
        cursor.execute(command3)


if __name__ == '__main__':
    create_tables()
    bot.polling(none_stop=True)
