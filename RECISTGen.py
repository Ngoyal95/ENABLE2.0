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

def RECISTSheet(RECISTDir, OutDir, dirName, baseNames, StudyRoot):
    #creates a RECIST worksheet for each patient given the patient object
    for file in baseNames:

        MRN, SID = getMRNSID(file) #gets MRN and SID from the file name
        key = MRN+r'/'+SID #patient key

        patient = StudyRoot.patients[key] #get a specific patient

        if patient.ignore == False:
            #Patient is not ignored, user wants to include them in outputs
            
            for key,exam in patient.exams.items():
                if exam.ignore == False:
                    #Now, print RECIST Sheets for entire study (ie baseline sheet, FU1 to baseline sheet, FU2 to baseline sheet, etc)
                    template = docx.Document(RECISTDir + '\\RECISTForm.docx') #open template         
                    
                    #### ONLY PRINT RECIST DATA FOR THE EXAM SELECTED AS CURRENT ####
                    #find the 'current' exam for printing, iterate from most recent to oldest, break at first instance of current == True (set depending on user exam selection in GUI)
                    numExams = len(patient.exams.keys())
                    # for l in range (1, numExams+1):
                    #     #search for current exam
                    #     if patient.exams[l].current == True:
                    #         break

                    #### GENERAL PT DATA ####
                    table = template.tables[4] #use to print patient ID info
                    table.cell(1,0).text = patient.name + '\n' + MRN

                    table = template.tables[1] #print study info
                    table.cell(0,1).text = SID
                    if (exam.baseline == True): #based on current exam
                        table.cell(0,5).text = 'X'
                    else:
                        table.cell(0,8).text = 'X'
                    table.cell(0,3).text = 'Course ' + patient.course + '  /Day ' + patient.day

                    #### TUMOR MEASUREMENT DATA - ONLY PRINT FOR EXAM SET WITH STATUS current == True ####
                    table = template.tables[2] #lesion data
                    #exam = patient.exams[l] #current exam

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