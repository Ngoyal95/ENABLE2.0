#7/14/17

import json
from bson import json_util
from pprint import pprint

def json_serialize(StudyRoot):
    '''
    Maps the StudyRoot to a JSON object format for uploading to the MongoDB database.
    Returns a list of JSON-format objects.
    '''

    for key,patient in StudyRoot.patients.items():
        for keys,exams in patient.exams.items():
            for lesion in exams.lesions:
                print(json.dumps(lesion.params, default=json_util.default,sort_keys=True, indent=4,allow_nan = True))

    