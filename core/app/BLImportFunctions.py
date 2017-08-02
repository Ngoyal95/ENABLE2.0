#Code to import a Bookmark List
#Revision 7/7/17
import os
import pandas as pd
import core.app.BLDataClasses as BLDataClasses
import re
import xlrd
import queue
from multiprocessing import Pool
import multiprocessing as mp
from functools import partial
from pprint import pprint

def bl_import(df, root, dirName, baseNames):
    '''
    Function to import patient data from a bookmark list and store in data classes (see BLImporterUIVersion.py)
    '''
    for file in baseNames:
        MRN,SID = get_mrn_sid(file)
        key = (MRN+r'/'+SID)
        xl = pd.ExcelFile(dirName + r'/'+file)
        dTemp = xl.parse() # parse_dates=True so that date values are not type 'Timestamp'

        if 'Study Date' in list(dTemp):
            #dTemp['Study Date'] = pd.to_datetime(dTemp['Study Date'],format= "%H:%M:%S %Y-%d-%m") #nconvert Timestamp datatype --> datetime datatype compatible with Python
            dTemp = dTemp.drop('Study Date',1)

        pd.DataFrame(dTemp)
        dTemp = dTemp.where((pd.notnull(dTemp)),None) #convert nan to None for JSON compliance

        #correct column headers
        dTemp = dTemp.rename(columns = {'Unnamed: 1':'Lesion Header'}) #name to the blank column which has the data about exam date, time, modality, description
        columnNames = list(dTemp) #get a list of the column headers
        columnNames_Update = [re.sub("\\s+(?=[^()]*\\))", "", x) for x in columnNames] #remove whitespace in prentheses (if present)
        renameCols = dict(zip(columnNames,columnNames_Update)) #dict for renaming columns
        dTemp = dTemp.rename(columns = renameCols)
        ptname = dTemp.get_value(1,'Patient Name') #get patient name before cleaning, always in same row 
        
        #NOTE: When this line is included, the days/weeks from baseline will be incorrectly determined for any exam which does not have T, NT, NL (program crashes)
        #dTemp = drop_df_rows(dTemp) #drop unnecessary rows (ie not Target or Non-Target or new lesions)
        
        root.add_patient({key:BLDataClasses.Patient(MRN,SID,ptname,columnNames_Update)}) #add patient to the patients dict under the root
        columnNames_Update.remove("Study Description") #remove these headers for lesion data extraction
        columnNames_Update.remove("Patient Name")
        extractData(dTemp,key,root,columnNames_Update)
        df[key] = dTemp #append the BL to the overall dict of BL tables
    pd.DataFrame(df[key])




        


def drop_df_rows(df):
    NLcheck = re.compile('\s+new lesion\s+|\snl\s+', re.IGNORECASE)
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

def get_mrn_sid(file): 
    '''
    Function used to pull a patient MRN and protocol (the SID, or Study ID) from the filename, passed as a string.
    Expected file format contains continguous 7 digit MRN (ie xxxxxxx) and 7 character study protocol (ie xx-x-xxxx) seperated by an underscore.
    For example: MRN#######_##-X-#### is the recommended format.
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
    link = root.patients[ID] #selected patient
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
            link.add_exam({examCount:BLDataClasses.Exam(examCount,SIUID.split("STUDY INSTANCE UID: ",1)[1].strip())}) #add an exam to patient's exam list, store the 'index', and SIUID
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
                
                description = extractDescription(date,time,modality,lesionHeader)
                link.exams[examCount].add_date_time_modality_description(date,time,modality,description)

                if beforeBaselineReg.search(lesionHeader) is not None:
                    #exam is before baseline, set it to ignore
                    link.exams[examCount].add_ignore(True)    
    
    for key,exam in link.exams.items():
        #-----Organize lesions by Target, then Non-Target, then NL, then unspec.; also get all clinician names who measured----#
        numLesion = 0 #number of T,NT,or NL lesions
        for lesion in exam.lesions:
            if lesion.params['Target'].lower() != 'unspecified':
                numLesion += 1

        exam.lesions.sort(key=lambda x:x.params['Target'], reverse = False) #sort in order NewLesion,NonTarget,Target,Unspec for RECIST sheet printing
        ptA = exam.lesions[:numLesion] #slice to extract the Newlesion,nontarget,target lesions
        ptA.sort(key = lambda x:x.params['Target'], reverse = True) #reverse alphabetize the slice
        exam.lesions = ptA + exam.lesions[numLesion:] #append to the Unspec. lesions

        measurers = list(set([lesion.params['Creator'] for lesion in exam.lesions])) #get names of all people who measured in an exam
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

def extractLesionData(df,index,exam,columnNames):
    '''
    Function used to pull the data for a lesion from the bookmark list.
    Data pulled depends on what fields are available in the BL.
    Function creates and returns a lesion object with attributes populated.
    '''

    # Used to check for lesion type - if not Target, Non-Target, or New lesion, call it Unspecified
    tsearch = re.compile('\s+target\s+|\s+t\s+', re.IGNORECASE)
    ntsearch = re.compile('\s+non-target\s+|\s+nt\s+|\snon target\s+', re.IGNORECASE)
    NLcheck = re.compile('\s+new lesion\s+|\s+nl\s+', re.IGNORECASE)

    targetStr = str(df.get_value(index, 'Target')).lower()
    lesionDesc = str(df.get_value(index, 'Description')).lower()

    lesion = BLDataClasses.Lesion()
    params = {}
    for header in columnNames:
        #pull lesion data from present columns
        if header == 'Series' or header == 'Slice#':
            params[header] = int(df.get_value(index, header))
        else:
            params[header] = df.get_value(index, header)
    
    if targetStr == 'target' or bool(tsearch.search(lesionDesc)):
        params['Target'] = 'Target'
    elif targetStr == 'non-target'or bool(ntsearch.search(lesionDesc)):
        params['Target'] = 'Non-Target'
    elif bool(NLcheck.search(lesionDesc)):
        params['Target'] = 'New Lesion'
        lesion.add_newlesion(True)
        lesion.set_target('New lesion')
        exam.add_containsnewlesion(True) # exam contains a new lesion, exclude from best response determination
    else:
        params['Target'] = 'Unspecified'
 
    lesion.add_params(params)
    return lesion

def extractDescription(date,time,modality,lesionHeader):
    ''' 
    Extraction the study description which includes the areas of the body scanned.
    '''

    # Strip extraneous data from the 'lesion header' in order to extract the study description
    # typical format is: MM/DD/YYYY HH:MM AM/PM, DESCRIPTION, MODALITY, (body part) (# days from baseline)
    # NOTE: the description might empty!
    
    str1  = lesionHeader.replace(date,'').replace(lesionHeader.split(', ')[-1],'').replace(modality,'')
    if time is not '':
        str1 = str1.replace(time,'') #check because time might be None -> time = '', so we need to check seperately.
    str1 = re.sub(r'^[^a-zA-Z0-9]*', '',str1) #strip front chars (whitespace and commas)
    str1 = str1[::-1] #reverse str
    str1 = re.sub(r'^[^a-zA-Z0-9]*', '',str1) #strip trailing chars (whitespace and commas), now at front of reversed str
    return str1[::-1]

#### MULTI THREADING CODE ####
def extractData_multi(df,patient,columnNames):
    ''' 
    ExtractData function extracts patient tumor data from the patient Bookmark List.
    Data is first stored into pandas dataframe and then into custom datastructures in BLImporterUIVersion.py 
    NOTE: 'ID' is string MRN+r'/'+SID used to find the patient in the patient dictionary, and 'root' is the StudyRoot 
    '''
    link = patient
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
            link.add_exam({examCount:BLDataClasses.Exam(examCount,SIUID.split("STUDY INSTANCE UID: ",1)[1].strip())}) #add an exam to patient's exam list, store the 'index', and SIUID
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
                
                description = extractDescription(date,time,modality,lesionHeader)
                link.exams[examCount].add_date_time_modality_description(date,time,modality,description)

                if beforeBaselineReg.search(lesionHeader) is not None:
                    #exam is before baseline, set it to ignore
                    link.exams[examCount].add_ignore(True)    
    
    for key,exam in link.exams.items():
        #-----Organize lesions by Target, then Non-Target, then NL, then unspec.; also get all clinician names who measured----#
        numLesion = 0 #number of T,NT,or NL lesions
        for lesion in exam.lesions:
            if lesion.params['Target'].lower() != 'unspecified':
                numLesion += 1

        exam.lesions.sort(key=lambda x:x.params['Target'], reverse = False) #sort in order NewLesion,NonTarget,Target,Unspec for RECIST sheet printing
        ptA = exam.lesions[:numLesion] #slice to extract the Newlesion,nontarget,target lesions
        ptA.sort(key = lambda x:x.params['Target'], reverse = True) #reverse alphabetize the slice
        exam.lesions = ptA + exam.lesions[numLesion:] #append to the Unspec. lesions

        measurers = list(set([lesion.params['Creator'] for lesion in exam.lesions])) #get names of all people who measured in an exam
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

def multi_process_import(df,root,dirName,baseNames):
    # pool = Pool()
    # func = partial(target,root,dirName,baseNames)
    # pool.close()
    # pool.join()
    # print(vars(root))

    out_q = mp.Queue()
    procs = []

    for f in baseNames:
        p = mp.Process(target = single_bl_import,args=(dirName,f,out_q))
        procs.append(p)
        p.start()

    #collect results
    for i in range(0,len(baseNames)):
        pt = out_q.get()
        key = pt.mrn + '/' + pt.study_protocol
        root.patients[key] = pt
    
    for p in procs:
        p.join()

    return root

    #results = Pool(len(baseNames)).map(partial(single_bl_import,dirName),baseNames) #list of patient objects

    # for pt in results:
    #     key = str(pt.mrn) + '/' + str(pt.study_protocol)
    #     root.patients[key] = pt
    #     #pprint(pt)

def single_bl_import(dirName,file,out_q):
    MRN,SID = get_mrn_sid(file)
    key = (MRN+r'/'+SID)
    xl = pd.ExcelFile(dirName + r'/'+file)
    dTemp = xl.parse() # parse_dates=True so that date values are not type 'Timestamp'

    if 'Study Date' in list(dTemp):
        #dTemp['Study Date'] = pd.to_datetime(dTemp['Study Date'],format= "%H:%M:%S %Y-%d-%m") #nconvert Timestamp datatype --> datetime datatype compatible with Python
        dTemp = dTemp.drop('Study Date',1)

    pd.DataFrame(dTemp)
    dTemp = dTemp.where((pd.notnull(dTemp)),None) #convert nan to None for JSON compliance

    #correct column headers
    dTemp = dTemp.rename(columns = {'Unnamed: 1':'Lesion Header'}) #name to the blank column which has the data about exam date, time, modality, description
    columnNames = list(dTemp) #get a list of the column headers
    columnNames_Update = [re.sub("\\s+(?=[^()]*\\))", "", x) for x in columnNames] #remove whitespace in prentheses (if present)
    renameCols = dict(zip(columnNames,columnNames_Update)) #dict for renaming columns
    dTemp = dTemp.rename(columns = renameCols)
    ptname = dTemp.get_value(1,'Patient Name') #get patient name before cleaning, always in same row 
    
    #NOTE: When this line is included, the days/weeks from baseline will be incorrectly determined for any exam which does not have T, NT, NL (program crashes)
    #dTemp = drop_df_rows(dTemp) #drop unnecessary rows (ie not Target or Non-Target or new lesions)
    
    #root.add_patient({key:BLDataClasses.Patient(MRN,SID,ptname,columnNames_Update)}) #add patient to the patients dict under the root
    patient = BLDataClasses.Patient(MRN,SID,ptname,columnNames_Update)
    columnNames_Update.remove("Study Description") #remove these headers for lesion data extraction
    columnNames_Update.remove("Patient Name")
    extractData_multi(dTemp,patient,columnNames_Update)
    out_q.put(patient)