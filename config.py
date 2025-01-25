import json
# Константы
API_TOKEN = None
BACKUP_PASSWORD = None
ALLOWED_USERS = []
BOT_MESSAGES_FILE = 'bot-messages-lib.json'

# Загрузка данных из JSON
def load_config(file_path: str) -> dict:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Ошибка загрузки данных: {e}")
        return {}

# Загрузка данных
config_data = load_config(BOT_MESSAGES_FILE)
app_data = config_data.get('appdata', [])
allowed_users = [user['tag'] for user in config_data.get('allowed_users', [])]

# Установка констант
CLIENT_API_TOKEN = app_data[0]['data']
MASTER_API_TOKEN = app_data[2]['data']
BACKUP_PASSWORD = app_data[1]['data']
ALLOWED_USERS = allowed_users
