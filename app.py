import os
import sys

from flask import Flask, jsonify, request, abort, send_file
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookParser, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage

import utils
from fsm import TocMachine
from utils import send_text_message

from cairosvg import svg2png

load_dotenv()
states = ["initial", "show_state",
          "remove_bg", "remove_bg_processing_img", "remove_bg_wait_user_revise",
          "gray_scale", "gray_scale_process",
          "gaussian_blur_ask_kernel", "gaussian_blur_wait_image", "gaussian_blur"]


def new_machine():
    return TocMachine(
        states=states,
        transitions=[
            {
                "trigger": "trans",
                "source": "initial",
                "dest": "remove_bg",
                "conditions": "is_going_to_remove_bg",
            },
            {
                "trigger": "trans_image",
                "source": "remove_bg",
                "dest": "remove_bg_processing_img",  # send the result, then move to wait_user_revise
            },
            # from revise to processing, reprocess if user reply a number.
            # return to initial if user says ok.
            {
                "trigger": "goto_wait_user_revise",
                "source": "remove_bg_processing_img",
                "dest": "remove_bg_wait_user_revise",
            },
            {
                "trigger": "trans",
                "source": "remove_bg_wait_user_revise",
                "dest": "remove_bg_wait_user_revise",
                "conditions": "is_going_to_remove_bg_revise_img"
            },
            {
                "trigger": "trans",
                "source": "remove_bg_wait_user_revise",
                "dest": "initial",
                "conditions": "is_going_to_remove_bg_user_ok"
            },
            # Gray scale
            {
                "trigger": "trans",
                "source": "initial",
                "dest": "gray_scale_wait_image",
                "conditions": "is_going_to_gray_scale",
            },
            {
                "trigger": "trans_image",
                "source": "gray_scale_wait_image",
                "dest": "gray_scale",
            },
            {
                "trigger": "task_finished",
                "source": "gray_scale",
                "dest": "initial",
            },
            # Gaussian Blur
            {
                "trigger": "trans",
                "source": "initial",
                "dest": "gaussian_blur_ask_kernel",
                "conditions": "is_going_to_gaussian_blur_ask_kernel",
            },
            {
                "trigger": "trans",
                "source": "gaussian_blur_ask_kernel",
                "dest": "gaussian_blur_wait_image",
                "conditions": "is_going_to_gaussian_blur_wait_image",
            },
            {
                "trigger": "trans_image",
                "source": "gaussian_blur_wait_image",
                "dest": "gaussian_blur",
            },
            {
                "trigger": "task_finished",
                "source": "gaussian_blur",
                "dest": "initial",
            },

            # Connect all state to initial, make user able to abort any ongoing process.
            {
                "trigger": "trans",
                "source": states.copy(),
                "dest": "initial",
                "conditions": "is_going_to_initial",
            },
            # {
            #     "trigger": "trans",
            #     "source": states.copy(),
            #     "dest": "show_state",
            #     "conditions": "is_going_to_show_state",
            # },
            {
                "trigger": "go_initial",
                "source": states.copy(),
                "dest": "initial",
            }
        ],
        # initial="initial",
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
# print(channel_access_token)
base_url = os.getenv('base_url')

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

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    machine = get_user_machine(user_id)
    print(f"\nFSM STATE: {machine.state}")
    print('message:', event.message.text)
    if event.message.text.strip().lower() == 'state':
        send_text_message(event.reply_token, f"current state: {machine.state}")
    response = machine.trans(event)
    if response is False:
        send_text_message(event.reply_token, f"Not Entering any State: {machine.state}")


@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    user_id = event.source.user_id
    machine = get_user_machine(user_id)
    machine.trans_image(event)
    # print(f"\nFSM STATE: {machine.state}")
    # print('ImageMessageId:', event.message.id)
    # content_path = utils.save_event_image(event)
    # print(content_path)
    # if response is False:
    #     send_text_message(event.reply_token, f"Not Entering any State: {machine.state}")


@app.route("/show-fsm", methods=["GET"])
def show_fsm():
    fsm_path = 'fsm.svg'
    global_machine.get_graph().draw(fsm_path, prog="dot")
    with open(fsm_path, 'rb') as fr:
        svg2png(bytestring=fr.read(), write_to='fsm.png')
    return send_file("fsm.png", mimetype="image/png")


@app.route('/static/<path:path>', methods=["GET"])
def send_static(path):
    return send_file("./static/" + path, mimetype="image/png")


if __name__ == "__main__":
    port = os.environ.get("PORT", 8000)
    app.run(host="0.0.0.0", port=port, debug=True)
