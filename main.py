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
button5 = types.InlineKeyboardButton('Отменить расход', callback_data='cancel_exp')
button6 = types.InlineKeyboardButton('Отменить доход', callback_data='cancel_inc')
keyboard.add(button1, button2, button3, button4, button5, button6)


# Команда "/start"
@bot.message_handler(commands=['start'])
def start(message):
    global message_id_inline
    com = """
    Привет!\n
    Это бот, который умеет запоминать твои расходы и доходы, а также предлагать советы по финансовой грамотности.\n
    Если хочешь добавить свои расходы, то нажми на кнопку <u><b>Доход</b></u> и сумму.\n
    Если хочешь добавить свои доходы, то нажми на кнопку <u><b>Расход</b></u>, его тип и сумму.\n
    Если хочешь посмотреть свои расходы, то нажми на кнопку <u><b>Узнать расход</b></u>.\n
    Если хочешь посмотреть свои доходы, то нажми на кнопку <u><b>Узнать Доход</b></u>.\n
    Если хочешь отменить добавленный <u>доход</u>, то нажми <u><b>Отменить доход</b></u>. 
    <b>(только учти, что удаляется самый последний добавленный доход)</b>.\n
    Если хочешь отменить добавленный <u>расход</u>, то нажми <u><b>Отменить расход</b></u>.\n
    Для более подробной информации о боте нажмите /help.
    """
    bot.send_message(message.chat.id, com, parse_mode='html')
    response = bot.send_message(message.chat.id, 'Что вы хотите выбрать?', reply_markup=keyboard)
    message_id_inline = response.message_id
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


@bot.message_handler(commands=['help'])
def helping(message):
    global message_id_inline
    com = """
        Я умею запоминать ваши доходы и расходы, выбирать их за определённый период времени, а также давать советы по
финансовой грамотности, исходя из ваших трат и заработков.\n
    Если хочешь добавить свои расходы, то нажми на кнопку <u><b>Доход</b></u>.\n
    Если хочешь добавить свои доходы, то нажми на кнопку <u><b>Расход</b></u>.\n
    Если хочешь посмотреть свои расходы, то нажми на кнопку <u><b>Узнать расход</b></u>.\n
    Если хочешь посмотреть свои доходы, то нажми на кнопку <u><b>Узнать доход</b></u>.\n
    Если хочешь отменить добавленный <u>доход</u>, то нажми <u><b>Отменить доход</b></u>. 
    <b>(только учти, что удаляется самый последний добавленный доход)</b>.\n
    Если хочешь отменить добавленный <u>расход</u>, то нажми <u><b>Отменить расход</b></u>. 
    """
    bot.delete_message(message.chat.id, message.message_id)
    try:
        edit_message(com, message.chat.id, markup=True, parse='html')
    except telebot.apihelper.ApiTelegramException:
        pass


def edit_message(com, chat, markup=None, parse=None):
    global message_id_inline
    if markup is True:
        markup = keyboard
    response = bot.edit_message_text(com, chat, message_id_inline, reply_markup=markup,
                                     parse_mode=parse)
    message_id_inline = response.message_id


@bot.message_handler(func=lambda message: pre_com in ('Доход', 'Расход'))
def counting_money(message):
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
            error = 'Пожалуйста, следуйте инструкции.\nЕсли вам что-то непонятно, то напишите /help\n'
            raise ValueError
        elif not money:
            error = 'Ноль не считается :)'
            raise ValueError
    except ValueError:
        bot.delete_message(message.chat.id, message.message_id)
        edit_message(f'{error}\nЧто вы хотите выбрать?', message.chat.id, markup=True)
    else:
        if pre_com == 'Доход':
            insert_income(message, money)
        else:
            insert_expense(message, money)


@bot.message_handler(func=lambda message: pre_com in ('othere', 'otheri'))
def time_period(message):
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
                             SELECT Expenses.expense_amount, Expenses.expense_type, Expenses.expense_date
                              FROM Users INNER JOIN Expenses
                             ON Users.user_id = Expenses.user_id
                             WHERE Users.user_id = (?) AND
                             expense_date = (?);
                        """
            result = cursor.execute(commands, (message.from_user.id, message.text))
            column_values = result.fetchall()
            if column_values:
                if pre_com == 'otheri':
                    rows = [["Сумма", "Дата"]]
                else:
                    rows = [["Сумма", "Тип расхода", "Дата"]]
                for column_value in column_values:
                    rows.append([f'{column_value[0]} руб.', column_value[1]])
                table = tabulate(rows, headers="firstrow")
                edit_message(f'{table}\n\nЧто вы хотите выбрать?', message.chat.id, markup=True)
            else:
                edit_message(f'У вас нет {"доходов" if pre_com == "otheri" else "расходов"}'
                             f' за данный период.\nЧто вы хотите выбрать?', message.chat.id, markup=True)

    else:
        try:
            edit_message('Пожалуйста, введите дату, в формате YYYY-MM-DD', message.chat.id)
        except telebot.apihelper.ApiTelegramException:
            pass
    bot.delete_message(message.chat.id, message.message_id)


@bot.message_handler(func=lambda message: pre_com == 'Другое')
def other_type_expense(message):
    global type_expenses, pre_com
    bot.delete_message(message.chat.id, message.message_id)
    edit_message('Сколько рублей вы потратили?', message.chat.id)
    type_expenses = message.text[:26]
    pre_com = 'Расход'


@bot.message_handler(func=lambda message: True)
def other_message(message):
    global pre_com
    if pre_com == 'MESSAGE':
        bot.delete_message(message.chat.id, message.message_id)
        edit_message('Пожалуйста, пишите сообщения только тогда, когда вас просят :)', message.chat.id, markup=True)


def insert_income(message, money):
    with sqlite3.connect('data.db') as cursor:
        cursor.execute("INSERT INTO Income (user_id, income_amount, income_date) "
                       "VALUES (?, ?, STRFTIME('%Y-%m-%d', datetime('now')));",
                       (message.from_user.id, money))
    bot.delete_message(message.chat.id, message.message_id)
    edit_message('Доход успешно добавлен.\nЧто вы хотите выбрать?', message.chat.id, markup=True)


def insert_expense(message, money):
    with sqlite3.connect('data.db') as cursor:
        cursor.execute("INSERT INTO Expenses (user_id, expense_amount, expense_date, expense_type)"
                       " VALUES (?, ?, STRFTIME('%Y-%m-%d', datetime('now')), ?);",
                       (message.from_user.id, money, type_expenses))
    bot.delete_message(message.chat.id, message.message_id)
    edit_message('Расход успешно добавлен.\nЧто вы хотите выбрать?', message.chat.id, markup=True)


@bot.callback_query_handler(func=lambda message: message.data in ('cancel_inc', 'cancel_exp'))
def cancel_income(message):
    global pre_com
    pre_com = 'MESSAGE'
    with sqlite3.connect('data.db') as cursor:
        if message.data == 'cancel_inc':
            commands = """
                 DELETE FROM Income
                 WHERE Income.user_id = (?) AND
                 income_id = (SELECT MAX(income_id) FROM Income);
            """
        else:
            commands = """
                 DELETE FROM Expenses
                 WHERE Expenses.user_id = (?) AND
                 expense_id = (SELECT MAX(expense_id) FROM Expenses);
            """
        cursor.execute(commands, (message.from_user.id, ))
        result = cursor.execute('SELECT CHANGES();').fetchone()
        if result[0]:
            com = f'Последний {"расход" if message.data == "cancel_exp" else "доход"} успешно удалён.'
        else:
            com = f'{"Доходов" if message.data == "cancel_exp" else "Расходов"} больше не осталось.'
        try:
            edit_message(com, message.message.chat.id, markup=True)
        except telebot.apihelper.ApiTelegramException:
            pass


@bot.callback_query_handler(func=lambda message: message.data == 'income')
def income(message):
    global pre_com
    pre_com = 'Доход'
    edit_message('Сколько рублей вы заработали?', message.message.chat.id)


@bot.callback_query_handler(func=lambda message: message.data == 'expense')
def expense(message):
    global pre_com
    pre_com = 'MESSAGE'
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
    global pre_com
    pre_com = 'MESSAGE'
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
    edit_message("За какой период вы хотите узнать доход?", message.message.chat.id, markup=keyboard_)


@bot.callback_query_handler(func=lambda message: message.data == 'find_exp')
def find_expense(message):
    global pre_com
    pre_com = 'MESSAGE'
    keyboard_ = types.InlineKeyboardMarkup(row_width=3)
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
    edit_message("За какой период вы хотите узнать расход?", message.message.chat.id, markup=keyboard_)


@bot.callback_query_handler(func=lambda message: message.data in ('Питание', 'Одежда', 'Развлечения',
                                                                  'Образование', 'Квартплата', 'Спорт', 'Транспорт'))
def button_inline_type_expense(message):
    """Пользователь нажал кнопку типа расхода"""
    global pre_com, type_expenses
    pre_com = 'Расход'
    type_expenses = message.data
    edit_message('Сколько рублей вы потратили?', message.message.chat.id)


@bot.callback_query_handler(func=lambda message: message.data == 'Другое')
def button_inline_other(message):
    """Пользователь нажал на кнопку типа расхода Другое"""
    global pre_com, type_expenses
    pre_com = 'Другое'
    edit_message('Уточните, пожалуйста, тип расхода.\nДо <b>25</b> символов.', message.message.chat.id, parse='html')


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
                rows.append([f'{column_value[0]} руб.', column_value[1]])
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
                 SELECT Expenses.expense_amount, Expenses.expense_type, Expenses.expense_date 
                 FROM Users INNER JOIN Expenses
                 ON Users.user_id = Expenses.user_id
                 WHERE Users.user_id = (?) AND
                 CAST(JULIANDAY(STRFTIME('%Y-%m-%d', datetime('now'))) - JULIANDAY(expense_date) AS INTEGER) = (?);
            """
            result = cursor.execute(commands, (message.from_user.id, int(message.data[1:])))
        else:
            commands = """
                SELECT Expenses.expense_amount, Expenses.expense_type, Expenses.expense_date 
                FROM Users INNER JOIN Expenses
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
                rows.append([f'{column_value[0]} руб.', column_value[1], column_value[2]])
            table = tabulate(rows, headers="firstrow")
            bot.edit_message_text(f'{table}\n\nЧто вы хотите выбрать?', message.message.chat.id, message_id_inline,
                                  reply_markup=keyboard)
        else:
            bot.edit_message_text('У вас нет расходов за данный период.\nЧто вы хотите выбрать?',
                                  message.message.chat.id, message_id_inline, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda message: message.data in ('othere', 'otheri'))
def button_find_expense_or_income_other(message):
    global pre_com
    pre_com = message.data
    com = f'Уточните, пожалуйста, за какую дату вы хотите узнать {"расход" if message.data == "othere" else "доход"}?\n' \
          f'Вводите дату в формате YYYY-MM-DD'
    edit_message(com, message.message.chat.id)


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
