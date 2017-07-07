#RECIST computation module
#Revision 6/21/17
from operator import attrgetter
from pprint import pprint
from datetime import date

def RECISTComp(patient):
    #module to compute the RECIST values, takes the a patient obj as argument

    tsum = 0
    ntsum = 0
    for key, exam in patient.exams.items(): #iterate over exam objects in the patient obj
        for lesion in exam.lesions: #iterate over lesions for the current exam

            #Note that if an exam has a new lesion, the diameter of the new lesion is not added to either target sum or non target sum
            #Also skip lesions who have .target == 'Unspecified'
            if lesion.tool.lower() == 'two diameters' or lesion.tool.lower() == 'line': #don't want to add any other type of segmentation (single line, or volume)
                if lesion.target.lower() == 'target':
                    print("Target",key)
                    tsum += lesion.recistdia
                elif lesion.target.lower() == 'non-target':
                    ntsum += lesion.recistdia

        exam.add_RECISTsums(round(tsum, 1), round(ntsum, 1)) #store sums after all lesion diameters added up
        tsum = 0
        ntsum = 0

    BR = getBestResponse(patient) #best response sum (variable used later)
    patient.add_bestresponse(BR) #get and store patient best response

    #number of exams (used to access baseline exam from exams dictionary (keys are the exam number, 1 is most recent, numExams is baseline (keys are indexed at 1)))
    numExams = len(patient.exams.keys())
    
    #now compute percent changes in diameters
    #need to use the baseline exam selected by user (if not selected, defsaults as oldest exam)
    for key, exam in patient.exams.items():
        if exam.baseline == True:
            baselineTRS = exam.trecistsum
            patient.add_baselinesum(baselineTRS) #store patient baseline RECIST sum
            baselineNTRS = exam.ntrecistsum

    '''
    perform computations for every exam, relative to baseline (even if the selected current exam is after the most recent)
    reason why: want to keep all patient data, just only print the exam selected as current to the RECIST sheet
    '''
    numKeys = len(patient.exams.keys())
    for i in range(1,numKeys+1): #need +1 on end of range since exam dict keywords are numerated from 1
        exam = patient.exams[i] #go to current exam in loop
    #for key,exam in patient.exams.items():
        currTRS = exam.trecistsum
        currNTRS = exam.ntrecistsum

        tfrombaseline = 0.0
        tfrombestresponse = 0.0
        ntfrombaseline = 0.0

        if exam.baseline == False:
            if (currTRS > 0 and baselineTRS != 0):
                tfrombaseline = round(100*(currTRS-baselineTRS)/baselineTRS)
            if(currTRS > 0 and BR != 0):
                tfrombestresponse = round(100*(currTRS-BR)/BR)
            if(currNTRS > 0 and baselineNTRS != 0):
                ntfrombaseline = round(100*(currNTRS-baselineNTRS)/baselineNTRS)
            
            exam.add_percentchanges(ntfrombaseline,tfrombaseline,tfrombestresponse)

            #Target and NT responses
            if((currTRS == 0) and (exam.lymphsize == True)):
                exam.tresponse = 'CR'
            elif (bool(exam.containsnewlesion == True) or (bool(exam.tfrombestresponse > 20) and bool(exam.trecistsum-patient.exams[i+1].trecistsum > 0.5))):
                exam.tresponse = 'PD'
            elif (exam.tfrombaseline < -30):
                exam.tresponse = 'PR'
            else:
                exam.tresponse = 'SD'

            #NT response
            if ( (currNTRS == 0) and (exam.lymphsize == True)): 
                exam.ntresponse = 'CR'
            elif ( (exam.containsnewlesion == True) or bool(exam.ntrecistsum-patient.exams[i+1].ntrecistsum > 0)):
                exam.ntresponse = 'PD'
            else:
                exam.ntresponse = 'IR/SD'
    
            #overall response
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

        elif exam.baseline == True: #baseline exam
            exam.tfrombaseline = '-'
            exam.tfrombestresponse = '-'
            exam.ntfrombaseline = '-'
            exam.tresponse = '-'
            exam.ntresponse = '-'
            exam.overallresponse = '-'
            break #hit the baseline exam, need to break out of loop

    deltaT_BaselineToCurrent(patient)
    
    #pprint(vars(patient))
    # for key,exam in patient.exams.items():
    # 	pprint(vars(exam))
    

def getBestResponse(pt):
    #note that finding the best response will EXCLUDE exams which are not baseline <= exam <= current (based on user selection)
    bestResp = 0
    newSum = 0
    flag = 0
    numExams = len(pt.exams.keys())

    # Note that exams marked as ignore == True are skipped
    for i in range(numExams,0,-1): #need to set ending val at 0 bc range is numExams --> 1 (so if BL contains only one exam it is not skipped)
        if pt.exams[i].ignore == False:
            if flag == 0: #init values
                bestResp = pt.exams[i].trecistsum
                newSum = bestResp
                flag = 1

            newSum = pt.exams[i].trecistsum

            if ((newSum <= bestResp) & (pt.exams[i].containsnewlesion == False)): #bestresponse cannot have a new lesion present in exam
                bestResp = newSum
        else:
            pass #skip the exams which are ignored

    return bestResp

def deltaT_BaselineToCurrent(pt):
    #computes the amount of time (in days and weeks) between every exam and baseline exam
        #NOTE: Assumed format is mm/dd/yyyy

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