#! python3

#Revision 7/5/17
from PyQt5.QtWidgets import QDate, QProgressBar, QDialog, QTableWidget, QFileDialog, QHBoxLayout, QVBoxLayout, QTextEdit, QAction, qApp, QApplication, QWidget, QToolTip, QPushButton, QMessageBox, QDesktopWidget, QMainWindow
from PyQt5.QtGui import QIcon, QFont
from PyQt5 import QtCore

#plotting dependencies
import pyqtgraph as pg

import pyqtgraph.exporters
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np

#Dialog templates
import design # This file holds our MainWindow and all design related things
import examselect #file holds exam selection window design
import plotandgraph #file holds plot window design
import uploader #database upload page

#All other dependencies
from BLImporterUIVersion import BLImport
from RECISTComp import RECISTComp
import pandas as pd
from RECISTGen import RECISTSheet
from DataExport import exportToExcel, waterfallPlot, spiderPlot, exportPlotData
import BLDataClasses
import shelve
import sys # We need sys so that we can pass argv to QApplication
import os
import re
import ctypes
from pprint import pprint

class ExamSelectWindow(QDialog, examselect.Ui_Form):
    def __init__(self, parent=None):
        QMainWindow.__init__(self)
        self.setupUi(self) #setup the selection window

    #### Initialize Data ####
        #populate patient list
        for key,patient in form.StudyRoot.patients.items(): #note, StudyRoot belongs to form (main application window)
            if patient.ignore == False:
                self.patientList.addItem(patient.name + ' - ' + key)

    #### BUTTON FUNCTIONS ####
        self.returnToHome.clicked.connect(self.returnHome)
        self.patientList.itemClicked.connect(self.patientSelected)
        self.setExams.clicked.connect(self.setPatientExams)

    #### SIGNALS ####
        self.currentExamSelect.currentIndexChanged.connect(self.updateOptions) #update the baseline exam dropdown menu

    #### FUNCTIONS ####
    def setPatientExams(self):
        #once user selects Set Exams, change the exam.baseline and exam.current statuses
        try:
            getattr(self,'link') #check to see if a patient has been selected
            self.indexFind = re.compile(r'^\d{1,3}')
            self.currExamIndex = int(self.indexFind.search(self.currentExamSelect.currentText()).group())
            self.baseExamIndex = int(self.indexFind.search(self.baselineExamSelect.currentText()).group())
            self.numExams = len(form.StudyRoot.patients[self.selkey].exams.items())
        
            #Warm user that if they select an exam which has no T,NT,or NL lesions that the diameter changes relative to baseline will be incorrect, and best repsonse will be incorrect
            #self.indexFind = dateReg = re.compile(r'\d+/\d+/\d+')          
            #if self.indexFind.search(self.baselineExamSelect.currentText()) == None:
            if form.StudyRoot.patients[self.selkey].exams[self.baseExamIndex].containsnoT_NT_NL == True:
                #Warn user that they selected a bad baseline exam
                QMessageBox.warning(self,'Warning!',\
                    'Selected baseline exam does NOT contain Target lesions!\nDiameter changes relative to baseline will be incorrect.\n\nDifferent baseline selection is advised.')

            for self.i in range(1,self.numExams+1):
                #Note, we use form.StudyRoot so that we modify the StudyRoot that belongs to the main program (whereas self.link in patientSelected would not push changes to the form.StudyRoot)
                #set current and baseline status to False for every exam (will be set after loop)
                form.StudyRoot.patients[self.selkey].exams[self.i].add_current(False)
                form.StudyRoot.patients[self.selkey].exams[self.i].add_baseline(False)
            
            form.StudyRoot.patients[self.selkey].exams[self.currExamIndex].add_current(True)
            form.StudyRoot.patients[self.selkey].exams[self.baseExamIndex].add_baseline(True)
            
            self.CurrFound = False
            self.BaseFound = False
            for self.i in range(1,self.numExams+1): #numexams+1 because range excludes end of range, start at 1 because indexing of exam dict starts at 1
                #loop to set the ignore status of exams
                if (self.CurrFound == False and self.BaseFound == False) or (self.CurrFound == True and self.BaseFound == True):
                    #these exams are before the baseline or after the selected 'current' exam, they should be ignored in best response determination
                    if form.StudyRoot.patients[self.selkey].exams[self.i].current == False and form.StudyRoot.patients[self.selkey].exams[self.i].baseline == False:
                        form.StudyRoot.patients[self.selkey].exams[self.i].add_ignore(True)
                
                #do this later so that the baseline does not incorrectly get marked at ignore == True (occurs because currFound and baseFound == True)
                if form.StudyRoot.patients[self.selkey].exams[self.i].current == True and \
                form.StudyRoot.patients[self.selkey].exams[self.i].baseline == False:
                    self.CurrFound = True #current exam found
                elif form.StudyRoot.patients[self.selkey].exams[self.i].baseline == True and \
                form.StudyRoot.patients[self.selkey].exams[self.i].current == False:
                    self.BaseFound = True #baseline found
        
        except AttributeError:
            QMessageBox.information(self,'Message','Please select a patient.')

    def patientSelected(self):
        #get selected patient
        self.examList.clear() #clear when new patient selected

        currPt = self.patientList.currentItem().text() #current patient string
        MRNSID = re.compile(r'\d{7}/\w{2}-\w-\w{4}')
        self.selkey = MRNSID.search(currPt).group() #selected patient

        #display patient exams
        self.link = form.StudyRoot.patients[self.selkey].exams.items() #link contains the exams
        self.exams1 = []
        for key,exam in self.link:
            self.examList.addItem(str(key) + ': ' + str(exam.modality) + ' - ' + str(exam.date))
            self.exams1.append(str(key) + ': ' + str(exam.modality) + ' - ' + str(exam.date))
        
        #display exam date options in dropdown menu
            #first display current exam options, then once selected, display the baseline exam options, only allowing users to select older exams
        #Updating these fields takes place in function updateOptions()
        self.currentExamSelect.clear()
        self.currentExamSelect.addItems(self.exams1)
        selection1 = self.currentExamSelect.currentText()

        #NOTE: baseline field is not specified here, specified in updateOptions() which is called immediately after the currentExam field changes (signal is sent, see the widget __init__)

    def updateOptions(self,index):
        #display exam date options in dropdown menu
            #first display current exam options, then once selected, display the baseline exam options, only allowing users to select older exams

        self.exams2 = self.exams1[index+1:]
        self.baselineExamSelect.clear()
        self.baselineExamSelect.addItems(self.exams2) #populate list

        #set default selection to oldest exam, assumed to be baseline
        count = self.baselineExamSelect.count()
        self.baselineExamSelect.setCurrentIndex(count-1)

    def returnHome(self):
        #Close selection dialog
        self.close()



class MainWindow(QMainWindow, design.Ui_mainWindow):
    def __init__(self):
        # super use here because it allows us to
        # access variables, methods etc in the design.py file
        super(self.__class__, self).__init__()
        self.setupUi(self)  # This is defined in design.py file automatically
                            # It sets up layout and widgets that are defined     

        #### INITIALIZATION ####
        self.settings() #initialize user settings
        self.operatingMode(1) #default to Export mode, self.opMode stores operating mode state (1 == export, 0 == consult)
        self.setWindowIcon(QtGui.QIcon('../icons/enable_icon.png'))
        self.consultDate.setCurrentDate(QDate.currentDate())


        #### BUTTON FUNCTIONS ####
        self.importPatients.clicked.connect(self.importBookmarks)
        self.removePatients.clicked.connect(self.clearBookmarks)
        
        self.recistCalc.clicked.connect(self.recistCalculations)
        self.generateRECIST.clicked.connect(self.genRECIST)
        self.generateSpreadsheets.clicked.connect(self.genSpreadsheets)
        self.removePatient.clicked.connect(self.removeSelectedPatient)
        self.includePatient.clicked.connect(self.includeSelectedPatient)
        self.exportPlotData.clicked.connect(self.EPD)

        self.configureButton.clicked.connect(self.configProg)
        self.configureButton.setIcon(QtGui.QIcon('../icons/configIcon.png'))

        #### LAUNCH SECONDARY DIALOGS ####
        self.modExamDates.clicked.connect(self.launchExamSelect)
        self.plotsAndGraphs.clicked.connect(self.launchPlotAndGraph)

        #### Operating mode select ####
        self.exportMode.clicked.connect(lambda: self.operatingMode(1))
        self.consultMode.clicked.connect(lambda: self.operatingMode(0))

        #### DISPLAY RELATED ####
        self.show()

        #### DATABASE EXPORTS ####
        self.databaseUploader.clicked.connect(self.launchDbUploadDialog) #open uploader dialog

    #### MAIN FUNCTIONS ####
    def EPD(self):
        #Export plot data (all 3 types)
        try:
            self.StudyRoot #check if patients imported
            try:
                if self.Calcs == True: #check if calcs performed
                    self.statusbar.showMessage('Exporting Plot Data')
                    exportPlotData(self.StudyRoot,self.OutDir) #call external function to generate
                    QMessageBox.information(self,'Message','Plot data exported.')
                elif self.Calcs == False:
                    QMessageBox.information(self,'Message','Please perform RECIST calculations.')
            except AttributeError:
                QMessageBox.information(self,'Message','Please perform RECIST calculations.')

        except Exception:
            QMessageBox.information(self,'Message','Please import Bookmark List(s).')
        self.statusbar.showMessage('Done.', 1000)

    def recistCalculations(self):
        #perform recist calculations by passing each patient in self.StudyRoot to the RECISTComp function
        try:
            getattr(self,'StudyRoot')
            self.Calcs = True
            self.statusbar.showMessage('Performing RECIST calculations')
            for key, patient in self.StudyRoot.patients.items():
                RECISTComp(patient) #perform RECIST computations for the selected patient
            self.statusbar.showMessage('Done with RECIST calculations!', 1000)
        except AttributeError:
            QMessageBox.information(self,'Message','Please import Bookmark List(s).')
            self.Calcs = False

    def removeSelectedPatient(self):
        #remove highlighted patients, flag them in StudyRoot so they are skipped (ignore == True)
        try:
            temp = self.patientList.currentItem()
            self.excludeList.addItem(temp.text())
            self.patientList.takeItem(self.patientList.row(temp))

            currPt = temp.text() #current patient string
            MRNSID = re.compile(r'\d{7}/\w{2}-\w-\w{4}')
            selkey = MRNSID.search(currPt).group() #selected patient

            #mark patient for ignore status
            form.StudyRoot.patients[selkey].add_ignore(True) #mark patient for ignore
        except AttributeError:
            QMessageBox.information(self,'Message','No patient selected for removal.')

    def includeSelectedPatient(self):
        #include highlighted patient, flag them in StudyRoot so they are included (ignore == False)
        try:
            temp = self.excludeList.currentItem()
            self.patientList.addItem(temp.text())
            self.excludeList.takeItem(self.excludeList.row(temp))

            currPt = temp.text() #current patient string
            MRNSID = re.compile(r'\d{7}/\w{2}-\w-\w{4}')
            selkey = MRNSID.search(currPt).group() #selected patient

            #mark patient for ignore status
            form.StudyRoot.patients[selkey].add_ignore(False) #mark patient for ignore

        except AttributeError:
            QMessageBox.information(self,'Message','No patient selected for inclusion.')

    def clearBookmarks(self):
        #Clear the list widget containing patient names/mrn
        try:
            getattr(self,'StudyRoot')
            self.patientList.clear()
            self.excludeList.clear()
            del self.StudyRoot #delete the study root
            del self.Calcs #delete to catch when patients are removed and user attemps to generate sheets
            QMessageBox.information(self,'Message','All patients removed.')
        except AttributeError:
            pass
        
    def settings(self):
        #get application settings (default directories)
        try:
            with shelve.open('LocalPreferences') as shelfFile:
                self.BLDir = shelfFile['BLDir']
                self.RECISTDir = shelfFile['RECISTDir']
                self.OutDir = shelfFile['OutDir']
                shelfFile.close()
        except KeyError:
            QMessageBox.information(self,'Message','Please configure ENABLE 2')
            self.configProg()
            self.settings()

    def configProg(self):
        shelfFile = shelve.open('LocalPreferences')
        BLDirT = str(QFileDialog.getExistingDirectory(self, "Select Bookmark List Directory"))
        if BLDirT != '':
            shelfFile['BLDir'] = BLDirT
            self.BLDir = BLDirT
        else:
            QMessageBox.information(self,'Message','Directory unchanged.')

        shelfFile['RECISTDir'] = os.path.dirname(os.path.realpath('RECISTForm.docx'))
        shelfFile['LMUploader']=os.path.dirname(os.path.realpath('RadiologyImportClient.jar'))

        OutDirT = str(QFileDialog.getExistingDirectory(self, "Select Output Directory"))
        if OutDirT != '':
            shelfFile['OutDir'] = OutDirT
            self.OutDir = OutDirT
        else:
            QMessageBox.information(self,'Message','Directory unchanged.')
        shelfFile.close()

    def importBookmarks(self):
        self.statusbar.showMessage('Importing Bookmark List(s)...')
        self.patientList.clear()
        self.StudyRoot = BLDataClasses.StudyRoot() #create a StudyRoot
        self.df = pd.DataFrame()

        flag = 0
        try: #catch error when user hits "ESC" in file select dialogue
            ret = QFileDialog.getOpenFileNames(self, "Select Bookmark List(s)", self.BLDir) #returns tuple (list of file names, filter)
            files = ret[0] #absolute file paths to bookmark lists selected
            
            self.dirName = os.path.dirname(files[0]) #all BL in same directory, take dir from first
            self.baseNames = [] #initialize list of base names
            for i in files:
                self.baseNames.append(os.path.basename(i)) #add the base names to a list
            flag = 0
            
        except Exception:
            self.dirName = ''
            self.baseNames = ''
            flag = 1 #no imports

        if flag == 0:
            #for self.file in self.baseNames:
            BLImport(self.df,self.StudyRoot,self.dirName,self.baseNames) #send one patient at a time, adding them to the StudyRoot one at a time
            QMessageBox.information(self,'Message','Bookmark List(s) successfully imported.')
            self.statusbar.showMessage('Done importing Bookmark List(s)', 1000)
            
            ### Populate List with Pt names ###
            for key,patient in self.StudyRoot.patients.items():
                self.patientList.addItem(patient.name + ' - ' + key)
        elif flag == 1:
            QMessageBox.information(self,'Message','No Bookmark List(s) imported.')
            del self.StudyRoot
            self.statusbar.clearMessage()

    def genSpreadsheets(self):
        #call the function to create spreadsheets
        try:
            self.StudyRoot #check if patients imported
            try:
                if self.Calcs == True: #check if calcs performed
                    self.statusbar.showMessage('Generating spreadsheets.')
                    exportToExcel(self.StudyRoot,self.OutDir)
                    QMessageBox.information(self,'Message','Spreadsheets generated.')
                elif self.Calcs == False:
                    QMessageBox.information(self,'Message','Please perform RECIST calculations.')
            except AttributeError:
                QMessageBox.information(self,'Message','Please perform RECIST calculations.')

        except Exception:
            QMessageBox.information(self,'Message','Please import Bookmark List(s).')
        self.statusbar.showMessage('Done generating spreadsheets.', 1000)

    def genRECIST(self):
        self.statusbar.showMessage('Generating RECIST worksheets...')
        RECISTSheet(self.RECISTDir,self.OutDir,self.dirName,self.baseNames,self.StudyRoot)
        try:
            self.StudyRoot #check if patients imported
            try:
                if self.Calcs == True: #check if calcs performed
                    RECISTSheet(self.RECISTDir,self.OutDir,self.dirName,self.baseNames,self.StudyRoot)
                    QMessageBox.information(self,'Message','RECIST worksheets generated.')
                elif self.Calcs == False:
                    QMessageBox.information(self,'Message','Please perform RECIST calculations.')
            except AttributeError:
                QMessageBox.information(self,'Message','Please perform RECIST calculations.')

        except Exception:
            QMessageBox.information(self,'Message','Please import Bookmark List(s).')
        self.statusbar.showMessage('Done generating RECIST worksheets.', 1000)

    #### UI FUNCTIONS ####
    def closeEvent(self,event):
        reply = QMessageBox.question(self,'Exit ENABLE 2.0',"Are you sure to quit ENABLE 2?", QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def launchExamSelect(self):
        #launch exam selection dialog if the StudyRoot exists (BLs have been imported)
        try:
            getattr(self,'StudyRoot')
            self.examSelect = ExamSelectWindow()
            self.examSelect.exec()
        except AttributeError:
            QMessageBox.information(self,'Message','Please Import Bookmark List(s).')

    def launchPlotAndGraph(self):
        try:
            self.StudyRoot #check if patients imported
            try:
                if self.Calcs == True: #check if calcs performed
                    self.plotandgraph = PlotAndGraphingDialog()
                    self.plotandgraph.exec()
                elif self.Calcs == False:
                    QMessageBox.information(self,'Message','Please perform RECIST calculations.')
            except AttributeError:
                QMessageBox.information(self,'Message','Please perform RECIST calculations.')

        except Exception:
            QMessageBox.information(self,'Message','Please import Bookmark List(s).')
    
    def operatingMode(self,mode):
        #sets program to operate in Export or Consultation mode
        if mode == 1:
            self.statusbar.showMessage("Operating Mode: Export")
            self.consultFrame.setEnabled(False)
        elif mode == 0:
            self.statusbar.showMessage("Operating Mode: Consultation")
            self.consultFrame.setEnabled(True)
        self.opMode = mode

    def launchDbUploadDialog(self):
        try:
            self.StudyRoot #check if patients imported
            try:
                if self.Calcs == True: #check if calcs performed
                    self.uploaddialog = DatabaseUploadDialog()
                    self.uploaddialog.exec()
                elif self.Calcs == False:
                    QMessageBox.information(self,'Message','Please perform RECIST calculations.')
            except AttributeError:
                QMessageBox.information(self,'Message','Please perform RECIST calculations.')
        except Exception:
            QMessageBox.information(self,'Message','Please import Bookmark List(s).')


class PlotAndGraphingDialog(QDialog, plotandgraph.Ui_plotAndGraphUtility):
    def __init__(self, parent=None):
        QMainWindow.__init__(self)
        self.setupUi(self) #setup the graphing window

        #### INITIALIZE ####
        #Patient tab
        for key,patient in form.StudyRoot.patients.items(): #note, StudyRoot belongs to form (main application window)
            if patient.ignore == False:
             self.patientList.addItem(patient.name + ' - ' + key)

        #Waterfall Plot tab
        for key,patient in form.StudyRoot.patients.items(): #note, StudyRoot belongs to form (main application window)
            if patient.ignore == False:
             self.cohortList.addItem(patient.name + ' - ' + key)

        #### BUTTON FUNCTIONS ####
        self.genSwimmerPlot.clicked.connect(self.SWP)
        self.genSpiderPlot.clicked.connect(self.SP)
        self.genWaterfallPlot.clicked.connect(self.WFP)
        self.exportPlotData.clicked.connect(self.EPD)
        self.clearPlot.clicked.connect(self.CP)

        #### INDIVIDUAL PT PLOTS ####
        self.patientList.itemSelectionChanged.connect(self.plotPatientSelected)

       ####PLOTS ####
    def plotPatientSelected(self):
        #get selected patient
        self.graphicsView.clear()

        currPt = self.patientList.currentItem().text() #current patient string
        MRNSID = re.compile(r'\d{7}/\w{2}-\w-\w{4}')
        self.selkey = MRNSID.search(currPt).group() #selected patient

        #display patient exams
        self.link = form.StudyRoot.patients[self.selkey].exams.items() #link contains the exams
        self.trecistsums = []
        self.exdate = []
        for key,exam in self.link:
            self.trecistsums.append(exam.trecistsum)
            self.exdate.append(exam.date)
        
        self.exdateTup = list(enumerate(self.exdate))

        #plot
        self.plt1 = pg.PlotDataItem(self.trecistsums,pen='b')
        self.plt2 = pg.PlotDataItem(self.trecistsums, pen=None,symbol='o',symbolBrush='k')
        #self.plt1.getAxis('bottom').setTicks([self.exdatedict])
        self.graphicsView.addItem(self.plt1)
        self.graphicsView.addItem(self.plt2)
        self.graphicsView.showGrid(x=False,y=True,alpha = 0.5)
        ax = self.graphicsView.getAxis('bottom')
        ax.setTicks([self.exdateTup,[]])
        self.graphicsView.setLabel('left',text ='Target RECSIT Sum vs. Exam')
        self.graphicsView.setLabel('bottom',text='Date')
        self.graphicsView.setTitle(title='Target RECIST Sum vs. Exam')
  
    def WFP(self):
        self.graphicsView.clear()
        self.vals = waterfallPlot(form.StudyRoot)
        self.x = np.arange(len(self.vals))
        self.bg1 = pg.BarGraphItem(x=self.x, height=self.vals, width=1, brush='b')
        self.graphicsView.showGrid(x=False,y=True,alpha = 0.5)
        self.graphicsView.addItem(self.bg1)

        #formatting
        self.graphicsView.addLine(y=-30,pen = {'color':'k', 'width': 2,'style':QtCore.Qt.DashLine}) #partial response line
        self.graphicsView.addLine(y=20,pen = {'color':'k', 'width': 2,'style':QtCore.Qt.DashLine}) #PD line
        self.graphicsView.setLabel('left',text ='Target Lesion % Change from Baseline')
        self.graphicsView.setLabel('bottom',text='Patient')
        self.graphicsView.setTitle(title='Waterfall Plot')

    def SP(self):
        #spider plot
        self.graphicsView.clear()
        self.vals = spiderPlot(form.StudyRoot) #returns dict of format {'key':[[measurements],[weeks from baseline],[days from baseline]]}
        for key,tup in self.vals.items():
            self.scp1 = pg.PlotDataItem(tup[1],tup[0],pen = 'k')
            self.scp2 = pg.PlotDataItem(tup[1],tup[0], pen=None,symbol='o',symbolBrush='k')
            self.graphicsView.addItem(self.scp1)
            self.graphicsView.addItem(self.scp2)
        

        self.graphicsView.setLabel('left',text ='Target sum relative to baseline')
        self.graphicsView.setLabel('bottom',text='Weeks from baseline')
        self.graphicsView.setTitle(title='Spider Plot')

    def SWP(self):
        #swimmerplot
        pass

    def EPD(self):
        #Export plot data (all 3 types)
        #note, don't need to add error catching here since the plotting dialog only opens if calcs have been performed and bookmark lists imported
        exportPlotData(form.StudyRoot,form.OutDir) #call external function to generate
        QMessageBox.information(self,'Message','Plot data exported.')

    #### PLOTTING SHARED FNX ####
    def CP(self):
        #clear plot window
        self.graphicsView.clear()






class DatabaseUploadDialog(QDialog, uploader.Ui_databaseuploaddialog):
    def __init__(self, parent=None):
        QMainWindow.__init__(self)
        self.setupUi(self) #setup the graphing window


if __name__ == '__main__':              # if we're running file directly and not importing it
    #set application icon
    myappid = u'ENABLE 2.0_V1' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')

    #create app instance and launch
    app = QApplication(sys.argv)        # A new instance of QApplication
    app.setApplicationName('ENABLE 2.0')
    form = MainWindow()                 # We set the form to be our ExampleApp (design)
    form.show()                         # Show the form
    sys.exit(app.exec_())               # and execute the app