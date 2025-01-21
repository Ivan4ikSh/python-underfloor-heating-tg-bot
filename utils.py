import json
import datetime

def load_bot_data(file_path: str) -> dict:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Ошибка загрузки данных: {e}")
        return {}

def custom_print(text: str):
    moscow_tz = datetime.timezone(datetime.timedelta(hours=3))
    current_time = datetime.datetime.now(moscow_tz)
    print("["+current_time.strftime("%H:%M:%S")+"] "+text)
