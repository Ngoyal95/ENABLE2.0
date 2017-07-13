#data classes to store BL data
#from collections import OrderedDict
#Revision 6/21/17
class StudyRoot:
    #root linking to patients
    def __init__(self):
        self.patients = {} #patient dictionary

    def add_patient(self, patient): #patient = {'key':'value'}
        self.patients.update(patient)


class Patient:
    #class for a patient
    def __init__(
                self,
                mrn, 
                sid,
                name,
                fields
                ):
        #self.name #patient name
        self.mrn = mrn #Medical Record Number
        self.sid = sid #Study ID
        self.exams = {} #dictonary storing exams
        self.name = name
        self.fields = fields #store the fields present in the BL, needed to determine what data will be imported (it needs to be present)

        #set after obj initialization, set in BLImporter.py
        self.bestresponse = 0 #best response
        self.baselinesum = 0
        self.course = '-' #course number (blank until entered)
        self.day = '-' #day course (blank until entered)
        self.ignore = False #don't exclude patient unless selected in GUI

    def add_exam(self, exam): #function to add an exam to a patient, exam = {'key':'value'}
        self.exams.update(exam) #update the exams dictionary

    def add_bestresponse(self, bestresponse):
        self.bestresponse = bestresponse

    def add_baselinesum(self, baseline):
        self.baselinesum = baseline

    def add_courseday(self, course, day):
        self.course = course
        self.day = day

    def add_ignore(self, ignore):
        self.ignore = ignore

class Exam:
    ''' Exam class used to store data about the exam as well as the lesion objects within that exam '''
    def __init__(
                self, 
                enum, 
                study_instance_uid
                ):
        self.enum = enum #exam number
        self.study_instance_uid = study_instance_uid #study instance uid, stored for future querying/access in PACS online browser

        #variables to be set after obj initialization
        self.lesions = [] #list storing lesions
        self.time = ''
        self.date = '' #exam date
        self.modality = '' #exam modality (CT, MRI, PET, PET-CT)
        self.baseline = False #is it a baseline exam (boolean)
        self.current = False #is it the current exam (most recent)
        self.description = '' #CTCHABDPEL for example
        
        self.ignore = False
        '''NOTE:
        ignore status used to exclude exams from best response determination 
        if they are not in the (user specified or default) baselie to current exam range
        default: dont ignore any exams (assume most recent exam is current, oldest is baseline)

        also used when printing all the RECIST sheets for a patient to exclude exams we don't include in the baseline->current range
        '''

        #set in RECISTComp.py
        self.trecistsum = 0 #target lesion sum
        self.ntrecistsum = 0 #nontarget lesion sum

        #percent changes, set in RECISTComp.py
        self.ntfrombaseline = 0
        self.tfrombaseline = 0
        self.tfrombestresponse = 0

        self.tresponse = ''
        self.ntresponse = ''
        self.overallresponse = ''
        self.measuredby = '' #who were all people who measured on this exam

        self.containsnewlesion = False #flag used to indicate if an exam has a new lesion (used when determining best response)
        self.containsnoT_NT_NL = False #field used to indicate if an exam doesnt have T,NT,or NL (false means it has T,NT,or NL, true means it lacks these)
        self.lymphsize = False #check if all lymph nodes are less than 1cm in size (used in response determinations)

        self.daysfromB = 0
        self.weeksfromB = 0

    def add_description(self,description):
        self.description = description

    def add_lesion(self, lesion): #lesion is a pointer to a lesion
        self.lesions.append(lesion)

    def add_time(self,time):
        self.time = time #format HH:MM AM/PM

    def add_date(self, date):
        self.date = date #format MM/DD/YYYY

    def add_modality(self, modality):
        self.modality = modality #update modality

    def add_baseline(self, baseline):
        self.baseline = baseline #update baseline exam status

    def add_current(self, current):
        self.current = current

    def add_ignore(self, ignore):
        self.ignore = ignore

    def add_RECISTsums(self, tsum, ntsum):
        self.trecistsum = tsum
        self.ntrecistsum = ntsum

    def add_percentchanges(self, nt, t, tbr):
        self.ntfrombaseline = nt
        self.tfrombaseline = t
        self.tfrombestresponse = tbr

    def add_responses(self, tresp, ntresp, oresp):
        self.tresponse = tresp
        self.ntresponse = ntresp
        self.overallresponse = oresp

    def add_containsnewlesion(self, nl):
        self.containsnewlesion = nl

    def add_containsnoT_NT_NL(self, val):
        self.containsnoT_NT_NL = val

    def add_timefromB(self, d, w):
        self.daysfromB = d
        self.weeksfromB = w


class Lesion:
    #class module for the Lesion datatype
    def __init__(
                self, 
                # fu, 
                # name, 
                # tool, 
                # desc, 
                # target, 
                # subtype, 
                # series,
                # slicenum, 
                # recistdia, 
                # longdia, 
                # shortdia,
                # creator
                ):
        # self.fu = fu
        # self.name = name
        # self.tool = tool #string
        # self.desc = desc
        # self.target = target #A STRING, either 'Target','Non-Target','Unspecified', or 'New Lesion' which is set by ENABLE (New Lesion is not a PACS option)
        # self.subtype = subtype #lesion sub type (ie lung, lymph, etc)
        # self.series = series
        # self.slice = slicenum
        # self.recistdia = recistdia #cm (rounded)
        # self.longdia = longdia #cm (unrounded)
        # self.shortdia = shortdia #cm (unrounded)
        # self.creator = creator


        #variables to be set after obj initialization
        self.volume = 0 #cm^3 (unrounded)
        self.humean = 0 #HU
        self.newlesion = False #False unless set to True

        self.params = {} #dictionary of parameters, populated according to the column names present in the Bookmark List

    def add_newlesion(self, newlesion):
        self.newlesion = newlesion #set to True if new lesion found

    def set_target(self, target):
        self.target = target #use when need to change the target status of a lesion (i.e for new lesions)

    def add_humean(self,humean):
        self.humean = humean
    
    def add_volume(self,volume):
        self.volume = volume

    def add_params(self,params):
        self.params = params