#RECIST Worksheet generator module
#Revision 6/21/17
import docx
from docx.shared import Pt
import re
import sys
import os
import pathlib
# import comtypes.client
# import glob
# import time

def generate_RECIST_Sheets(RECISTDir, OutDir, dirName, baseNames, StudyRoot,singleSheet):
    ''' Generate the RECIST sheets for each patient in the study (if they have not been put in the excludedlist) '''
    for file in baseNames:
        MRN, SID = getMRNSID(file) #gets MRN and SID from the file name
        key = MRN+r'/'+SID #patient key
        patient = StudyRoot.patients[key] #get a specific patient

        if patient.ignore == False:
            #Patient is not ignored, user wants to include them in outputs
            if singleSheet == True:
                numExams = len(patient.exams.keys())
                for l in range (1, numExams+1):
                    #search for current exam
                    if patient.exams[l].current == True:
                        break
                RECISTSheet(RECISTDir, OutDir,patient,patient.exams[l],file) #generate sheet for exam marked as 'current'
            elif singleSheet == False:
                #iterate through all exams within the baseline->current range and create RECIST worksheets
                for key,exam in patient.exams.items():
                    if exam.ignore == False:
                        RECISTSheet(RECISTDir, OutDir,patient,exam,file)
        else:
            pass
    
    #Conversion to PDF, throws an error, but does create PDFs
    # word = comtypes.client.CreateObject('Word.Application') #launch Word instance to convert files to PDFs
    # time.sleep(0.001)
    # in_files = glob.glob(OutDir + "/*.docx")
    # try:
    #     for in_file in in_files:
    #         out_file = os.path.splitext(in_file)[0]
    #         doc = word.Documents.Open(in_file)
    #         doc.SaveAs(out_file,FileFormat = 17)
    #         doc.Close()
    # except Exception as e:
    #     word.Quit()
    #     word = None
    #     print('Error: ',e)
    
    # if word is not None:
    #     word.Quit()

def getMRNSID(file): #file arg is a str
    #extract the MRN and SID from the BL filename (expected format is MRN#xxxxxxx_xx-x-xxxx (7 digit MRN))
    regMRN = re.compile(r'\d{7}')
    regSID = re.compile(r'\w{2}-\w-\w{4}')
    MRN = regMRN.search(file).group()
    SID = regSID.search(file).group()
    return MRN,SID

def convDate(date):
    #converts date from format mm/dd/yyy to mm.dd.yyyy filepath
    return str(date.replace(r'/','.',))

def RECISTSheet(RECISTDir, OutDir,patient,exam,file):
    '''Generate a single RECIST sheet for the patient and specified exam'''
    MRN, SID = getMRNSID(file) #gets MRN and SID from the file name
    
    #### GENERAL PT DATA ####
    template = docx.Document(RECISTDir + '\\RECISTForm.docx') #open template
    table = template.tables[4] #use to print patient ID info
    table.cell(1,0).text = patient.name + '\n' + MRN

    table = template.tables[1] #print study info
    table.cell(0,1).text = SID
    if (exam.baseline == True): #based on current exam
        table.cell(0,5).text = 'X'
    else:
        table.cell(0,8).text = 'X'
    table.cell(0,3).text = 'Course ' + patient.course + '  /Day ' + patient.day

    #### TUMOR MEASUREMENT DATA ####
    table = template.tables[2] #lesion data

    totNumLesion = len(exam.lesions)
    numLesion = 0
    for lesion in exam.lesions:
        if lesion.target.lower() != 'unspecified':
            numLesion += 1

    for i in range(0,numLesion):
        row = i+1
        table.cell(row,1).text = exam.lesions[i].desc
        table.cell(row,2).text = exam.lesions[i].target

        if exam.lesions[i].newlesion == True:
            table.cell(row,3).text = "New Lesion"

        table.cell(row,4).text = exam.modality
        table.cell(row,6).text = (str(exam.lesions[i].series) + '/' + str(exam.lesions[i].slice))
        table.cell(row,7).text = str(exam.lesions[i].recistdia)
        table.cell(row,8).text = exam.date

    #Print response data
    table = template.tables[3] #response data
    table.cell(0,1).text = str(exam.trecistsum)
    table.cell(1,1).text = str(patient.baselinesum) #baseline sum
    table.cell(2,1).text = str(patient.bestresponse)
    table.cell(3,1).text = str(exam.tfrombestresponse)
    table.cell(4,1).text = str(exam.tfrombaseline)
    table.cell(5,1).text = exam.tresponse
    table.cell(6,1).text = exam.ntresponse
    table.cell(7,1).text = exam.overallresponse

    #date measured and measured by who
    table = template.tables[5]
    table.cell(0,1).text = exam.date
    table.cell(1,1).text = exam.measuredby

    #********** Temporary fix for the font size of the output RECIST worksheets ******** MUST CHANGE IN FUTURE#
    for table in template.tables[1:5]:
        for row in table.rows:
            for cell in row.cells:
                paragraphs = cell.paragraphs
                for paragraph in paragraphs:
                    for run in paragraph.runs:
                        font = run.font
                        font.size= Pt(7)
                        
    path = pathlib.Path(OutDir + r'/MRN' + MRN + "_" + SID ).mkdir(parents=True, exist_ok=True) #check if path exists (individual pt. folder) if not, create
    try:
        template.save(OutDir + r'/MRN' + MRN + "_" + SID +  r'/MRN' + MRN + "_" + SID + "_Exam_" + convDate(exam.date) + ".docx") #save word document
    except Exception as e:
        #throw error if file open
        print('Error: ',e)