#Code to import a Bookmark List

import easygui
import os
import pandas as pd
import numpy
import BLDataClasses
import re
import sys
from pprint import pprint
from RECISTComp import RECISTComp

def fileSelect(BLDir):
	#function to select file(s) and obtain the directory name (dirName) and base name(s) (baseNames) 
	#BLDir = BLDir.replace("\\","\\\\")
	defaultPath = BLDir + '\\'

	try: #catch error when user hits "ESC" in file select dialogue
		filePath = easygui.fileopenbox(msg = None, title = 'Select Bookmark List(s)', default = defaultPath, multiple = True)
		dirName = os.path.dirname(filePath[0]) #all BL in same directory, take dir from first
		baseNames = [] #initialize list of base names
		for i in filePath:
			baseNames.append(os.path.basename(i)) #add the base names to a list
		return dirName,baseNames,0 #error code is last return val

	except Exception:
		#print('No Bookmark List(s) imported')
		return '','',1

def BLImport(root,dirName,baseNames):
	#function to open a bookmark list, store in in pandas dataframes, and clean the dataframes
	renameCols ={'Unnamed: 1':'Lesion Header','RECIST Diameter ( mm )':'RECIST Diameter (cm)', 'Long Diameter ( mm )':'Long Diameter (cm)',\
				'Short Diameter ( mm )':'Short Diameter (cm)','Volume ( mm³ )':'Volume (cm³)','HU Mean ( HU )':'HU Mean (HU)'}
	colsA = list({'RECIST Diameter (cm)','Long Diameter (cm)','Short Diameter (cm)'})
	colsB = list({'RECIST Diameter (cm)','Long Diameter (cm)','Short Diameter (cm)','Volume (cm³)'})

	df = [] #final dataframe list, stores all BLs imported
	dList = []
	flag = 0
	for file in baseNames:
		xl = pd.ExcelFile(dirName + r'/' + file)
		dTemp = xl.parse()
		pd.DataFrame(dTemp)

		#correct column headers
		dTemp = dTemp.rename(columns = renameCols)

		#correct mm to cm
		dTemp[colsA] = dTemp[colsA].apply(lambda x: x/10, 0) #mm --> cm
		dTemp['Volume (cm³)'] = dTemp['Volume (cm³)'].apply(lambda x: x/1000, 0) #mm^3 --> cm^3
		dTemp[colsB] = dTemp[colsB].round(decimals=1) #round to one decimal place

		#drop unnecessary rows (ie not Target or Non-Target)
		#NOTE: **********************Drop criteria needs to be updated in future to incorporate new lesions**********************************
		dTemp = dropData(dTemp)
		
		MRN,SID = getMRNSID(file)
		root.add_patient({(MRN+r'/'+SID):BLDataClasses.Patient(MRN,SID)}) #add patient to the patients dict under the root
		extractData(dTemp,(MRN+r'/'+SID),root)

		df.append(dTemp) #append the BL to the overall list of BLs
	pd.DataFrame(df)
	#print(df)

def dropData(df):
	#df = df.dropna(subset=['Study Description','Target'], how='all') #drop rows where cols are "nan" (empty)
	NLcheck = re.compile('\s?new lesion\s?|\snl\s?', re.IGNORECASE)
	dropIndices = [] #list of indices to drop
	for index, row in df.iterrows():
		#iterate over rows, get indices of rows to drop, acces column with row['col header']
		#drop if Unspecified, or NOT Target or Non-Target
		#New lesions not dropped as long as Description field has keywords 'new lesion #' or 'nl #' (spaces between words and number optional)

		if (pd.isnull(row['Study Description']) and (pd.isnull(row['Target']) | bool(row['Target'] == 'Unspecified')) \
			and not bool(NLcheck.search(str(row['Description']))) ):
				dropIndices.append(index)

	df.drop(df.index[dropIndices], inplace = True)

	return df

def getMRNSID(file): #file arg is a str
	#extract the MRN and SID from the BL filename (expected format is MRN#xxxxxxx_xx-x-xxxx (7 digit MRN))
	regMRN = re.compile(r'\d{7}')
	regSID = re.compile(r'\w{2}-\w-\w{4}')
	MRN = regMRN.search(file).group()
	SID = regSID.search(file).group()
	return MRN,SID

def extractData(df,ID,root):
	#function pulls patient tumor data from a BL stored in a pandas df, stores in the custom data structures (see BLDataClasses.py)
	#ID is string MRN+r'/'+SID used to find the patient in the patient dictionary
	#root is study root

	#need to iterate through the rows of the dataframe, extracting data as we proceed.
		#create a new exam at every instance of "STUDY INSTANCE UID" in Col B
			#for subsequent rows until next instance of study header, create lesions, link them to the exam

	link = root.patients[ID] #go to patient
	
	#----prompt user for course# and day----#
	ptName = link.name + " (" + ID + ")"
	textMsg = "Enter course# & day# (numbers only) for patient: " + ptName
	title = 'Enter patient data'
	fieldNames = ['Course#:','Day#:']
	
	try:
		fieldVals = easygui.multenterbox(textMsg, title, fieldNames)
	except TypeError:
		course = '-'
		day = '-'

	if fieldVals == ['', '']:
		course,day = ['-','-']
	elif fieldVals == None:
		course,day = ['-','-']
	else:
		course,day = fieldVals
	
	link.add_courseday(course,day)

	examCount = 0
	lesionCount = 0
	date_modality_Flag = False #set to True when exam date + modality found
	name = True
	dateReg = re.compile(r'\d+/\d+/\d+')
	modalityReg = re.compile(r' \w+')

	#----Populate datastructure with patients' data----#
	for index, row in df.iterrows(): #iterate through dataframe rows to populate data structures
		SIUID = str(df.get_value(index,'Study Description'))
		lesionCheck = str(df.get_value(index,'Lesion Header'))

		if "STUDY INSTANCE" in SIUID: #locate a new exam
			examCount += 1
			date_modality_Flag = True
			link.add_exam({examCount:BLDataClasses.Exam(index)})
			lesionCount = 0


		elif ~pd.isnull(lesionCheck): #found a lesion, add to current exam
			lesionCount+=1
			link.exams[examCount].add_lesion(extractLesionData(df,index,link.exams[examCount]))
			
			if date_modality_Flag == True:
				#set the date and modality of exam
				date_modality_Flag = False
				link.exams[examCount].add_date(dateReg.search(str(df.get_value(index,'Lesion Header'))).group())
				link.exams[examCount].add_modality(modalityReg.search(str(df.get_value(index,'Lesion Header'))).group())
				
				if name == True:
					link.add_name(str(df.get_value(index,'Patient Name')))
					name = False
	
	
	for key,exam in link.exams.items():
		#-----Organize lesions by Target, then Non-Target; also get all clinician names who measured----#
		exam.lesions.sort(key=lambda x:x.target, reverse = True)

		#get all names of people who measured in the exam
		measurers = list(set([lesion.creator for lesion in exam.lesions]))
		creators = ', '.join(map(str,measurers))
		exam.measuredby = creators

		#check if all lymph are less than 1cm in size and set flag in exam obj
		for lesion in exam.lesions:
			lymph = 1 #set to 0 if any lymph short axis is >1cm
			if(lesion.subtype == 'Lymph'):
				if lesion.shortdia > 1:
					lymph = 0
			exam.lymphsize = bool(lymph) #sets lymphsize = True if all lymph have short axis < 1cm, else False

		#DEBUG CODE
		'''
		for lesion in link.exams[exam].lesions:
			pprint(vars(lesion))
		'''

	link.exams[examCount].add_baseline(True) #set last exam to baseline

	#Perform RECIST Calcs
	RECISTComp(link) #pass current patient object as argument


def extractLesionData(df,index,exam):
	lesion = BLDataClasses.Lesion( \
		str(df.get_value(index, 'Follow-Up')), str(df.get_value(index, 'Name')), str(df.get_value(index, 'Tool')), \
		str(df.get_value(index, 'Description')), str(df.get_value(index, 'Target')), str(df.get_value(index, 'Sub-Type')), \
		int(df.get_value(index, 'Series')), int(df.get_value(index, 'Slice#')), float(df.get_value(index, 'RECIST Diameter (cm)')), \
		float(df.get_value(index, 'Long Diameter (cm)')), float(df.get_value(index,'Short Diameter (cm)')), \
		float(df.get_value(index, 'Volume (cm³)')), float(df.get_value(index,'HU Mean (HU)')), str(df.get_value(index,'Creator'))  )

	NLcheck = re.compile('\s?new lesion\s?|\snl\s?', re.IGNORECASE)
	
	if bool( NLcheck.search(str(df.get_value(index,'Description'))) ):
		lesion.add_newlesion(True)
		lesion.set_target('New lesion')
		exam.add_containsnewlesion(True) #exam contains a new lesion, exclude from best response determination
	
	return lesion