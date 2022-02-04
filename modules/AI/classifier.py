from keras.preprocessing.image import img_to_array
from keras.models import load_model
import numpy as np
import pickle
import cv2
from os import path

class Classifier:
    def __init__(self, defaultModel, label_file):
        self.defaultModel = defaultModel
        self.modelPath = defaultModel
        self.model = load_model(self.modelPath)
        self.label = pickle.loads(open(label_file, "rb").read())
        return

    def setModel(self, modelPath):
        self.modelPath = modelPath
        self.model = load_model(self.modelPath)

    def getModel(self):
        # Get the model name (id)
        print(self.modelPath)
        return self.modelPath.split(path.sep)[-2]

    def predict(self, image, IMAGE_DIMS=(96, 96)):
        # pre-process
        image = cv2.resize(image, IMAGE_DIMS)
        image = image.astype("float") / 255.0
        image = img_to_array(image)
        image = np.expand_dims(image, axis=0)
        # prediction
        proba = self.model.predict(image)[0]
        idx = np.argmax(proba)
        label = self.label.classes_[idx]

        return label, proba[idx] * 100
