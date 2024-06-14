import json
import logging
import os
import sys

import requests
from bs4 import BeautifulSoup

# ログの設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

line_notify_token = os.getenv("LINE_NOTIFY_TOKEN")
url = os.getenv("URL")

# ユーザーエージェントを設定
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


# 設定ファイルを読み込む関数
def load_config(file_path):
    with open(file_path, "r") as config_file:
        config = json.load(config_file)
    return config


# データを取得する関数
def fetch_data(url):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        logging.info(f"Successfully accessed {url}")
        return response.content
    except requests.exceptions.RequestException as e:
        logging.error(f"Error accessing {url}: {e}")
        return None


# データを解析する関数
def parse_data(content, target_class, condition):
    soup = BeautifulSoup(content, "html.parser")
    result_count_span = soup.find("span", class_="f-list-menu__bold")
    if result_count_span.text == "0件のうち、0件を表示":
        logging.info("No results found.")
        return []
    
    # 1件以上の場合はリストの内容を取得
    sections = soup.find_all("section", class_="f-list-card")
    # Iterate through each section to extract the required details
    hotels = []

    for section in sections:
        hotel = {}
        
        # Extract the plan name
        plan_name = section.find('h2', class_='f-list-card-name')
        if plan_name:
            hotel['plan_name'] = plan_name.text.strip()
        
        # Extract the room details
        room_details = section.find('p', class_='f-list-card-room')
        if room_details:
            hotel['room_details'] = room_details.text.strip()
        
        # Extract the image URL
        image = section.find('img', class_='kkrs-img-loading')
        if image and image.has_attr('data-src'):
            hotel['image_url'] = image['data-src']
        
        # Extract the date range
        date_range = section.find('span', class_='f-list-card-text-min__dark')
        if date_range:
            hotel['date_range'] = date_range.text.strip()
        
        # Extract the check-in and check-out times
        check_in_out = section.find_all('span', class_='f-list-card-text-min__dark')[1:3]
        if check_in_out:
            hotel['check_in'] = check_in_out[0].text.strip()
            hotel['check_out'] = check_in_out[1].text.strip()
        
        # Extract the price details
        price = section.find('p', class_='f-list-card-price')
        if price:
            hotel['total_price'] = price.text.strip()
        
        # Extract the individual price details
        individual_price = section.find_all('p', class_='f-list-card-text-min')[2]
        if individual_price:
            hotel['individual_price'] = individual_price.text.strip()
        
        hotels.append(hotel)
    
    logging.info(hotels)
    messages = []

    for hotel in hotels:
        message = (
            f"JTB URL: {url}\n"
            f"Plan Name: {hotel.get('plan_name')}\n"
            f"Room Details: {hotel.get('room_details')}\n"
            f"Image URL: {hotel.get('image_url')}\n"
            f"Date Range: {hotel.get('date_range')}\n"
            f"Check-In: {hotel.get('check_in')}\n"
            f"Check-Out: {hotel.get('check_out')}\n"
            f"Total Price: {hotel.get('total_price')}\n"
            f"Individual Price: {hotel.get('individual_price')}\n"
            "\n" + "-"*50 + "\n"
        )
        messages.append(message)
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
    formatted_message += "\n"+ url + "\n\n"
    return formatted_message

# メイン関数
def main():
    content = fetch_data(url=url)
    if content:
        messages = parse_data(content, None, "空室は現在見つかっていません。")
        if messages:
            send_line_notification(line_notify_token, messages)
            sys.exit(1)
        else:
            logging.info("No messages to send.")
    else:
        logging.error("Failed to retrieve content.")
    sys.exit(0)


if __name__ == "__main__":
    main()
