import telebot
from telebot import types
from utils import load_bot_data, custom_print
import signal
import sys
import time
from config import CLIENT_API_TOKEN, MASTER_API_TOKEN, ALLOWED_USERS, BOT_MESSAGES_FILE
import requests

class ClientBot:
    def __init__(self):
        self.client_bot = telebot.TeleBot(CLIENT_API_TOKEN)
        self.sent_messages = []
        self.user_states = {}
        self.bot_data = load_bot_data(BOT_MESSAGES_FILE)
        self.bot_messages = self.bot_data.get('bot_messages', [])
        self.order_messages = self.bot_data.get('order', [])

    def send_welcome(self, message):
        markup = types.InlineKeyboardMarkup()
        create_order_btn = types.InlineKeyboardButton(text="Оставить заявку", callback_data="create_order")
        about_btn = types.InlineKeyboardButton(text="O нас", callback_data="about")
        contacts_btn = types.InlineKeyboardButton(text="Контакты", callback_data="contacts")

        markup.add(create_order_btn)
        markup.row(about_btn, contacts_btn)

        welcome_text = self.bot_messages[0]['text'].format(name=message.chat.first_name)
        sent_message = self.client_bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')
        self.sent_messages.append(sent_message.message_id)

    def handle_order(self, message):
        markup = types.InlineKeyboardMarkup()
        yes_btn = types.InlineKeyboardButton(text="Да", callback_data="continue_order")
        no_btn = types.InlineKeyboardButton(text="Нет", callback_data="cancel_order")
        markup.row(yes_btn, no_btn)

        response_msg = self.client_bot.send_message(message.chat.id, self.bot_messages[2]['text'].format(name=message.chat.first_name), reply_markup=markup)
        self.sent_messages.append(response_msg.message_id)

    def send_message_to_bot(self, bot_token, chat_id, message):
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        params = {
            "chat_id": chat_id,
            "text": message
        }
        response = requests.post(url, params=params)
        return response.json()

    def send_order_to_master(self, order_data):
        master_chat_id = 7975798590
        message_text = (
            f"Имя: {order_data['name']}\n"
            f"Telegram: {order_data['tg']}\n"
            f"Дата: {order_data['date']}\n"
            f"Город: {order_data['city']}\n"
            f"Адрес: {order_data['address']}\n"
            f"Телефон: {order_data['phone']}\n"
            f"Комментарий: {order_data['comment']}"
        )
        try:
            self.send_message_to_bot(MASTER_API_TOKEN, master_chat_id, message_text)
        except telebot.apihelper.ApiTelegramException as e:
            custom_print(f"Ошибка при отправке сообщения: {e}")

    def callback_query(self, call):
        user_id = call.from_user.id
        if call.data == "create_order":
            self.handle_order(call.message)
        elif call.data == "continue_order":
            self.ask(call.message, self.order_messages[0]['text'], self.order_messages[0]['state'])
        elif call.data == "cancel_order":
            self.start(call.message)
        elif call.data == "about":
            self.handle_info(call.message)
        elif call.data == "contacts":
            self.handle_contacts(call.message)
        elif call.data == "main_menu":
            self.start(call.message)
        elif call.data == "confirm_order":
            # Логика подтверждения заказа
            name = self.user_states[user_id]["name"]
            city = self.user_states[user_id]["city"]
            address = self.user_states[user_id]["address"]
            date = self.user_states[user_id]["date"]
            phone = self.user_states[user_id]["phone"]
            comment = self.user_states[user_id]["comment"]

            # Отправка сообщения пользователю
            self.client_bot.send_message(call.message.chat.id, "Заявка принята в обработку, скоро мастер с вами свяжется для уточнения деталей.")

            # Вывод данных о заявке в консоль
            custom_print(f"Создана заявка:\n{name}\n{city}\n{date}\nАдрес: {address}\nТелефон: {phone}\nКомментарий:\n{comment}")

            order_data = {
                "tg": "@"+call.from_user.username,
                "name": self.user_states[user_id]["name"],
                "city": self.user_states[user_id]["city"],
                "date": self.user_states[user_id]["date"],
                "address": self.user_states[user_id]["address"],
                "phone": self.user_states[user_id]["phone"],
                "comment": self.user_states[user_id]["comment"]
            }
            self.send_order_to_master(order_data)
            # Возвращаемся в главное меню
            self.start(call.message)

        elif call.data == "edit_order":
            self.ask(call.message, self.order_messages[0]['text'], self.order_messages[0]['state'])
            pass

        # Удаляем предыдущие сообщения, кроме последнего
        for msg_id in self.sent_messages[:-1]:
            try:
                self.client_bot.delete_message(call.message.chat.id, msg_id)
            except telebot.apihelper.ApiTelegramException as e:
                if e.result_json['description'] == 'Bad Request: message to delete not found':
                    custom_print(f"Сообщение с ID {msg_id} не найдено. Пропускаем.")
                else:
                    custom_print(f"Не удалось удалить сообщение с ID {msg_id}: {e}")

        # Очищаем список идентификаторов, оставляя только последнее сообщение
        self.sent_messages.clear()
        self.sent_messages.append(call.message.message_id)

        try:
            self.client_bot.delete_message(call.message.chat.id, call.message.message_id)
        except telebot.apihelper.ApiTelegramException as e:
            if e.result_json['description'] == 'Bad Request: message to delete not found':
                custom_print(f"Сообщение с ID {call.message.message_id} не найдено. Пропускаем.")
            else:
                custom_print(f"Не удалось удалить сообщение с ID {call.message.message_id}: {e}")

    def ask(self, message, msg, user_state):
        user_id = message.chat.id  # Получаем идентификатор пользователя
        if user_id not in self.user_states:
            self.user_states[user_id] = {
                "state": "",
                "name": "",
                "city": "",
                "date": "",
                "address": "",
                "phone": "",
                "comment": ""
            }
        self.user_states[user_id]["state"] = user_state
        response_msg = self.client_bot.send_message(message.chat.id, msg)
        self.sent_messages.append(response_msg.message_id)

    def confirm_order(self, message):
        # Извлечение данных из состояния пользователя
        user_id = message.from_user.id
        name = self.user_states.get(user_id, {}).get("name")
        city = self.user_states.get(user_id, {}).get("city")
        date = self.user_states.get(user_id, {}).get("date")
        address = self.user_states.get(user_id, {}).get("address")
        phone = self.user_states.get(user_id, {}).get("phone")
        comment = self.user_states.get(user_id, {}).get("comment")

        confirmation_msg = (
            f"Пожалуйста, проверьте ваши данные:\n"
            f"<b>Имя</b>: {name}\n"
            f"<b>Город</b>: {city}\n"
            f"<b>Адрес</b>: {address}\n"
            f"<b>Время</b>: {date}\n"
            f"<b>Телефон</b>: {phone}\n"
            f"<b>Комментарий</b>: {comment}\n"
            "\nВсе ли верно?"
        )

        markup = types.InlineKeyboardMarkup()
        confirm_btn = types.InlineKeyboardButton(text="Да", callback_data="confirm_order")
        edit_btn = types.InlineKeyboardButton(text="Нет", callback_data="edit_order")
        markup.row(confirm_btn, edit_btn)

        response_msg = self.client_bot.send_message(message.chat.id, confirmation_msg, reply_markup=markup, parse_mode='HTML')
        self.sent_messages.append(response_msg.message_id)
        self.user_states[user_id]["state"] = "none"

    def handle_text(self, message):
        user_id = message.from_user.id

        if user_id not in self.user_states:
            self.user_states[user_id] = {
                "state": "enter_name",
                "name": "",
                "city": "",
                "date": "",
                "address": "",
                "phone": "",
                "comment": ""
            }

        if self.user_states[user_id]["state"] == self.order_messages[0]['state']:
            self.user_states[user_id]["name"] = message.text
            self.ask(message, self.order_messages[1]['text'], self.order_messages[1]['state'])

        elif self.user_states[user_id]["state"] == self.order_messages[1]['state']:
            self.user_states[user_id]["city"] = message.text
            self.ask(message, self.order_messages[2]['text'], self.order_messages[2]['state'])

        elif self.user_states[user_id]["state"] == self.order_messages[2]['state']:
            self.user_states[user_id]["address"] = message.text
            self.ask(message, self.order_messages[3]['text'], self.order_messages[3]['state'])

        elif self.user_states[user_id]["state"] == self.order_messages[3]['state']:
            self.user_states[user_id]["phone"] = message.text
            self.ask(message, self.order_messages[4]['text'], self.order_messages[4]['state'])

        elif self.user_states[user_id]["state"] == self.order_messages[4]['state']:
            self.user_states[user_id]["date"] = message.text
            self.ask(message, self.order_messages[5]['text'], self.order_messages[5]['state'])

        elif self.user_states[user_id]["state"] == self.order_messages[5]['state']:
            self.user_states[user_id]["comment"] = message.text
            # Вызываем метод подтверждения данных
            self.confirm_order(message)

        # Обработка других текстовых сообщений
        if message.text == "Главное меню":
            self.user_states[user_id]["state"] = "none"
            self.start(message)

    def handle_contacts(self, message):
        markup = types.InlineKeyboardMarkup()
        main_btn = types.InlineKeyboardButton(text="Главное меню", callback_data="main_menu")
        markup.add(main_btn)

        response_msg = self.client_bot.send_message(message.chat.id, "Текст, по всем вопросам обращаться по следующим контактам:\nПочта: shupaevi000@gmail.com\nПоддержка: @IvanBusy", reply_markup=markup)
        self.sent_messages.append(response_msg.message_id)

    def handle_info(self, message):
        markup = types.InlineKeyboardMarkup()
        main_btn = types.InlineKeyboardButton(text="Главное меню", callback_data="main_menu")
        markup.add(main_btn)

        response_msg = self.client_bot.send_message(message.chat.id, self.bot_messages[1]['text'], reply_markup=markup, parse_mode='HTML')
        self.sent_messages.append(response_msg.message_id)

    def backup(self, message):
        custom_print(f"Пользователь {message.from_user.username} получил бэкап данных")
        self.client_bot.send_message(message.chat.id, "Бэкап создан успешно.")

    def start(self, message):
        for msg_id in self.sent_messages:
            try:
                self.client_bot.delete_message(message.chat.id, msg_id)
            except Exception as e:
                custom_print(f"Не удалось удалить сообщение с ID {msg_id}: {e}")

        self.sent_messages.clear()
        self.send_welcome(message)

    def backup_command(self, message):
        if message.from_user.username in ALLOWED_USERS:
            self.client_bot.send_message(message.chat.id, "Введите пароль:")
            self.user_states[message.from_user.id] = "enter_password"
        else:
            self.client_bot.send_message(message.chat.id, "У вас нет доступа к этой команде.")
            self.start(message)


    def run(self):
        @self.client_bot.message_handler(commands=['start'])
        def start(message):
            self.start(message)

        @self.client_bot.message_handler(commands=['backup'])
        def backup_command(message):
            self.backup_command(message)

        @self.client_bot.message_handler(content_types=['text'])
        def handle_text(message):
            self.handle_text(message)

        @self.client_bot.callback_query_handler(func=lambda call: True)
        def callback_query(call):
            self.callback_query(call)

        while True:
            try:
                self.client_bot.polling(non_stop=True)
            except Exception as e:
                custom_print(f"Ошибка: {e}")
                time.sleep(10)  # Ждем 10 секунд перед перезапуском
                continue

def signal_handler(sig, frame):
    custom_print('Выключение бота...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
