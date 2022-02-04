from flask import Flask, request, jsonify, Response
import uuid

from os.path import join, exists, dirname, realpath
from os import makedirs, path
import json
from distutils.dir_util import copy_tree

from routes.report import reports
from routes.classify import classifications
from routes.model import models

from services.settings import SettingsService
from services.users import UsersService
from services.classifier import ClassifierService


# flask run -h 10.0.0.2 -p 80
app = Flask(__name__)
SETTINGS_FILE = dirname(realpath(__file__)) + path.sep + 'settings.json'

# read settings file
SETTINGS = SettingsService(SETTINGS_FILE)
USERS = UsersService()
CLASSIFIER = ClassifierService()

# If generated_dataset is not created, create it with initial dataset
if not exists(SETTINGS.getDatasetFolder()):
    copy_tree(path.sep.join(["modules", "AI", "Dataset"]), SETTINGS.getDatasetFolder())

# if settings getModel is False, then close app
if (not exists(SETTINGS.getModel())):
    print("Please, train a model before launching the API.")
    exit()

app.register_blueprint(reports)
app.register_blueprint(classifications)
app.register_blueprint(models)


# Training model centralization
def trainModel():
    modelTrainedPath = reports.trainModel()

    # Set the new model
    CLASSIFIER.getClassifier().setModel(modelTrainedPath)

    SETTINGS.resetErrorCount()
    SETTINGS.setTraining(False)


# Default route, index of the API
@app.route('/')
def index():
    user_id = USERS.getUserId(request)
    if user_id is None:
        return Response(status=401)

    reports = USERS.getReports(user_id)

    # Return all reports with their json data file
    return jsonify([json.load(open(join(SETTINGS.getReportFolder(), f, 'data.json'))) for f in reports if exists(join(SETTINGS.getReportFolder(), f, 'data.json'))])
