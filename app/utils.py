import requests
import os
from io import BytesIO
from PIL import Image, ImageFilter, ImageOps
from rembg import remove, new_session
from handlers import validate_input_image, report_error

@validate_input_image
def load_image_from_url(url):
    response = requests.get(url)
    image_bytes = BytesIO(response.content)
    pil_image = Image.open(image_bytes)
    return pil_image

@report_error(10)
def get_cropped_image(pil_image):
    output = None
    if pil_image.mode == 'RGBA':
        if len(set(pil_image.getchannel("A").getextrema()))>1:
            output = pil_image
    if not output:
        n_s = new_session("isnet-general-use")
        output = remove(pil_image, session=n_s, alpha_matting=True)
    return output

@report_error(10)
def get_blurred_image(pil_image):
    
    # create outline and blurred outline mask
    outlines = pil_image.getchannel("A").filter(ImageFilter.FIND_EDGES)
    blurred_outlines = outlines.filter(ImageFilter.BLUR)
    blurred_outlines = blurred_outlines.point(lambda x: x+100 if x>10 else x)

    # create blurred image
    pil_image_blurred = pil_image.copy()
    pil_image_blurred = pil_image_blurred.filter(ImageFilter.GaussianBlur(1))
    
    # create final blurred image
    output_blurred_edges = Image.composite(pil_image_blurred, pil_image, blurred_outlines)

    return output_blurred_edges

@report_error(10)
def get_preprocessed_image(pil_image, buffer=0):
    cropped_image = pil_image

    x1, y1, x2, y2 = cropped_image.getbbox()
    w, h = x2 - x1, y2 - y1

    box_cropped_image = cropped_image.crop((x1-buffer, y1-buffer, x2+buffer, y2+buffer))
    resize_cropped_img = ImageOps.contain(box_cropped_image, (512, 512))
    width_size, height_size = resize_cropped_img.size[0], resize_cropped_img.size[1]

    new_img = ImageOps.expand(resize_cropped_img,
                              border = ((512-resize_cropped_img.size[0])//2, (512-resize_cropped_img.size[1])//2),
                              fill = (0, 0, 0, 0))

    if new_img.size[0] != 512:
        new_img = ImageOps.expand(new_img, (1, 0, 0, 0))
    if new_img.size[1] != 512:
        new_img = ImageOps.expand(new_img, (0, 1, 0, 0))

    return new_img


@report_error(10)
def send_info_back_to_BE(product_id, preprocessed_image_path, cropped_image_path):
    body = {
    "productId": product_id,
    "croppedProductKey": preprocessed_image_path,
    "croppedUhdProductKey": cropped_image_path
    }
    endpoint = os.environ["ENDPOINT"] + "product/" + product_id + "/crop-product"
    headers = {'content-type': 'application/json'}
    requests.put(endpoint, headers=headers, json=body)
    return None
