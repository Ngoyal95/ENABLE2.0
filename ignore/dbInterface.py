'''
Contains functions for export/import to MongoDB database
'''

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

def testFnx(serialized):
    '''
    Test function to submit serialied patient data to the database.
    Argument is expected to be a single dict corresponding to a patient.
    '''

    client = MongoClient() # connect to localhost on port 27017
    print(client.admin.command('ping'))
    # try:
    #     # The ismaster command is cheap and does not require auth.
    #     client.admin.command('ismaster')
    # except ConnectionFailure:
    #     print("Server not available")

    db = client.test # access the 'test' db
    result = db.patients.insert_one(serialized)
    # for i in serialized:
    #     result = db.patients.insert_one(i)
    #     print(result) #view result of insertion