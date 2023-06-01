import os
from exceptions import StatusException
from s3_utils import *
from utils import *


def init():
    """
    Init is ran on server startup
    Load model to GPU as global variable using variable name "model"
    """
    global model


def inference(model_inputs: dict) -> dict:
    """
    Inference is ran for every server call
    Reference your preloaded global model variable here.
    """
    global model
    try:
        # Getting Inputs
        product_id, product_image = get_inputs(model_inputs)
        preprocessed_img_urls = main_preprocess(
            product_id,
            product_image,
            os.environ["ACCESS"],
            os.environ["SECRET"]
            )
    except Exception as e:
        print("LOGGING ERROR:", e)
        if type(e) == StatusException:
            code = e.args[0][-3:]
        else:
            code = ""
        make_error_call(code)
        return ["Error code: {}".format(code)]

    return {'generatedImages': preprocessed_img_urls}


def main_preprocess(product_id, product_image, access, secret):
    # reduce the size of the image in order to make sure our server doesn't crash
    product_image.thumbnail((2048, 2048))

    cropped_image = get_cropped_image(product_image)
    blurred_image = get_blurred_image(cropped_image)
    preprocessed_image = get_preprocessed_image(blurred_image)

    preprocessed_image_file_name = product_id + ".png"

    blurred_image_name = "cropped-uhd-products/" + preprocessed_image_file_name
    preprocessed_image_name = "cropped-products/" + preprocessed_image_file_name

    ### getting s3 client
    s3_client = create_s3_client(access, secret)

    # saving the images
    keys = save_images(
        [blurred_image_name, preprocessed_image_name],
        [blurred_image, preprocessed_image],
        s3_client
    )

    if os.environ["ENV"] == "prod":
        # trigger BE API
        send_info_back_to_BE(
            product_id,
            preprocessed_image_file_name,
            preprocessed_image_file_name
        )

    img_urls = get_urls(s3_client, keys)
    return img_urls
