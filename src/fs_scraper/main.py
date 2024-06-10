import json
import logging
import os

import requests
from bs4 import BeautifulSoup

# ログの設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

line_notify_token = os.getenv("LINE_NOTIFY_TOKEN")
url = os.getenv("URL")


# 設定ファイルを読み込む関数
def load_config(file_path):
    with open(file_path, "r") as config_file:
        config = json.load(config_file)
    return config


# データを取得する関数
def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        logging.info(f"Successfully accessed {url}")
        return response.content
    except requests.exceptions.RequestException as e:
        logging.error(f"Error accessing {url}: {e}")
        return None


# データを解析する関数
def parse_data(content, target_class, condition):
    soup = BeautifulSoup(content, "html.parser")
    target_divs = soup.find_all("div", style="overflow:auto; white-space: nowrap;")
    messages = []

    for div in target_divs:
        tables = div.find_all("table", class_="general")
        for table in tables:
            tbody = table.find("tbody")
            if tbody:
                rows = tbody.find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    row_data = [col.text.strip() for col in cols]
                    messages.append(row_data)
    
    target_divs = soup.find_all("div", style="overflow-x:auto; white-space: nowrap;")
    
    for div in target_divs:
        tables = div.find_all("table", class_="general")
        for table in tables:
            tbody = table.find("tbody")
            if tbody:
                rows = tbody.find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    row_data = [col.text.strip() for col in cols]
                    messages.append(row_data)
    if all(all(col == condition for col in row) for row in messages):
        messages = []
    return messages



def send_line_notification(token, message):
    headers = {"Authorization": "Bearer " + token}
    data = {"message": message}

    try:
        response = requests.post("https://notify-api.line.me/api/notify", headers=headers, data=data)
        response.raise_for_status()
        logging.info("Notification sent successfully")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send notification: {e}")
        logging.error(f"Response: {e.response.text}")


def format_messages(messages):
    formatted_message = ""
    for message in messages:
        formatted_message += "\n".join(message) + "\n\n"
    return formatted_message

# メイン関数
def main():
    content = fetch_data(url=url)
    if content:
        messages = parse_data(content, None, "空室は現在見つかっていません。")
        if messages:
            formatted_message = format_messages(messages)
            send_line_notification(line_notify_token, formatted_message)
            send_line_notification(line_notify_token, url)
        else:
            logging.info("No messages to send.")
    else:
        logging.error("Failed to retrieve content.")


if __name__ == "__main__":
    main()
