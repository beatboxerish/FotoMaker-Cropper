from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import json
import os
import requests

from s3_utils import *
from utils import *

# Init is ran on server startup
# Load your model to GPU as a global variable here using the variable name "model"
def init():
    global model

# Inference is ran for every server call
# Reference your preloaded global model variable here.
def inference(model_inputs:dict) -> dict:
    global model

    # Parse out your arguments
    model_inputs = model_inputs["input"]
    product_id = model_inputs.get("productId")
    product_url = model_inputs.get("productUrl")

    preprocessed_img_urls = main_preprocess(
        product_id, 
        product_url,
        os.environ["ACCESS"], 
        os.environ["SECRET"]
        )

    return {'generatedImages': preprocessed_img_urls}

###---###---###---###---###---###---###---###---###---###---###---###---###---###---###---###---###---###---

# defining main function

def main_preprocess(product_id, product_url, access, secret):
  # creating paths out of the name
  image = load_image_from_url(product_url)
  
  # reduce the size of the image in order to make sure our server doesn't crash
  image.thumbnail((2048, 2048))

  cropped_image = get_cropped_image(image)
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
    s3_client)

  if os.environ["ENV"]=="prod": 
    # trigger BE API
    send_info_back_to_BE(
        product_id, 
        preprocessed_image_file_name,
        preprocessed_image_file_name
    )
    
  img_urls = get_urls(s3_client, keys)
  return img_urls