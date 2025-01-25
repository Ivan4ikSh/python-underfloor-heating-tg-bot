import telebot
from utils import custom_print
import time
from config import MASTER_API_TOKEN

class MasterBot:
    def __init__(self):
        self.master_bot = telebot.TeleBot(MASTER_API_TOKEN)
        self.master_chat_id = 8171869512

    def run(self):
        @self.master_bot.message_handler(commands=['start'])
        def start(message):
            self.master_chat_id = message.chat.id
            self.master_bot.send_message(message.chat.id, f"ID чата: {self.master_chat_id}")

        while True:
            try:
                self.master_bot.polling(non_stop=True)
            except Exception as e:
                custom_print(f"Ошибка: {e}")
                time.sleep(10)
                continue

        @self.master_bot.message_handler(commands=['info'])
        def start(message):
            self.master_bot.send_message(message.chat.id, message)

        @self.master_bot.message_handler(content_types=['text'])
        def handle_text(message):
            if message.chat.id == self.master_chat_id:
                custom_print(f"Получено сообщение от клиентского бота:\n{message.text}")

        while True:
            try:
                self.master_bot.polling(non_stop=True)
            except Exception as e:
                custom_print(f"Ошибка: {e}")
                time.sleep(10)
                continue
