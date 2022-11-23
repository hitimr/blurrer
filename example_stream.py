from blurrer import Blurrer
import json
import cv2
import os

with open("config.json") as f:
    json_config = json.load(f)
    json_config["ALPR"]["assets_folder"] = os.getcwd()

blurrer = Blurrer(json_config)

cv2.namedWindow("preview")
vc = cv2.VideoCapture(0)

if vc.isOpened():  # try to get the first frame
    rval, frame = vc.read()
else:
    rval = False

while rval:
    rval, frame = vc.read()
    frame = blurrer.blur_cv2(frame)
    cv2.imshow("preview", frame)
    key = cv2.waitKey(20)
    if key == 27:  # exit on ESC
        break

vc.release()
cv2.destroyWindow("preview")
