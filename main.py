import telebot
import openai
from telebot import types
import sqlite3
import re
from tabulate import tabulate

# Состояния пользователя
states = None
# Предыдущее сообщение
pre_com = None
# Тип расхода
type_expenses = None
message_id_inline = None
state_message = False
bot = telebot.TeleBot('6289799568:AAFArEfu7yepVGeseGNzwEdAC8F44H2Aiak')
openai_token = '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'
channel_id = '123'
openai.api_key = openai_token

keyboard = types.InlineKeyboardMarkup(row_width=2)
button1 = types.InlineKeyboardButton('Доход', callback_data='income')
button2 = types.InlineKeyboardButton('Расход', callback_data='expense')
button3 = types.InlineKeyboardButton('Узнать расход', callback_data='find_exp')
button4 = types.InlineKeyboardButton('Узнать доход', callback_data='find_inc')
keyboard.add(button1, button2, button3, button4)


# Команда "/start"
@bot.message_handler(commands=['start'])
def main(message):
    bot.send_message(message.chat.id, """
    Привет!\n
    Это бот, который умеет запоминать твои расходы и доходы, классифицировать их и создавать график по твоим расходам и
доходам, а также предлагать советы по улучшению расходов.\n
    Если хочешь добавить свои расходы, то нажми на кнопку <u><b>Доход</b></u> и сумму.\n
    Если хочешь добавить свои доходы, то нажми на кнопку <u><b>Расход</b></u>, его тип и сумму.\n
    Если хочешь посмотреть свои расходы, то нажми на кнопку <u><b>Узнать расход</b></u>.\n
    Если хочешь посмотреть свои доходы, то нажми на кнопку <u><b>Узнать Доход</b></u>.\n
    """, parse_mode='html')
    bot.send_message(message.chat.id, 'Что вы хотите выбрать?', reply_markup=keyboard)

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
            cursor.execute(command, (message.from_user.id,))


@bot.message_handler(func=lambda message: True)
def button(message):
    global states, pre_com, message_id_inline, state_message
    # Предполагается, что пользователь нажал кнопку из обычной клавиатуры
    states = 'BUTTON_MAIN'
    try:
        money = float(message.text)
        if not money:
            raise ValueError

        if pre_com == 'Доход':
            with sqlite3.connect('data.db') as cursor:

                cursor.execute("INSERT INTO Income (user_id, income_amount, income_date) "
                               "VALUES (?, ?, STRFTIME('%Y-%m-%d', datetime('now')));",
                               (message.from_user.id, money))
            bot.delete_message(message.chat.id, message.message_id)
            bot.edit_message_text(chat_id=message.chat.id, message_id=message_id_inline,
                                  text='Доход успешно добавлен.\nЧто вы хотите выбрать?', reply_markup=keyboard)
            state_message = True

        elif pre_com == 'Расход':
            with sqlite3.connect('data.db') as cursor:

                cursor.execute("INSERT INTO Expenses (user_id, expense_amount, expense_date, expense_type)"
                               " VALUES (?, ?, STRFTIME('%Y-%m-%d', datetime('now')), ?);",
                               (message.from_user.id, money, type_expenses))
            bot.delete_message(message.chat.id, message.message_id)
            bot.edit_message_text(chat_id=message.chat.id, message_id=message_id_inline,
                                  text='Расход успешно добавлен.\nЧто вы хотите выбрать?', reply_markup=keyboard)
            state_message = True

    except ValueError:
        bot.delete_message(message.chat.id, message.message_id)
        response = bot.send_message(message.chat.id, 'Вы неправильно ввели число.\nПожалуйста, следуйте инструкции :)')
        state_message = True
        message_id_inline = response.message_id


@bot.callback_query_handler(func=lambda message: message.data == 'income')
def income(message):
    global pre_com, message_id_inline
    pre_com = 'Доход'
    response = bot.edit_message_text('Сколько вы заработали?', message.message.chat.id, message.message.message_id)
    message_id_inline = response.message_id


@bot.callback_query_handler(func=lambda message: message.data == 'expense')
def expense(message):
    keyboard_exp = types.InlineKeyboardMarkup(row_width=2)
    button_in1 = types.InlineKeyboardButton('Питание', callback_data='Питание')
    button_in2 = types.InlineKeyboardButton('Одежда', callback_data='Одежда')
    button_in3 = types.InlineKeyboardButton('Транспорт', callback_data='Транспорт')
    button_in4 = types.InlineKeyboardButton('Спорт', callback_data='Спорт')
    button_in5 = types.InlineKeyboardButton('Квартплата', callback_data='Квартплата')
    button_in6 = types.InlineKeyboardButton('Образование', callback_data='Образование')
    button_in7 = types.InlineKeyboardButton('Развлечения', callback_data='Развлечения')
    button_in8 = types.InlineKeyboardButton('Другое', callback_data='Другое')
    keyboard_exp.add(button_in1, button_in2, button_in3, button_in4, button_in5, button_in6, button_in7, button_in8)
    response = bot.edit_message_text("К какой категории относится данный расход?", message.message.chat.id,
                                     message.message.message_id, reply_markup=keyboard_exp)


@bot.callback_query_handler(func=lambda message: message.data == 'find_inc')
def find_income(message):
    keyboard_ = types.InlineKeyboardMarkup(row_width=3)
    # i - income, цифра - это количество дней
    but1 = types.InlineKeyboardButton('Сегодня', callback_data='i0')
    but2 = types.InlineKeyboardButton('Вчера', callback_data='i1')
    but3 = types.InlineKeyboardButton('Неделю', callback_data='i7')
    but4 = types.InlineKeyboardButton('Месяц', callback_data='i30')
    but5 = types.InlineKeyboardButton('Три месяца', callback_data='i91')
    but6 = types.InlineKeyboardButton('Пол года', callback_data='i183')
    but7 = types.InlineKeyboardButton('Год', callback_data='i365')
    # button8 = types.InlineKeyboardButton('Всё время', callback_data='all')
    # button9 = types.InlineKeyboardButton('Другое', callback_data='other')
    keyboard_.add(but1, but2, but3, but4, but5, but6, but7)
    response = bot.edit_message_text("За какой период вы хотите узнать доход?", message.message.chat.id,
                                     message.message.message_id, reply_markup=keyboard_)


@bot.callback_query_handler(func=lambda message: message.data == 'find_exp')
def find_expense(message):
    keyboard_ = types.InlineKeyboardMarkup(row_width=3)
    # i - expense, цифра - это количество дней
    but1 = types.InlineKeyboardButton('Сегодня', callback_data='e0')
    but2 = types.InlineKeyboardButton('Вчера', callback_data='e1')
    but3 = types.InlineKeyboardButton('Неделю', callback_data='e7')
    but4 = types.InlineKeyboardButton('Месяц', callback_data='e30')
    but5 = types.InlineKeyboardButton('Три месяца', callback_data='e91')
    but6 = types.InlineKeyboardButton('Пол года', callback_data='e183')
    but7 = types.InlineKeyboardButton('Год', callback_data='e365')
    # button8 = types.InlineKeyboardButton('Всё время', callback_data='all')
    # button9 = types.InlineKeyboardButton('Другое', callback_data='other')
    keyboard_.add(but1, but2, but3, but4, but5, but6, but7)
    response = bot.edit_message_text("За какой период вы хотите узнать расход?", message.message.chat.id,
                                     message.message.message_id, reply_markup=keyboard_)


@bot.callback_query_handler(func=lambda message: message.data in ('Питание', 'Одежда', 'Другое', 'Развлечения',
                                                                  'Образование', 'Квартплата', 'Спорт', 'Транспорт'))
def button_inline_type_expense(message):
    """Пользователь нажал кнопку типа расхода"""
    global pre_com, type_expenses, message_id_inline
    pre_com = 'Расход'
    type_expenses = message.data
    response = bot.edit_message_text(chat_id=message.message.chat.id, message_id=message.message.message_id,
                                     text='Сколько вы потратили?')
    message_id_inline = response.message_id


@bot.callback_query_handler(func=lambda message: message.data in ('i365', 'i183', 'i91', 'i30', 'i7', 'i1', 'i0'))
def button_inline_time(message):
    global state_message
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
            rows = [
                ["Сумма", "Дата"]
            ]
            for column_value in column_values:
                rows.append([column_value[0], column_value[1]])
            table = tabulate(rows, headers="firstrow")
            bot.edit_message_text(f'{table}\n\nЧто вы хотите выбрать?', message.message.chat.id, message_id_inline,
                                  reply_markup=keyboard)
        else:
            bot.edit_message_text('У вас нет доходов за данный период.\nЧто вы хотите выбрать?',
                                  message.message.chat.id, message_id_inline,
                                  reply_markup=keyboard)
        state_message = True


@bot.callback_query_handler(func=lambda message: message.data in ('e365', 'e183', 'e91', 'e30', 'e7', 'e1', 'e0'))
def button_expense_time(message):
    global state_message
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
            rows = [
                ["Сумма", "Тип расхода", "Дата"]
            ]
            for column_value in column_values:
                rows.append([column_value[0], column_value[1], column_value[2]])
            table = tabulate(rows, headers="firstrow")
            bot.edit_message_text(f'{table}\n\nЧто вы хотите выбрать?', message.message.chat.id, message_id_inline,
                                  reply_markup=keyboard)
        else:
            bot.edit_message_text('У вас нет расходов за данный период.\nЧто вы хотите выбрать?',
                                  message.message.chat.id, message_id_inline, reply_markup=keyboard)
        state_message = True


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
