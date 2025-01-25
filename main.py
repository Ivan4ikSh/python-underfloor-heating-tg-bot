import threading
from client_bot import ClientBot
from master_bot import MasterBot

def run_client_bot():
    bot = ClientBot()
    bot.run()

def run_master_bot():
    m_bot = MasterBot()
    m_bot.run()

if __name__ == '__main__':
    client_thread = threading.Thread(target=run_client_bot)
    master_thread = threading.Thread(target=run_master_bot)

    client_thread.start()
    master_thread.start()

    client_thread.join()
    master_thread.join()
