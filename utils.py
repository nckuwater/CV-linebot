import os

from dotenv import load_dotenv
import requests
from linebot import LineBotApi, WebhookParser
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage

load_dotenv()
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)

if channel_access_token is None:
    print('utils cannot load channel_access_token')
    exit(-1)
line_bot_api = LineBotApi(channel_access_token)
base_url = os.getenv('base_url')


def send_text_message(reply_token, text):
    line_bot_api.reply_message(reply_token, TextSendMessage(text=text))
    return "OK"


def get_message_content(message_id):
    header_data = {'Authorization': 'Bearer ' + channel_access_token}
    response = requests.get(f'https://api-data.line.me/v2/bot/message/{message_id}/content', headers=header_data)
    return response


def save_event_image(event, fext='jpg'):
    message_id = event.message.id
    message_content = get_message_content(message_id)
    content_path = f"./static/images/{message_id}.{fext}"
    with open(os.path.abspath(content_path), "wb") as f:
        for chunk in message_content.iter_content():
            f.write(chunk)
    return content_path


def send_image(reply_token, image_url):
    line_bot_api.reply_message(reply_token, ImageSendMessage(
        original_content_url=image_url,
        preview_image_url=image_url))


def send_payload(reply_token, payload):
    line_bot_api.reply_message(reply_token, payload)


def get_text_send_message(text):
    return TextSendMessage(text=text)


def get_image_send_message(image_url):
    return ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)


def resolve_static_url(path):
    return base_url + '/' + path


"""
def send_image_url(id, img_url):
    pass

def send_button_message(id, text, buttons):
    pass
"""
