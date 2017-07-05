#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QFileDialog, QHBoxLayout, QVBoxLayout, QTextEdit, QAction, qApp, QApplication, QWidget, QToolTip, QPushButton, QMessageBox, QDesktopWidget, QMainWindow
from PyQt5.QtGui import QIcon, QFont

from UserPrefs import getSettings
from BLImporter import fileSelect,BLImport
from RECISTComp import RECISTComp
import BLDataClasses
from RECISTGen import RECISTSheet
import shelve

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()

        self.initUI()  
        
    def initUI(self):
        #QToolTip.setFont(QFont('SansSerif',10))

        # textEdit = QTextEdit()
        # self.setCentralWidget(textEdit)

        # okButton = QPushButton("OK")
        # cancelButton = QPushButton("CANCEL")

        # hbox = QHBoxLayout()
        # hbox.addStretch(1)
        # hbox.addWidget(okButton)
        # hbox.addWidget(cancelButton)

        # vbox = QVBoxLayout()
        # vbox.addStretch(1)
        # vbox.addLayout(hbox)

        # self.setLayout(vbox)

        # self.setToolTip('This is a <b>QWidget</b> widget')
        # btn = QPushButton('Button',self)
        # btn.setToolTip('This is a <b>QPushButton</b> widget')
        # btn.resize(btn.sizeHint())
        # btn.move(50,50)

        #BLDir,RECISTDir,OutDir = getSettings() #initialize settings
        #print(BLDir,RECISTDir,OutDir)  

        self.fetchPrefs

        exitAction = QAction(QIcon('application_exit.png'), 'Exit ENABLE 2', self)
        exitAction.setStatusTip('Exit Application')
        exitAction.triggered.connect(self.closeEvent)

        openFile = QAction(QIcon('Import_A-512.png'),'Open Bookmark Lists',self)
        openFile.setStatusTip('Import Bookmark Lists')
        openFile.triggered.connect(lambda: self.showDialog(BLDir))

        configProg = QAction(QIcon('configIcon.png'), 'Configure', self)
        configProg.setStatusTip('Configure ENABLE settings')
        configProg.triggered.connect(self.configProg)

        self.toolbar = self.addToolBar('Exit')
        self.toolbar.addAction(exitAction)
        self.toolbar = self.addToolBar('Open')
        self.toolbar.addAction(openFile)
        self.toolbar = self.addToolBar('Configuration')
        self.toolbar.addAction(configProg)

        self.resize(800,600)
        self.setWindowTitle('ENABLE 2')
        self.center()
        self.setWindowIcon(QIcon('ENABLEIcon.png'))        
        self.show()

    def configProg(self):
        prefs = shelve.open('LocalPreferences')

        BLDir = str(QFileDialog.getExistingDirectory(self, "Select Bookmark List Directory"))
        if BLDir != '':
            prefs['BLDir'] = BLDir
        else:
            QMessageBox.information(self,'Message','Directory unchanged.')

        RECISTDir = str(QFileDialog.getExistingDirectory(self, "Select RECIST Template Directory"))
        if RECISTDir != '':
            prefs['RECISTDir'] = RECISTDir
        else:
            QMessageBox.information(self,'Message','Directory unchanged.')

        OutDir = str(QFileDialog.getExistingDirectory(self, "Select Output Directory"))
        if OutDir != '':
            prefs['OutDir'] = OutDir
        else:
            QMessageBox.information(self,'Message','Directory unchanged.')

        prefs.close()

    def closeEvent(self,event):
        reply = QMessageBox.question(self,'Message',"Are you sure to quit ENABLE 2?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            sys.exit() 

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def showDialog(self,BLDir):  
        dirName,baseNames,err = fileSelect(BLDir)
        if err == 1:
            QMessageBox.information(self,'Message','No Bookmark List(s) imported.')

    def fetchPrefs(self):
        BLDir,RECISTDir,OutDir = getSettings() #initialize settings
        print(BLDir,RECISTDir,OutDir)  

if __name__ == '__main__':

    app = QApplication(sys.argv) 
    BLDir,RECISTDir,OutDir = getSettings() #initialize settings
    print(BLDir,RECISTDir,OutDir)  
    ex = Example()
    sys.exit(app.exec_())  
