from PIL import Image
from rembg import new_session, remove

random_img = Image.new("L", (512, 512), 255)
n_s = new_session("isnet-general-use")
output = remove(random_img, session=n_s, alpha_matting=True)