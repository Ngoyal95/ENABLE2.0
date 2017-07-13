#Code to import a Bookmark List
#Revision 7/7/17
import easygui
import os
import pandas as pd
import numpy
import BLDataClasses
import re
import sys
import xlrd
from pprint import pprint
from RECISTComp import RECISTComp
from string import punctuation

def BLImport(df, root, dirName, baseNames):
    '''
    Function to import patient data from a bookmark list and store in data classes (see BLImporterUIVersion.py)
    '''
    for file in baseNames:
        MRN,SID = getMRNSID(file)
        key = (MRN+r'/'+SID)
        xl = pd.ExcelFile(dirName + r'/'+file)
        dTemp = xl.parse()
        pd.DataFrame(dTemp)

        #correct column headers
        dTemp = dTemp.rename(columns = {'Unnamed: 1':'Lesion Header'}) #name to the blank column which has the data about exam date, time, modality, description
        columnNames = list(dTemp) #get a list of the column headers
        columnNames_Update = [re.sub("\\s+(?=[^()]*\\))", "", x) for x in columnNames] #remove whitespace in prentheses (if present)
        renameCols = dict(zip(columnNames,columnNames_Update)) #dict for renaming columns
        dTemp = dTemp.rename(columns = renameCols)
        ptname = dTemp.get_value(1,'Patient Name') #get patient name before cleaning, always in same row 
        
        #NOTE: When this line is included, the days/weeks from baseline will be incorrectly determined for any exam which does not have T, NT, NL (program crashes)
        #dTemp = dropData(dTemp) #drop unnecessary rows (ie not Target or Non-Target or new lesions)
        
        root.add_patient({key:BLDataClasses.Patient(MRN,SID,ptname,columnNames_Update)}) #add patient to the patients dict under the root
        columnNames_Update.remove("Study Description") #remove these headers for lesion data extraction
        columnNames_Update.remove("Patient Name")
        extractData(dTemp,key,root,columnNames_Update)
        df.append(dTemp) #append the BL to the overall list of BLs
    pd.DataFrame(df)
    

def dropData(df):
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

def getMRNSID(file): 
    '''
    Function used to pull a patient MRN and protocol (the SID, or Study ID) from the filename, passed as a string.
    Expected file format contains continguous 7 digit MRN (ie xxxxxxx) and 7 character study protocol (ie xx-x-xxxx) seperated by an underscore.
    For example: MRNxxxxxxx_xx-x-xxxx is the recommended format.
    '''
    regMRN = re.compile(r'\d{7}')
    regSID = re.compile(r'\w{2}-\w-\w{4}')
    MRN = regMRN.search(file).group()
    SID = regSID.search(file).group()
    return MRN,SID

def extractData(df,ID,root,columnNames):
    ''' 
    ExtractData function extracts patient tumor data from the patient Bookmark List.
    Data is first stored into pandas dataframe and then into custom datastructures in BLImporterUIVersion.py 
    NOTE: 'ID' is string MRN+r'/'+SID used to find the patient in the patient dictionary, and 'root' is the StudyRoot 
    '''

    #need to iterate through the rows of the dataframe, extracting data as we proceed.
        #create a new exam at every instance of "STUDY INSTANCE UID" in Col 'Study Description' (added while parsing)
            #for subsequent rows until next instance of study header, create lesions, link them to the exam

    link = root.patients[ID] #go to patient

    examCount = 0
    lesionCount = 0
    date_modality_Flag = False #set to True when new exam found, so need to find date + modality
    dateReg = re.compile(r'^\d+/\d+/\d+')  #format MM/DD/YYYY, check at beginning of str
    timeReg = re.compile(r'\d+:\d+ \w\w')  #format HH:MM AM/PM
    beforeBaselineReg = re.compile(r'-\d+') #used to determine if an exam should be ignored

    #----Populate datastructure with patients' data----#
    for index, row in df.iterrows(): #iterate through dataframe rows to populate data structures
        SIUID = str(df.get_value(index,'Study Description'))
        lesionHeader = str(df.get_value(index,'Lesion Header')) #example: '10/10/2014 3:06 PM, CT, CTCHABDPEL (51 Days from Baseline)'
        
        if "STUDY INSTANCE" in SIUID: #locate a new exam
            examCount += 1
            date_modality_Flag = True
            link.add_exam({examCount:BLDataClasses.Exam(index,SIUID.split("STUDY INSTANCE UID: ",1)[1].strip())}) #add an exam to patient's exam list, store the 'index', and SIUID
            lesionCount = 0

        elif ~pd.isnull(lesionHeader): #found a lesion, add to current exam
            lesionCount+=1
            link.exams[examCount].add_lesion(extractLesionData(df,index,link.exams[examCount],columnNames))
            
            if date_modality_Flag == True:
                #set the date and modality of exam, also get scan area, and check if is before baseline
                date_modality_Flag = False
                modality = lesionHeader.split(', ')[-2] #modality is always 2nd to last entry in the lesionheader
                date = dateReg.search(str(df.get_value(index,'Lesion Header'))).group()
                tCheck = timeReg.search(str(df.get_value(index,'Lesion Header')))
                if tCheck == None:
                    time = ''
                else:
                    time = tCheck.group()
                
                examDescription = extractDescription(date,time,modality,lesionHeader)

                link.exams[examCount].add_date(date)
                link.exams[examCount].add_time(time)
                link.exams[examCount].add_modality(modality)
                link.exams[examCount].add_description(examDescription)

                if beforeBaselineReg.search(lesionHeader) is not None:
                    #exam is before baseline, set it
                    link.exams[examCount].add_ignore(True)    
    
    for key,exam in link.exams.items():
        #-----Organize lesions by Target, then Non-Target, then NL, then unspec.; also get all clinician names who measured----#
        numLesion = 0 #number of T,NT,or NL lesions
        for lesion in exam.lesions:
            if lesion.params['Target'].lower() != 'unspecified':
                numLesion += 1

        #NOTE: THIS STILL WORKS EVEN IF WE DROP THE ROWS WHICH ARE UNSPEC. LESIONS (OR BLANK 'Target' FIELD)
        exam.lesions.sort(key=lambda x:x.params['Target'], reverse = False) #sort in order NewLesion,NonTarget,Target,Unspec
        ptA = exam.lesions[:numLesion] #slice to extract the Newlesion,nontarget,target lesions
        ptA.sort(key = lambda x:x.params['Target'], reverse = True) #reverse alphabetize the slice
        exam.lesions = ptA + exam.lesions[numLesion:] #append to the Unspec. lesions
        #Now order of list of lesions  is T,NT,NL,Unspec. (needed for proper recist sheet printing)

        #------Get all names of people who measured in the exam-----#
        measurers = list(set([lesion.params['Creator'] for lesion in exam.lesions]))
        creators = ', '.join(map(str,measurers))
        exam.measuredby = creators

        #check if all lymph are less than 1cm in size and set flag in exam obj
        #Also get if exam contains no T,NT,or NL to set flag containsnoT_NT_NL in the exam object (needed later to detect bad baseline choices)
        detNoLs = True
        beforeBaseline = False #used to determine which exams to ignore (i.e they are before baseline and were exported as such (so they have a -# days from baseline))
        for lesion in exam.lesions:
            
            lymph = 1 #set to 0 if any lymph short axis is >10mm (1cm)
            if(lesion.params['Sub-Type'] == 'Lymph'):
                if lesion.params['Short Diameter (mm)'] > 10:
                    lymph = 0
            exam.lymphsize = bool(lymph) #sets lymphsize = True if all lymph have short axis < 1cm, else False
            
            if (lesion.params['Target'].lower() == 'target' or lesion.params['Target'].lower() == 'non-target' or lesion.newlesion == True):
                detNoLs = False
        
        exam.add_containsnoT_NT_NL(detNoLs) #set, defaults to False if we find T, NT, or NL

    link.exams[1].add_current(True) #set the first exam to be current by default
    link.exams[examCount].add_baseline(True) #set last exam to baseline by default

    #----prompt user for course# and day----#
    # ptName = link.name + ' (' + str(ID) + ')'
    # textMsg = "Enter course# & day# (numbers only) for patient:\n" + ptName
    # title = 'Enter patient data'
    # fieldNames = ['  Course#:','  Day#:'] #spaces added for appearance formatting
    
    # try:
    # 	fieldVals = easygui.multenterbox(textMsg, title, fieldNames)
    # except TypeError:
    # 	course = '-'
    # 	day = '-'

    # if fieldVals == ['', '']:
    # 	course,day = ['-','-']
    # elif fieldVals == None:
    # 	course,day = ['-','-']
    # else:
    # 	course,day = fieldVals
    # 	link.add_courseday(course,day)

    #at this point all patient data has been stored in datastructures held by StudyRoot
    #next: Perform RECIST Calcs **** DONE WITH SEPERATE BUTTON IN GUI *****

def extractLesionData(df,index,exam,columnNames):
    '''
    Function used to pull the data for a lesion from the bookmark list.
    Data pulled depends on what fields are available in the BL.
    Function creates and returns a lesion object with attributes populated.
    '''

    # Used to check for lesion type - if not Target, Non-Target, or New lesion, call it Unspecified
    tsearch = re.compile('\s?target\s?|\st\s?', re.IGNORECASE)
    ntsearch = re.compile('\s?non-target\s?|\snt\s?|\snon target\s?', re.IGNORECASE)
    NLcheck = re.compile('\s?new lesion\s?|\snl\s?', re.IGNORECASE)

    targetStr = str(df.get_value(index, 'Target')).lower()
    lesionDesc = str(df.get_value(index, 'Description')).lower()

    lesion = BLDataClasses.Lesion()
    params = {}
    for header in columnNames:
        if header == 'Series' or header == 'Slice#':
            params[header] = int(df.get_value(index, header))
        else:
            params[header] = df.get_value(index, header)
    
    if targetStr == 'target' or bool(tsearch.search(str(df.get_value(index, 'Description')))):
        lesionType = 'Target'
    elif targetStr == 'non-target'or bool(ntsearch.search(str(df.get_value(index, 'Description')))):
        lesionType = 'Non-Target'
    elif bool(NLcheck.search(str(df.get_value(index, 'Description')))):
        lesionType = 'New Lesion'
        lesion.add_newlesion(True)
        lesion.set_target('New lesion')
        exam.add_containsnewlesion(True) # exam contains a new lesion, exclude from best response determination
    else:
        lesionType = 'Unspecified'

    params['Target'] = lesionType # store parameters
  
    lesion.add_params(params)

    return lesion

def extractDescription(date,time,modality,lesionHeader):
    ''' 
    Strip extraneous data from the 'lesion header' in order to extract the study description
    typical format is: MM/DD/YYYY HH:MM AM/PM, DESCRIPTION, MODALITY, (body part) (# days from baseline)
    NOTE: the description might empty!
    '''
    str1  = lesionHeader.replace(date,'').replace(lesionHeader.split(', ')[-1],'').replace(modality,'')
    if time is not '':
        str1 = str1.replace(time,'') #check because time might be None -> time = '', so we need to check seperately.
    str1 = re.sub(r'^[^a-zA-Z0-9]*', '',str1) #strip front chars (whitespace and commas)
    str1 = str1[::-1] #reverse str
    str1 = re.sub(r'^[^a-zA-Z0-9]*', '',str1) #strip trailing chars (whitespace and commas), now at front of reversed str
    return str1[::-1]