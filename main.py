import telebot
import openai
from telebot import types
import sqlite3
import re
from tabulate import tabulate

# Предыдущее сообщение
pre_com = None
# Тип расхода
type_expenses = None
message_id_inline = None
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


@bot.message_handler(func=lambda message: pre_com in ('Доход', 'Расход'))
def counting_money(message):
    global message_id_inline
    money = message.text
    error = ''
    try:
        if 'рубл' in money:
            for i in money.split():
                try:
                    money = float(i)
                    break
                except ValueError:
                    pass
        else:
            for i in money.split():
                try:
                    money = float(i)
                    break
                except ValueError:
                    pass
        if type(money) == str:
            error = 'Извините, я не умею отвечать на простые сообщения.\nПожалуйста, следуйте инструкции ^_^\n'
            raise ValueError
        elif not money:
            error = 'Ноль не считается :)'
            raise ValueError
    except ValueError:
        bot.delete_message(message.chat.id, message.message_id)
        response = bot.edit_message_text(f'{error}\nЧто вы хотите выбрать?', message.chat.id,
                                         message_id_inline, reply_markup=keyboard)
        message_id_inline = response.message_id
    else:
        if pre_com == 'Доход':
            insert_income(message, money)
        else:
            insert_expense(message, money)


@bot.message_handler(func=lambda message: pre_com in ('othere', 'otheri'))
def time_period(message):
    global message_id_inline
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    if re.match(pattern, message.text):
        with sqlite3.connect('data.db') as cursor:
            if pre_com == 'otheri':
                commands = """
                             SELECT Income.income_amount, Income.income_date FROM Users INNER JOIN Income
                             ON Users.user_id = Income.user_id
                             WHERE Users.user_id = (?) AND
                             income_date = (?);
                        """
            else:
                commands = """
                             SELECT Expenses.expense_amount, Expenses.expense_type, Expenses.expense_date FROM Users INNER JOIN Expenses
                             ON Users.user_id = Expenses.user_id
                             WHERE Users.user_id = (?) AND
                             expense_date = (?);
                        """
            result = cursor.execute(commands, (message.from_user.id, message.text))
            column_values = result.fetchall()
            # Если есть расходы за указанный период
            if column_values:
                rows = [
                    ["Сумма", "Дата"]
                ]
                for column_value in column_values:
                    rows.append([f'{column_value[0]} руб.', column_value[1]])
                table = tabulate(rows, headers="firstrow")
                response = bot.edit_message_text(f'{table}\n\nЧто вы хотите выбрать?', message.chat.id,
                                                 message_id_inline, reply_markup=keyboard)
            else:
                response = bot.edit_message_text(f'У вас нет {"доходов" if pre_com == "otheri" else "расходов"}'
                                                 f' за данный период.\nЧто вы хотите выбрать?',
                                                 message.chat.id, message_id_inline, reply_markup=keyboard)
            message_id_inline = response.message_id
    else:
        try:
            response = bot.edit_message_text('Пожалуйста, введите дату, в формате YYYY-MM-DD', message.chat.id,
                                             message_id_inline)
            message_id_inline = response.message_id
        except telebot.apihelper.ApiTelegramException:
            pass
    bot.delete_message(message.chat.id, message.message_id)


@bot.message_handler(func=lambda message: pre_com == 'Другое')
def other_type_expense(message):
    global type_expenses, message_id_inline, pre_com
    bot.delete_message(message.chat.id, message.message_id)
    response = bot.edit_message_text('Сколько рублей вы потратили?', message.chat.id, message_id_inline)
    type_expenses = message.text
    message_id_inline = response.message_id
    pre_com = 'Расход'


def insert_income(message, money):
    global message_id_inline
    with sqlite3.connect('data.db') as cursor:
        cursor.execute("INSERT INTO Income (user_id, income_amount, income_date) "
                       "VALUES (?, ?, STRFTIME('%Y-%m-%d', datetime('now')));",
                       (message.from_user.id, money))
    bot.delete_message(message.chat.id, message.message_id)
    response = bot.edit_message_text(chat_id=message.chat.id, message_id=message_id_inline,
                                     text='Доход успешно добавлен.\nЧто вы хотите выбрать?', reply_markup=keyboard)
    message_id_inline = response.message_id


def insert_expense(message, money):
    global message_id_inline
    with sqlite3.connect('data.db') as cursor:
        cursor.execute("INSERT INTO Expenses (user_id, expense_amount, expense_date, expense_type)"
                       " VALUES (?, ?, STRFTIME('%Y-%m-%d', datetime('now')), ?);",
                       (message.from_user.id, money, type_expenses))
    bot.delete_message(message.chat.id, message.message_id)
    response = bot.edit_message_text(chat_id=message.chat.id, message_id=message_id_inline,
                                     text='Расход успешно добавлен.\nЧто вы хотите выбрать?', reply_markup=keyboard)
    message_id_inline = response.message_id


@bot.callback_query_handler(func=lambda message: message.data == 'income')
def income(message):
    global pre_com, message_id_inline
    pre_com = 'Доход'
    response = bot.edit_message_text('Сколько рублей вы заработали?', message.message.chat.id,
                                     message.message.message_id)
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
    bot.edit_message_text("К какой категории относится данный расход?", message.message.chat.id,
                          message.message.message_id, reply_markup=keyboard_exp)


@bot.callback_query_handler(func=lambda message: message.data == 'find_inc')
def find_income(message):
    global message_id_inline
    keyboard_ = types.InlineKeyboardMarkup(row_width=3)
    but1 = types.InlineKeyboardButton('Сегодня', callback_data='i0')
    but2 = types.InlineKeyboardButton('Вчера', callback_data='i1')
    but3 = types.InlineKeyboardButton('Неделю', callback_data='i7')
    but4 = types.InlineKeyboardButton('Месяц', callback_data='i30')
    but5 = types.InlineKeyboardButton('Три месяца', callback_data='i91')
    but6 = types.InlineKeyboardButton('Пол года', callback_data='i183')
    but7 = types.InlineKeyboardButton('Год', callback_data='i365')
    but8 = types.InlineKeyboardButton('Всё время', callback_data='iall')
    but9 = types.InlineKeyboardButton('Другое', callback_data='otheri')
    keyboard_.add(but1, but2, but3, but4, but5, but6, but7, but8, but9)
    response = bot.edit_message_text("За какой период вы хотите узнать доход?", message.message.chat.id,
                                     message.message.message_id, reply_markup=keyboard_)
    message_id_inline = response.message_id


@bot.callback_query_handler(func=lambda message: message.data == 'find_exp')
def find_expense(message):
    global message_id_inline
    keyboard_ = types.InlineKeyboardMarkup(row_width=3)
    # i - expense, цифра - это количество дней
    but1 = types.InlineKeyboardButton('Сегодня', callback_data='e0')
    but2 = types.InlineKeyboardButton('Вчера', callback_data='e1')
    but3 = types.InlineKeyboardButton('Неделю', callback_data='e7')
    but4 = types.InlineKeyboardButton('Месяц', callback_data='e30')
    but5 = types.InlineKeyboardButton('Три месяца', callback_data='e91')
    but6 = types.InlineKeyboardButton('Пол года', callback_data='e183')
    but7 = types.InlineKeyboardButton('Год', callback_data='e365')
    but8 = types.InlineKeyboardButton('Всё время', callback_data='eall')
    but9 = types.InlineKeyboardButton('Другое', callback_data='othere')
    keyboard_.add(but1, but2, but3, but4, but5, but6, but7, but8, but9)
    response = bot.edit_message_text("За какой период вы хотите узнать расход?", message.message.chat.id,
                                     message.message.message_id, reply_markup=keyboard_)
    message_id_inline = response.message_id


@bot.callback_query_handler(func=lambda message: message.data in ('Питание', 'Одежда', 'Развлечения',
                                                                  'Образование', 'Квартплата', 'Спорт', 'Транспорт'))
def button_inline_type_expense(message):
    """Пользователь нажал кнопку типа расхода"""
    global pre_com, type_expenses, message_id_inline
    pre_com = 'Расход'
    type_expenses = message.data
    response = bot.edit_message_text(chat_id=message.message.chat.id, message_id=message.message.message_id,
                                     text='Сколько рублей вы потратили?')
    message_id_inline = response.message_id


@bot.callback_query_handler(func=lambda message: message.data == 'Другое')
def button_inline_other(message):
    """Пользователь нажал на кнопку типа расхода Другое"""
    global pre_com, type_expenses, message_id_inline
    pre_com = 'Другое'
    response = bot.edit_message_text(chat_id=message.message.chat.id, message_id=message.message.message_id,
                                     text='Уточните, пожалуйста, тип расхода')
    message_id_inline = response.message_id


@bot.callback_query_handler(func=lambda message: message.data[0] == 'i')
def button_inline_time(message):
    """Пользователь нажал кнопку периода доходов"""
    with sqlite3.connect('data.db') as cursor:
        if message.data != 'iall':
            commands = """
                 SELECT Income.income_amount, Income.income_date FROM Users INNER JOIN Income
                 ON Users.user_id = Income.user_id
                 WHERE Users.user_id = (?) AND
                 CAST(JULIANDAY(STRFTIME('%Y-%m-%d', datetime('now'))) - JULIANDAY(income_date) AS INTEGER) = (?);
            """
            result = cursor.execute(commands, (message.from_user.id, int(message.data[1:])))
        else:
            commands = """
                SELECT Income.income_amount, Income.income_date FROM Users INNER JOIN Income
                ON Users.user_id = Income.user_id
                WHERE Users.user_id = (?);
            """
            result = cursor.execute(commands, (message.from_user.id, ))
        column_values = result.fetchall()
        # Если есть расходы за указанный период
        if column_values:
            rows = [
                ["Сумма", "Дата"]
            ]
            for column_value in column_values:
                rows.append([f'{column_value[0]} рубл.', column_value[1]])
            table = tabulate(rows, headers="firstrow")
            bot.edit_message_text(f'{table}\n\nЧто вы хотите выбрать?', message.message.chat.id, message_id_inline,
                                  reply_markup=keyboard)
        else:
            bot.edit_message_text('У вас нет доходов за данный период.\nЧто вы хотите выбрать?',
                                  message.message.chat.id, message_id_inline,
                                  reply_markup=keyboard)


@bot.callback_query_handler(func=lambda message: message.data[0] == 'e')
def button_expense_time(message):
    """Пользователь нажал кнопку периода расходов"""
    with sqlite3.connect('data.db') as cursor:
        if message.data != 'eall':
            commands = """
                 SELECT Expenses.expense_amount, Expenses.expense_type, Expenses.expense_date FROM Users INNER JOIN Expenses
                 ON Users.user_id = Expenses.user_id
                 WHERE Users.user_id = (?) AND
                 CAST(JULIANDAY(STRFTIME('%Y-%m-%d', datetime('now'))) - JULIANDAY(expense_date) AS INTEGER) = (?);
            """
            result = cursor.execute(commands, (message.from_user.id, int(message.data[1:])))
        else:
            commands = """
                SELECT Expenses.expense_amount, Expenses.expense_type, Expenses.expense_date FROM Users INNER JOIN Expenses
                ON Users.user_id = Expenses.user_id
                WHERE Users.user_id = (?);
            """
            result = cursor.execute(commands, (message.from_user.id,))
        column_values = result.fetchall()
        # Если есть расходы за указанный период
        if column_values:
            rows = [
                ["Сумма", "Тип расхода", "Дата"]
            ]
            for column_value in column_values:
                rows.append([f'{column_value[0]} рубл.', column_value[1], column_value[2]])
            table = tabulate(rows, headers="firstrow")
            bot.edit_message_text(f'{table}\n\nЧто вы хотите выбрать?', message.message.chat.id, message_id_inline,
                                  reply_markup=keyboard)
        else:
            bot.edit_message_text('У вас нет расходов за данный период.\nЧто вы хотите выбрать?',
                                  message.message.chat.id, message_id_inline, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda message: message.data == 'othere')
def button_find_expense_other(message):
    global pre_com, message_id_inline
    pre_com = 'othere'
    response = bot.edit_message_text('Уточните, пожалуйста, за какую дату вы хотите узнать расход?\n'
                          'Вводите дату в формате YYYY-MM-DD', message.message.chat.id, message_id_inline)
    message_id_inline = response.message_id


@bot.callback_query_handler(func=lambda message: message.data == 'otheri')
def button_find_expense_other(message):
    global pre_com, message_id_inline
    pre_com = 'otheri'
    response = bot.edit_message_text('Уточните, пожалуйста, за какую дату вы хотите узнать доход?\n'
                                     'Вводите дату в формате YYYY-MM-DD', message.message.chat.id, message_id_inline)
    message_id_inline = response.message_id


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
