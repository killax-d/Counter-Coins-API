from os import path
from os.path import join, exists, dirname, realpath
from flask import Blueprint, Response, request, jsonify
import json

from services.settings import SettingsService

models = Blueprint('models', __name__)

# read settings file
SETTINGS_FILE = path.sep.join(["settings.json"])
SETTINGS = SettingsService(SETTINGS_FILE)

# GET /model?id=<model_id>
@models.route('/model')
def getModel():
    model_id = request.args.get("id")
    if model_id is None:
        return Response(status=400)

    # Get model path
    modelPath = path.sep.join(SETTINGS.getModelFolder(), model_id)

    # Check if its the default Model "AI"
    if model_id == "AI":
        modelPath = path.sep.join(["modules", "AI"])

    # PATH of the model data file
    modelInfoPath = path.sep.join(modelPath, "info.json")

    # Model doesn't exist in the model folder
    if (not exists(modelInfoPath)):
        return Response(status=404)

    # Read model data file
    with open(modelInfoPath, 'r') as f:
        modelInfo = json.load(f)
    return jsonify(modelInfo)
