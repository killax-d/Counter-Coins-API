import json
from datetime import datetime
from os.path import join, dirname, sep

from services.settings import SettingsService
from modules.AI.classifier_trainer import ClassifierTrainer

SETTINGS = SettingsService('settings.json')

print("Training DEFAULT model...")

modelInfoPath = join(dirname(SETTINGS.getModel()), "info.json")

imgCount = ClassifierTrainer().train(SETTINGS.getModel(), SETTINGS.getLabel(), sep.join(["modules", "AI", "dataset", ""]), SETTINGS.getTrainEpochs())

modelInfo = {
    'id': "DEFAULT",
    'pictures_count': imgCount,
    'datetime': datetime.now().isoformat()
}
with open(modelInfoPath, 'w') as f:
    json.dump(modelInfo, f)

print("Model DEFAULT trained")

