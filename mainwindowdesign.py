# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.8.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_mainWindow(object):
    def setupUi(self, mainWindow):
        mainWindow.setObjectName("mainWindow")
        mainWindow.resize(700, 600)
        mainWindow.setMinimumSize(QtCore.QSize(700, 600))
        mainWindow.setMaximumSize(QtCore.QSize(700, 600))
        mainWindow.setAutoFillBackground(False)
        self.centralwidget = QtWidgets.QWidget(mainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(400, 20, 261, 531))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label.setObjectName("label")
        self.verticalLayout_2.addWidget(self.label)
        self.listWidget = QtWidgets.QListWidget(self.verticalLayoutWidget)
        self.listWidget.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.listWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.listWidget.setObjectName("listWidget")
        self.verticalLayout_2.addWidget(self.listWidget)
        self.importPatients = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.importPatients.setObjectName("importPatients")
        self.verticalLayout_2.addWidget(self.importPatients)
        self.removeSelectedPatients = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.removeSelectedPatients.setObjectName("removeSelectedPatients")
        self.verticalLayout_2.addWidget(self.removeSelectedPatients)
        self.clearPatients = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.clearPatients.setObjectName("clearPatients")
        self.verticalLayout_2.addWidget(self.clearPatients)
        self.verticalLayoutWidget_2 = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_2.setGeometry(QtCore.QRect(49, 19, 231, 151))
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.modExamDates = QtWidgets.QPushButton(self.verticalLayoutWidget_2)
        self.modExamDates.setObjectName("modExamDates")
        self.verticalLayout_3.addWidget(self.modExamDates)
        self.generateRECIST = QtWidgets.QPushButton(self.verticalLayoutWidget_2)
        self.generateRECIST.setObjectName("generateRECIST")
        self.verticalLayout_3.addWidget(self.generateRECIST)
        self.verticalLayoutWidget.raise_()
        self.verticalLayoutWidget_2.raise_()
        mainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(mainWindow)
        self.statusbar.setObjectName("statusbar")
        mainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(mainWindow)
        QtCore.QMetaObject.connectSlotsByName(mainWindow)

    def retranslateUi(self, mainWindow):
        _translate = QtCore.QCoreApplication.translate
        mainWindow.setWindowTitle(_translate("mainWindow", "ENABLE 2.0"))
        self.label.setText(_translate("mainWindow", "Patient bookmark list(s) imported:"))
        self.importPatients.setText(_translate("mainWindow", "Import Bookmark List(s)"))
        self.removeSelectedPatients.setText(_translate("mainWindow", "Remove highlighted patient(s)"))
        self.clearPatients.setText(_translate("mainWindow", "Remove All Patients"))
        self.modExamDates.setText(_translate("mainWindow", "Specify Exams (optional)"))
        self.generateRECIST.setText(_translate("mainWindow", "Generate RECIST Worksheets"))

