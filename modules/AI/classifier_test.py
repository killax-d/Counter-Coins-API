import argparse
import cv2
from classifier import Classifier

# argument parser
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True,
                help="image to analyze")
ap.add_argument("-m", "--model", required=True,
                help="model file")
ap.add_argument("-l", "--label", required=True,
                help="label file")
args = vars(ap.parse_args())

CLASSIFIER = Classifier(args["model"], args["label"])
(name, confidence) = CLASSIFIER.predict(cv2.imread((args["image"])))
print("[INFO] I think the image is a {} with {:.2f}% confidence".format(name, confidence))
