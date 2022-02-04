from keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.optimizers import Adam
from keras.preprocessing.image import img_to_array
from sklearn.preprocessing import LabelBinarizer
from sklearn.model_selection import train_test_split
from .VGGNet import SmallerVGGNet
from imutils import paths
import numpy as np
import argparse
import random
import pickle
import cv2
import os
import tensorflow as tf
import sys

class ClassifierTrainer:

    def train(self, model_file, label_file, dataset_folder, EPOCHS, INIT_LR=0.001, BS=32, IMAGE_DIMS=(96, 96, 3)):
        if (not model_file.endswith(".h5")):
            raise ValueError("The output file must end with .h5")
        if (not label_file.endswith(".pickle")):
            raise ValueError("The pickle file must end with .pickle")

        # Data and labels array to hold all informations
        data = []
        labels = []

        imagesCount = {}

        print("[INFO] Loading images set...")
        imagePaths = sorted(list(paths.list_images(dataset_folder)))
        if (len(imagePaths) == 0):
            raise ValueError("No image found in the dataset folder")

        print("[INFO] Succesfully loaded %d image%s" % (len(imagePaths), "s" if len(imagePaths) > 1 else ""))

        # Adjust randomizer with a seed, 42 for life
        # Then shuffle the images list
        random.seed(42)
        random.shuffle(imagePaths)

        for imagePath in imagePaths:
            # Reading image and resizing to fit the model
            image = cv2.imread(imagePath)
            image = cv2.resize(image, (IMAGE_DIMS[1], IMAGE_DIMS[0]))
            image = img_to_array(image)

            # Add to data array
            data.append(image)

            # Add to labels array
            label = imagePath.split(os.path.sep)[-2] # Taking folder as label
            if (label not in imagesCount):
                imagesCount[label] = 0
            imagesCount[label] += 1
            
            labels.append(label)

        # Convert to numpy array
        data = np.array(data, dtype="float") / 255.0
        labels = np.array(labels)

        # Binarize labels
        lb = LabelBinarizer()
        labels = lb.fit_transform(labels)

        # Split data into training and testing sets
        # train = 80% and test = 20% in that case
        (trainX, testX, trainY, testY) = train_test_split(data, labels, test_size=0.2, random_state=42)

        # Add virtual data augmentation (in case of low quantity of data)
        datagen = ImageDataGenerator(
            rotation_range=90, 
            width_shift_range=0.0,
            height_shift_range=0.0,
            shear_range=0.0, 
            zoom_range=0.0,
            horizontal_flip=True, 
            fill_mode="nearest"
        )

        # Init and compile model
        model = SmallerVGGNet.build(width=IMAGE_DIMS[1], height=IMAGE_DIMS[0], depth=IMAGE_DIMS[2], classes=len(lb.classes_))
        opt = Adam(learning_rate=INIT_LR, decay=INIT_LR / EPOCHS)
        model.compile(loss="categorical_crossentropy", optimizer=opt, metrics=["accuracy"])

        # Train the model
        H = model.fit(
            datagen.flow(trainX, trainY, batch_size=BS),
            validation_data=(testX, testY),
            steps_per_epoch=len(trainX) // BS,
            epochs=EPOCHS,
            verbose=1 # Show progress
        )

        # Save the model and label binarizer to disk
        print("[INFO] Saving model...")
        model.save(model_file)
        f = open(label_file, "wb")
        f.write(pickle.dumps(lb))
        f.close()

        return imagesCount

gpus = tf.config.list_physical_devices('GPU')
if gpus:
  # Restrict TensorFlow to only use the first GPU
  try:
    tf.config.set_visible_devices(gpus[0], 'GPU')
    logical_gpus = tf.config.list_logical_devices('GPU')
    print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPU")
  except RuntimeError as e:
    # Visible devices must be set before GPUs have been initialized
    print(e)

def launch():
    # argument parser
    ap = argparse.ArgumentParser()
    ap.add_argument("-m", "--model", required=False, default="model.h5",
                    help="model save location, default : ./model.h5")
    ap.add_argument("-l", "--label", required=False, default="label.pickle",
                    help="pickle save location, default : ./label.pickle")
    ap.add_argument("-d", "--dataset", required=True,
                    help="dataset folder")
    ap.add_argument("-e", "--epoch", required=False, default=500,
                    help="epoch counts, default : 500")
    args = vars(ap.parse_args())

    # py .\classifier_trainer.py -d .\Dataset\ -m .\coins_model.h5 -l .\lab.pickle
    ClassifierTrainer().train(
        model_file=args["model"], 
        label_file=args["label"], 
        dataset_folder=args["dataset"], 
        EPOCHS=int(args["epoch"]))