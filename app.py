from PIL import Image, ImageFilter, ImageEnhance, ImageOps
from rembg import remove, new_session
import boto3
import json
import os
from io import BytesIO
import requests

# Init is ran on server startup
# Load your model to GPU as a global variable here using the variable name "model"
def init():
    global model
    # Create an object with default values
    # model = Generate(
    #     model='stable-diffusion-1.5',
    #     conf='/workspace/configs/models.yaml.example',
    #     sampler_name ='ddim'
    #     )

    # do the slow model initialization
    # model.load_model()

# Inference is ran for every server call
# Reference your preloaded global model variable here.
def inference(model_inputs:dict) -> dict:
    global model

    # Parse out your arguments
    product_id = model_inputs.get("productId")
    product_url = model_inputs.get("productUrl")
    access = model_inputs.get("access_key") 
    secret = model_inputs.get("secret_key")

    preprocessed_img_urls = main_preprocess(
        product_id, 
        product_url,
        access, 
        secret
        )

    return {'generatedImages': preprocessed_img_urls}

###---###---###---###---###---###---###---###---###---###---###---###---###---###---###---###---###---###---

# defining all other functions

def main_preprocess(product_id, product_url, access, secret):
  # creating paths out of the name
  image = load_image_from_url(product_url)
  
  # reduce the size of the image in order to make sure our server doesn't crash
  image.thumbnail((2048, 2048))

  cropped_image = get_cropped_image(image)
  blurred_image = get_blurred_image(cropped_image)
  preprocessed_image = get_preprocessed_image(blurred_image)

  blurred_image_name = "Cropped/" + file_name + ".png"
  preprocessed_image_name = "Preprocessed/" + file_name + ".png"

  ### getting s3 client
  s3_client = create_s3_client(access, secret)

  # saving the images
  keys = save_images(
    [blurred_image_name, preprocessed_image_name],
    [blurred_image, preprocessed_image],
    s3_client)
  img_urls = get_urls(s3_client, keys)

  return img_urls

def load_image_from_url(url):
    # send a GET request to the URL and read the image contents into memory
    response = requests.get(url)
    image_bytes = BytesIO(response.content)
    pil_image = Image.open(image_bytes)
    return pil_image

def get_cropped_image(pil_image):
    n_s = new_session("isnet-general-use")
    output = remove(pil_image, session=n_s, alpha_matting=True)
    return output

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

# s3 utils

def create_s3_client(access_key, secret_key):
  s3_client = boto3.client(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key, 
        region_name="ap-south-1"
    )
  return s3_client

def load_image_s3(img_name, s3_client):
    save_location = download_file(s3_client, img_name)
    image = Image.open(save_location)
    return image

def download_file(client, path, bucket_name='fotomaker'):
    save_location = "/tmp/" + path.split("/")[-1]
    client.download_file(bucket_name, path, save_location)
    return save_location

# def load_image_s3(img_name, s3_client):
#     obj = s3_client.get_object(
#         Bucket='fotomaker', 
#         Key=img_name
#         )
#     body = obj['Body']
#     img = body.read()
#     image = Image.open(BytesIO(img))
#     return image

def save_images(img_names, imgs, s3_client):
    for idx, img in enumerate(imgs):
        key = img_names[idx]
        save_response_s3(
            s3_client,
            img,
            key
            )
    return img_names

def save_response_s3(client, file, key):
    in_mem_file = BytesIO()
    file.save(in_mem_file, format="PNG")
    in_mem_file.seek(0)
    
    client.upload_fileobj(in_mem_file, 'fotomaker', key)
    return None

def get_urls(s3_client, keys):
    img_urls = []
    for key in keys:
        url = create_presigned_url(s3_client, key)
        img_urls.append(url)
    return img_urls

def create_presigned_url(client, key, expiration=60*5):
    # Generate a presigned URL for the S3 object
    response = client.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'fotomaker','Key': key},
        ExpiresIn=expiration)
    return response
