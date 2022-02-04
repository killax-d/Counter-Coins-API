from os.path import dirname, realpath
from os import path
from services.settings import SettingsService
from modules.AI.classifier import Classifier

SETTINGS_FILE = 'settings.json'

# read settings file
SETTINGS = SettingsService(SETTINGS_FILE)

class Singleton(object):
  _instances = {}
  def __new__(class_, *args, **kwargs):
    if class_ not in class_._instances:
        class_._instances[class_] = super(Singleton, class_).__new__(class_, *args, **kwargs)
    return class_._instances[class_]

class ClassifierService(Singleton):

    def __init__(self):
        self.classifier = Classifier(SETTINGS.getModel(), SETTINGS.getLabel())

    def getClassifier(self):
        return self.classifier