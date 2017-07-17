'''
Functions related to JSON serialization, uploading to database backend, and pulling from database backend
'''
#7/17/17

import json
import copy
from bson import json_util
from pprint import pprint
from dbInterface import testFnx
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

def json_serialize(foo):
    '''
    Function to serialize patient objects in preparation for upload to MongoDB database.
    Function calls database push function.
    '''
    localfoo = copy.deepcopy(foo) #need to copy to prevent modifying original StudyRoot

    for k1, patient in localfoo.patients.items():
        patientDict = vars(patient)
        for k2,exam in patient.exams.items():
            newLesionList = []
            for lesion in exam.lesions:
                newLesionList.append(vars(lesion))
            num = exam.exam_num #use to insert into correct dict location in patient.exams
            patientDict['exams'][num] = vars(exam)
            patientDict['exams'][num]['lesions'] = newLesionList
        pushVal = json.loads(json.dumps(patientDict, default=json_util.default,sort_keys=True, indent=4,allow_nan = True))
        push_to_mongodb(pushVal)

def push_to_mongodb(serialized):
    '''
    Function to submit serialied patient data to the database.
    Argument is expected to be a single dict corresponding to a patient.
    '''

    client = MongoClient() # connect to localhost on port 27017
    # try:
    #     # The ismaster command is cheap and does not require auth.
    #     client.admin.command('ismaster')
    # except ConnectionFailure:
    #     print("Server not available")

    db = client.test # access the 'test' db
    result = db.patients.insert_one(serialized)