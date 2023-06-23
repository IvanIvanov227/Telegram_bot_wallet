import telebot
import openai
from telebot import types
import sqlite3

# Состояния пользователя
states = None
# Предыдущее сообщение
pre_com = None
# Тип расхода
type_expenses = None
bot = telebot.TeleBot('6289799568:AAFArEfu7yepVGeseGNzwEdAC8F44H2Aiak')
openai_token = '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'
channel_id = '123'
openai.api_key = openai_token


# Команда "/start"
@bot.message_handler(commands=['start', 'hello'])
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
    Если хочешь добавить свои расходы, то нажми на кнопку <b>Доход</b> и сумму.\n
    Если хочешь добавить свои доходы, то нажми на кнопку <b>Расход</b> и сумму.\n
    Если хочешь посмотреть свои расходы, то нажми на кнопку <b>Узнать расход</b>.\n
    Если хочешь посмотреть свои доходы, то нажми на кнопку <b>Узнать Доход</b>.\n
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


@bot.message_handler(func=lambda message: True)
def button(message):
    global states
    global pre_com
    # Предполагается, что пользователь нажал кнопку из обычной клавиатуры
    states = 'BUTTON_MAIN'
    if message.text == 'Расход':
        pre_com = 'Расход'
        try:
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

        except sqlite3.Error as e:
            bot.send_message(message.chat.id, f"Ошибка при добавлении расхода: {e}")

    elif message.text == 'Доход':
        pre_com = 'Доход'


    elif message.text == 'Узнать расход':
        pre_com = 'Узнать расход'

        with sqlite3.connect('data.db') as cursor:
            commands = """
                    SELECT Expenses.expense_amount, Expenses.expense_type, Expenses.expense_date 
                    FROM Users INNER JOIN Expenses
                    ON Users.user_id = Expenses.user_id
                    WHERE Users.user_id = (?);
                    """
            result = cursor.execute(commands, (message.from_user.id,))
            column_values = result.fetchall()
            total_expenses = column_values[0] if column_values else 0
        bot.send_message(message.chat.id, f'{column_values}')

    elif message.text == 'Узнать доход':
        pre_com = 'Узнать доход'

        with sqlite3.connect('data.db') as cursor:
            commands = """
                 SELECT Income.income_amount, Income.income_date FROM Users INNER JOIN Income
                 ON Users.user_id = Income.user_id
                 WHERE Users.user_id = (?);
            """
            result = cursor.execute(commands, (message.from_user.id,))
            column_values = result.fetchall()
            total_expenses = column_values[0] if column_values else 0
        bot.send_message(message.chat.id, f'{column_values}')

    else:
        try:
            money = float(message.text)

            if pre_com == 'Доход':
                with sqlite3.connect('data.db') as cursor:

                    cursor.execute("INSERT INTO Income (user_id, income_amount, income_date) "
                                   "VALUES (?, ?,STRFTIME('%Y-%m-%d %H:%M:%S', datetime('now')));",
                                   (message.from_user.id, money))

                bot.send_message(message.chat.id, "Доход успешно добавлен.")

            elif pre_com == 'Расход':
                with sqlite3.connect('data.db') as cursor:

                    cursor.execute("INSERT INTO Expenses (user_id, expense_amount, expense_date, expense_type)"
                                   " VALUES (?, ?, STRFTIME('%Y-%m-%d %H:%M:%S', datetime('now')), ?);",
                                   (message.from_user.id, money, type_expenses))

                bot.send_message(message.chat.id, "Расход успешно добавлен.")

        except ValueError:
            bot.send_message(message.chat.id, 'Вы неправильно ввели число.\nПожалуйста, следуйте инструкции :)')


@bot.message_handler(func=lambda message: "доход" in message.text.lower())
def button_income(message):
    bot.send_message(message.chat.id, "Сколько вы заработали?")

@bot.message_handler(func=lambda message: "доход" in message.text.lower())
def button_income(message):
    bot.send_message(message.chat.id, "Сколько вы заработали?")
@bot.callback_query_handler(func=lambda call: True)
def button_inline(message):
    global states, type_expenses
    # Пользователь нажал кнопку INLINE клавиатуры
    states = 'INLINE'
    bot.send_message(message.message.chat.id, 'Сколько вы потратили?')
    type_expenses = message.data


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
