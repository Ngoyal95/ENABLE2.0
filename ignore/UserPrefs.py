#Module for saving and getting user preferences
import shelve
import easygui

def getSettings():
	### CONSIDER USING PICKLE INSTEAD?
	shelfFile = shelve.open('LocalPreferences')
	BLDir = shelfFile['BLDir']
	RECISTDir = shelfFile['RECISTDir']
	OutDir = shelfFile['OutDir']
	#print(BLDir,RECISTDir,OutDir)
	shelfFile.close()

	return BLDir,RECISTDir,OutDir

def programInit():
	prefs = shelve.open('LocalPreferences')
	if (prefs['FirstRun']==True):
		setSettings(prefs)

	shelfFile['FirstRun'] = True #Used to check if first time user is running the interface

	prefs.close()