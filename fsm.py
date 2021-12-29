import traceback

from transitions.extensions import GraphMachine

import utils
from utils import send_text_message, send_image, send_payload
import cv_utils
import os.path


class TocMachine(GraphMachine):
    # service datas
    def __init__(self, **machine_configs):
        # super().__init__(self, **machine_configs)
        self.machine = GraphMachine(model=self, **machine_configs)

        self.remove_bg_image_path = None
        self.remove_bg_result = None
        self.remove_bg_result_path = None
        self.remove_bg_masks = None
        self.remove_bg_contour = 1

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
        return text.strip().lower() == "gray"

    def is_going_to_remove_bg_revise_img(self, event):
        text = event.message.text
        if text.strip().lower() == "ok":
            # self.go_initial()
            return False
        try:
            self.remove_bg_contour = int(text)
            return True
        except:
            return False

    def is_going_to_remove_bg_user_ok(self, event):
        text = event.message.text
        if text.strip().lower() == 'ok':
            self.remove_bg_contour = None
            return True
        return False

    def on_enter_initial(self, event):
        print(f"state: initial")
        reply_token = event.reply_token
        send_text_message(reply_token, f"current state: {self.machine.state}")
        self.go_initial()

    def on_enter_show_state(self, event):
        print(f"showing state: {self.machine.state}")
        reply_token = event.reply_token
        send_text_message(reply_token, f"current state: {self.machine.state}")
        self.go_initial()

    def on_enter_remove_bg(self, event):
        print("waiting for user image")
        self.remove_bg_image_path = None
        self.remove_bg_contour = 1
        reply_token = event.reply_token
        send_text_message(reply_token, "Send an image to process")

    def on_enter_remove_bg_processing_img(self, event):
        # ImageEvent from remove_bg
        # or MessageEvent from user reply revise
        """
            An short state, exit to wait_user_revise after image send,
            this checks the self.remove_bg_contours to check if user have already processed a image
        """
        print(f'handling remove bg image {event.message.id}')
        self.remove_bg_image_path = utils.save_event_image(event)
        print('image saved at:', self.remove_bg_image_path)
        img = cv_utils.read_path(self.remove_bg_image_path)
        # OLD METHOD
        # mask = cv_utils.generate_image_background_mask(img)
        # result = cv_utils.apply_transparent_mask(img, mask)
        # img_path = f'static/images/{event.message.id}_rbg.jpg'
        # cv_utils.write_path(img_path, result)
        # print('reply the result', utils.resolve_static_url(img_path))
        # reply_token = event.reply_token
        # send_image(reply_token, utils.resolve_static_url(img_path))
        # send_text_message(reply_token, 'Type ok if ok, Type number to remove more.')

        disp_img, masks = cv_utils.generate_image_background_mask_set(img)
        result = cv_utils.apply_transparent_mask(img, masks[0])

        disp_img_path = f'static/images/{event.message.id}_disp.png'
        img_path = f'static/images/{event.message.id}_result.png'
        cv_utils.write_path(disp_img_path, disp_img)
        cv_utils.write_path(img_path, result)

        self.remove_bg_result_path = img_path
        self.remove_bg_result = result
        self.remove_bg_masks = masks

        # resolve the image path to http url.
        print('reply the result', utils.resolve_static_url(img_path))
        reply_token = event.reply_token
        # send_image(reply_token, utils.resolve_static_url(disp_img_path))
        # send_image(reply_token, utils.resolve_static_url(img_path))
        # send_text_message(reply_token, 'Type ok if ok, Type number to remove more.')

        send_payload(reply_token, [
            utils.get_image_send_message(utils.resolve_static_url(disp_img_path)),
            utils.get_image_send_message(utils.resolve_static_url(img_path)),
            utils.get_text_send_message('Type ok if ok, Type number to remove more.')
        ])

        # self.trans()  # go to wait_user_revise
        self.goto_wait_user_revise(None)  # go to wait_user_revise

    def on_enter_remove_bg_wait_user_revise(self, event):
        # dont do revise when first entering
        # event is not None if user reply
        # message event, user reply the index.
        if event is None:
            # this is the first enter right after processing, just send the result.
            pass
        else:
            # user request to revise
            try:
                text = event.message.text
                reply_token = event.reply_token

                img_path = self.remove_bg_result_path
                self.remove_bg_contour = int(text)

                if self.remove_bg_contour == 0:
                    send_image(reply_token, utils.resolve_static_url(self.remove_bg_result_path))
                    return True
                if self.remove_bg_contour >= len(self.remove_bg_masks):
                    return False
                img = cv_utils.apply_remove_mask(self.remove_bg_result, self.remove_bg_masks[self.remove_bg_contour])
                self.remove_bg_result = img
                cv_utils.write_path(self.remove_bg_result_path, img)

                send_image(reply_token, utils.resolve_static_url(img_path))
                return True
            except:
                traceback.print_exc()
                return False

    def on_enter_gray_scale_wait_image(self, event):
        print("I'm entering gray_scale")
        self.remove_bg_image_path = None
        reply_token = event.reply_token
        send_text_message(reply_token, "請發送圖片")

    def on_enter_gray_scale(self, event):
        print(f'handling gray scale image {event.message.id}')
        gray_scale_input_image_path = utils.save_event_image(event)
        img = cv_utils.read_path(gray_scale_input_image_path)
        img = cv_utils.to_gray_scale(img)
        img_path = f'static/images/{event.message.id}_gray.jpg'
        cv_utils.write_path(img_path, img)
        send_image(event.reply_token, utils.resolve_static_url(img_path))
        self.task_finished()

    def is_going_to_gaussian_blur_ask_kernel(self, event):
        text = event.message.text
        return text.strip().lower() == "gau"

    def is_going_to_gaussian_blur_wait_image(self, event):
        text = event.message.text
        try:
            ksize = int(text)
            if ksize % 2 == 1:
                return True
            return False
        except:
            return False

    def on_enter_gaussian_blur_ask_kernel(self, event):
        send_text_message(event.reply_token, '請輸入kernel大小(須為奇數)')

    def on_enter_gaussian_blur_wait_image(self, event):
        self.gaussian_kernel_size = int(event.message.text)
        send_text_message(event.reply_token, '請發送圖片')

    def on_enter_gaussian_blur(self, event):
        print(f'handling gaussian image {event.message.id}')
        gaussian_input_image_path = utils.save_event_image(event)
        img = cv_utils.read_path(gaussian_input_image_path)

        img = cv_utils.do_gaussian(img, self.gaussian_kernel_size)
        img_path = f'static/images/{event.message.id}_gau.jpg'
        cv_utils.write_path(img_path, img)
        send_image(event.reply_token, utils.resolve_static_url(img_path))
        self.task_finished()
