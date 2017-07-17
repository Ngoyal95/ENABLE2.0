#7/14/17

import json
import copy
from bson import json_util
from pprint import pprint
from dbInterface import testFnx

# def json_serialize(StudyRoot):
#     '''
#     Maps the StudyRoot to a JSON object format for uploading to the MongoDB database.
#     Returns a list of JSON-format objects.
#     '''
#     """NOTES"""
#     """
#     The lesion object appears to serialize okay, but the serialized item is NOT correct format. It needs to then be json.loads
#     Simple solution is to use dict(vars(lesion)) which produces a dictionary from the lesion object, and this can be inserted into db

#     """
#     lesions = [] #list for inserting into DB
#     for key,patient in StudyRoot.patients.items():
#         for keys,exams in patient.exams.items():
#             for lesion in exams.lesions:
#                 #serialized = json.dumps(vars(lesion), default=json_util.default,sort_keys=True, indent=4,allow_nan = True)
#                 #unserialized = json.loads(serialized, object_hook=json_util.object_hook)
#                 serialized = vars(lesion)
#                 lesions.append(serialized)

#     testFnx(lesions) # submit to db

def json_serialize(foo):
    '''
    Test function to dump objects as dicts to see their format.
    vars(patient), vars(exam), and vars(lesion) are all dictionaries
    '''
    localfoo = copy.deepcopy(foo) #need to copy to prevent modifying original StudyRoot

    # for key,patient in StudyRoot.patients.items():
    #     pprint(vars(patient))
    # # vars(patient) is a dictionary!

    # print('PATIENT EXAM: \n')
    # pprint(vars(patient.exams[1]))
    # # vars(exam) is also a dictionary

    # print('PATIENT LESION: \n')
    # pprint(vars(patient.exams[1].lesions[1]))
    #also a dictionary

    rootDict = vars(localfoo)
    for k1, patient in localfoo.patients.items():
        patientDict = vars(patient)
        for k2,exam in patient.exams.items():
            newLesionList = []
            for lesion in exam.lesions:
                newLesionList.append(vars(lesion))
            num = exam.exam_num #use to insert into correct dict location in patient.exams
            patientDict['exams'][num] = vars(exam)
            patientDict['exams'][num]['lesions'] = newLesionList
        rootDict['patients'][k1] = patientDict
    
    #pprint(rootDict['patients'])
    #testFnx(rootDict)

    
    #dumped = json.dumps(rootDict)
    #print('\n\n',dumped)
    #loaded = json.loads(json.dumps(rootDict))
    #print('\n\n',loaded)

    #print(vars(localfoo))
    #pprint(vars(localfoo))

    #print(type(vars(localfoo)))

    # print(json.dumps(vars(localfoo)))

    # if vars(localfoo) == rootDict:
    #     print("TRUE THEY ARE EQAL")

    #testFnx(vars(localfoo))

    #testFnx(json.dumps(vars(localfoo)))
    pushVal = json.loads(json.dumps(patientDict, default=json_util.default,sort_keys=True, indent=4,allow_nan = True))
    print(len(pushVal))
    testFnx(pushVal)