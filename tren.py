import telebot

bot = telebot.TeleBot('6289799568:AAFArEfu7yepVGeseGNzwEdAC8F44H2Aiak')


def my_decorator(func):
    def wrapper(message):
        bot.send_message(message.chat.id, 'Привет! Напиши мне что-нибудь.')
        bot.register_next_step_handler(message, func)  # Регистрация обработчика следующего шага
    return wrapper


@my_decorator
def process_user_response(message):
    user_response = message.text
    bot.send_message(message.chat.id, f'Вы написали: {user_response}')

bot.polling(none_stop=True)
# if message.data == 'food':
    #     pass
    # if message.data == 'clothes':
    #     pass
    # if message.data == 'transport':
    #     pass
    # if message.data == 'sport':
    #     pass
    # if message.data == 'rent':
    #     pass
    # if message.data == 'education':
    #     pass
    # if message.data == 'entertainments':
    #     pass
    # if message.data == 'other':
    #     pass
