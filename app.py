import os
import sys

from flask import Flask, jsonify, request, abort, send_file
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookParser, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage

from fsm import TocMachine
from utils import send_text_message

load_dotenv()


def new_machine():
    return TocMachine(
        states=["initial", "remove_bg", "gray_scale", "remove_bg_processing_img",
                "remove_bg_wait_user_revise"],
        transitions=[
            {
                "trigger": "trans",
                "source": "initial",
                "dest": "remove_bg",
                "conditions": "is_going_to_remove_bg",
            },
            {
                "trigger": "trans",
                "source": "initial",
                "dest": "gray_scale",
                "conditions": "is_going_to_gray_scale",
            },
            {
                "trigger": "trans",
                "source": ["remove_bg", "gray_scale"],
                "dest": "initial",
                "conditions": "is_going_to_initial",
            },
            {
                "trigger": "trans_image",
                "source": "remove_bg",
                "dest": "remove_bg_processing_img",
            },
            # from revise to processing, reprocess with user input number.
            {
                "trigger": "trans",
                "source": "remove_bg_wait_user_revise",
                "dest": "remove_bg_wait_user_revise",
                "conditions": "is_going_to_remove_bg_processing_img"
            }
        ],
        initial="initial",
        auto_transitions=False,
        show_conditions=True,
    )


global_machine = new_machine()
user_machines = {}  # {user: machine}
app = Flask(__name__, static_url_path="")

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)
if channel_secret is None:
    print("Specify LINE_CHANNEL_SECRET as environment variable.")
    sys.exit(1)
if channel_access_token is None:
    print("Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)
handler = WebhookHandler(channel_secret)


def get_user_machine(user_id):
    global user_machines
    machine = user_machines.get(user_id)
    if machine is None:
        machine = new_machine()
        user_machines[user_id] = machine
    return machine


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        print('SignatureError')
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            print("received")
            print(event)
            continue
        if not isinstance(event.message, TextMessage):
            continue

        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.message.text)
        )

    return "OK"


@app.route("/webhook", methods=["POST"])
def webhook_handler():
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    # parse webhook body
    try:
        handler.handle(body, signature)
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        pass
        # if not isinstance(event, MessageEvent):
        #     continue
        # if not isinstance(event.message, TextMessage):
        #     continue
        # if not isinstance(event.message.text, str):
        #     continue
        # user_id = event.source.userId
        # machine = get_user_machine(user_id)
        # print(f"\nFSM STATE: {machine.state}")
        # print(f"REQUEST BODY: \n{body}")
        # response = machine.trans(event)
        # if response is False:
        #     send_text_message(event.reply_token, "Not Entering any State")

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    machine = get_user_machine(user_id)
    print(f"\nFSM STATE: {machine.state}")
    print('message:', event.message.text)
    response = machine.trans(event)
    if response is False:
        send_text_message(event.reply_token, f"Not Entering any State: {machine.state}")


@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    user_id = event.source.user_id
    machine = get_user_machine(user_id)
    print(f"\nFSM STATE: {machine.state}")
    print('message:', event.message.text)
    response = machine.trans_image(event)
    if response is False:
        send_text_message(event.reply_token, f"Not Entering any State: {machine.state}")


@app.route("/show-fsm", methods=["GET"])
def show_fsm():
    global_machine.get_graph().draw("fsm.png", prog="dot", format="png")
    return send_file("fsm.png", mimetype="image/png")


if __name__ == "__main__":
    port = os.environ.get("PORT", 8000)
    app.run(host="0.0.0.0", port=port, debug=True)
