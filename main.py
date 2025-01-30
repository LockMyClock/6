import requests
from bs4 import BeautifulSoup
import time
import logging
from telegram import Bot
from telegram.error import TelegramError

# Настройка логирования
logging.basicConfig(filename='habr_parser.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

# Настройка логирования в консоль
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logging.getLogger().addHandler(console_handler)

# URL страницы с новостями
url = "https://habr.com/ru/feed/"

# Задержка между запросами (в секундах)
delay = 2

# Токен вашего Telegram бота
TELEGRAM_BOT_TOKEN = "
# ID вашего Telegram канала
TELEGRAM_CHANNEL_ID = ""

# Имя файла для хранения отправленных ссылок
SENT_LINKS_FILE = "sent_links.txt"

# Создаем объект бота
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def send_telegram_message(message):
    try:
        bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message, parse_mode="HTML")
        logging.info("Сообщение успешно отправлено в Telegram!")
        print("Сообщение успешно отправлено в Telegram!")
        return True  # Успешная отправка
    except TelegramError as e:
        logging.error(f"Ошибка при отправке сообщения в Telegram: {e}")
        print(f"Ошибка при отправке сообщения в Telegram: {e}")
        return False  # Ошибка отправки


def load_sent_links():
    try:
        with open(SENT_LINKS_FILE, "r", encoding="utf-8") as f:
            links = [line.strip() for line in f]
            logging.info(f"Загружено {len(links)} отправленных ссылок из файла")
            return links
    except FileNotFoundError:
        logging.info(f"Файл {SENT_LINKS_FILE} не найден. Создается новый.")
        print(f"Файл {SENT_LINKS_FILE} не найден. Создается новый.")
        return []
    except Exception as e:
        logging.error(f"Ошибка при загрузке списка отправленных ссылок: {e}")
        print(f"Ошибка при загрузке списка отправленных ссылок: {e}")
        return []


def save_sent_links(links):
    try:
        with open(SENT_LINKS_FILE, "w", encoding="utf-8") as f:
            for link in links:
                f.write(link + "\n")
        logging.info(f"Сохранено {len(links)} отправленных ссылок в файл.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении списка отправленных ссылок: {e}")
        print(f"Ошибка при сохранении списка отправленных ссылок: {e}")


def check_and_send_new_news():
    try:
        response = requests.get(url)
        response.raise_for_status()
        html = response.text

        soup = BeautifulSoup(html, 'html.parser')
        news_items = soup.find_all('li', class_='posts-list__item_article')

        if not news_items:
            logging.warning("Нет новостей на странице.")
            print("Нет новостей на странице.")
            return

        sent_links = load_sent_links()
        new_links = []

        logging.info(f"Найдено новостей на странице: {len(news_items)}")
        print(f"Найдено новостей на странице: {len(news_items)}")

        for item in news_items:
            title_element = item.find('a', class_='post__title_link')
            if not title_element:
                logging.warning("Заголовок не найден.")
                print("Заголовок не найден.")
                continue

            title = title_element.text.strip()
            link = title_element['href']

            description_element = item.find('div', class_='post__body post__body_crop')
            description_paragraph = None
            if description_element:
                first_paragraph = description_element.find('p')
                if first_paragraph:
                    description_paragraph = first_paragraph.text.strip()
            description = description_paragraph or "Описание не найдено"


            if link not in sent_links:
                message = f"<b>{title}</b>\n\n{description}\n\n<a href='{link}'>Читать полностью</a>"
                logging.info(f"Отправляется новость: {title} - {link}")
                print(f"Отправляется новость: {title} - {link}")
                if send_telegram_message(message):  # Проверяем результат отправки
                    new_links.append(link)
                time.sleep(delay)
            else:
                logging.info(f" - {title} - Уже отправлено")
                print(f" - {title} - Уже отправлено")

        save_sent_links(sent_links + new_links)

    except requests.exceptions.RequestException as e:
        logging.exception(f"Ошибка запроса: {e}")
        print(f"Ошибка запроса: {e}")
    except Exception as e:
        logging.exception(f"Произошла непредвиденная ошибка: {e}")
        print(f"Произошла непредвиденная ошибка: {e}")


if __name__ == "__main__":
    while True:  # Бесконечный цикл
        check_and_send_new_news()
        time.sleep(5)  # Пауза между итерациями 10 минут (600 секунд)
