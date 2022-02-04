from datetime import datetime
from os import makedirs, path, remove
from os.path import join, exists
from shutil import rmtree
from flask import Blueprint, Response, request
from flask.helpers import send_file
from threading import Thread
from modules.AI.classifier_trainer import ClassifierTrainer
from services.classifier import ClassifierService
import json
import uuid
from shutil import copyfile

from services.settings import SettingsService
from services.users import UsersService
reports = Blueprint('reports', __name__)

SETTINGS_FILE = path.sep.join(["settings.json"])
SETTINGS = SettingsService(SETTINGS_FILE)
USERS = UsersService()
CLASSIFIER = ClassifierService()

# GET /report?id=<uuid>
@reports.route('/report')
def report():
    user_id = USERS.getUserId(request)
    if user_id is None:
        return Response(status=401)

    # get report id from request
    if 'id' in request.args:
        id = request.args['id']

        # Not the owner
        if not isOwner(user_id, id):
            return Response(status=403)

        path = join(SETTINGS.getReportFolder(), id, 'data.json')

        # check if report exists
        if (not exists(path)):
            return Response(status=404)

        # just send the report data file
        return send_file(path, mimetype='application/json')

    return Response("{'success': false, 'message': 'Incorrect request'}", status=500, mimetype='application/json')

# GET /report/image?id=<id>
# GET /report/image?id=<id>&zone=<id>
@reports.route('/report/image')
def report_image():
    # We need an user id to proceed with firebase storage methods
    user_id = USERS.getUserId(request)
    if user_id is None:
        return Response(status=401)

    # get zone image (need report id & zone id)
    path = None
    if 'id' in request.args and 'zone' in request.args:
        id = request.args['id']
        
        # Not the owner
        if not isOwner(user_id, id):
            return Response(status=403)

        zone = request.args['zone']
        path = join(SETTINGS.getReportFolder(), id, 'zones', str(zone) + '.png')


    # get report image (need report id 'debug' or 'normal')
    elif 'id' in request.args:
        id = request.args['id']

        # Not the owner
        if not isOwner(user_id, id):
            return Response(status=403)

        # check if 'debug' is requested
        file = "detections.png" if ('debug' in request.args and request.args['debug']) else "original.png"
        path = join(SETTINGS.getReportFolder(), id, file)

        # if 'debug' is requested, check if the file exists
        # else, return the original file
        if (not exists(path)):
            path = join(SETTINGS.getReportFolder(), id, 'original.png')
    
    # if 'path' is not None, send the image
    if (path is not None):
        return send_file(path, mimetype='image/png')
    return Response("{'success': false, 'message': 'Incorrect request'}", status=500, mimetype='application/json')

# DELETE /report?uid=<uid>&id=<uuid>
@reports.route('/report', methods=['DELETE'])
def delete_report():
    # We need an user id to proceed with firebase storage methods
    user_id = USERS.getUserId(request)
    if user_id is None:
        return Response(status=401)

    if 'id' in request.args:
        id = request.args['id']
        path = join(SETTINGS.getReportFolder(), id)

        # Retrieve list from firebase
        reports = USERS.getReports(user_id)

        owner = False
        # Check if the report is owned by the user
        for (i, report) in enumerate(reports):
            if report['id'] == id:
                reports.pop(i)
                owner = True
                break
        
        # Not the owner
        if not owner:
            return Response(status=403)

        # Delete report folder if the user is the owner
        rmtree(path)

        # Remove report from firebase
        reports.remove(id)

        # Tell firebase to update
        USERS.setReports(user_id, reports)

        # Return success
        return Response("{'success': true}", status=200, mimetype='application/json')
    return Response("{'success': false, 'message': 'Incorrect request'}", status=500, mimetype='application/json')

# PUT /report/?id=<uuid>&zone=<zone_id>
# Update zone and make correction, need to set confidence to 0, to recalculate score
# TODO: Add image that are incorrect to our Dataset automatically
@reports.route('/report', methods=['PUT'])
def report_put():
    # We need an user id to proceed with firebase storage methods
    user_id = USERS.getUserId(request)
    if user_id is None:
        return Response(status=401)

    
    # edit zone result (need report id & zone id)
    if 'id' in request.args and 'zone' in request.args:
        id = request.args['id']
        zone = int(request.args['zone'])

        # Not the owner
        if not isOwner(user_id, id):
            return Response(status=403)

        # Check if the coin is in the data body of the request
        if 'coin' in request.json:
            coin = request.json['coin']
            # coin is like '1e_front'
            # '{class}_{face}'

            coinParts = coin.split('_') # split parts

            # We need only 2 parts, not less or more
            if (len(coinParts) != 2):
                return Response("{'success': false, 'message': 'Incorrect format'}", status=500, mimetype='application/json')

            # Check that the coin is in the list of valid coins
            if (coinParts[0] not in SETTINGS.getCoins()):
                return Response("{'success': false, 'message': 'Incorrect coin'}", status=500, mimetype='application/json')

            # Check that the face is in the list of valid faces
            if (coinParts[1] not in ['back','front']):
                return Response("{'success': false, 'message': 'Incorrect side'}", status=500, mimetype='application/json')

            # PATH of the data
            path = join(SETTINGS.getReportFolder(), id, 'data.json')

            # Check if the report exists
            if (not exists(path)):
                return Response(status=404)

            # Load the data from the file
            data = json.load(open(path))

            # retrieve the zone
            for zone_data in data['zones']:
                if zone_data['id'] == zone:

                    # Make path to dataset folder
                    addToDataset = False
                    # Path of folder, if is already in the generated dataset
                    oldDataset_path = join(SETTINGS.getDatasetFolder(), zone_data['coin'])
                    # Path of folder, in case if is not in the generated dataset
                    newDataset_path = join(SETTINGS.getDatasetFolder(), coin)
                    
                    # Create the folder if it does not exist
                    if (not exists(oldDataset_path)):
                        makedirs(oldDataset_path)
                    if (not exists(newDataset_path)):
                        makedirs(newDataset_path)

                    # Build path of the image
                    oldDataset_path = join(oldDataset_path, '%s_%d.png' % (id, zone))
                    newDataset_path = join(newDataset_path, '%s_%d.png' % (id, zone))

                    # Backup the original data
                    if "old_coin" not in zone_data:
                        zone_data['old_coin'] = zone_data['coin']
                        zone_data['old_confidence'] = zone_data['confidence']
                        # Need to add to our generated dataset
                        addToDataset = True

                    # Restore the original data if the new coin is the same than the old one
                    if zone_data['old_coin'] == coin:
                        # Remove from generated dataset
                        # because the new coin is the same than the old one so the AI didn't make a mistake
                        if exists(oldDataset_path):
                            remove(oldDataset_path)

                        # Restore the old data
                        zone_data['coin'] = zone_data['old_coin']
                        zone_data['confidence'] = zone_data['old_confidence']

                        # Delete the old data from json
                        del zone_data['old_coin']
                        del zone_data['old_confidence']

                        # Decrease the error count
                        SETTINGS.decErrorCount()

                    # Else, that mean the AI made a mistake
                    # need to null the old data
                    else:
                        # Remove from generated dataset
                        # in case of the previous coin was also edited and marked as incorrect
                        # ex: initial : 2e_front,
                        # request 1 : change to '1e_front'
                        # request 2 : change to '1e_back'
                        if exists(oldDataset_path):
                            # Decrease the error count if the old coin was also edited
                            SETTINGS.decErrorCount()
                            # Remove the old image
                            remove(oldDataset_path)

                        # Null the old data
                        zone_data['coin'] = coin
                        zone_data['confidence'] = 0.0
                        # Need to add to our generated dataset
                        addToDataset = True
                        # Increase the error count
                        SETTINGS.incErrorCount()
                    
                    
                    # Add the image to the dataset if needed and the coin is not a null coin
                    if (addToDataset and coinParts[0] != '0'):
                        # if is not already in training and check if error count is enought to make a new training
                        if (not SETTINGS.isTraining() and SETTINGS.getErrorCount() >= SETTINGS.getTrainAfter()):
                            # Try to start a new Thread to don't interrupt the API
                            try:
                                thread = Thread(target=trainModel)
                                thread.daemon = True
                                thread.start()
                                print("Started training")
                                SETTINGS.setTraining(True)
                            except:
                                # If an error occurs, set the training to false to cancel it
                                SETTINGS.setTraining(False)
                                pass
                        
                        # Copy the coin image to the correct dataset folder
                        copyfile(join(SETTINGS.getReportFolder(), id, "zones", "%d.png" % zone), join(SETTINGS.getDatasetFolder(), coin, '%s_%d.png' % (id, zone)))
                    break


            # Update the values
            # Calculated, score
            data['calculated'] = 0
            data['score'] = 0.0
            for zone_data in data['zones']:
                # zone_data['coin'] is like '1e_front', need to split to get the coin value
                data['calculated'] += SETTINGS.getCoins()[zone_data['coin'].split('_')[0]]
                data['score'] += zone_data['confidence']
            
            # if number of coins is 0, useless to calculate the score
            if (len(data['zones']) > 0):
                data['score'] /= len(data['zones'])

            # Update the file
            with open(path, 'w') as f:
                json.dump(data, f)

        return Response("{'success': true}", status=200, mimetype='application/json')
    return Response("{'success': false, 'message': 'Incorrect request'}", status=500, mimetype='application/json')



def isOwner(user_id, report_id):
    # Retrieve list from firebase
    reports = USERS.getReports(user_id)
    
    # Check if the report is owned by the user
    for report in reports:
        if report == report_id:
            return True


def trainModel():
    id = str(uuid.uuid4())
    print("Training model %s..." % id)

    # PATH to each file
    modelPath = join(SETTINGS.getModelFolder(), id)
    modelTrainedPath = join(modelPath, "model.h5")
    modelInfoPath = join(modelPath, "info.json")

    # Retrieve the images count for each label
    imgCount = ClassifierTrainer().train(modelTrainedPath, SETTINGS.getLabel(), SETTINGS.getDatasetFolder(), SETTINGS.getTrainEpochs())
    
    # Create the folder if it does not exist
    if (not exists(modelPath)):
        makedirs(modelPath)


    modelInfo = {
        'id': id,
        'pictures_count': imgCount,
        'datetime': datetime.now().isoformat()
    }

    # Dump the file
    with open(modelInfoPath, 'w') as f:
        json.dump(modelInfo, f)
    
    print("Model %s trained" % id)

    # update config
    CLASSIFIER.getClassifier().setModel(modelTrainedPath)
    return modelTrainedPath
