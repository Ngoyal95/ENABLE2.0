#! python3

from UserPrefs import getSettings
from BLImporter import fileSelect,BLImport
from RECISTComp import RECISTComp
import BLDataClasses
from RECISTGen import RECISTSheet


BLDir,RECISTDir,OutDir = getSettings()
dirName,baseNames = fileSelect(BLDir)
StudyRoot = BLDataClasses.StudyRoot() #create a study root
BLImport(StudyRoot,dirName,baseNames) #now patient data stored in memory, accessable through StudyRoot
RECISTSheet(RECISTDir,OutDir,dirName,baseNames,StudyRoot) #generates RECIST sheets for all patients