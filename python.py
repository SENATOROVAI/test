import requests
from bs4 import BeautifulSoup
import sqlite3
import traceback
import logging
import time


logging.basicConfig(filename='debug.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

headers = {
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# Создание сессии 
session = requests.Session()


def create_table(conn):
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS processed_jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, job_link TEXT UNIQUE, post_date TEXT, job_response TEXT, title_text TEXT)")


def save_processed_job(conn, job_link, post_date, job_response, title_text):
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO processed_jobs (job_link, post_date,job_response, title_text) VALUES (?, ?,?, ?)", (job_link, post_date, job_response, title_text))
    conn.commit()
    send_notification(f"{post_date},{job_response}\n\n{job_link}")


def load_processed_jobs():
    conn = sqlite3.connect('processed_jobs_free.db')
    cursor = conn.cursor()
    sql = "SELECT id, job_link, post_date, job_response, title_text FROM processed_jobs ORDER BY id DESC LIMIT 50"
    sql_exec = cursor.execute(sql).fetchall()
    processed_jobs = []
    for row in sql_exec:
        job = {
            "id": row[0],
            "job_link": row[1],
            "post_date": row[2],
            "job_response": row[3],
            "title_text": row[4]
        }
        processed_jobs.append(job)
    return processed_jobs


# Подключение к базе данных SQLite
conn = sqlite3.connect('processed_jobs_free.db')

# Создание таблицы, если она не существует
create_table(conn)


# Функция для отправки уведомления в Telegram
def send_notification(message):
    # data = load_processed_jobs()
    # for dcit_ in data:
    #     link = dcit_["job_link"]
    #     time_ = dcit_["post_date"]
    #     direction = dcit_["job_response"]
    #     message = f"{time_}, {direction}\n\n{link}"
    # bot = telegram.Bot(token="6248467563:AAFposQd6a0jAyWCAfYcevGoLFy4KBJIaL8")
        time.sleep(1)
    # bot.send_message(chat_id="618781484", text=message)
        url = f"https://api.telegram.org/bot6248467563:AAFposQd6a0jAyWCAfYcevGoLFy4KBJIaL8/sendMessage?chat_id=618781484&text={message}"
        session.get(url, headers=headers)
    
    
def extract_post_date(item):
    post_date_element = item.find(class_="col-sm-4 text-sm-end")
    if post_date_element is not None:
        span_element = post_date_element.find("span", {"data-bs-toggle": "tooltip"})
        if span_element is not None:
            title = span_element.get("title")
            title_time = span_element.text
            return title, title_time


while True:
    
    try:
        # search_query = input("Enter the word to search: ").lower()  # Accept user input
        full_link = []  
        processed_jobs = load_processed_jobs()
        for dict_ in processed_jobs:
            full_link.append(dict_['job_link'])

        for page in range(1, 50):
            print(page)
            url = f"https://www.weblancer.net/jobs/?page={page}"
            html = session.get(url, headers=headers).text
            soup = BeautifulSoup(html, "lxml")
            job_items = soup.find_all(class_="row click_container-link set_href")
        
            for item in job_items:
                job_link = item.find("div", class_="title").find("a")["href"]
                job_response = item.find(class_="col-sm-8 text-muted dot_divided text_field d-sm-flex").text.strip() if item.find(class_="col-sm-8 text-muted dot_divided text_field d-sm-flex").text is not None else "нет категории"
                
                if job_link is not None:
                    title_text = item.find("div", class_="title").text.lower().strip() if item.find("div", class_="title").text.lower() else ""
                    description_element = item.find("div", class_="collapse").text if item.find("div", class_="collapse") else ""
             
                    # print(title_text)
                    favorite_task = ["парсер","парсинг","спарсить", "python", "пайтон", "питон", "flask", "django", "fastapi"]
                    # if any(word in title_text for word in favorite_task):
                    if (title_text in favorite_task) or (description_element in favorite_task):
                        job_link = "https://www.weblancer.net/"+job_link
                        post_date, title_time = extract_post_date(item)
                        # print(title_time)
                        
                        if job_link not in full_link:
                            save_processed_job(conn, job_link, title_time, job_response, title_text)
                         
            time.sleep(1)
        time.sleep(60)

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        traceback.print_exc()
        # Задержка в 10 минут перед повторной попыткой
conn.close()


