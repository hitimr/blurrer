from PIL import Image, ExifTags, ImageOps, ImageDraw
from PIL import ImageFilter
from pathlib import Path
import numpy as np
import traceback
import time
import json
import cv2
import os

# os.environ["LD_LIBRARY_PATH"] = os.path.join(Path(__file__).parent, "lib:$LD_LIBRARY_PATH")
# os.environ["PYTHONPATH"] = os.path.join(Path(__file__).parent, "lib")

import lib.ultimateAlprSdk as ultimateAlprSdk  # noqa

def check_op(operation, result):
    if not result.isOK():
        print(operation + ": failed -> " + result.phrase())
    else:
        print(operation + ": OK -> " + result.json())


class Blurrer:
    IMAGE_TYPES_MAPPING = {
        "RGB": ultimateAlprSdk.ULTALPR_SDK_IMAGE_TYPE_RGB24,
        "RGBA": ultimateAlprSdk.ULTALPR_SDK_IMAGE_TYPE_RGBA32,
        "L": ultimateAlprSdk.ULTALPR_SDK_IMAGE_TYPE_Y,
    }

    def __init__(self, json_config):
        self.json_config = json_config

        # Initialize SDK
        check_op(
            "Init",
            ultimateAlprSdk.UltAlprSdkEngine_init(json.dumps(self.json_config["ALPR"])),
        )

        # Perform Warmup
        check_op("Warmup", ultimateAlprSdk.UltAlprSdkEngine_warmUp(0))

    def __del__(self):
        check_op("Deconstructor", ultimateAlprSdk.UltAlprSdkEngine_deInit())

    def blur_cv2(self, cv2_image):
        pil_image = Image.fromarray(cv2_image)
        return np.asarray(self.blur_PIL(pil_image))

    def blur_PIL(self, pil_image):
        iter = 0
        blur_radius = self.json_config["BLURRER"]["blur_radius"]
        while True:
            result = self._process(pil_image)
            json_result = json.loads(result.json())

            if result.numPlates() == 0:
                break  # nothing found. we can stop

            if iter > self.json_config["BLURRER"]["max_iter"]:
                print("MAX ITER")
                break  # prevent infinite loop

            # Plates are detected add some blur
            self._add_blur(pil_image, json_result, blur_radius)

            # Add outline if specified
            if self.json_config["BLURRER"]["add_outline"] is True:
                self._add_polygon(pil_image, json_result)

            blur_radius += self.json_config["BLURRER"]["blur_radius_increment"]
            iter += 1

        return pil_image

    def process_file(self, input_file, output_file=None):
        pil_image = self._load_pil_image(input_file)

        self.blur_PIL(pil_image)

        # save image if specified
        if output_file is not None:
            pil_image.save(output_file)

    def process_folder(self, in_path: Path, out_path: Path):
        # make sure output path exists
        Path(out_path).mkdir(parents=True, exist_ok=True)

        # run through all files
        files = Path(in_path).iterdir()
        n_frames = 0  # iterdir yields a generator. we dont know how long it runs yet

        t_start = time.time()
        for file in files:
            self.process_file(file, Path(out_path) / file.name)
            n_frames += 1

        duration = time.time() - t_start
        fps = n_frames / float(duration)

        print(f"Finished processing {n_frames} pictures")
        print(f"Total time: {duration}s ({fps} FPS)")

    def _load_pil_image(self, path):
        pil_image = Image.open(path)
        img_exif = pil_image.getexif()
        ret = {}
        orientation = 1
        try:
            if img_exif:
                for tag, value in img_exif.items():
                    decoded = ExifTags.TAGS.get(tag, tag)
                    ret[decoded] = value
                orientation = ret["Orientation"]
        except Exception as e:
            print("An exception occurred: {}".format(e))
            traceback.print_exc()

        if orientation > 1:
            pil_image = ImageOps.exif_transpose(pil_image)

        return pil_image

    def _get_image_type(self, pil_image):
        if pil_image.mode in self.IMAGE_TYPES_MAPPING:
            return self.IMAGE_TYPES_MAPPING[pil_image.mode]
        else:
            raise ValueError("Invalid mode: %s" % pil_image.mode)


    def _process(self, pil_image):

        width, height = pil_image.size

        result = ultimateAlprSdk.UltAlprSdkEngine_process(
            self._get_image_type(pil_image),
            pil_image.tobytes(),  # type(x) == bytes
            width,
            height,
            0,  # stride
            # exifOrientation (already rotated in load_image -> use default value: 1)
            1,
        )

        if result.isOK() is not True:
            raise RuntimeError("Error while processing the image")

        return result

    def _add_polygon(self, image, json_result):
        draw = ImageDraw.Draw(image)
        for palte in json_result["plates"]:
            draw.polygon(palte["warpedBox"], width=4, outline=(255, 255, 0))

    def _add_blur(self, image, json_result, blur_radius):
        draw = ImageDraw.Draw(image)
        for palte in json_result["plates"]:
            mask = Image.new("L", image.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.polygon(palte["warpedBox"], fill=255)
            blurred = image.filter(ImageFilter.GaussianBlur(blur_radius))
            image.paste(blurred, mask=mask)


if __name__ == "__main__":
    with open("config.json") as f:
        json_config = json.load(f)
        json_config["ALPR"]["assets_folder"] = os.getcwd()

    blurrer = Blurrer(json_config)
    blurrer.process_folder("input", "output")
