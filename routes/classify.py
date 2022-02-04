from datetime import datetime
from os import makedirs, path
from os.path import join, dirname, realpath
from flask import Blueprint, Response, request, jsonify
import json
import uuid
from modules.AI.utils import prepare
import numpy as np
import cv2

from services.classifier import ClassifierService
from services.settings import SettingsService
from services.users import UsersService

classifications = Blueprint('classify', __name__)

# read settings file
SETTINGS_FILE = path.sep.join(["settings.json"])
SETTINGS = SettingsService(SETTINGS_FILE)
USERS = UsersService()
CLASSIFIER = ClassifierService().getClassifier()


# POST /classify {@file: image/png}
@classifications.route('/classify', methods=['POST'])
def classify():
    user_id = USERS.getUserId(request)
    if user_id is None:
        return Response(status=401)

    if request.headers['Content-Type'].startswith('image/png'):
        nparr = np.fromstring(request.data, np.uint8)
        # decode image
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Prepare image
        # if Debug is None, that mean no circle has been detected
        image, debug, images = prepare(image)

        # Prepare data json
        data = {
            "id": str(uuid.uuid4()),
            "status": "done",
            "datetime": datetime.now().astimezone().isoformat(),
            "calculated": 0,
            "score": 0.0,
            "model": CLASSIFIER.getModel(),
            "zones": []
        }

        # Classify images
        for i in range(len(images)):
            (classification, confidence) = CLASSIFIER.predict(images[i]["image"])
            data["zones"].append({
                "id": images[i]["id"],
                "zone": {
                    "x": int(images[i]["area"]["x"]),
                    "y": int(images[i]["area"]["y"]),
                    "width": int(images[i]["area"]["width"]),
                    "height": int(images[i]["area"]["height"])
                },
                "coin": classification,
                "confidence": confidence
            })
            data['calculated'] += SETTINGS.getCoins()[classification.split('_')[0]]
            data['score'] += confidence
        
        # Define score
        if (len(images) > 0):
            data['score'] /= len(images)

        # PATH for files
        report_path = join(SETTINGS.getReportFolder(), str(data['id']))
        report_data_path = join(report_path, 'data.json')
        report_image_original_path = join(report_path, 'original.png')
        report_image_path = join(report_path, 'detections.png')
        report_zone_path = join(report_path, 'zones')
        
        # Create report folder
        makedirs(report_path)
        
        # if debug == None, that mean no circle has been detected
        if (debug is not None):
            # Circles have been detected
            makedirs(report_zone_path) # Create zone folder to store coins image
            cv2.imwrite(report_image_original_path, image) # Save original image
            cv2.imwrite(report_image_path, debug) # Save image with circles and id drawn on it
            for zone in images:
                cv2.imwrite(join(report_zone_path, str(zone["id"]) + '.png'), zone["image"]) # Save each coin image

        else:
            # No circles have been detected
            cv2.imwrite(report_image_original_path, image) # Save original image
        
        # Dump the result into a json file
        with open(report_data_path, 'w') as f:
            json.dump(data, f)

        # Retrieve list and add the new reports
        reports = USERS.getReports(user_id)
        reports.append(data["id"])

        # Tell firebase to update
        USERS.setReports(user_id, reports)

        return jsonify(data)
    return Response("{'success': false, 'message': 'Incorrect request'}", status=500, mimetype='application/json')
