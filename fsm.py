from transitions.extensions import GraphMachine

import utils
from utils import send_text_message
import cv_utils
import os.path


class TocMachine(GraphMachine):
    # service datas
    def __init__(self, **machine_configs):
        # super().__init__(self, **machine_configs)
        self.machine = GraphMachine(model=self, **machine_configs)
        self.remove_bg_image_path = None
        self.remove_bg_contours = 1

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

    def is_going_to_remove_bg_wait_user_revise(self, event):
        text = event.message.text
        if text.strip().lower() == "ok":
            self.go_initial()
            return False
        try:
            val = int(text)
            if self.remove_bg_contours == val:
                return False
            self.remove_bg_contours = int(text)
            return True
        except:
            return False

    def on_enter_remove_bg(self, event):
        print("waiting for user image")
        self.remove_bg_image_path = None
        self.remove_bg_contours = 1
        reply_token = event.reply_token
        send_text_message(reply_token, "Send an image to process")

    def on_enter_remove_bg_processing_img(self, event):
        # ImageEvent
        print(f'handling remove bg image {event.message.id}')
        self.remove_bg_image_path = utils.save_event_image(event)
        print('image saved at:', self.remove_bg_image_path)
        img = cv_utils.read_path(self.remove_bg_image_path)
        mask = cv_utils.generate_image_background_mask(img)
        result = cv_utils.apply_transparent_mask(img, mask)

        self.trans()  # go to wait_user_revise

    def on_enter_gray_scale(self, event):
        print("I'm entering gray_scale")
        reply_token = event.reply_token
        send_text_message(reply_token, "Trigger state2")
