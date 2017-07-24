#RECIST computation module
#Revision 7/14/17
from pprint import pprint
from datetime import date

def recist_computer(patient):
    '''
    Function computes RECIST values
    '''
    tsum = 0
    ntsum = 0
    for key, exam in patient.exams.items():
        for lesion in exam.lesions:
            #if lesion.params['Tool'].lower() == 'two diameters' or lesion.params['Tool'].lower() == 'line': #ignore any other type of segmentation
                #Only Target and Non-Target lesions considered for summation
            if lesion.params['RECIST Diameter (mm)'] is not None:
                if lesion.params['RECIST Diameter (mm)'] is not None:
                    tsum += round(round(lesion.params['RECIST Diameter (mm)'],2)/10, 1)
                else:
                    tsum += round(round(lesion.params['RECIST Diameter (mm)'],2)/10, 1)
        exam.add_RECISTsums(tsum, ntsum)
        tsum = 0
        ntsum = 0

    BR = find_best_response_sum(patient) #best response sum (variable used later)
    patient.add_bestresponse(BR)

    #compute percent changes in diameters
    for key, exam in patient.exams.items():
        if exam.baseline == True:
            baselineTRS = exam.trecistsum
            patient.add_baselinesum(baselineTRS)
            baselineNTRS = exam.ntrecistsum

    # Perform computations for every exam, relative to baseline (even if the selected current exam is after the most recent)
    # because want to keep all patient data, just only print the exam selected as current to the RECIST sheet
    numKeys = len(patient.exams.keys())
    for i in range(1,numKeys+1): #+1 on end of range because exam dict keywords are numerated from 1
        exam = patient.exams[i]
        currTRS = exam.trecistsum
        currNTRS = exam.ntrecistsum
        tfrombaseline = 0.0
        tfrombestresponse = 0.0
        ntfrombaseline = 0.0

        if exam.baseline == False:
            if (currTRS > 0 and baselineTRS != 0):
                tfrombaseline = round(100*(currTRS-baselineTRS)/baselineTRS,0)
            if(currTRS > 0 and BR != 0):
                tfrombestresponse = round(100*(currTRS-BR)/BR,0)
            if(currNTRS > 0 and baselineNTRS != 0):
                ntfrombaseline = round(100*(currNTRS-baselineNTRS)/baselineNTRS,0)
            exam.add_percentchanges(ntfrombaseline,tfrombaseline,tfrombestresponse)

            #Target response based on RECIST1.1
            if((currTRS == 0) and (exam.lymphsize == True)):
                exam.tresponse = 'CR'
            elif (bool(exam.containsnewlesion == True) or (bool(exam.tfrombestresponse > 20) and bool(exam.trecistsum-patient.exams[i+1].trecistsum > 0.5))):
                exam.tresponse = 'PD'
            elif (exam.tfrombaseline < -30):
                exam.tresponse = 'PR'
            else:
                exam.tresponse = 'SD'

            #NT response based on RECIST1.1
            if ( (currNTRS == 0) and (exam.lymphsize == True)): 
                exam.ntresponse = 'CR'
            elif ( (exam.containsnewlesion == True) or bool(exam.ntrecistsum-patient.exams[i+1].ntrecistsum > 0)):
                exam.ntresponse = 'PD'
            else:
                exam.ntresponse = 'IR/SD'
    
            #overall response based on RECIST1.1
            if ((exam.tresponse == 'PD') or (exam.ntresponse == 'PD')):
                exam.overallresponse = 'PD'
            elif ((exam.tresponse == 'CR') and (exam.ntresponse == 'CR')):
                exam.overallresponse = 'CR'
            elif( \
                (((exam.tresponse == 'CR') or (exam.tresponse == 'PR')) and (exam.ntresponse == 'IR/SD')) \
                or ((exam.tresponse == 'PR') and (exam.ntresponse == 'CR'))):
                exam.overallresponse = 'PR'
            elif( \
                ((exam.tresponse == 'SD') and (exam.ntresponse == 'IR/SD' or exam.ntresponse == 'CR')) ):
                exam.overallresponse = 'SD'

        elif exam.baseline == True:
            exam.tfrombaseline = '-'
            exam.tfrombestresponse = '-'
            exam.ntfrombaseline = '-'
            exam.tresponse = '-'
            exam.ntresponse = '-'
            exam.overallresponse = '-'
            break #at the baseline exam, exit loop

    time_from_baselime(patient)

def find_best_response_sum(pt):
    '''
    Determine the patient's best response target sum. Determined by excluding exams prior to baseline or after current. 
    Exams with new lesions cannot be best response.
    '''
    bestResp = 0
    newSum = 0
    flag = 0
    numExams = len(pt.exams.keys())

    #bubble sort
    for i in range(numExams,0,-1): #need to set ending val at 0 bc range is numExams --> 1 (so if BL contains only one exam it is not skipped)
        if pt.exams[i].ignore == False and pt.exams[i].containsnewlesion == False: #skip exams prior to baseline, after current, or have new lesion
            if flag == 0:
                bestResp = pt.exams[i].trecistsum
                newSum = bestResp
                flag = 1

            newSum = pt.exams[i].trecistsum

            if ((newSum <= bestResp) & (pt.exams[i].containsnewlesion == False)): #bestresponse cannot have a new lesion present in exam
                bestResp = newSum
        else:
            pass
    return bestResp

def time_from_baselime(pt):
    '''
    Computes the amount of time (in days and weeks) between every exam and baseline exam and stores the result in the patient object.
    Input format is MM/DD/YYYY
    '''
    for key,exam in pt.exams.items():
        if exam.baseline == True:
            basedate = exam.date
            break

    d1 = list(map(int,basedate.split('/'))) #produces list of integers [month,day,year]
    d1 = date(d1[2],d1[0],d1[1]) #arg format is year,month,day

    for key,exam in pt.exams.items():
        d2 = list(map(int,exam.date.split('/')))
        d2 = date(d2[2],d2[0],d2[1])
        delta = d2-d1
        exam.add_timefromB(delta.days,round(delta.days/7,1))