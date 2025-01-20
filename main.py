import telebot
import json
from telebot import types
import time
import datetime
import signal
import sys

# Константы
BOT_MESSAGES_FILE = 'bot-messages-lib.json'
API_TOKEN = None
BACKUP_PASSWORD = None
ALLOWED_USERS = []

# Загрузка данных из JSON
def load_bot_data(file_path: str) -> dict:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Ошибка загрузки данных: {e}")
        return {}

# Загрузка данных
bot_data = load_bot_data(BOT_MESSAGES_FILE)
bot_messages = bot_data.get('bot_messages', [])
app_data = bot_data.get('appdata', [])
allowed_users = [user['tag'] for user in bot_data.get('allowed_users', [])]

# Установка констант
API_TOKEN = app_data[0]['data']
BACKUP_PASSWORD = app_data[1]['data']
ALLOWED_USERS = allowed_users

# Инициализация бота
client_bot = telebot.TeleBot(API_TOKEN)

# Список для хранения идентификаторов сообщений
sent_messages = []

# Словарь для хранения состояний пользователей
user_states = {}
def custom_print(text: str):
    moscow_tz = datetime.timezone(datetime.timedelta(hours=3))
    current_time = datetime.datetime.now(moscow_tz)
    print("["+current_time.strftime("%H:%M:%S")+"] "+text)

# Функция для отправки приветственного сообщения
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    create_order_btn = types.InlineKeyboardButton(text="Оставить заявку", callback_data="create_order")
    about_btn = types.InlineKeyboardButton(text="O нас", callback_data="about")
    contacts_btn = types.InlineKeyboardButton(text="Контакты", callback_data="contacts")

    markup.add(create_order_btn)
    markup.row(about_btn, contacts_btn)

    welcome_text = bot_messages[0]['text'].format(name=message.chat.first_name)
    sent_message = client_bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')
    sent_messages.append(sent_message.message_id)

# Функция для обработки заявки
def handle_order(message):
    markup = types.InlineKeyboardMarkup()
    main_btn = types.InlineKeyboardButton(text="Главное меню", callback_data="main_menu")
    markup.add(main_btn)

    response_msg = client_bot.send_message(message.chat.id, "Форма заявки на установку/ремонт теплого пола",
                                           reply_markup=markup)
    sent_messages.append(response_msg.message_id)

# Функция для обработки контактов
def handle_contacts(message):
    markup = types.InlineKeyboardMarkup()
    main_btn = types.InlineKeyboardButton(text="Главное меню", callback_data="main_menu")
    markup.add(main_btn)

    response_msg = client_bot.send_message(message.chat.id,
                                           "Текст, по всем вопросам обращаться по:\nпочта проекта, тг поддержки",
                                           reply_markup=markup)
    sent_messages.append(response_msg.message_id)

# Функция для обработки информации о проекте
def handle_info(message):
    markup = types.InlineKeyboardMarkup()
    main_btn = types.InlineKeyboardButton(text="Главное меню", callback_data="main_menu")
    markup.add(main_btn)

    response_msg = client_bot.send_message(message.chat.id, bot_messages[1]['text'], reply_markup=markup, parse_mode='HTML')
    sent_messages.append(response_msg.message_id)

# Функция для создания бэкапа
def backup(message):
    custom_print("Бэкап создан")
    client_bot.send_message(message.chat.id, "Бэкап создан успешно.")

# Обработчик команды start
@client_bot.message_handler(commands=['start'])
def start(message):
    for msg_id in sent_messages:
        try:
            client_bot.delete_message(message.chat.id, msg_id)
        except Exception as e:
            custom_print(f"Не удалось удалить сообщение с ID {msg_id}: {e}")

    sent_messages.clear()
    send_welcome(message)

# Обработчик команды backup
@client_bot.message_handler(commands=['backup'])
def backup_command(message):
    if message.from_user.username in ALLOWED_USERS:
        client_bot.send_message(message.chat.id, "Введите пароль:")
        user_states[message.from_user.id] = "enter_password"
    else:
        client_bot.send_message(message.chat.id, "У вас нет доступа к этой команде.")
        start(message)

# Обработчик текстовых сообщений
@client_bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.from_user.id in user_states and user_states[message.from_user.id] == "enter_password":
        if message.text == BACKUP_PASSWORD:
            backup(message)
            user_states.pop(message.from_user.id)
            start(message)
        else:
            client_bot.send_message(message.chat.id, "Неправильный пароль. Попробуйте еще раз.")
    else:
        # Обработка других текстовых сообщений
        if message.text == "Главное меню":
            start(message)

# Обработчик callback-запросов
@client_bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "create_order":
        handle_order(call.message)
    elif call.data == "about":
        handle_info(call.message)
    elif call.data == "contacts":
        handle_contacts(call.message)
    elif call.data == "main_menu":
        start(call.message)

    # Удаляем предыдущие сообщения, кроме последнего
    for msg_id in sent_messages[:-1]:
        try:
            client_bot.delete_message(call.message.chat.id, msg_id)
        except telebot.apihelper.ApiTelegramException as e:
            if e.result_json['description'] == 'Bad Request: message to delete not found':
                custom_print(f"Сообщение с ID {msg_id} не найдено. Пропускаем.")
            else:
                custom_print(f"Не удалось удалить сообщение с ID {msg_id}: {e}")

    # Очищаем список идентификаторов, оставляя только последнее сообщение
    sent_messages.clear()
    sent_messages.append(call.message.message_id)

    try:
        client_bot.delete_message(call.message.chat.id, call.message.message_id)
    except telebot.apihelper.ApiTelegramException as e:
        if e.result_json['description'] == 'Bad Request: message to delete not found':
            custom_print(f"Сообщение с ID {call.message.message_id} не найдено. Пропускаем.")
        else:
            custom_print(f"Не удалось удалить сообщение с ID {call.message.message_id}: {e}")

def signal_handler(sig, frame):
    custom_print('Выключение бота...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    while True:
        try:
            client_bot.polling(non_stop=True)
        except Exception as e:
            custom_print(f"Ошибка: {e}")
            time.sleep(10)  # Ждем 10 секунд перед перезапуском
            continue
