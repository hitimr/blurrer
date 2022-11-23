from blurrer import Blurrer
from PIL import Image
import json
import cv2
import os


if __name__ == "__main__":
    with open("config.json") as f:
        json_config = json.load(f)
        json_config["ALPR"]["assets_folder"] = os.getcwd()  # must be manually specified

    blurrer = Blurrer(json_config)

    # process all files in a folder
    blurrer.process_folder("input", "out/bulk")

    # process single image
    blurrer.process_file("input/at1.jpg", "out/at1_single.jpg")

    # process PIL data
    with Image.open("input/at1.jpg") as im:
        blurred = blurrer.blur_PIL(im)
        blurred.save("out/at1_pil.jpg")

    # process cv2 data
    im = cv2.imread("input/at1.jpg")
    blurred = blurrer.blur_cv2(im)
    cv2.imwrite("out/at1_cv2.jpg", blurred)

    
