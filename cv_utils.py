import cv2
import numpy as np

cv = cv2


def read_path(path):
    return cv.imread(path)


def generate_image_background_mask(image, kernel_size=7):
    """ Apply Gaussian filter """
    # image = image.resize((image.size[0]*2, image.size[1]*2))
    img = np.asarray(image)
    # img = (255 * color.rgba2rgb(img)).astype("uint8")
    img = (255 * cv.cvtColor(img, cv.COLOR_RGBA2RGB)).astype("uint8")
    gray_img = (255 * cv.cvtColor(img, cv.COLOR_RGB2GRAY)).astype("uint8")

    # plt.subplot(331), plt.imshow(img)
    # plt.subplot(332), plt.imshow(gray_img, cmap='gray')

    """ edge canny """
    # Canny will convert image to grayscale
    edges = cv.Canny(img, 100, 200)
    # plt.subplot(333), plt.imshow(edges, cmap='gray')
    # kernel size should be odd
    if kernel_size % 2 == 0:
        kernel_size += 1
    edges = cv.GaussianBlur(edges, (1, 1), 0)
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    # edges = cv.morphologyEx(edges, cv.MORPH_CLOSE, kernel)
    edges = cv.dilate(edges, kernel, iterations=1)
    edges = cv.erode(edges, None)

    # plt.subplot(334), plt.imshow(edges, cmap='gray')
    # plt.show()

    """
        cv.findContours find contours [np.array(points...), ...] by gray scale points (use edges img here)
        pack contour-points, contour-area and append to contour_info,
        then use sort to find the contour with largest area and assume it is the background contour.
    """
    contour_info = []
    contours, _ = cv.findContours(edges, cv.RETR_LIST, cv.CHAIN_APPROX_NONE)
    for c in contours:
        contour_info.append((
            c,
            cv.isContourConvex(c),
            cv.contourArea(c),
        ))
    # sort by area
    contour_info = sorted(contour_info, key=lambda contour: contour[2], reverse=True)

    max_contour = contour_info[0]  # mentioned above, assume that this is the background.
    mask = np.zeros(edges.shape)
    # cv.fillConvexPoly(mask, max_contour[0], 255)  # max_contour is the struct above, index 0 is contour-points

    cv.fillPoly(mask, [max_contour[0]], 255)

    # for debugging
    edge_with_contour = edges.copy()
    cv.drawContours(edge_with_contour, (max_contour[0],), 0, color=(1.0, 0.0, 0.0))
    # plt.subplot(335), plt.imshow(edge_with_contour)
    # plt.subplot(336), plt.imshow(mask)
    # plt.show()

    BLUR = 3
    mask = cv.dilate(mask, None)
    mask = cv.erode(mask, None)
    mask = cv.GaussianBlur(mask, (BLUR, BLUR), 0)
    bg_mask_uint8 = np.array(mask.copy()).astype(
        'uint8')  # mask will be convert to float, so make a backup here for return.
    # print(mask)
    # -- Blend masked img into fill_color background
    # img = img.astype('float32') / 255.0
    # masked = (mask_stack * img[:, :, :3]) + ((1 - mask_stack) * fill_color)
    # masked = (masked * 255).astype('uint8')

    # plt.subplot(335), plt.imshow(mask_stack)
    # plt.subplot(336), plt.imshow(masked)
    # plt.show()

    return bg_mask_uint8  # A single tunnel 0,255 image


def apply_transparent_mask(img, mask, fill_color=(0.0, 0.0, 1.0)):
    # img : rgb
    # mask: 1dim 255 mask, 1=remain, 0=replace by fill_color
    mask_stack = np.dstack([mask] * 3)  # Create 3-channel alpha mask
    mask_stack = mask_stack.astype('float32') / 255.0
    img = img.astype('float32') / 255.0
    masked = (mask_stack * img[:, :, :3]) + ((1 - mask_stack) * fill_color)
    masked = (masked * 255).astype('uint8')
    return masked
