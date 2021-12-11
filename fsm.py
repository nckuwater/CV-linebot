from transitions.extensions import GraphMachine

from utils import send_text_message


class TocMachine(GraphMachine):
    # service datas
    input_image = None

    def __init__(self, **machine_configs):
        self.machine = GraphMachine(model=self, **machine_configs)

    @staticmethod
    def is_going_to_initial(event):
        text = event.message.text
        return text.strip().lower() == 'init'

    @staticmethod
    def is_going_to_remove_bg(event):
        text = event.message.text
        return text.strip().lower() == "rbg"

    @staticmethod
    def is_going_to_gray_scale(event):
        text = event.message.text
        return text.strip().lower() == "gscale"

    def on_enter_remove_bg(self, event):
        print("I'm entering remove_bg")
        print("waiting for user image")

        reply_token = event.reply_token
        send_text_message(reply_token, "Trigger remove_bg")

    def on_enter_gray_scale(self, event):
        print("I'm entering gray_scale")
        reply_token = event.reply_token
        send_text_message(reply_token, "Trigger state2")

