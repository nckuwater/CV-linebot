from transitions.extensions import GraphMachine

import utils
from utils import send_text_message, send_image
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
    def is_going_to_show_state(event):
        text = event.message.text
        return text.strip().lower() == "state"

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

    def on_enter_show_state(self, event):
        print(f"showing state: {self.machine.state}")
        reply_token = event.reply_token
        send_text_message(reply_token, f"current state: {self.machine.state}")
        self.go_initial()

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
        img_path = f'static/images/{event.message.id}_rbg.jpg'
        cv_utils.write_path(img_path, result)
        print('reply the result', utils.resolve_static_url(img_path))
        reply_token = event.reply_token
        send_image(reply_token, utils.resolve_static_url(img_path))
        send_text_message(reply_token, 'Type ok if ok, Type number to remove more.')

        self.trans()  # go to wait_user_revise

    def on_enter_gray_scale(self, event):
        print("I'm entering gray_scale")
        self.remove_bg_image_path = None
        self.remove_bg_contours = 1
        reply_token = event.reply_token
        send_text_message(reply_token, "Send an image to process")

    def on_enter_gray_scale_process(self, event):
        print(f'handling gray scale image {event.message.id}')
        gray_scale_input_image_path = utils.save_event_image(event)
        img = cv_utils.read_path(gray_scale_input_image_path)
        img = cv_utils.to_gray_scale(img)
        img_path = f'static/images/{event.message.id}_gray.jpg'
        cv_utils.write_path(img_path, img)
        send_image(event.reply_token, utils.resolve_static_url(img_path))
        self.go_initial()
