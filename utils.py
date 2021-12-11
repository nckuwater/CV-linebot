import os

from linebot import LineBotApi, WebhookParser
from linebot.models import MessageEvent, TextMessage, TextSendMessage

channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)


def send_text_message(reply_token, text):
    line_bot_api = LineBotApi(channel_access_token)
    line_bot_api.reply_message(reply_token, TextSendMessage(text=text))

    return "OK"


def save_event_image(event, fext='jpg'):
    line_bot_api = LineBotApi(channel_access_token)
    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)
    content_path = f"static/images/{message_id}.{fext}"
    with open(os.path.abspath(content_path), "wb") as f:
        for chunk in message_content.iter_content():
            f.write(chunk)
    return content_path


"""
def send_image_url(id, img_url):
    pass

def send_button_message(id, text, buttons):
    pass
"""
