#! python3
import shelve
import easygui

prefs = shelve.open('LocalPreferences')

print('Navigate to bookmark list filepath')
BLDir = easygui.diropenbox(msg = None, title = 'Select Folder')
prefs['BLDir'] = BLDir

print('Navigate to RECIST Form location')
RECISTDir = easygui.diropenbox(msg = None, title = 'Select Folder')
prefs['RECISTDir'] = RECISTDir

print('Navigate to where to output')
OutDir = easygui.diropenbox(msg = None, title = 'Select Folder')
prefs['OutDir'] = OutDir

prefs.close()