from functools import wraps
import time
from exceptions import StatusException


def report_error(code=000):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                output = func(*args, **kwargs)
            except Exception as e:
                if type(e) == StatusException:
                    raise e
                else:
                    raise StatusException(f"Error Code: {code}")
            return output
        return wrapper
    return decorator


def validate_input_image(func):
    """
    Use this function to validate input image for cropping
    """
    @wraps(func)
    def wrapper(url, *args, **kwargs):
        # Call the original function first to get the image
        pil_image = func(url, *args, **kwargs)

        # validations
        validate_image_format(pil_image)
        validate_image_layers(pil_image)
        # If the image passed all the checks, return the image.
        return pil_image
    return wrapper


@report_error(110)
def validate_image_format(pil_image):
    # check the image file type
    image_format = pil_image.format.lower()
    if image_format not in ['png', 'jpg', 'jpeg']:
        raise Exception("Invalid image format")


@report_error(112)
def validate_image_layers(pil_image):
    if pil_image.mode not in ["RGB", "RGBA"]:
        raise Exception("Invalid image layer format")


@report_error(100)
def validate_request_args(func):
    @wraps(func)
    def wrapper(model_inputs, *args, **kwargs):
        # Call the original function first to get the outputs
        product_id, product_url = func(model_inputs, *args, **kwargs)

        # validations
        if (not product_id) or (not product_url):
            raise Exception("Argument from request is null")
        # If the image passed all the checks, return the image.
        return product_id, product_url
    return wrapper


@report_error(330)
def validate_s3_client(func):
    """
    Use this function to validate functioning of S3
    """
    @wraps(func)
    def wrapper(url, *args, **kwargs):
        retries = 3
        for i in range(retries):
            try:
                # Call the original function first to get the image
                s3_client = func(url, *args, **kwargs)
                s3_client.list_buckets()
                return s3_client  # If no exception is raised, return the client
            except Exception as e:
                if i < retries - 1:  # i is zero indexed, so retries-1
                    print("retrying...")
                    time.sleep(3)  # wait for m seconds before trying again
                    continue
                else:
                    raise e
    return wrapper
