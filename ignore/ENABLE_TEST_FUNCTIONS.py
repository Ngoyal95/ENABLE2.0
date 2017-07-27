import easygui
import os
import pandas as pd
import numpy
import BLDataClasses
import re
import sys
from pprint import pprint

class TestFunctions:
    def __init__(self):
        print ("init") # never prints

    def fileSelect(self):
        try: #catch error when user hits "ESC" in file select dialogue
            filePath = easygui.fileopenbox(msg = None, title = 'Select Bookmark List(s)', multiple = True)
            dirName = os.path.dirname(filePath[0]) #all BL in same directory, take dir from first
            baseNames = [] #initialize list of base names
            for i in filePath:
                baseNames.append(os.path.basename(i)) #add the base names to a list
            return dirName,baseNames,0 #error code is last return val

        except Exception as e:
            print("Error: ",e)
            return None

