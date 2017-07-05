# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'selectexampage.ui'
#
# Created by: PyQt5 UI code generator 5.8.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(650, 600)
        Form.setMinimumSize(QtCore.QSize(650, 600))
        Form.setMaximumSize(QtCore.QSize(650, 600))
        self.verticalLayoutWidget = QtWidgets.QWidget(Form)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(410, 40, 201, 521))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.examList = QtWidgets.QListWidget(self.verticalLayoutWidget)
        self.examList.setObjectName("examList")
        self.verticalLayout.addWidget(self.examList)
        self.formLayoutWidget = QtWidgets.QWidget(Form)
        self.formLayoutWidget.setGeometry(QtCore.QRect(40, 410, 351, 91))
        self.formLayoutWidget.setObjectName("formLayoutWidget")
        self.formLayout = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout.setObjectName("formLayout")
        self.label_2 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.currentExamSelect = QtWidgets.QComboBox(self.formLayoutWidget)
        self.currentExamSelect.setObjectName("currentExamSelect")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.currentExamSelect)
        self.baselineExamSelect = QtWidgets.QComboBox(self.formLayoutWidget)
        self.baselineExamSelect.setObjectName("baselineExamSelect")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.baselineExamSelect)
        self.label_3 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.setExams = QtWidgets.QPushButton(self.formLayoutWidget)
        self.setExams.setObjectName("setExams")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.setExams)
        self.verticalLayoutWidget_2 = QtWidgets.QWidget(Form)
        self.verticalLayoutWidget_2.setGeometry(QtCore.QRect(40, 40, 351, 341))
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_4 = QtWidgets.QLabel(self.verticalLayoutWidget_2)
        self.label_4.setObjectName("label_4")
        self.verticalLayout_2.addWidget(self.label_4)
        self.patientList = QtWidgets.QListWidget(self.verticalLayoutWidget_2)
        self.patientList.setObjectName("patientList")
        self.verticalLayout_2.addWidget(self.patientList)
        self.returnToHome = QtWidgets.QPushButton(Form)
        self.returnToHome.setGeometry(QtCore.QRect(40, 520, 351, 41))
        self.returnToHome.setObjectName("returnToHome")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Patient Exam Selection"))
        self.label.setText(_translate("Form", "Available Exams:"))
        self.label_2.setText(_translate("Form", "Current Exam:"))
        self.label_3.setText(_translate("Form", "Baseline Exam:"))
        self.setExams.setText(_translate("Form", "Set Exams"))
        self.label_4.setText(_translate("Form", "Patient Selection (highlight patient you wish to modify):"))
        self.returnToHome.setText(_translate("Form", "Return to Home Screen"))

