#data classes to store BL data
#from collections import OrderedDict
#Revision 6/21/17
class StudyRoot:
    '''
    StudyRoot class stores dictionary of patients in format {'MRN/SID':patient object} (MRN = ####, SID = ##-X-####)
    '''
    def __init__(self):
        self.patients = {} #patient dict

    def add_patient(self, patient):
        ''' Append patient dict '''
        self.patients.update(patient)

class Patient:
    '''
    Patient class stored general patient information.
    Dictionary of exams in format {'#': exam object}, where #=1 is the most recent exam
    '''
    def __init__(
                self,
                mrn,
                sid,
                name,
                fields
                ):
        self.mrn = mrn #Medical Record Number
        self.sid = sid #Study ID
        self.name = name
        self.fields = fields #store the fields present in the BL, needed to determine what data will be imported (it needs to be present)

        self.exams = {}
        self.bestresponse = 0
        self.baselinesum = 0
        self.course = '-' #course (cycle)
        self.day = '-' #day of the cycle
        self.ignore = False #patient exclude flag

    def add_exam(self, exam):
        self.exams.update(exam) #Add an exam to dict

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
    '''
    Exam class used to store data about the exam as well as the lesion objects within that exam
    '''
    def __init__(
                self, 
                exam_num, 
                study_instance_uid
                ):
        self.exam_num = exam_num #exam number
        self.study_instance_uid = study_instance_uid #study instance uid, stored for future querying/access in PACS online browser

        self.lesions = [] #list storing lesions
        self.time = ''
        self.date = '' #exam date
        self.modality = '' #exam modality (CT, MRI, PET, PET-CT)
        self.baseline = False #is it a baseline exam (boolean)
        self.current = False #is it the current exam (most recent)
        self.description = '' #indicates area of body in scan
        self.ignore = False

        # NOTE:
        # ignore status used to exclude exams from best response determination 
        # if they are not in the (user specified or default) baselie to current exam range
        # default: dont ignore any exams (assume most recent exam is current, oldest is baseline)
        # also used when printing all the RECIST sheets for a patient to exclude exams we don't include in the baseline->current range

        #target and nontarget lesion sums
        self.trecistsum = 0
        self.ntrecistsum = 0

        #percent changes
        self.ntfrombaseline = '-'
        self.tfrombaseline = '-'
        self.tfrombestresponse = '-'

        self.tresponse = '-'
        self.ntresponse = '-'
        self.overallresponse = '-'
        self.measuredby = '-' #All people who measured on this exam

        self.containsnewlesion = False #Indicate if an exam has a new lesion (used when determining best response)
        self.containsnoT_NT_NL = False #Indicate if an exam doesnt have T,NT,or NL (false means it has T,NT,or NL, true means it lacks these)
        self.lymphsize = False #Indicate if all lymph nodes are less than 1cm in size (used in response determinations)

        self.daysfromB = 0
        self.weeksfromB = 0

    def add_description(self,description):
        self.description = description

    def add_lesion(self, lesion):
        self.lesions.append(lesion)

    def add_time(self,time):
        self.time = time #format HH:MM AM/PM

    def add_date(self, date):
        self.date = date #format MM/DD/YYYY

    def add_modality(self, modality):
        self.modality = modality

    def add_baseline(self, baseline):
        self.baseline = baseline #update baseline exam status, True or False

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
    '''
    Lesion class.
    Utilize dictionary to store the parameters based on what is present in patient bookmark list.

    '''
    def __init__(self):
        self.newlesion = False #False unless set to True
        self.params = {} #dictionary of parameters, populated according to the column names present in the Bookmark List

    def add_newlesion(self, newlesion):
        self.newlesion = newlesion #set to True if new lesion found

    def set_target(self, target):
        self.target = target #Change target status of a lesion (i.e for new lesions)

    def add_humean(self,humean):
        self.humean = humean
    
    def add_volume(self,volume):
        self.volume = volume

    def add_params(self,params):
        self.params = params