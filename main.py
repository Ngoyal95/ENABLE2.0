#! python3

#Revision 7/20/17
from PyQt5.QtWidgets import (QLineEdit, QProgressBar, QDialog, QTableView, 
                            QFileDialog, QAction, QApplication, QWidget, 
                            QPushButton, QMessageBox, QDesktopWidget, QMainWindow,
                            QStyleFactory)
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
import login #login page
import config

#Custom widgets
from custom_tree import PatientTree

from BLImporterUIVersion import bl_import
from RECISTComp import recist_computer
import pandas as pd
from RECISTGen import generate_recist_sheets
from DataExport import exportToExcel, waterfallPlot, spiderPlot, exportPlotData, exportToLog
from backend_interface import patient_uploader_func, pull_patient_list_from_mongodb, pull_patients_from_mongodb
import BLDataClasses
import shelve
import sys
import os
import psutil
import win32api
import win32net
import re
import ctypes
import traceback
import hashlib
import pymongo
import time
import yaml
from pprint import pprint

class DataOverrides(QDialog, examselect.Ui_Form):
    def __init__(self, parent=None):
        QMainWindow.__init__(self)
        self.setupUi(self) #setup the selection window

        #### Initialize ####
        for key,patient in form.StudyRoot.patients.items(): #note, StudyRoot belongs to form (main application window)
            if patient.ignore == False:
                self.patientList.addItem(patient.name + ' - ' + key)
        
        #### BUTTON FUNCTIONS ####
        self.returnToHome.clicked.connect(self.returnHome)
        self.patientList.itemClicked.connect(self.patientSelected)
        self.patientList.itemClicked.connect(self.populate_view)
        self.setExams.clicked.connect(self.setPatientExams)

        #### Signal Connections ####
        self.currentExamSelect.currentIndexChanged.connect(self.updateOptions) #update the baseline exam dropdown menu
        
    #### Functions ####
    def setPatientExams(self):
        '''
        Changes the exam.baseline and exam.current statuses after user selects Set Exams
        '''
        try:
            getattr(self,'link') #check to see if a patient has been selected
            self.indexFind = re.compile(r'^\d{1,3}')
            self.currExamIndex = int(self.indexFind.search(self.currentExamSelect.currentText()).group())
            self.baseExamIndex = int(self.indexFind.search(self.baselineExamSelect.currentText()).group())
            self.numExams = len(form.StudyRoot.patients[self.selkey].exams.items())
        
            if form.StudyRoot.patients[self.selkey].exams[self.baseExamIndex].containsnoT_NT_NL == True:
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
            for self.i in range(1,self.numExams+1): #set ignore status of exams, exams are before the baseline or after the selected 'current' exam, they should be ignored in best response determination
                if (self.CurrFound == False and self.BaseFound == False) or (self.CurrFound == True and self.BaseFound == True):
                    if form.StudyRoot.patients[self.selkey].exams[self.i].current == False and form.StudyRoot.patients[self.selkey].exams[self.i].baseline == False:
                        form.StudyRoot.patients[self.selkey].exams[self.i].add_ignore(True)
                
                #do this later so that the baseline does not incorrectly get marked at ignore == True (occurs because currFound and baseFound == True)
                if form.StudyRoot.patients[self.selkey].exams[self.i].current == True and \
                form.StudyRoot.patients[self.selkey].exams[self.i].baseline == False:
                    self.CurrFound = True #current exam found
                elif form.StudyRoot.patients[self.selkey].exams[self.i].baseline == True and \
                form.StudyRoot.patients[self.selkey].exams[self.i].current == False:
                    self.BaseFound = True #baseline found
        
        except Exception as e:
            print("Error: ",e)
            traceback.print_exc()
            QMessageBox.information(self,'Message','Please select a patient.')

    def patientSelected(self):
        '''
        List exams for selected patient
        '''
        self.examList.clear() #clear when new patient selected
        currPt = self.patientList.currentItem().text() #current patient string
        MRNSID = re.compile(r'\d{7}/\w{2}-\w-\w{4}')
        self.selkey = MRNSID.search(currPt).group() #selected patient

        self.link = form.StudyRoot.patients[self.selkey].exams.items() #link contains the exams
        self.exams1 = []
        for key,exam in self.link:
            self.examList.addItem(str(key) + ': ' + str(exam.modality) + ' - ' + str(exam.date))
            self.exams1.append(str(key) + ': ' + str(exam.modality) + ' - ' + str(exam.date))
        
        self.currentExamSelect.clear() #clear before listing, otherwise entries aggregate
        self.currentExamSelect.addItems(self.exams1)
        selection1 = self.currentExamSelect.currentText()

    def updateOptions(self,index):
        self.exams2 = self.exams1[index+1:]
        self.baselineExamSelect.clear()
        self.baselineExamSelect.addItems(self.exams2) #populate list

        #set default selection to oldest exam, assumed to be baseline
        count = self.baselineExamSelect.count()
        self.baselineExamSelect.setCurrentIndex(count-1)
    def returnHome(self):
        self.close()

    def populate_view(self):
        currPt = self.patientList.currentItem().text() #current patient string
        MRNSID = re.compile(r'\d{7}/\w{2}-\w-\w{4}')
        self.selkey = MRNSID.search(currPt).group() #selected patient

        self.lineedit_patient_name.setText(currPt)
        self.patient = form.StudyRoot.patients[self.selkey]
        self.tree_container.addWidget(PatientTree(self.patient))

class MainWindow(QMainWindow, design.Ui_mainWindow):
    
    recist_calc_signal = QtCore.pyqtSignal(bool) #indicate if FetchRoot should be used (if False), or StudyRoot (if True)
    recist_sheets_signal = QtCore.pyqtSignal(bool) #indicate if FetchRoot should be used (if False), or StudyRoot (if True)

    def __init__(self):
        # super use here because it allows us to access variables, methods etc in the design.py file
        super(MainWindow, self).__init__()
        self.setupUi(self)  # This is defined in design.py file automatically. It sets up layout and widgets that are defined     

        #### Login Window ####
        self.LoginWindow = ENABLELoginWindow(self)
        self.LoginWindow.loginSignal.connect(self.launch_main_window)
        self.LoginWindow.closeSignal.connect(self.login_close)
        self.LoginWindow.exec_()

        #### Init ####
        self.settings() #load user settings
        self.setWindowIcon(QtGui.QIcon('../icons/enable_icon.png'))
        self.consultDate.setDate(QtCore.QDate.currentDate())
        self.StudyRoot = BLDataClasses.StudyRoot() #stores imported Bookmark List data
        self.FetchRoot = BLDataClasses.StudyRoot() #stores data pulled from ENABLE database

        #### Signal Connections ####
        self.recist_calc_signal.connect(self.recistCalculations)
        self.recist_sheets_signal.connect(self.genRECIST)

        #### Toolbar and Secondary Dialog Launch ####
        configAction = QAction(QtGui.QIcon('../icons/configIcon.png'),'Configure',self)
        configAction.triggered.connect(self.config)
        self.mainToolbar.addAction(configAction)
        self.modExamDates.clicked.connect(self.launchExamSelect)
        self.plotsAndGraphs.clicked.connect(self.launchPlotAndGraph)

        #### Connect to DB ####
        # self.conf = yaml.load(open(os.path.realpath('usrp.yml')))
        # self.usr = self.conf['user']['usr']
        # self.usrp = self.conf['user']['p']
            
        #### Consultation Tab ####
        self.importPatients.clicked.connect(self.importBookmarks)
        self.removePatients.clicked.connect(self.clearBookmarks)
        self.excludePatient.clicked.connect(self.removeSelectedPatient)  #exclude selected patient
        self.includePatient.clicked.connect(self.includeSelectedPatient)  #include patient
        self.patientListAppend.clicked.connect(self.appendPatientList)
        self.patientList.clicked.connect(self.updateConsult)
        self.generateConsultLog.clicked.connect(self.genConsultLog)
        self.databaseUploader.clicked.connect(self.launchDbUploadDialog) #open uploader dialog

        self.btn_consult_generate_recist.clicked.connect(self.recist_sheet_with_studyroot)
        self.btn_consult_recist_calcs.clicked.connect(self.recist_cal_with_studyroot)

        #### Clinical Tab ####
        self.generateSpreadsheets.clicked.connect(self.genSpreadsheets)  #generate spreadsheets (singles and cohort)
        self.exportPlotData.clicked.connect(self.EPD)  #export waterfall/spider/swimmer plot data
        self.btn_load_patients_from_db.clicked.connect(self.import_patients_from_db)
        self.btn_clinical_generate_recist.clicked.connect(self.recist_sheet_with_fetchrot)
        self.btn_clinical_recist_calcs.clicked.connect(self.recist_cal_with_fetchroot)

        self.database_list = pull_patient_list_from_mongodb()
        self.search_list = []
        for i in range(0,len(self.database_list[0])):
            self.list_available_patients.addItem(self.database_list[0][i] + ' - ' + self.database_list[1][i] + '/' + self.database_list[2][i])
            self.search_list.append(self.database_list[0][i] + ' - ' + self.database_list[1][i] + '/' + self.database_list[2][i])

        self.search_lineedit = QLineEdit()
        self.combobox_patient_search.setLineEdit(self.search_lineedit)
        self.completer = QtGui.QCompleter(self.search_list,self)
        self.completer.setCompletionMode(QtGui.QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.combobox_patient_search.setCompleter(self.completer)
        self.btn_add_patient_to_load.clicked.connect(self.add_patient_selected)
        self.btn_dont_load_selected_patient.clicked.connect(self.dont_load_selected_patient)
        self.btn_unload_all_patients.clicked.connect(self.unload_all_patients)

    #### Signal Functions ####
    def recist_cal_with_fetchroot(self):
        self.recist_calc_signal.emit(False) #recist calc with FetchRoot

    def recist_cal_with_studyroot(self):
        self.recist_calc_signal.emit(True) #recist calc with StudyRoot

    def recist_sheet_with_fetchrot(self):
        self.recist_sheets_signal.emit(False)
    
    def recist_sheet_with_studyroot(self):
        self.recist_sheets_signal.emit(True)

    #### Consult Tab Functions ####
    def appendPatientList(self):
        self.appendList = [] #list specifically for appending
        try:
            getattr(self,'StudyRoot')  #crash if StudyRoot not available  
            self.statusbar.showMessage('Appending Patient List...')
            flag = 0
            try: #catch error when user hits "ESC" in file select dialogue
                ret = QFileDialog.getOpenFileNames(self, "Select Bookmark List(s)", self.BLDir) #returns tuple (list of file names, filter)
                files = ret[0] #absolute file paths to bookmark lists selected
                
                self.dirName = os.path.dirname(files[0]) #all BL in same directory, take dir from first
                for i in files:
                    if i not in self.baseNames: #only add if not already in list
                        self.baseNames.append(os.path.basename(i)) #add the base names to a list
                    self.appendList.append(os.path.basename(i))
                flag = 0
                
            except Exception as e:
                print("Error: ",e)
                traceback.print_exc()
                self.dirName = ''
                self.baseNames = ''
                flag = 1 #no imports
        
            if flag == 0:
                #for self.file in self.baseNames:
                bl_import(self.df,self.StudyRoot,self.dirName,self.appendList) #send one patient at a time, adding them to the StudyRoot one at a time
                QMessageBox.information(self,'Message','Bookmark List(s) successfully appended.')
                self.statusbar.showMessage('Done importing Bookmark List(s)', 1000)
                
                ### Populate List with Pt names ###
                self.patientList.clear() #cleat to update
                for key,patient in self.StudyRoot.patients.items():
                    self.patientList.addItem(patient.name + ' - ' + key)
            elif flag == 1:
                QMessageBox.information(self,'Message','No Bookmark List(s) imported.')
                del self.StudyRoot
                self.statusbar.clearMessage()
        except Exception as e:
            print("Error: ",e)
            traceback.print_exc()
            self.importBookmarks()

    def updateConsult(self):
        self.currPt = self.patientList.currentItem().text()
        self.MRNSID = re.compile(r'\d{7}/\w{2}-\w-\w{4}')
        self.selkey = self.MRNSID.search(self.currPt).group() #selected patient
        
        self.ptname = self.StudyRoot.patients[self.selkey].name
        self.ptmrn = self.StudyRoot.patients[self.selkey].mrn
        self.ptsid = self.StudyRoot.patients[self.selkey].study_protocol

        #Update display panel
        self.consultPatient.setText(self.ptname)
        self.consultMRN.setText(self.ptmrn)
        self.consultProtocol.setText(self.ptsid)

        self.link = self.StudyRoot.patients[self.selkey].exams.items() #link contains the exams
        self.exams = []
        for key,exam in self.link:
            self.exams.append(str(exam.date))

        self.priorBaselineDate.clear()
        self.baselineDate.clear()
        self.restagingDate.clear()
        self.priorBaselineDate.addItems(self.exams)
        self.baselineDate.addItems(self.exams)
        self.restagingDate.addItems(self.exams)

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



    def removeSelectedPatient(self):
        #remove highlighted patients, flag them in StudyRoot so they are skipped (ignore == True)
        try:
            temp = self.patientList.currentItem()
            self.excludeList.addItem(temp.text())
            self.patientList.takeItem(self.patientList.row(temp))
            currPt = temp.text() #current patient string
            MRNSID = re.compile(r'\d{7}/\w{2}-\w-\w{4}')
            selkey = MRNSID.search(currPt).group() #selected patient
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
            form.StudyRoot.patients[selkey].add_ignore(False) #mark patient for ignore
        except Exception as e:
            print("Error: ",e)
            traceback.print_exc()
            QMessageBox.information(self,'Message','No patient selected for inclusion.')

    def clearBookmarks(self):
        #Clear the list widget containing patient names/mrn
        try:
            getattr(self,'StudyRoot')
            self.patientList.clear()
            self.excludeList.clear()
            del self.StudyRoot #delete the study root
            del self.Calcs #delete to catch when patients are removed and user attemps to generate sheets
            self.btn_consult_recist_calcs.setEnabled(False)
            self.btn_consult_generate_recist.setEnabled(False)
            self.databaseUploader.setEnabled(False)
            self.modExamDates.setEnabled(False)
            QMessageBox.information(self,'Message','All patients removed.')
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()
            pass
        
    def settings(self):
        #get application settings (default directories)
        try:
            with shelve.open('LocalPreferences') as shelfFile:
                self.BLDir = shelfFile['BLDir']
                self.RECISTDir = shelfFile['RECISTDir']
                self.OutDir = shelfFile['OutDir']
                self.mongodb_address = shelfFile['mongodb_address']
                shelfFile.close()
        except KeyError:
            QMessageBox.information(self,'Message','Please configure ENABLE 2')
            self.config()

    def config(self):
        self.config_page = ConfigurationPage()
        self.config_page.exec()
        self.settings()

    

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
            except Exception as e:
                QMessageBox.information(self,'Message','Please perform RECIST calculations.')
                print("Error: ",e)

        except Exception as e:
            QMessageBox.information(self,'Message','Please import Bookmark List(s).')
            print("Error: ",e)
        self.statusbar.showMessage('Done generating spreadsheets.', 1000)

   

    def genConsultLog(self):
        self.vals = [
                    self.selkey,
                    self.consultant.text(),
                    self.consultPhys.text(),
                    str(self.consultDate.date().toPyDate()),
                    self.priorBaselineDate.currentText(),
                    self.baselineDate.currentText(),
                    self.restagingDate.currentText(),
                    self.describe_1.toPlainText(),
                    self.reason_2a.isChecked(),
                    self.reason_2b.isChecked(),
                    self.describe_2.toPlainText(),
                    self.generalComments.toPlainText()
                    ]
        exportToLog(self.RECISTDir,self.OutDir,self.StudyRoot,self.vals)
        
    #### UI Functions ####
    def login_close(self,signal):
        if signal == True:
            sys.exit()
    def launch_main_window(self,signal):
        if signal == True:
            QtCore.QTimer.singleShot(2000,self.start)
            
    def start(self):
        self.show()
        self.LoginWindow.hide()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def launchExamSelect(self):
        #launch exam selection dialog if the StudyRoot exists (BLs have been imported)
        try:
            getattr(self,'StudyRoot')
            self.dataoverride = DataOverrides()
            self.dataoverride.exec()
        except Exception as e:
            print(e)
            traceback.print_exc()
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
    


    def launchDbUploadDialog(self):
        try:
            self.StudyRoot #check if patients imported
            try:
                if self.Calcs == True: #check if calcs performed
                    self.uploaddialog = DatabaseUploadDialog()
                    self.uploaddialog.exec()
                elif self.Calcs == False:
                    QMessageBox.information(self,'Message','Please perform RECIST calculations.')
            except Exception as e:
                print(e)
                traceback.print_exc()
                QMessageBox.information(self,'Message','Please perform RECIST calculations.')
        except Exception as e:
            print(e)
            traceback.print_exc()
            QMessageBox.information(self,'Message','Please import Bookmark List(s).')

    #### Clinical Tab Functions ####   
    def import_patients_from_db(self):
        # if self.FetchRoot is None:
        #     self.FetchRoot = BLDataClasses.StudyRoot()
        
        try:
            self.FetchRoot
        except Exception as e:
            print(e)
            self.FetchRoot = BLDataClasses.StudyRoot()

        self.statusbar.showMessage('Importing from Database!', 1000)
        self.fetch_list = [i.text() for i in self.list_patients_to_load.findItems("", QtCore.Qt.MatchContains)]
        pull_patients_from_mongodb(self.FetchRoot,self.fetch_list)
        self.statusbar.showMessage('Done importing!',1000)

        self.list_patients_to_load.clear()
        self.list_loaded_patients.addItems(self.fetch_list)

        self.btn_clinical_generate_recist.setEnabled(True)
        self.generateSpreadsheets.setEnabled(True)
        self.exportPlotData.setEnabled(True)
        self.plotsAndGraphs.setEnabled(True)
        self.btn_clinical_recist_calcs.setEnabled(True)
        self.btn_unload_all_patients.setEnabled(True)

    def add_patient_selected(self):
        if not self.list_patients_to_load.findItems(str(self.combobox_patient_search.currentText()), QtCore.Qt.MatchFixedString):
            self.list_patients_to_load.addItem(str(self.combobox_patient_search.currentText()))
        self.search_lineedit.clear()

    def unload_all_patients(self):
        try:
            self.list_loaded_patients.clear()
            del self.FetchRoot
        except Exception as e:
            print(e)

    def dont_load_selected_patient(self):
        try:
            temp = self.list_patients_to_load.currentItem()
            self.list_patients_to_load.takeItem(self.list_patients_to_load.row(temp))
        except Exception as e:
            print(e)
            traceback.print_exc()
            QMessageBox.information(self,'Message','No patient selected for removal.')

    #### Shared Computational/Operation Functions ####
    def recistCalculations(self,signal):
        #perform recist calculations by passing each patient in self.root_to_use to the recist_computer() function
        if signal == True:
            self.root_to_use = self.StudyRoot
            self.btn_consult_generate_recist.setEnabled(True)
            self.databaseUploader.setEnabled(True)
        else:
            self.root_to_use = self.FetchRoot

        try:
            getattr(self,'StudyRoot')
            self.Calcs = True
            self.statusbar.showMessage('Performing RECIST calculations')
            for key, patient in self.root_to_use.patients.items():
                recist_computer(patient) #perform RECIST computations for the selected patient  
            if signal == True:
                patient_uploader_func(self.root_to_use,None,True)
            self.statusbar.showMessage('Done with RECIST calculations!', 1000)
        except Exception as e:
            QMessageBox.information(self,'Message','Please import Bookmark List(s).')
            print("Error: ",e)
            traceback.print_exc()
            self.Calcs = False

    def importBookmarks(self):
        self.statusbar.showMessage('Importing Bookmark List(s)...')
        self.patientList.clear()
        self.df = {}
        self.baseNames = [] #initialize list of base names
        
        flag = 0
        try: #catch error when user hits "ESC" in file select dialogue
            ret = QFileDialog.getOpenFileNames(self, "Select Bookmark List(s)", self.BLDir) #returns tuple (list of file names, filter)
            files = ret[0] #absolute file paths to bookmark lists selected
            
            self.dirName = os.path.dirname(files[0]) #all BL in same directory, take dir from first
            #self.baseNames = [] #initialize list of base names
            for i in files:
                self.baseNames.append(os.path.basename(i)) #add the base names to a list
            flag = 0
            
        except Exception as e:
            print(e)
            traceback.print_exc()
            self.dirName = ''
            self.baseNames = ''
            flag = 1 #no imports

        if flag == 0:
            bl_import(self.df,self.StudyRoot,self.dirName,self.baseNames) #import patients
            QMessageBox.information(self,'Message','Bookmark List(s) successfully imported.')
            self.statusbar.showMessage('Done importing Bookmark List(s)', 1000)
            
            ### Populate List with Pt names ###
            for key,patient in self.StudyRoot.patients.items():
                self.patientList.addItem(patient.name + ' - ' + key)
        elif flag == 1:
            QMessageBox.information(self,'Message','No Bookmark List(s) imported.')
            del self.StudyRoot
            self.statusbar.clearMessage()

        self.modExamDates.setEnabled(True)
        self.btn_consult_recist_calcs.setEnabled(True)

    def genRECIST(self,signal):
        if signal == True:
            self.root_to_use = self.StudyRoot
        else:
            self.root_to_use = self.FetchRoot
        try:
            self.root_to_use #check if patients imported
            try:
                #if self.Calcs == True: #check if calcs performed
                generate_recist_sheets(self.RECISTDir, self.OutDir, self.root_to_use, self.singleSheet.isChecked())
                #QMessageBox.information(self,'Message','RECIST worksheets generated.')
                #elif self.Calcs == False:
                #QMessageBox.information(self,'Message','Please perform RECIST calculations.')
            except Exception as e:
                QMessageBox.information(self,'Message','Please perform RECIST calculations.')
                traceback.print_exc()
                print('Error: ',e)

        except Exception as e:
            QMessageBox.information(self,'Message','Please import Bookmark List(s).')
            traceback.print_exc()
            print('Error: ',e)
        self.statusbar.showMessage('Done generating RECIST worksheets.', 1000)
class PlotAndGraphingDialog(QDialog, plotandgraph.Ui_plotAndGraphUtility):
    def __init__(self, parent=None):
        QMainWindow.__init__(self)
        self.setupUi(self) #setup the graphing window

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
        '''
        Plot patient Target RECIST sum vs.Time
        '''
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

        self.plt1 = pg.PlotDataItem(self.trecistsums,pen='b')
        self.plt2 = pg.PlotDataItem(self.trecistsums, pen=None,symbol='o',symbolBrush='k')
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
        exportPlotData(form.StudyRoot,form.OutDir) #call external function to generate
        QMessageBox.information(self,'Message','Plot data exported.')

    #### PLOTTING SHARED FNX ####
    def CP(self):
        self.graphicsView.clear()

class DatabaseUploadDialog(QDialog, uploader.Ui_databaseuploaddialog):
    def __init__(self, parent=None):
        QMainWindow.__init__(self)
        self.setupUi(self) #setup the graphing window
        
class ENABLELoginWindow(QDialog, login.Ui_logindialog):
    '''
    Login page class
    '''
    loginSignal = QtCore.pyqtSignal(bool) #indicate if user login accepted and mainwindow should load
    closeSignal = QtCore.pyqtSignal(bool) #indicate that user closed login - close entire application
    offlineSignal = QtCore.pyqtSignal(bool) #launch offline mode with limited features

    def __init__(self, parent = None):
        QDialog.__init__(self)
        self.setupUi(self) #setup the graphing window

        self.pixmax = QtGui.QPixmap('../icons/enable_icon.png')
        self.ENABLE_logo.setPixmap(self.pixmax)
        self.ENABLE_logo.show()
        self.setWindowIcon(QtGui.QIcon('../icons/enable_icon.png'))
        self.show()

        self.btn_log_in.clicked.connect(self.run_login)
        self.btn_offline_mode.clicked.connect(self.run_offline_mode)
        self.count = 0

    def run_login(self):
        self.actual_name = win32api.GetUserNameEx(3) #actual name of the user
        #self.user_info = win32net.NetUserGetInfo (win32net.NetGetAnyDCName (), win32api.GetUserName (), 1) #returns dict, use field 'home_dir' to find 'nih.gov'
        if self.actual_name is not None:
            self.welcome_label.setText('Welcome ' + self.actual_name)
        if 'nih' in self.actual_name.lower():
            try: #open connecting for availability test
                client = pymongo.MongoClient(serverSelectionTimeoutMS=30) #timeout after 30ms connect attempt
                client.server_info() # force connection on a request, err if no server available
                client.close()
                self.connecting_label.setText('Connection established! Launching ENABLE 2.0.')
                self.loginSignal.emit(True)
            except pymongo.errors.ServerSelectionTimeoutError as err:
                self.count += 1
                self.btn_log_in.setText('Retry')
                self.count_label.setText('Attempt...'+ str(self.count))
                self.connecting_label.setText('Server unavailable. Retry or use Offline Mode.')
                print(err)
                traceback.print_exc()
        else:
            self.connecting_label.setText('Unauthorized user. Please contact administrator')

    def run_offline_mode(self):
        self.connecting_label.setText('Launching in Offline Mode.')

    def closeEvent(self,event):
        self.closeSignal.emit(True)
    
    def keyPressEvent(self,event):
        # Did the user press the Escape key?
        if event.key() == QtCore.Qt.Key_Escape:
            event.ignore()

class ConfigurationPage(QDialog, config.Ui_configuration):
    def __init__(self, parent=None):
        QMainWindow.__init__(self)
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon('../icons/configIcon.png'))     

        shelfFile = shelve.open('LocalPreferences')
        shelfFile['RECISTDir'] = os.path.dirname(os.path.realpath('RECISTForm.docx'))
        shelfFile['LMUploader'] = os.path.dirname(os.path.realpath('RadiologyImportClient.jar'))
        self.bl_directory.setText(shelfFile['BLDir'])
        self.output_directory.setText(shelfFile['OutDir'])
        shelfFile.close()

        self.btn_bl_directory.clicked.connect(self.bl_directory_select)
        self.btn_output_directory.clicked.connect(self.output_directory_select)
        self.btn_db_path.clicked.connect(self.set_db_address)

        self.admin_pass.textChanged.connect(self.admin_pass_check)
        
        self.show()

    def bl_directory_select(self):
        shelfFile = shelve.open('LocalPreferences')
        BLDirT = str(QFileDialog.getExistingDirectory(self, "Select Bookmark List Directory"))
        if BLDirT != '':
            shelfFile['BLDir'] = BLDirT
        else:
            QMessageBox.information(self,'Message','Directory unchanged.')
        shelfFile.close()

    def output_directory_select(self):
        OutDirT = str(QFileDialog.getExistingDirectory(self, "Select Output Directory"))
        if OutDirT != '':
            shelfFile['OutDir'] = OutDirT
        else:
            QMessageBox.information(self,'Message','Directory unchanged.')
        shelfFile.close()

    def admin_pass_check(self):
        self.entered_pass = hashlib.md5(str(self.admin_pass.text()).encode('utf-8')).hexdigest()
        self.boolVal = bool(self.entered_pass == '719b6d1c52edbb355a8e9f8c0ada6ad4')
        self.db_path.setEnabled(self.boolVal)
        self.btn_db_path.setEnabled(self.boolVal)

    def set_db_address(self):
        shelfFile = shelve.open('LocalPreferences')
        mongodb_address = self.db_path.text()
        if mongodb_address != '':
            shelfFile['mongodb_address'] = mongodb_address
            self.admin_pass.clear()
            self.db_path.setEnabled(False)
            self.btn_db_path.setEnabled(False)  
        shelfFile.close()

def kill_proc_tree(pid, including_parent=True):    
    '''
    Kill process based on its pid
    '''
    parent = psutil.Process(pid)
    for child in parent.children(recursive=True):
        child.kill()
    if including_parent:
        parent.kill()
if __name__ == '__main__':
    myappid = u'ENABLE 2.0_V1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    #pyqtgraph settings
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')

    #create app instance and launch
    app = QApplication([])
    app.setApplicationName('ENABLE 2.0')
    #app.setStyle(QStyleFactory.create("Fusion"))
    
    form = MainWindow() #dont show yet, show after validated log-in

    app.exec_()

    me = os.getpid()
    kill_proc_tree(me)

#CHANGELOG
#7/6/17 commit 45177f75869b17652c82adaeddd97055c9ff15bc - Added ability to 'append' patient list
#7/7/17 commit f5c60f23f0f25f3146ac38c2ab8755062d5894a0 - Fixed error where exams were incorrectly marked as containsnoT_NT_NL = True due to faulty logic in BLImporterUIVersion.py around line 140
#7/11/17 commit 7ae65da84eb97f6e5c3640bd4c8f6e343500b42e - added ablity to export consult log
#7/12/17 commit 46788ce22a5be2eb805079e429313faab986e305 - modified RECIST gen to print sheets for every exam