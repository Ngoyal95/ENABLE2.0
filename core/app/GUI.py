#! python3
#Revision 7/26/17
#Custom packages
import core.gui.design as design # This file holds our MainWindow and all design related things
import core.gui.data as data #file holds data entry page
import core.gui.uploader as uploader #database upload page
import core.gui.login as login #login page
import core.gui.config as config
import core.app.BLDataClasses as BLDataClasses
from core.app.BLImportFunctions import bl_import, multi_process_import
from core.app.RECISTComp import recist_computer
from core.app.RECISTGen import generate_recist_sheets
from core.app.DataExport import exportToExcel, waterfallPlot, spiderPlot, exportPlotData, exportToLog
from core.app.backend_interface import patient_uploader_func, pull_patient_list_from_mongodb, pull_patients_from_mongodb

import pandas as pd
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
import yaml
import copy
from PyQt5.QtWidgets import (QLineEdit, QProgressBar, QDialog, QTableView, 
                            QFileDialog, QAction, QApplication, QWidget, 
                            QPushButton, QMessageBox, QDesktopWidget, QMainWindow,
                            QTreeWidget, QTreeWidgetItem, QItemDelegate
                            )
from PyQt5 import QtCore, QtGui
from pprint import pprint


#TO FIX ON DATA ENTRY PANEL:
#No need for ability to de-select exams to change their ignore status (but leave in since it's easier)
#managing a new baseline.

class MyDelegate(QItemDelegate):
    '''
    Custom delegate for the patient data viewing tree, used to prevent user from editing the first 3 columns of the tree
    (the exam description, lesion follow-up, and lesion name)
    '''
    def createEditor(self, parent, option, index):
        if index.column() not in {0,1,3,4}:
            return super(MyDelegate,self).createEditor(parent,option,index)
        return None
class DataEntry(QDialog, data.Ui_Form):
    def __init__(self, parent):
        super(DataEntry,self).__init__(parent)
        self.setupUi(self) #setup the selection window

        for key,patient in self.parent().StudyRoot.patients.items(): #note, StudyRoot belongs to form (main application window)
            if patient.ignore == False:
                self.patientList.addItem(patient.name + ' - ' + key)
        
        self.temp_root = copy.deepcopy(self.parent().StudyRoot)

        self.btn_set_params.setEnabled(False)
        self.btn_deep_reset.setEnabled(False)
        self.btn_reset.setEnabled(False)
        self.delegate = MyDelegate()

        self.returnToHome.clicked.connect(self.returnHome)
        self.patientList.itemClicked.connect(self.patientSelected)
        self.btn_set_baseline.clicked.connect(self.set_patient_baseline)
        self.btn_set_params.clicked.connect(self.set_patient_params)
       
        self.btn_deep_reset.clicked.connect(self.deep_reset)
        self.btn_reset.clicked.connect(self.reset)

    def deep_reset(self):
        '''
        Reset patient data to the state contained in OriginalRoot
        '''
        reply = QMessageBox.warning(self,'Warning!','Deep Rest will remove ALL changes which have been made to patient data and revert to Bookmark List values.',
            QMessageBox.StandardButtons(QMessageBox.Yes|QMessageBox.Cancel))
        
        if reply == QMessageBox.Yes:
            self.temp_patient = copy.deepcopy(self.parent().OriginalRoot.patients[self.selkey])
            self.parent().StudyRoot.patients[self.selkey] = copy.deepcopy(self.parent().OriginalRoot.patients[self.selkey])
            self.populate_view()
            self.btn_reset.setEnabled(False)
        pass

    def reset(self):
        '''
        Reset state to StudyRoot values prior to edits (ONLY FUNCTIONS BEFORE commiting changes from self.tenp_patient to the StudyRoot, using the btn_set_params)
        '''
        #NOT a deep reset to the object stored in the OriginalRoot, just to StudyRoot state.
        reply = QMessageBox.warning(self,'Warning!','Reset will remove ALL recent changes to patient data.',
            QMessageBox.StandardButtons(QMessageBox.Yes|QMessageBox.Cancel))
        
        if reply == QMessageBox.Yes:
            self.temp_patient = copy.deepcopy(self.parent().StudyRoot.patients[self.selkey])
            self.populate_view()
            self.btn_reset.setEnabled(False)

    def set_patient_baseline(self):
        '''
        Set all exams prior to baseline to ignore = False
        '''
        self.baseline_key = self.baselineExamSelect.currentIndex() + 1

        for key,exam in self.temp_patient.exams.items():
            exam.add_ignore(False)
            exam.add_baseline(False)

        self.temp_patient.exams[self.baseline_key].add_baseline(True) #set baseline

        self.base_found = False
        for key,exam in self.temp_patient.exams.items():
            if exam.baseline and self.base_found == False:
                self.base_found = True
            elif self.base_found == True:
                exam.add_ignore(True)
        
        self.btn_set_params.setEnabled(True)
        self.btn_reset.setEnabled(True)
        self.populate_view()

    def patientSelected(self):
        '''
        List exams for selected patient
        '''
        self.btn_set_params.setEnabled(False)
        self.btn_deep_reset.setEnabled(True)
        self.btn_reset.setEnabled(True)

        currPt = self.patientList.currentItem().text() #current patient string
        MRNSID = re.compile(r'\d{7}/\w{2}-\w-\w{4}')
        self.selkey = MRNSID.search(currPt).group() #selected patient

        self.temp_patient = self.temp_root.patients[self.selkey] #temp patient for updating values

        self.exams = []
        for key,exam in self.temp_patient.exams.items():
            self.exams.append(str(key) + ': ' + str(exam.modality) + ' - ' + str(exam.date))
        
        self.baselineExamSelect.clear()
        self.baselineExamSelect.addItems(self.exams) #populate list
        self.baselineExamSelect.setCurrentIndex(self.baselineExamSelect.count()-1) #display the oldest exam
        self.btn_set_baseline.setEnabled(True)
        self.populate_view()

    def returnHome(self):
        if hasattr(self,'temp_patient'):
            reply = QMessageBox.question(self,'Commit?','Would you like to save all unsaved changes (if any)?',QMessageBox.StandardButtons(QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel))
            if reply == QMessageBox.Yes:
                self.set_patient_params()
                self.close()
            elif reply == QMessageBox.Cancel:
                pass
            else:
                self.close()
        else:
            #no pt selected
            self.close()

    def populate_view(self):
        currPt = self.patientList.currentItem().text() #current patient string
        self.lineedit_patient_name.setText(currPt)
        self.patient = self.temp_patient

        if hasattr(self,'patient_tree'):
            self.patient_tree.setParent(None) #drop pointer so multiple don't get added to the tree_container
            del self.patient_tree
            self.patient_tree = self.create_patient_tree()
            self.tree_container.addWidget(self.patient_tree)
        else:
            self.patient_tree = self.create_patient_tree()
            self.tree_container.addWidget(self.patient_tree)
        self.patient_tree.itemChanged.connect(self.update_temp_patient_obj)
        self.patient_tree.setItemDelegate(self.delegate) #custom delegate to prevent editing the first 3 columns

    def update_temp_patient_obj(self,item,col):
        self.btn_set_params.setEnabled(True)

        ### Need to view exam item and then reflect the change in the self.temp_patient
        self.headers = [
                        'Exam',
                        'Baseline',
                        'Inc.',
                        'Follow-Up',
                        'Name',
                        'Description',
                        'Target',
                        'Sub-Type',
                        'Series',
                        'Slice#',
                        'RECIST Diameter (mm)'
                        ]
        #col in the self.headers list -> use to access properties for update
        self.data_in_item_col = item.text(col)
        self.lesion_name = item.text(4)

        if item.parent() is not None:
            #lesion_item
            self.parent_exam_date = item.parent().text(0).split(',')[0]
            self.exam = next((x for key,x in self.temp_patient.exams.items() if x.date == self.parent_exam_date), None)
            self.lesion = next((x for x in self.exam.lesions if x.params['Name'] == self.lesion_name), None) #find lesion obj w/ matching name
        
            if col == 2:
                #lesion included/excluded
                #included by default
                if not item.checkState(col) == QtCore.Qt.Checked:
                    self.lesion.add_include(False) #exclude
                else:
                    self.lesion.add_include(True) #include)
            else:
                self.lesion.params[self.headers[col]] = self.data_in_item_col
        else:
            #exam_item
            self.exam_date = item.text(0).split(',')[0]
            self.exam = next((x for key,x in self.temp_patient.exams.items() if x.date == self.exam_date), None)
            if item.checkState(col) == QtCore.Qt.Checked:
                self.exam.add_ignore(False)
            else:
                self.exam.add_ignore(True)

    def set_patient_params(self):
        self.temp_patient.course = str(self.pt_course.value())
        self.temp_patient.day = str(self.pt_day.value())
        self.parent().StudyRoot.patients[self.selkey] = self.temp_patient
    
    def create_patient_tree(self):
        '''
        Create QTreeWidget populated with a patient's data for the DataEntry dialog.
        Assumes that self.temp_patient is the patient of interest and that the variable belongs to the dialog.
        '''
        self.tree = QTreeWidget()
        self.root = self.tree.invisibleRootItem()
        self.headers = [
                        'Exam',
                        'Baseline',
                        'Inc.',
                        'Follow-Up',
                        'Name',
                        'Description',
                        'Target',
                        'Sub-Type',
                        'Series',
                        'Slice#',
                        'RECIST Diameter (cm)'
                        ]
        self.headers_item = QTreeWidgetItem(self.headers)
        self.tree.setColumnCount(len(self.headers))
        self.tree.setHeaderItem(self.headers_item)
        self.root.setExpanded(True)
        self.addItems()
        self.tree.header().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.tree.header().setStretchLastSection(False)
        return self.tree

    def addItems(self):
        '''
        Add items to the table from the patient object
        '''
        self.temp_patient
        for key,exam in self.temp_patient.exams.items():
            column = 0
            self.exam_item = QTreeWidgetItem(self.root)
            self.exam_item.setText(column,', '.join([str(exam.date),str(exam.modality),str(exam.description)]))
            
            if exam.ignore == False and exam.baseline == False:
                self.exam_item.setText(column+1,'No')
                self.exam_item.setCheckState (column, QtCore.Qt.Checked)
            elif not(exam.ignore == False and exam.baseline == True):
                self.exam_item.setText(column+1,'No')
                self.exam_item.setCheckState (column, QtCore.Qt.Unchecked)
                #self.exam_item.setDisabled(True) #don't allow user to interact with item if these exams are to be ignored (prevents them from checking the box)
            else:
                self.exam_item.setText(column+1,'Yes')

            for lesion in exam.lesions:
                column = 2
                if lesion.params['Target'].lower() == 'target' or lesion.params['Target'].lower() == 'non-target':
                    self.header_params = [
                                        lesion.params['Follow-Up'],
                                        lesion.params['Name'],
                                        lesion.params['Description'],
                                        lesion.params['Target'],
                                        lesion.params['Sub-Type'],
                                        lesion.params['Series'],
                                        lesion.params['Slice#'],
                                        round(lesion.params['RECIST Diameter (mm)']/10,1)
                                        ]        
                    self.lesion_item = QTreeWidgetItem(self.exam_item)
                    self.lesion_item.setCheckState(column,QtCore.Qt.Checked)
                    column += 1
                    for param_str in self.header_params:
                        self.lesion_item.setText(column,str(self.header_params[column-3]))
                        self.lesion_item.setTextAlignment(column,4) #align center of column
                        column += 1
                    self.lesion_item.setFlags(self.lesion_item.flags() | QtCore.Qt.ItemIsEditable)


class MainWindow(QMainWindow, design.Ui_mainWindow):
    
    recist_calc_signal = QtCore.pyqtSignal(bool) #indicate if FetchRoot should be used (if False), or StudyRoot (if True)
    recist_sheets_signal = QtCore.pyqtSignal(bool) #indicate if FetchRoot should be used (if False), or StudyRoot (if True)

    def __init__(self,parent=None):
        # super use here because it allows us to access variables, methods etc in the design.py file
        
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)  # This is defined in design.py file automatically. It sets up layout and widgets that are defined     

        #### Login Window ####
        self.LoginWindow = ENABLELoginWindow(self)
        self.LoginWindow.loginSignal.connect(self.launch_main_window)
        self.LoginWindow.closeSignal.connect(self.login_close)
        self.LoginWindow.exec_()

        #### Init ####
        self.settings() #load user settings
        self.setWindowIcon(QtGui.QIcon('icons/enable_icon.png'))
        self.consultDate.setDate(QtCore.QDate.currentDate())
        self.OriginalRoot = BLDataClasses.StudyRoot() #used to store original data imported, NOT edited and not used in program (unless for reset purposes)
        self.StudyRoot = BLDataClasses.StudyRoot() #stores imported Bookmark List data
        self.FetchRoot = BLDataClasses.StudyRoot() #stores data pulled from ENABLE database

        #### Signal Connections ####
        self.recist_calc_signal.connect(self.recistCalculations)
        self.recist_sheets_signal.connect(self.genRECIST)

        #### Toolbar and Secondary Dialog Launch ####
        configAction = QAction(QtGui.QIcon('icons/configIcon.png'),'Configure',self)
        configAction.triggered.connect(self.config)
        self.mainToolbar.addAction(configAction)
        self.modExamDates.clicked.connect(self.launch_data_entry)

        #### Connect to DB ####
        # self.conf = yaml.load(open(os.path.realpath('usrp.yml')))
        # self.usr = self.conf['user']['usr']
        # self.usrp = self.conf['user']['p']
            
        #### Consultation Tab ####
        self.importPatients.clicked.connect(self.importBookmarks)
        self.removePatients.clicked.connect(self.clearBookmarks)
        self.excludePatient.clicked.connect(self.removeSelectedPatient)  #exclude selected patient
        self.includePatient.clicked.connect(self.includeSelectedPatient)  #include patient
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
        self.list_available_patients.itemClicked.connect(self.update_combobox_lineedit) #if patient in list is clicked, update search_lineedit
        self.search_lineedit.setClearButtonEnabled(True)
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
            self.parent().StudyRoot.patients[selkey].add_ignore(True) #mark patient for ignore
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
            self.parent().StudyRoot.patients[selkey].add_ignore(False) #mark patient for ignore
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
            del self.OriginalRoot
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
        try:
            #settings have been selected before
            with shelve.open('LocalPreferences') as shelfFile:
                self.BLDir = shelfFile['BLDir']
                self.RECISTDir = shelfFile['RECISTDir']
                self.OutDir = shelfFile['OutDir']
                self.mongodb_address = shelfFile['mongodb_address']
                #print(self.BLDir,self.RECISTDir,self.OutDir)
                shelfFile.close()
        except:
            #need to configure for the first time
            QMessageBox.information(self,'Message','First time use detected. Please configure ENABLE 2')
            self.config()

    def config(self):
        self.config_page = ConfigurationPage(self)
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

    def launch_data_entry(self):
        #launch exam selection dialog if the StudyRoot exists (BLs have been imported)
        try:
            getattr(self,'StudyRoot')
            self.dataoverride = DataEntry(self)
            self.dataoverride.exec()
        except Exception as e:
            print(e)
            traceback.print_exc()
            QMessageBox.information(self,'Message','Please Import Bookmark List(s).')

    def launchDbUploadDialog(self):
        try:
            self.StudyRoot #check if patients imported
            try:
                if self.Calcs == True: #check if calcs performed
                    self.uploaddialog = DatabaseUploadDialog(self)
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
        if  (    not self.list_patients_to_load.findItems(str(self.combobox_patient_search.currentText()), QtCore.Qt.MatchFixedString) and 
                re.search('[a-zA-Z]+',self.combobox_patient_search.currentText()) != None
            ): 
                #if patient not already in load list, add
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
    def update_combobox_lineedit(self,signal):
        self.combobox_patient_search.setCurrentText(signal.text())
    def clear_combobox_lineedit(self):
        self.search_lineedit.clear()
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
            exportPlotData(self.root_to_use,self.OutDir)
            self.statusbar.showMessage('Done with RECIST calculations!', 1000)
        except Exception as e:
            QMessageBox.information(self,'Message','Please import Bookmark List(s).')
            print("Error: ",e)
            traceback.print_exc()
            self.Calcs = False

    def importBookmarks(self):
        if hasattr(self,'OriginalRoot') == False:
            self.OriginalRoot = BLDataClasses.StudyRoot()
            self.StudyRoot = BLDataClasses.StudyRoot()
        
        self.statusbar.showMessage('Importing Bookmark List(s)...')
        self.patientList.clear()
        self.df = {}
        self.baseNames = [] #initialize list of base names
        
        flag = 0
        try: #catch error when user hits "ESC" in file select dialogue
            ret = QFileDialog.getOpenFileNames(self, "Select Bookmark List(s)", self.BLDir) #returns tuple (list of file names, filter)
            files = ret[0] #absolute file paths to bookmark lists selected
            
            self.dirName = os.path.dirname(files[0]) #all BL in same directory, take dir from first
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
            #bl_import(self.df,self.OriginalRoot,self.dirName,self.baseNames)
            
            multi_process_import(self.df,self.OriginalRoot,self.dirName,self.baseNames)
            
            for key,patient in self.OriginalRoot.patients.items():
                self.patientList.addItem(patient.name + ' - ' + key)
            
            self.modExamDates.setEnabled(True)
            self.btn_consult_recist_calcs.setEnabled(True)
            self.statusbar.showMessage('Done importing Bookmark List(s)', 1000)

        elif flag == 1:
            self.statusbar.showMessage('No Bookmark List(s) imported.',1000)
            del self.StudyRoot
            self.statusbar.clearMessage()

        self.StudyRoot = copy.deepcopy(self.OriginalRoot) #use a copy for all further computations and operations

    def genRECIST(self,signal):
        if signal == True:
            self.root_to_use = self.StudyRoot
        else:
            self.root_to_use = self.FetchRoot
        
        try:
            self.root_to_use #check if patients imported
            generate_recist_sheets(self.RECISTDir, self.OutDir, self.root_to_use, self.singleSheet.isChecked())
            self.statusbar.showMessage('Generating RECIST worksheets.',1000)
        except Exception as e:
            QMessageBox.information(self,'Message','Please import Bookmark List(s).')
            traceback.print_exc()
            print('Error: ',e)
        self.statusbar.showMessage('Done generating RECIST worksheets.', 1000)

class DatabaseUploadDialog(QDialog, uploader.Ui_databaseuploaddialog):
    def __init__(self, parent):
        super(DatabaseUploadDialog,self).__init__(parent)
        self.setupUi(self) #setup the graphing window
        
class ENABLELoginWindow(QDialog, login.Ui_logindialog):
    '''
    Login page class
    '''
    loginSignal = QtCore.pyqtSignal(bool) #indicate if user login accepted and mainwindow should load
    closeSignal = QtCore.pyqtSignal(bool) #indicate that user closed login - close entire application
    offlineSignal = QtCore.pyqtSignal(bool) #launch offline mode with limited features

    def __init__(self, parent):
        super(ENABLELoginWindow,self).__init__(parent)
        self.setupUi(self) #setup the graphing window

        self.pixmax = QtGui.QPixmap('icons/enable_icon.png')
        self.ENABLE_logo.setPixmap(self.pixmax)
        self.ENABLE_logo.show()
        self.setWindowIcon(QtGui.QIcon('icons/enable_icon.png'))
        

        self.btn_log_in.clicked.connect(self.run_login)
        self.btn_offline_mode.clicked.connect(self.run_offline_mode)
        self.count = 0

        self.show()
        
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
        super(ConfigurationPage,self).__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon('icons/configIcon.png'))     

        #set known/or initialize
        shelfFile = shelve.open('LocalPreferences')

        shelfFile['RECISTDir'] = os.path.dirname(os.path.realpath('./files/RECISTForm.docx'))
        shelfFile['LMUploader'] = os.path.dirname(os.path.realpath('./files/RadiologyImportClient.jar'))
        shelfFile['mongodb_address'] = 'mongodb://db.patients.net'
        
        try:
            self.bl_directory.setText(shelfFile['BLDir'])
            self.output_directory.setText(shelfFile['OutDir'])
            shelfFile.close()
        except Exception as e:
            #KeyError thrown if launched without the shelve files existing.
            #catch error and prevent crash since the config panel will come up and settings will be reloaded after config panel is closed.
            print(e)
            traceback.print_exc()

        self.btn_bl_directory.clicked.connect(self.bl_directory_select)
        self.btn_output_directory.clicked.connect(self.output_directory_select)
        self.btn_db_path.clicked.connect(self.set_db_address)
        self.admin_pass.textChanged.connect(self.admin_pass_check)
        
        self.show()

    def bl_directory_select(self):
        shelfFile = shelve.open('LocalPreferences')
        BLDirT = str(QFileDialog.getExistingDirectory(self, "Select Bookmark List Directory"))
        try:
            if BLDirT != '':
                shelfFile['BLDir'] = BLDirT
                self.bl_directory.setText(shelfFile['BLDir'])
            else:
                #user may have hit ESC, but on first launch this will crash ENABLE.
                self.bl_directory.setText(shelfFile['BLDir'])
        except Exception as e:
            print(e)
            traceback.print_exc()
            QMessageBox.information(self,'Message','Bookmark List Directory must be selected.')
            self.bl_directory_select()
        shelfFile.close()

    def output_directory_select(self):
        shelfFile = shelve.open('LocalPreferences')
        OutDirT = str(QFileDialog.getExistingDirectory(self, "Select Output Directory"))
        try:
            if OutDirT != '':
                shelfFile['OutDir'] = OutDirT
                self.output_directory.setText(shelfFile['OutDir'])
            else:
                #user may have hit ESC, but on first launch this will crash ENABLE.
                self.output_directory.setText(shelfFile['OutDir'])
        except Exception as e:
            print(e)
            traceback.print_exc()
            QMessageBox.information(self,'Message','Output Directory must be selected.')
            self.output_directory_select()
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

def runner():
    myappid = u'ENABLE 2.0_V1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    #create app instance and launch
    app = QApplication([])
    app.setApplicationName('ENABLE 2.0')

    form = MainWindow() #dont show yet, show after validated log-in

    app.exec_()

    me = os.getpid()
    kill_proc_tree(me)