import boto3
from PIL import Image
from io import BytesIO
from handlers import validate_s3_client, report_error


@validate_s3_client
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

def download_file(client, path, bucket_name='fotomaker-engineering'):
    save_location = "/tmp/" + path.split("/")[-1]
    client.download_file(bucket_name, path, save_location)
    return save_location

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
    
    client.upload_fileobj(in_mem_file, 'fotomaker-engineering', key)
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
        Params={'Bucket': 'fotomaker-engineering','Key': key},
        ExpiresIn=expiration)
    return response
