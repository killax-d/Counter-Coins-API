from os import path
import json

class Singleton(object):
  _instances = {}
  def __new__(class_, file_path, *args, **kwargs):
    if class_ not in class_._instances:
        class_._instances[class_] = super(Singleton, class_).__new__(class_, *args, **kwargs)
    return class_._instances[class_]

class SettingsService(Singleton):

    def __init__(self, file_path):
        self.file_path = file_path
        # Default values
        self.model = path.sep.join(["modules", "AI", "coins.h5"])
        self.label = path.sep.join(["modules", "AI", "label.pickle"])
        self.report_folder = path.sep.join(["reports"])
        self.model_folder = path.sep.join(["models"])
        self.dataset_folder = path.sep.join(["generated_dataset"])
        self.error_count = 0
        self.train_after = 500
        self.train_epochs = 1000
        self.is_training = False

        self.coins = {
            "0": 0,
            "1c": 1,
            "2c": 2,
            "5c": 5,
            "10c": 10,
            "20c": 20,
            "50c": 50,
            "1e": 100,
            "2e": 200,
        }

        if path.exists(self.file_path):
            # Load settings from file
            self.load()
        else:
            # Save default settings to file
            self.save()


    def save(self):
        with open(self.file_path, "w") as file:
            json.dump(self.toJson(), file)


    def load(self):
        with open(self.file_path, "r") as file:
            self.fromJson(json.load(file))


    def toJson(self):
        return {
            "model": self.model,
            "label": self.label,
            "train_after": self.train_after,
            "train_epochs": self.train_epochs
        }


    def fromJson(self, json_data):
        self.model = json_data["model"]
        self.label = json_data["label"]
        # Optional
        if ("train_after" in json_data):
            self.train_after = json_data["train_after"]
        if ("train_epochs" in json_data):
            self.train_epochs = json_data["train_epochs"]


    def getModel(self):
        return self.model


    def setModel(self, model):
        self.model = model
        self.save()


    def getLabel(self):
        return self.label

    def getReportFolder(self):
        return self.report_folder

    def getModelFolder(self):
        return self.model_folder

    def getDatasetFolder(self):
        return self.dataset_folder

    def getCoins(self):
        return self.coins

    def incErrorCount(self):
        self.error_count += 1

    def decErrorCount(self):
        self.error_count += 1

    def getErrorCount(self):
        return self.error_count

    def setErrorCount(self, error_count):
        self.error_count = error_count
    
    def resetErrorCount(self):
        self.error_count = 0
    
    def getTrainAfter(self):
        return self.train_after

    def getTrainEpochs(self):
        return self.train_epochs

    def isTraining(self):
        return self.is_training

    def setTraining(self, is_training):
        self.is_training = is_training