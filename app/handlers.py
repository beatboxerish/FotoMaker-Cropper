from functools import wraps
import time


def validate_input_image(func):
	"""
	Use this function to validate input image for cropping
	"""
	@wraps(func)
	def wrapper(url, *args, **kwargs):
		# Call the original function first to get the image
		pil_image = func(url, *args, **kwargs)
		
		# check the image file type
		image_format = pil_image.format.lower()
		if image_format not in ['png', 'jpg', 'jpeg']:
			raise ValueError("Invalid image format")

		# check the image size
		if pil_image.mode not in ["RGB", "RGBA"]:
			raise ValueError("Invalid image layer format")
		
		# If the image passed all the checks, return the image.
		return pil_image
	return wrapper

def report_error(code=10):
	"""
	Use this function to report specific error codes
	"""
	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			try:
				output = func(*args, **kwargs)
			except:
				raise ValueError(f"Error: {code}")
			return output
		return wrapper
	return decorator

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
		
				s3_client.list_buckets() # check the connection

				return s3_client  # If no exception is raised, return the client
			except:
				if i < retries - 1:  # i is zero indexed, so retries-1
					print("retrying...")
					time.sleep(3)  # wait for m seconds before trying again
					continue
				else:
					raise ValueError("Problem with S3 connection")
	return wrapper
